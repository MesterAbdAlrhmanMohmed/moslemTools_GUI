import guiTools, requests, json, os, gui, functions, subprocess, shutil, winsound
from guiTools import TextViewer
from guiTools import speak
from guiTools.QCustomListDialog import QCustomListDialog
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    cancelled = qt2.pyqtSignal()
    def __init__(self, parent, url, filepath):
        super().__init__(parent)
        self.url = url
        self.filepath = filepath
        self.is_cancelled = False
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            with open(self.filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if self.is_cancelled:
                        self.cancelled.emit()
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percent)
            self.finished.emit()
        except Exception as e:
            print(f"Error during download or file writing: {e}")
            self.cancelled.emit()
    def cancel(self):
        self.is_cancelled = True
class MergeThread(qt2.QThread):
    finished = qt2.pyqtSignal(bool, str)
    def __init__(self, parent, ffmpeg_path, input_files, output_file):
        super().__init__(parent)
        self.ffmpeg_path = ffmpeg_path
        self.input_files = input_files
        self.output_file = output_file
        self.process = None
    def run(self):
        list_filepath = os.path.join(os.path.dirname(self.output_file), "mergelist.txt")
        try:
            with open(list_filepath, 'w', encoding='utf-8') as f:
                for file_path in self.input_files:
                    safe_path = file_path.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")
            command = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_filepath, "-ar", "44100", "-ac", "2", "-b:a", "192k", self.output_file]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = self.process.communicate()
            if self.process.returncode == 0:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"فشل الدمج أو تم إلغاؤه.\n{stderr}")
        except Exception as e:
            self.finished.emit(False, f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if os.path.exists(list_filepath):
                os.remove(list_filepath)
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
class StoryPlayer(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج القصص لن تعمل.")
        qt1.QShortcut("ctrl+s", self).activated.connect(lambda: self.mp.stop())
        qt1.QShortcut("space", self).activated.connect(self.play)
        qt1.QShortcut("alt+right", self).activated.connect(self.seek_forward_5s)
        qt1.QShortcut("alt+left", self).activated.connect(self.seek_backward_5s)
        qt1.QShortcut("alt+up", self).activated.connect(self.seek_forward_10s)
        qt1.QShortcut("alt+down", self).activated.connect(self.seek_backward_10s)
        qt1.QShortcut("ctrl+right", self).activated.connect(self.seek_forward_30s)
        qt1.QShortcut("ctrl+left", self).activated.connect(self.seek_backward_30s)
        qt1.QShortcut("ctrl+up", self).activated.connect(self.seek_forward_60s)
        qt1.QShortcut("ctrl+down", self).activated.connect(self.seek_backward_60s)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("shift+up", self).activated.connect(self.increase_volume)
        qt1.QShortcut("shift+down", self).activated.connect(self.decrease_volume)
        self.volume_timer = qt2.QTimer(self)
        self.volume_timer.setSingleShot(True)
        self.volume_timer.timeout.connect(self.restore_duration_text)
        self.merge_list = []
        self.download_batch_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.is_downloading_batch = False
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.successfully_downloaded_in_batch = []
        self.full_batch_cancellation_requested = False
        self.excluded_surahs_in_batch = []
        self.first_merge_selection_index = None
        self.first_download_selection_index = None
        self.batch_download_target = 'app'
        self.download_thread = None
        self.is_loaded = False
        self.categories_data = {}
        self.categoriesLabel = qt.QLabel("إختيار فئة")
        self.categoriesLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.categorySearchLabel = qt.QLabel("ابحث عن فئة")
        self.categorySearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.categorySearchLabel.setVisible(False)
        self.categorySearchEdit = qt.QLineEdit()
        self.categorySearchEdit.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.categorySearchEdit.setAccessibleName("ابحث عن فئة")
        self.categorySearchEdit.setObjectName("categorySearch")
        self.categorySearchEdit.setVisible(False)
        self.categoriesListWidget = guiTools.QListWidget()
        self.categoriesListWidget.setSpacing(3)
        self.categoriesListWidget.itemSelectionChanged.connect(self.on_category_selected)
        self.storiesLabel = qt.QLabel("القصص")
        self.storiesLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.storySearchLabel = qt.QLabel("ابحث عن قصة")
        self.storySearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.storySearchEdit = qt.QLineEdit()
        self.storySearchEdit.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.storySearchEdit.setAccessibleName("ابحث عن قصة")
        self.storySearchEdit.setObjectName("storySearch")
        self.storyListWidget = guiTools.QListWidget()
        self.storyListWidget.setSpacing(3)
        self.storyListWidget.clicked.connect(self.play_selected_audio)
        self.storySearchEdit.textChanged.connect(self.story_onsearch)
        self.progressBar = qt.QProgressBar()
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progressBar.setVisible(False)
        self.cancel_download_button = guiTools.QPushButton("إلغاء التنزيل")
        self.cancel_download_button.setShortcut("ctrl+c")
        self.cancel_download_button.setAccessibleDescription("control plus c")
        self.cancel_download_button.setVisible(False)
        self.cancel_download_button.clicked.connect(self.cancel_current_download)
        self.cancel_download_button.setStyleSheet("QPushButton {background-color: #8B0000;color: white;border: none;padding: 5px 10px;border-radius: 5px;}QPushButton:hover {background-color: #A52A2A;}")
        self.mp = QMediaPlayer()
        self.au = QAudioOutput()
        self.mp.setAudioOutput(self.au)
        self.openBookmarks = guiTools.QPushButton("العلامات المرجعية")
        self.openBookmarks.clicked.connect(self.onBookmarkOpened)
        self.openBookmarks.setShortcut("ctrl+shift+b")
        self.openBookmarks.setAccessibleDescription("control plus shift plus b")
        self.openBookmarks.setFixedSize(150, 40)
        self.User_guide=guiTools.QPushButton("دليل الاختصارات")
        self.User_guide.setFixedSize(150, 40)
        self.User_guide.setShortcut("ctrl+f1")
        self.User_guide.setAccessibleDescription("control plus f1")
        self.User_guide.clicked.connect(lambda:TextViewer(self,"دليل الاختصارات","ctrl+s: إيقاف\nspace: التشغيل والإيقاف المؤقت\nalt زائد السهم الأيمن: التقديم السريع لمدة 5 ثواني\nalt زائد السهم الأيسر: الترجيع السريع لمدة 5 ثواني\nalt زائد السهم الأعلى: التقديم السريع لمدة 10 ثواني\nalt زائد السهم الأسفل: الترجيع السريع لمدة 10 ثواني\nctrl زائد السهم الأيمن: التقديم السريع لمدة 30 ثانية\nctrl زائد السهم الأيسر: الترجيع السريع لمدة 30 ثانية\nctrl زائد السهم الأعلى: التقديم السريع لمدة دقيقة\nctrl زائد السهم الأسفل: الترجيع  السريع لمدة دقيقة\nctrl زائد رقم: الانتقال الى موضع محدد من المقطع, مثلا ctrl+10 الانتقال الى 10% من المقطع\nshift زائد السهم الأعلى: رفع الصوت\nshift زائد السهم الأسفل: خفض الصوت\nالضغط على زر التطبيقات أو click الأيمن على شريط مدة المقطع يسمح بإضافة علامة مرجعية للموضع الحالي").exec())
        self.play_all_to_end= guiTools.QPushButton("تشغيل كل القصص من القصة المحددة الى النهاية")
        self.play_all_to_end.setAccessibleDescription("control plus A")
        self.play_all_to_end.setCheckable(True)
        self.play_all_to_end.setShortcut("ctrl+a")
        self.play_all_to_end.toggled.connect(lambda checked: self.update_button_style(self.play_all_to_end, checked))
        self.play_all_to_end.toggled.connect(self.handle_play_all_toggled)
        self.repeat_story_button = guiTools.QPushButton("تكرار تشغيل القصة المحددة")
        self.repeat_story_button.setAccessibleDescription("control plus R")
        self.repeat_story_button.setCheckable(True)
        self.repeat_story_button.setShortcut("ctrl+r")
        self.repeat_story_button.toggled.connect(lambda checked: self.update_button_style(self.repeat_story_button, checked))
        self.repeat_story_button.toggled.connect(self.handle_repeat_toggled)
        self.repeat_story_button.setEnabled(False)
        self.Slider = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Slider.setAccessibleName("التحكم في تقدم القصة")
        self.Slider.setRange(0, 100)
        self.Slider.setTracking(True)
        self.Slider.valueChanged.connect(self.set_position_from_slider)
        self.Slider.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.Slider.customContextMenuRequested.connect(self.onAddNewBookmark)
        self.mp.durationChanged.connect(self.update_slider)
        self.mp.positionChanged.connect(self.update_slider)
        self.duration = qt.QLabel()
        self.duration.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.duration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.mp.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.dl_all_app = guiTools.QPushButton("تحميل جميع القصص المتاحة لهذه الفئة في التطبيق")
        self.dl_all_app.clicked.connect(self.download_all_audios_to_app)
        self.dl_all = guiTools.QPushButton("تحميل جميع القصص المتاحة لهذه الفئة في الجهاز")
        self.dl_all.clicked.connect(self.download_all_stories)
        self.delete = guiTools.QPushButton("حذف كل القصص للفئة الحالية من التطبيق")
        self.delete.setStyleSheet("background-color: #8B0000; color: white;")
        self.delete.setVisible(False)
        self.delete.clicked.connect(lambda: self.delete_story())
        self.info_menu = qt.QLabel("لخيارات القصة، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info_menu.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_menu.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_feedback_label.setVisible(False)
        self.batch_download_feedback_label = qt.QLabel()
        self.batch_download_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.batch_download_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.batch_download_feedback_label.setVisible(False)
        self.merge_action_button = guiTools.QPushButton("بدء دمج القصص المحددة")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        self.merge_action_button.setVisible(False)
        self.batch_download_action_button = guiTools.QPushButton("بدء تحميل القصص المحددة")
        self.batch_download_action_button.clicked.connect(self.handle_batch_download_action)
        self.batch_download_action_button.setVisible(False)
        self.merge_all_button = guiTools.QPushButton("دمج كل قصص الفئة")
        self.merge_all_button.clicked.connect(self.prepare_merge_all)
        self.merge_all_button.setVisible(True)
        categoriesLayout = qt.QVBoxLayout()
        categoriesLayout.addWidget(self.categoriesLabel)
        categoriesLayout.addWidget(self.categorySearchLabel)
        categoriesLayout.addWidget(self.categorySearchEdit)
        categoriesLayout.addWidget(self.categoriesListWidget)
        storiesLayout = qt.QVBoxLayout()
        storiesLayout.addWidget(self.storiesLabel)
        storiesLayout.addWidget(self.storySearchLabel)
        storiesLayout.addWidget(self.storySearchEdit)
        storiesLayout.addWidget(self.storyListWidget)
        storiesLayout.addWidget(self.info_menu)
        storiesLayout.addWidget(self.merge_feedback_label)
        storiesLayout.addWidget(self.batch_download_feedback_label)
        merge_buttons_layout = qt.QVBoxLayout()
        merge_buttons_layout.addWidget(self.merge_action_button)
        merge_buttons_layout.addWidget(self.batch_download_action_button)
        merge_buttons_layout.addWidget(self.merge_all_button)
        storiesLayout.addLayout(merge_buttons_layout)
        topLayout = qt.QHBoxLayout()
        topLayout.addLayout(categoriesLayout)
        topLayout.addLayout(storiesLayout)
        download_buttons_layout = qt.QHBoxLayout()
        download_buttons_layout.addWidget(self.dl_all_app)
        download_buttons_layout.addWidget(self.delete)
        download_buttons_layout.addWidget(self.dl_all)
        layout = qt.QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addLayout(download_buttons_layout)
        layout.addWidget(self.Slider)
        progress_cancel_layout = qt.QHBoxLayout()
        progress_cancel_layout.addWidget(self.cancel_download_button)
        progress_cancel_layout.addWidget(self.progressBar)
        layout.addLayout(progress_cancel_layout)
        playback_buttons_layout = qt.QHBoxLayout()
        playback_buttons_layout.addWidget(self.play_all_to_end)
        playback_buttons_layout.addWidget(self.repeat_story_button)
        layout.addLayout(playback_buttons_layout)
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.User_guide)
        layout1.addWidget(self.duration)
        layout1.addWidget(self.openBookmarks)
        layout.addLayout(layout1)
        self.setLayout(layout)
        self.storyListWidget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.storyListWidget.customContextMenuRequested.connect(self.open_context_menu)
        self.cleanup_pending_deletions()
    def showEvent(self, event):
        if not self.is_loaded:
            self.load_data()
            self.is_loaded = True
        super().showEvent(event)
    def load_data(self):
        self.categories_data = self.load_categories()
        self.categoriesList = list(self.categories_data.keys())
        self.categoriesList.sort()
        self.categoriesListWidget.addItems(self.categoriesList)
        if self.categoriesListWidget.count() > 0:
            self.categoriesListWidget.setCurrentRow(0)
            self.on_category_selected()
    def check_media_loaded(self):
        if self.mp.duration() <= 0:
            speak("لا توجد قصة مُشَغَّلَة حالياً")
            return False
        return True
    def check_if_busy(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None and self.download_thread.isRunning():
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "هناك عملية تحميل جارية بالفعل. الرجاء الانتظار حتى تنتهي أو قم بإلغائها.")
            return True
        if hasattr(self, 'merge_thread') and self.merge_thread is not None and self.merge_thread.isRunning():
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "هناك عملية دمج جارية بالفعل. الرجاء الانتظار.")
            return True
        return False
    def seek_forward_5s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() + 5000)
    def seek_backward_5s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() - 5000)
    def seek_forward_10s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() + 10000)
    def seek_backward_10s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() - 10000)
    def seek_forward_30s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() + 30000)
    def seek_backward_30s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() - 30000)
    def seek_forward_60s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() + 60000)
    def seek_backward_60s(self):
        if not self.check_media_loaded():
            return
        self.mp.setPosition(self.mp.position() - 60000)
    def handle_merge_action(self):
        if self.is_merging:
            self.confirm_and_cancel_merge()
        else:
            self.prepare_merge()
    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
    def add_to_merge_list(self):
        selected_category_item = self.categoriesListWidget.currentItem()
        selected_story_item = self.storyListWidget.currentItem()
        if not selected_category_item or not selected_story_item:
            return
        category = selected_category_item.text()
        story = selected_story_item.text()
        story_info = {"category": category, "story": story, "url": self.categories_data[category][story]}
        self.merge_list.append(story_info)
        self.update_merge_ui()
        self.update_download_batch_ui()
    def remove_from_merge_list(self):
        if not self.merge_list:
            return
        num_items = len(self.merge_list)
        item_names = [f"{i+1}: {item['story']}" for i, item in enumerate(self.merge_list)]
        selected_item_str, ok = QCustomListDialog.getItem(self, "إزالة قصة", "اختر القصة لإزالتها:", item_names)
        if ok and selected_item_str:
            index_to_remove = int(selected_item_str.split(':')[0]) - 1
            if 0 <= index_to_remove < num_items:
                del self.merge_list[index_to_remove]
                self.update_merge_ui()
                self.update_download_batch_ui()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرقم المدخل خارج النطاق الصحيح.")
    def update_merge_ui(self):
        count = len(self.merge_list)
        is_merging_selected = count > 0
        if count > 0:
            self.merge_feedback_label.setText(f"تم تحديد {count} قصة للدمج.")
            self.merge_feedback_label.setVisible(True)
        else:
            self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setVisible(count >= 2)
        self.merge_all_button.setVisible(not is_merging_selected)
        self.batch_download_action_button.setEnabled(not is_merging_selected)
        self.dl_all_app.setEnabled(not is_merging_selected)
    def cancel_merge(self):
        self.merge_list.clear()
        self.update_merge_ui()
        self.update_download_batch_ui()
    def set_as_merge_start(self):
        self.cancel_download_batch()
        self.cancel_download_start()
        self.first_merge_selection_index = self.storyListWidget.currentRow()
        speak(f"تم تحديد {self.storyListWidget.currentItem().text()} كبداية للدمج")
    def cancel_merge_start(self):
        self.first_merge_selection_index = None
        speak("تم إلغاء تحديد بداية الدمج")
    def merge_from_start_to_here(self):
        if self.first_merge_selection_index is None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء تحديد بداية الدمج أولاً.")
            return
        end_index = self.storyListWidget.currentRow()
        start_index = self.first_merge_selection_index
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.merge_list.clear()
        category = self.categoriesListWidget.currentItem().text()
        for i in range(start_index, end_index + 1):
            story_item = self.storyListWidget.item(i)
            if story_item:
                story = story_item.text()
                story_info = {"category": category, "story": story, "url": self.categories_data[category][story]}
                self.merge_list.append(story_info)
        self.first_merge_selection_index = None
        if len(self.merge_list) < 1:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم تحديد أي قصص للدمج.")
            return
        speak(f"سيتم دمج {len(self.merge_list)} قصة")
        self.prepare_merge(is_all=True)
    def set_as_download_start(self, target='app'):
        self.cancel_merge()
        self.cancel_merge_start()
        if self.download_batch_list and self.batch_download_target != target:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك تغيير وجهة التحميل أثناء وجود قائمة نشطة لـ {self.batch_download_target}. قم بإلغاء القائمة الحالية أولاً.")
             return
        self.batch_download_target = target
        self.first_download_selection_index = self.storyListWidget.currentRow()
        speak(f"تم تحديد {self.storyListWidget.currentItem().text()} كبداية للتحميل")
    def cancel_download_start(self):
        self.first_download_selection_index = None
        speak("تم إلغاء تحديد بداية التحميل")
    def download_from_start_to_here(self, target='app'):
        if self.first_download_selection_index is None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء تحديد بداية التحميل أولاً.")
            return
        if self.download_batch_list and self.batch_download_target != target:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك تغيير وجهة التحميل أثناء وجود قائمة نشطة لـ {self.batch_download_target}. قم بإلغاء القائمة الحالية أولاً.")
             return
        self.batch_download_target = target
        end_index = self.storyListWidget.currentRow()
        start_index = self.first_download_selection_index
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.download_batch_list.clear()
        category = self.categoriesListWidget.currentItem().text()
        for i in range(start_index, end_index + 1):
            story_item = self.storyListWidget.item(i)
            if story_item:
                story = story_item.text()
                if target == 'app':
                    local_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story}.mp3")
                    if os.path.exists(local_path):
                        continue
                story_info = {"category": category, "story": story, "url": self.categories_data[category][story]}
                self.download_batch_list.append(story_info)
        self.first_download_selection_index = None
        if not self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", "جميع القصص في النطاق المحدد محملة بالفعل.")
            return
        self.prepare_batch_download()
    def prepare_merge_all(self):
        if not self.categoriesListWidget.currentItem():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء اختيار فئة أولاً.")
            return
        self.merge_list.clear()
        category = self.categoriesListWidget.currentItem().text()
        story_list = self.categories_data[category].items()
        for story, url in story_list:
            self.merge_list.append({"category": category, "story": story, "url": url})
        self.prepare_merge(is_all=True)
    def prepare_merge(self, is_all=False):
        if self.check_if_busy(): return
        if len(self.merge_list) < 2 and not is_all:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يجب تحديد قصتين على الأقل للدمج.")
            return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return
        urls_to_download = []
        for item in self.merge_list:
            category = item["category"]
            story = item["story"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story}.mp3")
            if not os.path.exists(local_path):
                urls_to_download.append(item["url"])
        num_files_to_download = len(urls_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} قصة غير موجودة.\n\nسيتم الآن تحميل ودمج الملفات المحددة على مرحلتين:\nمرحلة التحميل: سيتم تحميل الملفات تباعًا. في هذه الأثناء، لا يمكنك إلغاء تحميل أي قصة.\nمرحلة الدمج: بعد انتهاء التحميل، لن تتمكن من استخدام الواجهة إلا لإلغاء عملية الدمج بأكملها.\n\nهل تريد المتابعة؟")
        else:
            confirm_message = ("جميع القصص المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة باستثناء زر إلغاء الدمج.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            if is_all:
                self.cancel_merge()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            if is_all:
                self.cancel_merge()
            return
        self.set_ui_for_merge_download(False)
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.process_next_in_merge_queue()
    def process_next_in_merge_queue(self):
        output_dir = os.path.dirname(self.current_merge_output_path)
        next_item_to_download = None
        for item in self.merge_list:
            category = item["category"]
            story = item["story"]
            url = item["url"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story}.mp3")
            if os.path.exists(local_path):
                continue
            if url in self.completed_merge_downloads:
                continue
            next_item_to_download = item
            break
        if next_item_to_download:
            self.progressBar.setVisible(True)
            self.cancel_download_button.setVisible(False)
            url = next_item_to_download['url']
            category = next_item_to_download['category']
            story = next_item_to_download['story']
            safe_story_name = "".join(c for c in story if c.isalnum() or c in (' ', '_')).rstrip()
            download_path = os.path.join(output_dir, f"{category}_{safe_story_name}.mp3")
            self.current_download_url = url
            self.merge_feedback_label.setVisible(True)
            self.merge_feedback_label.setText(f"جاري تحميل: {category} - {story} ({len(self.completed_merge_downloads) + 1} من {len([item for item in self.merge_list if not os.path.exists(os.path.join(os.getenv('appdata'), app.appName, 'stories', item['category'], item['story'] + '.mp3'))])} ملف)")
            self.download_thread = DownloadThread(self, url, download_path)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.finalize_and_execute_merge()
    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()
    def finalize_and_execute_merge(self):
        self.set_ui_for_merge_download(True)
        files_for_ffmpeg = []
        self.files_to_delete_after_merge.clear()
        output_dir = os.path.dirname(self.current_merge_output_path)
        for item in self.merge_list:
            category, story, url = item["category"], item["story"], item["url"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story}.mp3")
            if os.path.exists(local_path):
                files_for_ffmpeg.append(local_path)
            else:
                safe_story_name = "".join(c for c in story if c.isalnum() or c in (' ', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"{category}_{safe_story_name}.mp3")
                files_for_ffmpeg.append(temp_path)
                if temp_path not in self.files_to_delete_after_merge:
                    self.files_to_delete_after_merge.append(temp_path)
        if not files_for_ffmpeg:
             guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على أي ملفات للدمج.")
             self.cancel_merge()
             return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)
    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.cancellation_requested = False
        self.set_ui_enabled(False)
        self.merge_feedback_label.setEnabled(True)
        count = len(self.merge_list)
        self.merge_feedback_label.setText(f"جاري دمج {count} قصص...")
        self.merge_feedback_label.setVisible(True)
        self.merge_action_button.setVisible(True)
        self.merge_action_button.setEnabled(True)
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
        self.merge_thread = MergeThread(self, self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()
    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.set_ui_enabled(True)
        self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setText("بدء دمج القصص المحددة")
        self.merge_action_button.setStyleSheet("")
        self.update_merge_ui()
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                os.remove(self.current_merge_output_path)
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف القصص الفردية التي تم تحميلها لهذه العملية الملغاة؟", "نعم", "لا")
                if reply == 0:
                    for f_path in self.files_to_delete_after_merge:
                        if os.path.exists(f_path):
                            try: os.remove(f_path)
                            except: pass
        elif success:
            merged_files_names = [f" {item['story']}" for item in self.merge_list]
            details = "\n".join(merged_files_names)
            success_message = f"تم دمج القصص بنجاح:\n{details}"
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", success_message)
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف القصص الفردية التي تم تحميلها للدمج؟", "نعم", "لا")
                if reply == 0:
                    for f_path in self.files_to_delete_after_merge:
                        if os.path.exists(f_path):
                            try: os.remove(f_path)
                            except: pass
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        self.cancellation_requested = False
        self.cancel_merge()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
    def handle_batch_download_action(self):
        if self.is_downloading_batch:
            self.full_batch_cancellation_requested = True
            self.cancel_current_download()
        else:
            self.prepare_batch_download()
    def add_to_download_batch(self, target='app'):
        selected_category_item = self.categoriesListWidget.currentItem()
        selected_story_item = self.storyListWidget.currentItem()
        if not selected_category_item or not selected_story_item:
            return
        category = selected_category_item.text()
        story = selected_story_item.text()
        if self.download_batch_list:
            if self.download_batch_list[0]["category"] != category:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لا يمكنك إضافة قصص من فئات مختلفة في دفعة واحدة. سيتم إلغاء الدفعة السابقة.")
                self.cancel_download_batch()
            elif self.batch_download_target != target:
                 guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك إضافة قصص لـ {target} لأن القائمة الحالية مخصصة لـ {self.batch_download_target}. يرجى إنهاء القائمة الحالية أو إلغاؤها أولاً.")
                 return
        self.batch_download_target = target
        if target == 'app':
            local_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story}.mp3")
            if os.path.exists(local_path):
                guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", f"قصة '{story}' تم تحميلها بالفعل.")
                return
        story_info = {"category": category, "story": story, "url": self.categories_data[category][story]}
        if story_info in self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", "تم إضافة هذه القصة إلى القائمة بالفعل.")
            return
        self.download_batch_list.append(story_info)
        self.update_download_batch_ui()
        self.update_merge_ui()
    def remove_from_download_batch(self):
        if not self.download_batch_list:
            return
        num_items = len(self.download_batch_list)
        item_names = [f"{i+1}: {item['story']}" for i, item in enumerate(self.download_batch_list)]
        selected_item_str, ok = QCustomListDialog.getItem(self, "إزالة قصة", "اختر القصة لإزالتها من قائمة التحميل:", item_names)
        if ok and selected_item_str:
            index_to_remove = int(selected_item_str.split(':')[0]) - 1
            if 0 <= index_to_remove < num_items:
                del self.download_batch_list[index_to_remove]
                self.update_download_batch_ui()
                self.update_merge_ui()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرقم المدخل خارج النطاق الصحيح.")
    def format_surah_count(self, count):
        if count == 1:
            return "قصة واحدة"
        elif count == 2:
            return "قصتين"
        elif count >= 3 and count <= 10:
            return f"{count} قصص"
        else:
            return f"{count} قصة"
    def update_download_batch_ui(self):
        count = len(self.download_batch_list)
        excluded_count = len(self.excluded_surahs_in_batch)
        if count > 0:
            target_str = 'تطبيق' if self.batch_download_target == 'app' else 'جهاز'
            message = f"تم تحديد {self.format_surah_count(count)} للتحميل ({target_str})."
            if excluded_count > 0:
                message += f" وتم استثناء {self.format_surah_count(excluded_count)}."
            self.batch_download_feedback_label.setText(message)
            self.batch_download_feedback_label.setVisible(True)
        else:
            self.batch_download_feedback_label.setVisible(False)
        self.batch_download_action_button.setVisible(count > 0)
        if self.is_downloading_batch:
            self.batch_download_action_button.setText("إلغاء تحميل الدفعة")
            self.batch_download_action_button.setStyleSheet("background-color: #8B0000; color: white;")
        else:
            self.batch_download_action_button.setText("بدء تحميل القصص المحددة")
            self.batch_download_action_button.setStyleSheet("")
            self.excluded_surahs_in_batch.clear()
        is_batching = count > 0
        self.merge_action_button.setEnabled(not is_batching)
        self.merge_all_button.setEnabled(not is_batching)
        self.dl_all_app.setEnabled(not is_batching)
    def cancel_download_batch(self):
        if self.is_downloading_batch:
            return
        self.download_batch_list.clear()
        self.excluded_surahs_in_batch.clear()
        self.batch_download_feedback_label.setVisible(False)
        self.batch_download_action_button.setVisible(False)
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.update_download_batch_ui()
        self.update_merge_ui()
    def prepare_batch_download(self):
        if self.check_if_busy(): return
        if not self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لم يتم تحديد أي قصص للتحميل.")
            return
        count = len(self.download_batch_list)
        surah_names = "\n".join([item["story"] for item in self.download_batch_list])
        if count == 1:
            intro_text = "سيتم تحميل قصة واحدة وهي:"
        elif count == 2:
            intro_text = "سيتم تحميل قصتين وهما:"
        else:
            intro_text = f"سيتم تحميل {self.format_surah_count(count)} وهم:"
        confirm_message = (f"{intro_text}\n{surah_names}\n\nيمكنك إلغاء أي قصة أثناء التحميل وسيكمل تحميل الباقي.")
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", confirm_message, "نعم", "لا")
        if response != 0:
            self.cancel_download_batch()
            return
        self.successfully_downloaded_in_batch.clear()
        category = self.download_batch_list[0]["category"]
        if self.batch_download_target == 'app':
            app_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
            os.makedirs(app_folder, exist_ok=True)
            self.save_folder = app_folder
        else:
            save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ القصص")
            if not save_folder:
                self.cancel_download_batch()
                return
            self.save_folder = save_folder
        self.files_to_download = []
        for item in self.download_batch_list:
            self.files_to_download.append( (item["story"], item["url"]) )
        self.current_file_index = 0
        self.is_downloading_batch = True
        self.set_ui_for_batch_download(False)
        self.merge_action_button.setVisible(False)
        self.merge_all_button.setVisible(False)
        self.merge_feedback_label.setVisible(False)
        self.update_download_batch_ui()
        self.cancel_download_button.setVisible(True)
        self.current_download_category = category
        self.info_menu.setEnabled(False)
        self.duration.setEnabled(False)
        self.download_next_audio_to_app()
    def set_ui_for_batch_download(self, enabled):
        widgets_to_toggle = [
            self.categoriesListWidget, self.storyListWidget,
            self.storySearchEdit, self.storySearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.repeat_story_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_action_button, self.merge_all_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        if not enabled:
            self.batch_download_action_button.setEnabled(True)
    def set_ui_enabled(self, enabled):
        widgets_to_toggle = [
            self.categoriesListWidget, self.storyListWidget,
            self.storySearchEdit, self.storySearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.repeat_story_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_button, self.categoriesLabel, self.storiesLabel,
            self.duration, self.info_menu,
            self.merge_feedback_label,
            self.batch_download_action_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        if not enabled:
            self.merge_action_button.setEnabled(True)
    def set_ui_for_merge_download(self, enabled):
        widgets_to_toggle = [
            self.categoriesListWidget, self.storyListWidget,
            self.categorySearchEdit, self.storySearchEdit,
            self.categorySearchLabel, self.storySearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.repeat_story_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_button, self.categoriesLabel, self.storiesLabel,
            self.duration, self.info_menu,
            self.merge_action_button,
            self.batch_download_action_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        self.progressBar.setVisible(not enabled)
        self.cancel_download_button.setVisible(False)
        self.merge_feedback_label.setEnabled(True)
    def cleanup_pending_deletions(self):
        stories_dir = os.path.join(os.getenv('appdata'), app.appName, "stories")
        if os.path.exists(stories_dir):
            for root, _, files in os.walk(stories_dir):
                for file in files:
                    if file.endswith(".delete_me"):
                        filepath = os.path.join(root, file)
                        try:
                            os.remove(filepath)
                            print(f"Cleaned up deleted file: {filepath}")
                        except Exception as e:
                            print(f"Could not delete {filepath} on startup: {e}")
    def update_button_style(self, button, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
        else:
            button.setStyleSheet("")
    def handle_play_all_toggled(self, checked):
        self.mp.stop()
        if checked:
            self.repeat_story_button.setEnabled(False)
            if self.storyListWidget.currentRow() == -1 and self.storyListWidget.count() > 0:
                self.storyListWidget.setCurrentRow(0)
            if self.mp.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.play_selected_audio()
        else:
            self.repeat_story_button.setEnabled(True)
    def handle_repeat_toggled(self, checked):
        if checked:
            if not self.check_media_loaded():
                self.repeat_story_button.setChecked(False)
                return
            self.play_all_to_end.setEnabled(False)
        else:
            self.play_all_to_end.setEnabled(True)
    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_story_button.isChecked():
                self.mp.setPosition(0)
                self.play_selected_audio()
            elif self.play_all_to_end.isChecked():
                self.play_next_in_list()
    def play_next_in_list(self):
        current_row = self.storyListWidget.currentRow()
        if current_row < self.storyListWidget.count() - 1:
            self.storyListWidget.setCurrentRow(current_row + 1)
            self.play_selected_audio()
        else:
            self.play_all_to_end.setChecked(False)
    def delete_story(self, story_name=None):
        selected_category_item = self.categoriesListWidget.currentItem()
        if not selected_category_item:
            return
        category = selected_category_item.text()
        category_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
        try:
            if story_name:
                story_path = os.path.join(category_folder, f"{story_name}.mp3")
                if os.path.exists(story_path):
                    confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف القصة المحددة؟", "نعم", "لا")
                    if confirm == 0:
                        try:
                            os.remove(story_path)
                            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف القصة بنجاح.")
                        except PermissionError:
                            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف القصة. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
            else:
                if os.path.exists(category_folder):
                    confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف جميع القصص؟", "نعم", "لا")
                    if confirm == 0:
                        for file in os.listdir(category_folder):
                            if file.endswith(".mp3"):
                                try:
                                    os.remove(os.path.join(category_folder, file))
                                except PermissionError:
                                    guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف بعض الملفات. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف جميع القصص بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ غير متوقع", str(e))
        self.check_all_stories_downloaded()
    def check_all_stories_downloaded(self):
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            category = selected_category_item.text()
            category_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
            if os.path.exists(category_folder):
                all_files = os.listdir(category_folder)
                all_stories = self.categories_data.get(category, {}).keys()
                downloaded_stories = {os.path.splitext(file)[0] for file in all_files if file.endswith(".mp3")}
                if downloaded_stories >= set(all_stories):
                    self.delete.setVisible(True)
                    self.dl_all_app.setVisible(False)
                else:
                    self.delete.setVisible(False)
                    self.dl_all_app.setVisible(True)
            else:
                self.delete.setVisible(False)
                self.dl_all_app.setVisible(True)
    def check_current_story_downloaded(self):
        selected_category_item = self.categoriesListWidget.currentItem()
        if not selected_category_item:
            return
        category = selected_category_item.text()
        selected_item = self.storyListWidget.currentItem()
        if not selected_item:
            return
        story_name = selected_item.text()
        story_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story_name}.mp3")
        if os.path.exists(story_path):
            action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("حذف القصة المحددة من التطبيق")
            btn.setStyleSheet("background-color: #8B0000; color: white;")
            btn.clicked.connect(lambda: self.delete_story(story_name))
            action.setDefaultWidget(btn)
            return action
        return None
    def download_selected_audio_to_app(self):
        if self.check_if_busy(): return
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storyListWidget.currentItem()
            if selected_item:
                url = self.categories_data[category][selected_item.text()]
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
                os.makedirs(audio_folder, exist_ok=True)
                filepath = os.path.join(audio_folder, f"{selected_item.text()}.mp3")
                if self.is_audio_downloaded(filepath):
                    guiTools.qMessageBox.MessageBox.view(self, "تنبيه", f"قصة '{selected_item.text()}' محملة بالفعل.")
                    return
                self.set_ui_enabled(False)
                self.progressBar.setVisible(True)
                self.cancel_download_button.setVisible(True)
                self.current_download_filename = selected_item.text()
                self.current_download_category = category
                self.download_thread = DownloadThread(self, url, filepath)
                self.download_thread.progress.connect(self.progressBar.setValue)
                self.download_thread.finished.connect(self.download_audio_complete)
                self.download_thread.cancelled.connect(self.on_download_cancelled)
                self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تحميل المقطع: " + str(e))
            self.set_ui_enabled(True)
            self.cancel_download_button.setVisible(False)
    def download_all_audios_to_app(self):
        if self.check_if_busy(): return
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            self.files_to_download = [
                (file_name, url)
                for file_name, url in self.categories_data.get(category, {}).items()
                if not self.is_audio_downloaded(
                    os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{file_name}.mp3")
                )
            ]
            self.current_file_index = 0
            if not self.files_to_download:
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "جميع القصص محملة بالفعل")
                return
            response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", "هل تريد تحميل جميع القصص المتاحة لهذه الفئة؟", "نعم", "لا")
            if response == 0:
                self.successfully_downloaded_in_batch.clear()
                self.excluded_surahs_in_batch.clear()
                app_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
                os.makedirs(app_folder, exist_ok=True)
                self.save_folder = app_folder
                self.set_ui_for_batch_download(False)
                self.cancel_download_button.setVisible(True)
                self.current_download_category = category
                self.info_menu.setEnabled(False)
                self.duration.setEnabled(False)
                self.download_next_audio_to_app()
            else:
                return
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء بدء التحميل: " + str(e))
            self.set_ui_for_batch_download(True)
            self.cancel_download_button.setVisible(False)
    def is_audio_downloaded(self, filepath):
        return os.path.exists(filepath)
    def on_single_batch_download_finished(self):
        if hasattr(self, 'current_download_filename'):
            self.successfully_downloaded_in_batch.append(self.current_download_filename)
        self.download_next_audio_to_app()
    def download_next_audio_to_app(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            if self.is_audio_downloaded(filepath):
                self.current_file_index += 1
                self.download_next_audio_to_app()
                return
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.current_download_filename = file_name
            self.download_thread = DownloadThread(self, url, filepath)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.on_single_batch_download_finished)
            self.download_thread.cancelled.connect(self.on_download_cancelled_batch_internal)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.info_menu.setEnabled(True)
            self.duration.setEnabled(True)
            message_parts = []
            if self.successfully_downloaded_in_batch:
                downloaded_list = "\n".join([name for name in self.successfully_downloaded_in_batch])
                message_parts.append(f"تم تحميل القصص التالية بنجاح:\n{downloaded_list}")
            if self.excluded_surahs_in_batch:
                excluded_list = "\n".join([name for name in self.excluded_surahs_in_batch])
                message_parts.append(f"\nتم إلغاء أو استثناء تحميل القصص التالية:\n{excluded_list}")
            if not message_parts:
                success_message = "اكتملت عملية التحميل (لم يتم تحميل ملفات جديدة)."
            else:
                success_message = "\n".join(message_parts)
            guiTools.qMessageBox.MessageBox.view(self, "تم الانتهاء من التحميل", success_message)
            self.successfully_downloaded_in_batch.clear()
            self.excluded_surahs_in_batch.clear()
            if self.is_downloading_batch:
                self.is_downloading_batch = False
                self.set_ui_for_batch_download(True)
                self.cancel_download_batch()
            else:
                self.set_ui_for_batch_download(True)
            self.update_merge_ui()
    def download_audio_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.set_ui_enabled(True)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل القصة بنجاح.")
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename
        if hasattr(self, 'current_download_category'):
            del self.current_download_category
    def download_all_stories(self):
        if self.check_if_busy(): return
        selected_category_item = self.categoriesListWidget.currentItem()
        if not selected_category_item:
            return
        category_name = selected_category_item.text()
        self.files_to_download = list(self.categories_data.get(category_name, {}).items())
        self.current_file_index = 0
        save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ القصص")
        if not save_folder:
            return
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", "هل أنت متأكد من تحميل جميع القصص؟", "نعم", "لا")
        if response == 0:
            self.save_folder = save_folder
            self.set_ui_enabled(False)
            self.progressBar.setVisible(True)
            self.cancel_download_button.setVisible(True)
            self.download_next_story()
        else:
            return
    def download_next_story(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.current_download_filename = file_name
            self.download_thread = DownloadThread(self, url, filepath)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.cancelled.connect(self.on_download_cancelled_batch_external)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.set_ui_enabled(True)
            guiTools.qMessageBox.MessageBox.view(self, "تم التحميل", "تم تحميل جميع القصص.")
    def update_progress(self, progress_percent):
        self.progressBar.setValue(progress_percent)
    def download_finished(self):
        self.progressBar.setValue(100)
        self.download_next_story()
    def download_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.set_ui_enabled(True)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل القصة")
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename
    def cancel_current_download(self):
        is_batch_download = self.is_downloading_batch or (hasattr(self, 'files_to_download') and self.current_file_index < len(self.files_to_download) and hasattr(self, 'current_download_category'))
        if is_batch_download and not self.full_batch_cancellation_requested:
            current_story_name = self.current_download_filename
            remaining_files = len(self.files_to_download) - self.current_file_index
            reply = guiTools.QQuestionMessageBox.view(self, "إلغاء قصة", f"هل تريد إلغاء تحميل القصة الحالية ({current_story_name}) ومتابعة تحميل باقي القصص ({self.format_surah_count(remaining_files)})؟\n\nاضغط 'نعم' للإلغاء، 'لا' للمتابعة دون إلغاء هذه القصة.", "نعم", "لا")
            if reply == 0:
                if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                    self.download_thread.cancel()
            else:
                pass
        else:
            if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                self.download_thread.cancel()
    def on_download_cancelled(self):
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'current_download_category'):
            self.mark_for_deletion(self.current_download_filename, self.current_download_category, app_internal=True)
            del self.current_download_filename
            del self.current_download_category
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل القصة.")
    def on_download_cancelled_batch_internal(self):
        if self.full_batch_cancellation_requested:
            self.full_batch_cancellation_requested = False
            self.current_file_index = len(self.files_to_download)
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.info_menu.setEnabled(True)
            self.duration.setEnabled(True)
            files_to_delete = list(self.successfully_downloaded_in_batch)
            if hasattr(self, 'current_download_filename') and self.current_download_filename not in files_to_delete:
                files_to_delete.append(self.current_download_filename)
            if files_to_delete and hasattr(self, 'current_download_category'):
                category = self.current_download_category
                for file_name in files_to_delete:
                    self.mark_for_deletion(file_name, category, app_internal=True)
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", f"تم إلغاء تحميل الدفعة وحذف {self.format_surah_count(len(files_to_delete))} ملفات.")
            else:
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل الدفعة.")
            self.successfully_downloaded_in_batch.clear()
            self.excluded_surahs_in_batch.clear()
            if hasattr(self, 'current_download_filename'): del self.current_download_filename
            if hasattr(self, 'current_download_category'): del self.current_download_category
            if self.is_downloading_batch:
                self.is_downloading_batch = False
                self.set_ui_for_batch_download(True)
                self.cancel_download_batch()
            self.update_merge_ui()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(True)
            current_story_name = self.current_download_filename
            self.mark_for_deletion(self.current_download_filename, self.current_download_category, app_internal=True)
            self.excluded_surahs_in_batch.append(current_story_name)
            self.update_download_batch_ui()
            del self.current_download_filename
            guiTools.qMessageBox.MessageBox.view(self, "تخطي القصة", f"تم إلغاء تحميل {current_story_name} وسيتم متابعة الباقي.")
            self.download_next_audio_to_app()
    def on_download_cancelled_batch_external(self):
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename
        self.current_file_index = len(self.files_to_download)
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل جميع القصص، لكن سيتم حذف آخر قصة كان يتم تحميلها")
    def mark_for_deletion(self, file_name, category, app_internal=False):
        if app_internal:
            filepath = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{file_name}.mp3")
        else:
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
        if not os.path.exists(filepath):
            return
        delete_me = filepath + ".delete_me"
        if os.path.exists(delete_me):
            try: os.remove(delete_me)
            except: pass
        try:
            os.rename(filepath, delete_me)
        except:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر وضع علامة للحذف على الملف: {file_name}.mp3. قد تحتاج إلى حذفه يدوياً بعد إغلاق التطبيق.")
    def on_category_selected(self):
        self.mp.stop()
        self.storyListWidget.clear()
        self.cancel_merge()
        self.cancel_download_batch()
        self.repeat_story_button.setEnabled(False)
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            self.merge_all_button.setVisible(True)
            category = selected_category_item.text()
            for story, link in self.categories_data[category].items():
                self.storyListWidget.addItem(story)
            self.check_all_stories_downloaded()
        else:
            self.merge_all_button.setVisible(False)
    def search(self, search_text, data):
        return [item for item in data if search_text in item.lower()]
    def story_onsearch(self):
        search_text = self.storySearchEdit.text().lower()
        self.storyListWidget.clear()
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            category = selected_category_item.text()
            story_list = list(self.categories_data[category].keys())
        else:
            story_list = []
        result = self.search(search_text, story_list)
        self.storyListWidget.addItems(result)
    def play_selected_audio(self):
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storyListWidget.currentItem()
            if selected_item:
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "stories", category)
                audio_path = os.path.join(audio_folder, selected_item.text() + ".mp3")
                if os.path.exists(audio_path):
                    self.mp.setSource(qt2.QUrl.fromLocalFile(audio_path))
                    self.mp.play()
                else:
                    url = self.categories_data[category][selected_item.text()]
                    self.mp.setSource(qt2.QUrl(url))
                    self.mp.play()
                self.repeat_story_button.setEnabled(True)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تشغيل المقطع:" + str(e))
    def download_selected_audio(self):
        if self.check_if_busy(): return
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storyListWidget.currentItem()
            if selected_item:
                url = self.categories_data[category][selected_item.text()]
                filepath, _ = qt.QFileDialog.getSaveFileName(self, "save story", "", "Audio Files (*.mp3)")
                if filepath:
                    self.set_ui_enabled(False)
                    self.progressBar.setVisible(True)
                    self.cancel_download_button.setVisible(True)
                    self.save_folder = os.path.dirname(filepath)
                    self.current_download_filename = os.path.splitext(os.path.basename(filepath))[0]
                    self.download_thread = DownloadThread(self, url, filepath)
                    self.download_thread.progress.connect(self.progressBar.setValue)
                    self.download_thread.finished.connect(self.download_complete)
                    self.download_thread.cancelled.connect(self.on_download_cancelled_external_single)
                    self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ ما: " + str(e))
            self.set_ui_enabled(True)
            self.cancel_download_button.setVisible(False)
    def on_download_cancelled_external_single(self):
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'save_folder'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename
            del self.save_folder
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل القصة.")
    def open_context_menu(self, position):
        menu = qt.QMenu(self)
        menu.setAccessibleName("خيارات القصة")
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        is_merging_active = self.merge_list or self.first_merge_selection_index is not None
        is_batch_download_active = bool(self.download_batch_list) or self.first_download_selection_index is not None
        if not is_batch_download_active:
            merge_menu = menu.addMenu("دمج القصص")
            if self.first_merge_selection_index is None:
                if not self.merge_list:
                    start_merge_action = qt1.QAction("بدء الدمج من هذه القصة", self)
                    start_merge_action.triggered.connect(self.add_to_merge_list)
                    merge_menu.addAction(start_merge_action)
                else:
                    add_next_action = qt1.QAction(f"إضافة القصة رقم {len(self.merge_list) + 1}", self)
                    add_next_action.triggered.connect(self.add_to_merge_list)
                    merge_menu.addAction(add_next_action)
                    undo_action = qt1.QAction("التراجع عن تحديد قصة", self)
                    undo_action.triggered.connect(self.remove_from_merge_list)
                    merge_menu.addAction(undo_action)
                    cancel_merge_action = qt1.QAction("إلغاء عملية الدمج الحالية", self)
                    cancel_merge_action.triggered.connect(self.cancel_merge)
                    merge_menu.addAction(cancel_merge_action)
            merge_menu.addSeparator()
            if not self.merge_list:
                if self.first_merge_selection_index is None:
                    set_start_action = qt1.QAction("تحديد كبداية للدمج", self)
                    set_start_action.triggered.connect(self.set_as_merge_start)
                    merge_menu.addAction(set_start_action)
                else:
                    current_index = self.storyListWidget.currentRow()
                    start_item_text = self.storyListWidget.item(self.first_merge_selection_index).text()
                    merge_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                    if current_index != self.first_merge_selection_index:
                        merge_range_action = qt1.QAction("الدمج من البداية المحددة إلى هنا", self)
                        merge_range_action.triggered.connect(self.merge_from_start_to_here)
                        merge_menu.addAction(merge_range_action)
                    cancel_start_action = qt1.QAction("إلغاء تحديد بداية الدمج", self)
                    cancel_start_action.triggered.connect(self.cancel_merge_start)
                    merge_menu.addAction(cancel_start_action)
            menu.addSeparator()
        if not is_merging_active:
            if not is_batch_download_active or self.batch_download_target == 'app':
                batch_download_app_menu = menu.addMenu("تحميل مخصص في التطبيق")
                if self.first_download_selection_index is None:
                    if not self.download_batch_list:
                        start_batch_dl_action = qt1.QAction("بدء التحميل المخصص من هذه القصة", self)
                        start_batch_dl_action.triggered.connect(lambda: self.add_to_download_batch('app'))
                        batch_download_app_menu.addAction(start_batch_dl_action)
                    else:
                        add_next_dl_action = qt1.QAction(f"إضافة القصة رقم {len(self.download_batch_list) + 1} للتحميل", self)
                        add_next_dl_action.triggered.connect(lambda: self.add_to_download_batch('app'))
                        batch_download_app_menu.addAction(add_next_dl_action)
                        remove_dl_action = qt1.QAction("إزالة قصة من قائمة التحميل", self)
                        remove_dl_action.triggered.connect(self.remove_from_download_batch)
                        batch_download_app_menu.addAction(remove_dl_action)
                        cancel_batch_dl_action = qt1.QAction("إلغاء التحميل المخصص", self)
                        cancel_batch_dl_action.triggered.connect(self.cancel_download_batch)
                        batch_download_app_menu.addAction(cancel_batch_dl_action)
                batch_download_app_menu.addSeparator()
                if not self.download_batch_list:
                    if self.first_download_selection_index is None:
                        set_start_dl_action = qt1.QAction("تحديد كبداية للتحميل", self)
                        set_start_dl_action.triggered.connect(lambda: self.set_as_download_start('app'))
                        batch_download_app_menu.addAction(set_start_dl_action)
                    else:
                        current_index = self.storyListWidget.currentRow()
                        if self.batch_download_target == 'app':
                            start_item_text = self.storyListWidget.item(self.first_download_selection_index).text()
                            batch_download_app_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                            if current_index != self.first_download_selection_index:
                                download_range_action = qt1.QAction("التحميل من البداية المحددة إلى هنا", self)
                                download_range_action.triggered.connect(lambda: self.download_from_start_to_here('app'))
                                batch_download_app_menu.addAction(download_range_action)
                            cancel_start_dl_action = qt1.QAction("إلغاء تحديد بداية التحميل", self)
                            cancel_start_dl_action.triggered.connect(self.cancel_download_start)
                            batch_download_app_menu.addAction(cancel_start_dl_action)
            if not is_batch_download_active or self.batch_download_target == 'device':
                batch_download_device_menu = menu.addMenu("تحميل مخصص في الجهاز")
                if self.first_download_selection_index is None:
                    if not self.download_batch_list:
                        start_batch_dl_action = qt1.QAction("بدء التحميل المخصص من هذه القصة", self)
                        start_batch_dl_action.triggered.connect(lambda: self.add_to_download_batch('device'))
                        batch_download_device_menu.addAction(start_batch_dl_action)
                    else:
                        add_next_dl_action = qt1.QAction(f"إضافة القصة رقم {len(self.download_batch_list) + 1} للتحميل", self)
                        add_next_dl_action.triggered.connect(lambda: self.add_to_download_batch('device'))
                        batch_download_device_menu.addAction(add_next_dl_action)
                        remove_dl_action = qt1.QAction("إزالة قصة من قائمة التحميل", self)
                        remove_dl_action.triggered.connect(self.remove_from_download_batch)
                        batch_download_device_menu.addAction(remove_dl_action)
                        cancel_batch_dl_action = qt1.QAction("إلغاء التحميل المخصص", self)
                        cancel_batch_dl_action.triggered.connect(self.cancel_download_batch)
                        batch_download_device_menu.addAction(cancel_batch_dl_action)
                batch_download_device_menu.addSeparator()
                if not self.download_batch_list:
                    if self.first_download_selection_index is None:
                        set_start_dl_action = qt1.QAction("تحديد كبداية للتحميل", self)
                        set_start_dl_action.triggered.connect(lambda: self.set_as_download_start('device'))
                        batch_download_device_menu.addAction(set_start_dl_action)
                    else:
                        current_index = self.storyListWidget.currentRow()
                        if self.batch_download_target == 'device':
                            start_item_text = self.storyListWidget.item(self.first_download_selection_index).text()
                            batch_download_device_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                            if current_index != self.first_download_selection_index:
                                download_range_action = qt1.QAction("التحميل من البداية المحددة إلى هنا", self)
                                download_range_action.triggered.connect(lambda: self.download_from_start_to_here('device'))
                                batch_download_device_menu.addAction(download_range_action)
                            cancel_start_dl_action = qt1.QAction("إلغاء تحديد بداية التحميل", self)
                            cancel_start_dl_action.triggered.connect(self.cancel_download_start)
                            batch_download_device_menu.addAction(cancel_start_dl_action)
            menu.addSeparator()
        play_action = qt1.QAction("تشغيل القصة المحددة", self)
        play_action.triggered.connect(self.play_selected_audio)
        menu.addAction(play_action)
        selected_item = self.storyListWidget.currentItem()
        if selected_item:
            story_name = selected_item.text()
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            story_path = os.path.join(os.getenv('appdata'), app.appName, "stories", category, f"{story_name}.mp3")
            if not os.path.exists(story_path):
                download_app_action = qt1.QAction("تحميل القصة المحددة في التطبيق", self)
                download_app_action.triggered.connect(self.download_selected_audio_to_app)
                menu.addAction(download_app_action)
            download_device_action = qt1.QAction("تحميل القصة المحددة في الجهاز", self)
            download_device_action.triggered.connect(self.download_selected_audio)
            menu.addAction(download_device_action)
        delete_option = self.check_current_story_downloaded()
        if delete_option:
            menu.addAction(delete_option)
        addNewBookmarkAction = qt1.QAction("إضافة علامة مرجعية", self)
        menu.addAction(addNewBookmarkAction)
        addNewBookmarkAction.triggered.connect(self.onAddNewBookmark)
        menu.exec(self.storyListWidget.viewport().mapToGlobal(position))
    def t10(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.1))
    def t20(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.2))
    def t30(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.3))
    def t40(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.4))
    def t50(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.5))
    def t60(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.6))
    def t70(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.7))
    def t80(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.8))
    def t90(self):
        if not self.check_media_loaded():
            return
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.9))
    def play(self):
        if self.mp.isPlaying():
            self.mp.pause()
        else:
            self.mp.play()
    def restore_duration_text(self):
        self.time_VA()
    def increase_volume(self):
        current_volume = self.au.volume()
        new_volume = min(current_volume + 0.10, 1.0)
        self.au.setVolume(new_volume)
        volume_percent = int(new_volume * 100)
        speak(f"نسبة الصوت {volume_percent}")
        self.duration.setText(f"نسبة الصوت: {volume_percent}%")
        self.volume_timer.start(1000)
    def decrease_volume(self):
        current_volume = self.au.volume()
        new_volume = max(current_volume - 0.10, 0.0)
        self.au.setVolume(new_volume)
        volume_percent = int(new_volume * 100)
        speak(f"نسبة الصوت {volume_percent}")
        self.duration.setText(f"نسبة الصوت: {volume_percent}%")
        self.volume_timer.start(1000)
    def set_position_from_slider(self, value):
        duration = self.mp.duration()
        if duration > 0:
            new_position = int((value / 100) * duration)
            self.mp.setPosition(new_position)
    def update_slider(self):
        if self.mp.duration() > 0:
            try:
                self.Slider.blockSignals(True)
                position_ratio = self.mp.position() / self.mp.duration()
                self.Slider.setValue(int(position_ratio * 100))
                self.Slider.blockSignals(False)
                self.time_VA()
            except ZeroDivisionError:
                self.Slider.setValue(0)
                if not self.volume_timer.isActive():
                    self.duration.setText("00:00:00")
        else:
            self.Slider.setValue(0)
            if not self.volume_timer.isActive():
                self.duration.setText("00:00:00")
    def time_VA(self):
        if self.volume_timer.isActive():
            return
        position = self.mp.position()
        duration = self.mp.duration()
        remaining = duration - position
        position_str = qt2.QTime(0, 0, 0).addMSecs(position).toString("HH:mm:ss")
        duration_str = qt2.QTime(0, 0, 0).addMSecs(duration).toString("HH:mm:ss")
        remaining_str = qt2.QTime(0, 0, 0).addMSecs(remaining).toString("HH:mm:ss")
        self.duration.setText("الوقت المنقضي: " + position_str + "، الوقت المتبقي: " + remaining_str + "، مدة المقطع: " + duration_str)
    @staticmethod
    def load_categories():
        file_path = "data/json/files/all_audio_stories.json"
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    def onBookmarkOpened(self):
        gui.book_marcks(self, "stories").exec()
    def onAddNewBookmark(self):
        name, ok = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب اسم العلامة المرجعية")
        if ok and name:
            type = self.categoriesListWidget.currentRow()
            story = self.storyListWidget.currentRow()
            position = self.mp.position()
            functions.bookMarksManager.addNewaudioBookMark("stories", type, story, position, name)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeaudioBookMark("stories",self.nameOfBookmark)
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم الحذف")
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")