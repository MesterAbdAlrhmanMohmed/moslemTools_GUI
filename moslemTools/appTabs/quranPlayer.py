import guiTools, requests, json, os, winsound, gui, functions, subprocess, shutil
from guiTools import TextViewer
from guiTools import speak
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    cancelled = qt2.pyqtSignal()
    def __init__(self, url, filepath):
        super().__init__()
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
    def __init__(self, ffmpeg_path, input_files, output_file):
        super().__init__()
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
            command = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_filepath,
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                self.output_file
            ]        
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
class QuranPlayer(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج السور لن تعمل.")
        qt1.QShortcut("ctrl+s", self).activated.connect(lambda: self.mp.stop())
        qt1.QShortcut("space", self).activated.connect(self.play)
        qt1.QShortcut("alt+right", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() + 5000))
        qt1.QShortcut("alt+left", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() - 5000))
        qt1.QShortcut("alt+up", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() + 10000))
        qt1.QShortcut("alt+down", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() - 10000))
        qt1.QShortcut("ctrl+right", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() + 30000))
        qt1.QShortcut("ctrl+left", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() - 30000))
        qt1.QShortcut("ctrl+up", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() + 60000))
        qt1.QShortcut("ctrl+down", self).activated.connect(lambda: self.mp.setPosition(self.mp.position() - 60000))
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
        qt1.QShortcut("shift+1", self).activated.connect(self.onChangeStartingPosition)
        qt1.QShortcut("shift+2", self).activated.connect(self.onChangeEndingPosition)
        qt1.QShortcut("backspace", self).activated.connect(self.removePosition)        
        self.volume_timer = qt2.QTimer(self)
        self.volume_timer.setSingleShot(True)
        self.volume_timer.timeout.connect(self.restore_duration_text)        
        self.bookmarksPosition = None
        self.isAMustToGoToBookmark = False
        self.startingPosition = None
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.reciters_data = self.load_reciters()
        self.recitersLabel = qt.QLabel("إختيار قارئ")
        self.recitersLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.reciterSearchLabel = qt.QLabel("ابحث عن قارئ")
        self.reciterSearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.reciterSearchEdit = qt.QLineEdit()
        self.reciterSearchEdit.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.reciterSearchEdit.setAccessibleName("ابحث عن قارئ")
        self.reciterSearchEdit.setObjectName("reciterSearch")
        self.recitersListWidget = guiTools.QListWidget()
        self.recitersListWidget.setSpacing(3)
        self.recitersListWidget.itemSelectionChanged.connect(self.on_reciter_selected)
        self.surahsLabel = qt.QLabel("السور")
        self.surahsLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahSearchLabel = qt.QLabel("ابحث عن سورة")
        self.surahSearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahSearchEdit = qt.QLineEdit()
        self.surahSearchEdit .setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahSearchEdit.setAccessibleName("ابحث عن سورة")
        self.surahSearchEdit.setObjectName("surahSearch")
        self.surahListWidget = guiTools.QListWidget()
        self.surahListWidget.setSpacing(3)
        self.surahListWidget.clicked.connect(self.play_selected_audio)
        self.reciterSearchEdit.textChanged.connect(self.reciter_onsearch)
        self.surahSearchEdit.textChanged.connect(self.surah_onsearch)
        self.recitersList = list(self.reciters_data.keys())
        self.recitersList.sort()
        self.recitersListWidget.addItems(self.recitersList)
        self.progressBar = qt.QProgressBar()
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progressBar.setVisible(False)        
        self.cancel_download_button = guiTools.QPushButton("إلغاء التنزيل")        
        self.cancel_download_button.setShortcut("ctrl+c")
        self.cancel_download_button.setAccessibleDescription("control plus c")        
        self.cancel_download_button.setVisible(False)
        self.cancel_download_button.clicked.connect(self.cancel_current_download)        
        self.cancel_download_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
        """)
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
        self.play_all_to_end = guiTools.QPushButton("تشغيل كل السور من السورة المحددة الى النهاية")        
        self.play_all_to_end.setAccessibleDescription("control plus A")
        self.play_all_to_end.setCheckable(True)        
        self.play_all_to_end.setShortcut("ctrl+a")
        self.play_all_to_end.toggled.connect(lambda checked: self.update_button_style(self.play_all_to_end, checked))
        self.play_all_to_end.toggled.connect(self.handle_play_all_toggled)
        self.play_all_to_start = guiTools.QPushButton("تشغيل كل السور من السورة المحددة الى البداية")        
        self.play_all_to_start.setAccessibleDescription("control plus shift plus A")
        self.play_all_to_start.setCheckable(True)
        self.play_all_to_start.setShortcut("ctrl+shift+a")
        self.play_all_to_start.toggled.connect(lambda checked: self.update_button_style(self.play_all_to_start, checked))
        self.play_all_to_start.toggled.connect(self.handle_play_all_start_toggled)
        self.repeat_surah_button = guiTools.QPushButton("تكرار تشغيل السورة المحددة")        
        self.repeat_surah_button.setAccessibleDescription("control plus R")
        self.repeat_surah_button.setCheckable(True)        
        self.repeat_surah_button.setShortcut("ctrl+r")
        self.repeat_surah_button.toggled.connect(lambda checked: self.update_button_style(self.repeat_surah_button, checked))
        self.repeat_surah_button.toggled.connect(self.handle_repeat_toggled)
        self.Slider = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Slider.setAccessibleName("التحكم في تقدم السورة")
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
        self.dl_all_app = guiTools.QPushButton("تحميل جميع السور المتاحة لهذا القارئ في التطبيق")                
        self.dl_all_app.clicked.connect(self.download_all_audios_to_app)
        self.dl_all = guiTools.QPushButton("تحميل جميع السور المتاحة لهذا القارئ في الجهاز")                
        self.dl_all.clicked.connect(self.download_all_soar)
        self.delete = guiTools.QPushButton("حذف كل السور للقارئ الحالي من التطبيق")        
        self.delete.setStyleSheet("background-color: #8B0000; color: white;")        
        self.delete.setVisible(False)
        self.delete.clicked.connect(lambda: self.delete_surah())        
        self.info_menu = qt.QLabel("لخيارات السورة، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info_menu.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
        self.info_menu.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_feedback_label.setVisible(False)    
        self.merge_action_button = guiTools.QPushButton("بدء دمج السور المحددة")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        self.merge_action_button.setVisible(False)        
        self.merge_all_from_start_button = guiTools.QPushButton("دمج كل السور من البداية الى النهاية")
        self.merge_all_from_start_button.clicked.connect(self.prepare_merge_all_from_start)
        self.merge_all_from_start_button.setVisible(True)        
        self.merge_all_from_end_button = guiTools.QPushButton("دمج كل السور من النهاية الى البداية")
        self.merge_all_from_end_button.clicked.connect(self.prepare_merge_all_from_end)
        self.merge_all_from_end_button.setVisible(True)        
        recitersLayout = qt.QVBoxLayout()
        recitersLayout.addWidget(self.recitersLabel)
        recitersLayout.addWidget(self.reciterSearchLabel)
        recitersLayout.addWidget(self.reciterSearchEdit)
        recitersLayout.addWidget(self.recitersListWidget)        
        surahsLayout = qt.QVBoxLayout()
        surahsLayout.addWidget(self.surahsLabel)
        surahsLayout.addWidget(self.surahSearchLabel)
        surahsLayout.addWidget(self.surahSearchEdit)
        surahsLayout.addWidget(self.surahListWidget)
        surahsLayout.addWidget(self.info_menu)
        surahsLayout.addWidget(self.merge_feedback_label)        
        merge_buttons_layout = qt.QVBoxLayout()
        merge_buttons_layout.addWidget(self.merge_action_button)
        merge_buttons_layout.addWidget(self.merge_all_from_start_button)
        merge_buttons_layout.addWidget(self.merge_all_from_end_button)
        surahsLayout.addLayout(merge_buttons_layout)        
        topLayout = qt.QHBoxLayout()
        topLayout.addLayout(recitersLayout)
        topLayout.addLayout(surahsLayout)                
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
        playback_buttons_layout.addWidget(self.play_all_to_start)
        layout.addLayout(playback_buttons_layout)
        layout.addWidget(self.repeat_surah_button)        
        layout1 = qt.QHBoxLayout()        
        layout1.addWidget(self.User_guide)
        layout1.addWidget(self.duration)
        layout1.addWidget(self.openBookmarks)
        layout.addLayout(layout1)        
        self.setLayout(layout)        
        if self.recitersListWidget.count() > 0:
            self.recitersListWidget.setCurrentRow(0)
            self.on_reciter_selected()            
        self.surahListWidget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.surahListWidget.customContextMenuRequested.connect(self.open_context_menu)
        self.cleanup_pending_deletions()
    def handle_merge_action(self):
        if self.is_merging:
            self.confirm_and_cancel_merge()
        else:
            self.prepare_merge()
    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", 
            "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
    def add_to_merge_list(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        selected_surah_item = self.surahListWidget.currentItem()
        if not selected_reciter_item or not selected_surah_item:
            return        
        reciter = selected_reciter_item.text()
        surah = selected_surah_item.text()        
        surah_info = {
            "reciter": reciter,
            "surah": surah,
            "url": self.reciters_data[reciter][surah]
        }
        self.merge_list.append(surah_info)
        winsound.Beep(440, 100)
        self.update_merge_ui()
    def remove_from_merge_list(self):
        if not self.merge_list:
            return        
        num_items = len(self.merge_list)
        number, ok = guiTools.QInputDialog.getSingleInt(
            self, 
            "إزالة سورة", 
            f"أدخل رقم السورة لإزالتها (من 1 إلى {num_items})", 
            1
        )
        if ok:
            if 1 <= number <= num_items:
                del self.merge_list[number - 1]
                winsound.Beep(600, 150)
                self.update_merge_ui()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرقم المدخل خارج النطاق الصحيح.")
    def update_merge_ui(self):
        count = len(self.merge_list)
        if count > 0:
            self.merge_feedback_label.setText(f"تم تحديد {count} سورة للدمج.")
            self.merge_feedback_label.setVisible(True)
            self.merge_all_from_start_button.setEnabled(False)
            self.merge_all_from_end_button.setEnabled(False)
        else:
            self.merge_feedback_label.setVisible(False)
            self.merge_all_from_start_button.setEnabled(True)
            self.merge_all_from_end_button.setEnabled(True)
        self.merge_action_button.setVisible(count >= 2)
    def cancel_merge(self):
        self.merge_list.clear()
        self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setVisible(False)
        self.merge_all_from_start_button.setEnabled(True)
        self.merge_all_from_end_button.setEnabled(True)
    def prepare_merge_all_from_start(self):
        if not self.recitersListWidget.currentItem():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء اختيار قارئ أولاً.")
            return
        self.merge_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        surah_names = list(self.reciters_data[reciter].keys())
        for surah in surah_names:
            url = self.reciters_data[reciter][surah]
            self.merge_list.append({"reciter": reciter, "surah": surah, "url": url})
        self.prepare_merge(is_all=True)
    def prepare_merge_all_from_end(self):
        if not self.recitersListWidget.currentItem():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء اختيار قارئ أولاً.")
            return
        self.merge_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        surah_names = list(self.reciters_data[reciter].keys())
        surah_names.reverse()
        for surah in surah_names:
            url = self.reciters_data[reciter][surah]
            self.merge_list.append({"reciter": reciter, "surah": surah, "url": url})
        self.prepare_merge(is_all=True)
    def prepare_merge(self, is_all=False):
        if len(self.merge_list) < 2 and not is_all:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يجب تحديد سورتين على الأقل للدمج.")
            return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return                
        urls_to_download = []
        for item in self.merge_list:
            reciter = item["reciter"]
            surah = item["surah"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if not os.path.exists(local_path):
                urls_to_download.append(item["url"])
        
        num_files_to_download = len(urls_to_download)
        
        if num_files_to_download > 0:
            confirm_message = (
                f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} سورة غير موجودة.\n"
                "سيتم الآن تحميل ودمج الملفات المحددة على مرحلتين:\n"
                "مرحلة التحميل: سيتم تحميل الملفات تباعًا. في هذه الأثناء، يمكنك استخدام قائمة السور للتراجع عن تحديد أي سورة لم يبدأ تحميلها بعد، وبذلك يتم إلغاء تحميلها.\n"
                "مرحلة الدمج: بعد انتهاء التحميل، لن تتمكن من استخدام الواجهة إلا لإلغاء عملية الدمج بأكملها.\n\n"
                "هل تريد المتابعة؟"
            )
        else:
            confirm_message = (
                "جميع السور المحددة جاهزة للدمج.\n"
                "ستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة باستثناء زر إلغاء الدمج.\n\n"
                "هل تريد المتابعة؟"
            )

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
            reciter = item["reciter"]
            surah = item["surah"]
            url = item["url"]            
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if os.path.exists(local_path):
                continue            
            if url in self.completed_merge_downloads:
                continue
            next_item_to_download = item
            break        
        if next_item_to_download:
            self.progressBar.setVisible(True)
            url = next_item_to_download['url']
            reciter = next_item_to_download['reciter']
            surah = next_item_to_download['surah']            
            safe_surah_name = "".join(c for c in surah if c.isalnum() or c in (' ', '_')).rstrip()
            download_path = os.path.join(output_dir, f"{reciter}_{safe_surah_name}.mp3")            
            self.current_download_url = url
            self.download_thread = DownloadThread(url, download_path)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
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
            reciter, surah, url = item["reciter"], item["surah"], item["url"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")            
            if os.path.exists(local_path):
                files_for_ffmpeg.append(local_path)
            else:
                safe_surah_name = "".join(c for c in surah if c.isalnum() or c in (' ', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"{reciter}_{safe_surah_name}.mp3")
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
        self.merge_feedback_label.setText(f"جاري دمج {count} سور...")
        self.merge_feedback_label.setVisible(True)
        self.merge_action_button.setVisible(True)
        self.merge_action_button.setEnabled(True)
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()        
    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.set_ui_enabled(True)        
        self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setText("بدء دمج السور المحددة")
        self.merge_action_button.setStyleSheet("")
        self.update_merge_ui()
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                os.remove(self.current_merge_output_path)            
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", 
                    "هل تريد حذف السور الفردية التي تم تحميلها لهذه العملية الملغاة؟", "نعم", "لا")
                if reply == 0:
                    for f_path in self.files_to_delete_after_merge:
                        if os.path.exists(f_path):
                            try: os.remove(f_path)
                            except: pass
        elif success:
            merged_files_names = [f" {item['surah']}" for item in self.merge_list]
            details = "\n".join(merged_files_names)
            success_message = f"تم دمج السور بنجاح:\n{details}"
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", success_message)
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", 
                    "هل تريد حذف السور الفردية التي تم تحميلها للدمج؟", "نعم", "لا")
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
    def set_ui_enabled(self, enabled):
        widgets_to_toggle = [
            self.recitersListWidget, self.surahListWidget,
            self.reciterSearchEdit, self.surahSearchEdit,
            self.reciterSearchLabel, self.surahSearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.play_all_to_start, self.repeat_surah_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_from_start_button, self.merge_all_from_end_button,
            self.recitersLabel, self.surahsLabel,
            self.duration, self.info_menu,
            self.merge_feedback_label
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        if not enabled:
            self.merge_action_button.setEnabled(True)
    def set_ui_for_merge_download(self, enabled):
        widgets_to_toggle = [
            self.recitersListWidget,
            self.reciterSearchEdit, self.surahSearchEdit,
            self.reciterSearchLabel, self.surahSearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.play_all_to_start, self.repeat_surah_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_from_start_button, self.merge_all_from_end_button,
            self.recitersLabel,
            self.duration, self.info_menu,
            self.merge_action_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
    def cleanup_pending_deletions(self):        
        quran_reciters_dir = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters")
        if os.path.exists(quran_reciters_dir):
            for root, _, files in os.walk(quran_reciters_dir):
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
            self.play_all_to_start.setEnabled(False)
            self.repeat_surah_button.setEnabled(False)
            if self.surahListWidget.currentRow() == -1 and self.surahListWidget.count() > 0:
                self.surahListWidget.setCurrentRow(0)
            self.play_selected_audio()
        else:
            self.play_all_to_start.setEnabled(True)
            self.repeat_surah_button.setEnabled(True)
    def handle_play_all_start_toggled(self, checked):
        self.mp.stop()
        if checked:
            self.play_all_to_end.setEnabled(False)
            self.repeat_surah_button.setEnabled(False)
            if self.surahListWidget.currentRow() == -1 and self.surahListWidget.count() > 0:
                self.surahListWidget.setCurrentRow(self.surahListWidget.count() - 1)
            self.play_selected_audio()
        else:
            self.play_all_to_end.setEnabled(True)
            self.repeat_surah_button.setEnabled(True)
    def handle_repeat_toggled(self, checked):
        self.mp.stop()
        if checked:
            self.play_all_to_end.setEnabled(False)
            self.play_all_to_start.setEnabled(False)
        else:
            self.play_all_to_end.setEnabled(True)
            self.play_all_to_start.setEnabled(True)
    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_surah_button.isChecked():
                self.mp.setPosition(0)
                self.play_selected_audio()
            elif self.play_all_to_end.isChecked():
                self.play_next_in_list()
            elif self.play_all_to_start.isChecked():
                self.play_previous_in_list()
    def play_next_in_list(self):
        current_row = self.surahListWidget.currentRow()
        if current_row < self.surahListWidget.count() - 1:
            self.surahListWidget.setCurrentRow(current_row + 1)
            self.play_selected_audio()
        else:
            self.play_all_to_end.setChecked(False)
    def play_previous_in_list(self):
        current_row = self.surahListWidget.currentRow()
        if current_row > 0:
            self.surahListWidget.setCurrentRow(current_row - 1)
            self.play_selected_audio()
        else:
            self.play_all_to_start.setChecked(False)
    def delete_surah(self, surah_name=None):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter = selected_reciter_item.text()
        reciter_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
        try:
            if surah_name:
                surah_path = os.path.join(reciter_folder, f"{surah_name}.mp3")
                if os.path.exists(surah_path):
                    confirm = guiTools.QQuestionMessageBox.view(
                        self,
                        "تأكيد الحذف",
                        "هل أنت متأكد أنك تريد حذف السورة المحددة؟","نعم","لا")
                    if confirm == 0:
                        try:
                            os.remove(surah_path)
                            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف السورة بنجاح.")
                        except PermissionError:
                            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف السورة. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
            else:
                if os.path.exists(reciter_folder):
                    confirm = guiTools.QQuestionMessageBox.view(
                        self,
                        "تأكيد الحذف",
                        "هل أنت متأكد أنك تريد حذف جميع السور؟","نعم","لا")
                    if confirm == 0:
                        for file in os.listdir(reciter_folder):
                            if file.endswith(".mp3"):
                                try:
                                    os.remove(os.path.join(reciter_folder, file))
                                except PermissionError:
                                    guiTools.qMessageBox.MessageBox.error(
                                        self,
                                        "خطأ",
                                        "تعذر حذف بعض الملفات. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج"
                                    )
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف جميع السور بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ غير متوقع", str(e))
        self.check_all_surahs_downloaded()
    def check_all_surahs_downloaded(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item:
            reciter = selected_reciter_item.text()
            reciter_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
            if os.path.exists(reciter_folder):
                all_files = os.listdir(reciter_folder)
                all_surahs = self.reciters_data.get(reciter, {}).keys()
                downloaded_surahs = {os.path.splitext(file)[0] for file in all_files if file.endswith(".mp3")}
                if downloaded_surahs >= set(all_surahs):
                    self.delete.setVisible(True)
                    self.dl_all_app.setVisible(False)
                else:
                    self.delete.setVisible(False)
                    self.dl_all_app.setVisible(True)
            else:
                self.delete.setVisible(False)
                self.dl_all_app.setVisible(True)
    def check_current_surah_downloaded(self):        
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter = selected_reciter_item.text()
        selected_item = self.surahListWidget.currentItem()
        if not selected_item:
            return
        surah_name = selected_item.text()
        surah_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah_name}.mp3")
        if os.path.exists(surah_path):
            action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("حذف السورة المحددة من التطبيق")            
            btn.setStyleSheet("background-color: #8B0000; color: white;")            
            btn.clicked.connect(lambda: self.delete_surah(surah_name))
            action.setDefaultWidget(btn)
            return action
        return None
    def download_selected_audio_to_app(self):
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                url = self.reciters_data[reciter][selected_item.text()]
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                os.makedirs(audio_folder, exist_ok=True)
                filepath = os.path.join(audio_folder, f"{selected_item.text()}.mp3")
                if self.is_audio_downloaded(filepath):
                    guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "السورة محملة بالفعل.")
                    return
                self.progressBar.setVisible(True)
                self.cancel_download_button.setVisible(True)
                self.current_download_filename = selected_item.text()
                self.current_download_reciter = reciter
                self.download_thread = DownloadThread(url, filepath)
                self.download_thread.progress.connect(self.progressBar.setValue)
                self.download_thread.finished.connect(self.download_audio_complete)
                self.download_thread.cancelled.connect(self.on_download_cancelled)
                self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تحميل المقطع: " + str(e))
            self.cancel_download_button.setVisible(False)
    def download_all_audios_to_app(self):
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            self.files_to_download = [
                (file_name, url)
                for file_name, url in self.reciters_data.get(reciter, {}).items()
                if not self.is_audio_downloaded(
                    os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{file_name}.mp3")
                )
            ]
            self.current_file_index = 0
            if not self.files_to_download:
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "جميع السور محملة بالفعل")
                return
            response = guiTools.QQuestionMessageBox.view(
                self,
                "تأكيد التحميل",
                "هل تريد تحميل جميع السور المتاحة لهذا القارئ؟","نعم","لا")
            if response == 0:
                app_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                os.makedirs(app_folder, exist_ok=True)
                self.save_folder = app_folder
                self.cancel_download_button.setVisible(True)
                self.current_download_reciter = reciter
                self.download_next_audio_to_app()
            else:
                return
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء بدء التحميل: " + str(e))
            self.cancel_download_button.setVisible(False)
    def is_audio_downloaded(self, filepath):
        return os.path.exists(filepath)
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
            self.download_thread = DownloadThread(url, filepath)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.download_next_audio_to_app)
            self.download_thread.cancelled.connect(self.on_download_cancelled_batch_internal)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل جميع السور بنجاح.")
    def download_audio_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل السورة بنجاح.")        
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename
        if hasattr(self, 'current_download_reciter'):
            del self.current_download_reciter
    def download_all_soar(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter_name = selected_reciter_item.text()
        self.files_to_download = list(self.reciters_data.get(reciter_name, {}).items())
        self.current_file_index = 0
        save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ السور")
        if not save_folder:
            return
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل",
            "هل أنت متأكد من تحميل جميع السور؟","نعم","لا")
        if response == 0:
            self.save_folder = save_folder
            self.cancel_download_button.setVisible(True)
            self.download_next_sora()
        else:
            return
    def download_next_sora(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.current_download_filename = file_name
            self.download_thread = DownloadThread(url, filepath)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.cancelled.connect(self.on_download_cancelled_batch_external)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.cancel_download_button.setVisible(False)
            guiTools.qMessageBox.MessageBox.view(self, "تم التحميل", "تم تحميل جميع السور.")
    def update_progress(self, progress_percent):
        self.progressBar.setValue(progress_percent)
    def download_finished(self):
        self.progressBar.setValue(100)        
        self.download_next_sora()
    def download_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل السورة")
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename
    def cancel_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel()            
    def on_download_cancelled(self):        
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'current_download_reciter'):
            self.mark_for_deletion(self.current_download_filename, self.current_download_reciter, app_internal=True)
            del self.current_download_filename
            del self.current_download_reciter
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل السورة.")
    def on_download_cancelled_batch_internal(self):        
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)        
        if hasattr(self, 'current_download_filename') and hasattr(self, 'current_download_reciter'):
            self.mark_for_deletion(self.current_download_filename, self.current_download_reciter, app_internal=True)
            del self.current_download_filename
            del self.current_download_reciter        
        self.current_file_index = len(self.files_to_download)
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل جميع السور، لكن سيتم حذف آخر سورة كان يتم تحميلها")
    def on_download_cancelled_batch_external(self):        
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        if hasattr(self, 'current_download_filename'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")            
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename        
        self.current_file_index = len(self.files_to_download)
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل جميع السور، لكن سيتم حذف آخر سورة كان يتم تحميلها")
    def mark_for_deletion(self, file_name, reciter, app_internal=False):        
        if app_internal:
            filepath = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{file_name}.mp3")
        else:                        
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3") 
        if os.path.exists(filepath):
            try:
                os.rename(filepath, filepath + ".delete_me")
                print(f"Marked for deletion: {filepath}. Will be deleted on next startup.")
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر وضع علامة للحذف على الملف: {file_name}.mp3. قد تحتاج إلى حذفه يدوياً بعد إغلاق التطبيق. {e}")
        else:
            print(f"File not found to mark for deletion: {filepath}")
    def on_reciter_selected(self):
        self.mp.stop()
        self.surahListWidget.clear()
        self.cancel_merge()
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item:
            self.merge_all_from_start_button.setEnabled(True)
            self.merge_all_from_end_button.setEnabled(True)
            reciter = selected_reciter_item.text()
            for surah, link in self.reciters_data[reciter].items():
                self.surahListWidget.addItem(surah)
            self.check_all_surahs_downloaded()
        else:
            self.merge_all_from_start_button.setEnabled(False)
            self.merge_all_from_end_button.setEnabled(False)

    def search(self, search_text, data):
        return [item for item in data if search_text in item.lower()]
    def reciter_onsearch(self):
        search_text = self.reciterSearchEdit.text().lower()
        self.recitersListWidget.clear()
        result = self.search(search_text, self.recitersList)
        self.recitersListWidget.addItems(result)
    def surah_onsearch(self):
        search_text = self.surahSearchEdit.text().lower()
        self.surahListWidget.clear()
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item:
            reciter = selected_reciter_item.text()
            surah_list = list(self.reciters_data[reciter].keys())
        else:
            surah_list = []
        result = self.search(search_text, surah_list)
        self.surahListWidget.addItems(result)
    def play_selected_audio(self):
        self.repeatFromPositionToPosition = False
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                audio_path = os.path.join(audio_folder, selected_item.text() + ".mp3")
                if os.path.exists(audio_path):
                    self.mp.setSource(qt2.QUrl.fromLocalFile(audio_path))
                    self.mp.play()
                else:
                    url = self.reciters_data[reciter][selected_item.text()]
                    self.mp.setSource(qt2.QUrl(url))
                    self.mp.play()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تشغيل المقطع:" + str(e))
    def download_selected_audio(self):
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                url = self.reciters_data[reciter][selected_item.text()]
                filepath, _ = qt.QFileDialog.getSaveFileName(self, "save surah", "", "Audio Files (*.mp3)")
                if filepath:
                    self.progressBar.setVisible(True)
                    self.cancel_download_button.setVisible(True)
                    self.save_folder = os.path.dirname(filepath)
                    self.current_download_filename = os.path.splitext(os.path.basename(filepath))[0]
                    self.download_thread = DownloadThread(url, filepath)
                    self.download_thread.progress.connect(self.progressBar.setValue)
                    self.download_thread.finished.connect(self.download_complete)
                    self.download_thread.cancelled.connect(self.on_download_cancelled_external_single)
                    self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ ما: " + str(e))
            self.cancel_download_button.setVisible(False)
    def on_download_cancelled_external_single(self):        
        self.progressBar.setVisible(False)
        self.cancel_download_button.setVisible(False)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'save_folder'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename
            del self.save_folder
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل السورة.")
    def open_context_menu(self, position):
        menu = qt.QMenu(self)
        menu.setAccessibleName("خيارات السورة")
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)

        merge_menu = menu.addMenu("دمج السور")
        if not self.merge_list:
            start_merge_action = qt1.QAction("بدء الدمج من هذه السورة", self)
            start_merge_action.triggered.connect(self.add_to_merge_list)
            merge_menu.addAction(start_merge_action)
        else:
            add_next_action = qt1.QAction(f"إضافة السورة رقم {len(self.merge_list) + 1}", self)
            add_next_action.triggered.connect(self.add_to_merge_list)
            merge_menu.addAction(add_next_action)
            
            undo_action = qt1.QAction("التراجع عن تحديد سورة", self)
            undo_action.triggered.connect(self.remove_from_merge_list)
            merge_menu.addAction(undo_action)

            cancel_merge_action = qt1.QAction("إلغاء عملية الدمج الحالية", self)
            cancel_merge_action.triggered.connect(self.cancel_merge)
            merge_menu.addAction(cancel_merge_action)

        menu.addSeparator()

        repeateFromPositionTopositionMenue = menu.addMenu("التكرار من موضع إلى موضع")
        setStartingPositionAction = qt1.QAction("تحديد موضع البداية", self)
        setStartingPositionAction.setShortcut("shift+1")
        setStartingPositionAction.triggered.connect(self.onChangeStartingPosition)
        repeateFromPositionTopositionMenue.addAction(setStartingPositionAction)
        repeateFromPositionTopositionMenue.setDefaultAction(setStartingPositionAction)
        setEndingPositionAction = qt1.QAction("تحديد موضع النهاية", self)
        setEndingPositionAction.setShortcut("shift+2")
        setEndingPositionAction.triggered.connect(self.onChangeEndingPosition)
        repeateFromPositionTopositionMenue.addAction(setEndingPositionAction)
        resetAndStopRepeatingAction = qt1.QAction("حذف الموضع المحدد وإيقاف التكرار", self)
        resetAndStopRepeatingAction.setShortcut("backspace")
        resetAndStopRepeatingAction.triggered.connect(self.removePosition)
        repeateFromPositionTopositionMenue.addAction(resetAndStopRepeatingAction)
        repeateFromPositionTopositionMenue.setFont(boldFont)
        play_action = qt1.QAction("تشغيل السورة المحددة", self)
        play_action.triggered.connect(self.play_selected_audio)
        menu.addAction(play_action)
        selected_item = self.surahListWidget.currentItem()
        if selected_item:
            surah_name = selected_item.text()
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            surah_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah_name}.mp3")
            if not os.path.exists(surah_path):
                download_app_action = qt1.QAction("تحميل السورة المحددة في التطبيق", self)
                download_app_action.triggered.connect(self.download_selected_audio_to_app)
                menu.addAction(download_app_action)
            download_device_action = qt1.QAction("تحميل السورة المحددة في الجهاز", self)
            download_device_action.triggered.connect(self.download_selected_audio)
            menu.addAction(download_device_action)
        delete_option = self.check_current_surah_downloaded()
        if delete_option:
            menu.addAction(delete_option)
        addNewBookmarkAction = qt1.QAction("إضافة علامة مرجعية", self)
        menu.addAction(addNewBookmarkAction)
        addNewBookmarkAction.triggered.connect(self.onAddNewBookmark)
        menu.exec(self.surahListWidget.viewport().mapToGlobal(position))
    def t10(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.1))
    def t20(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.2))
    def t30(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.3))
    def t40(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.4))
    def t50(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.5))
    def t60(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.6))
    def t70(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.7))
    def t80(self):
        total_duration = self.mp.duration()
        self.mp.setPosition(int(total_duration * 0.8))
    def t90(self):
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
        if self.isAMustToGoToBookmark and self.mp.position() >= 3000:
            self.isAMustToGoToBookmark = False
            self.mp.setPosition(self.bookmarksPosition)
        if self.repeatFromPositionToPosition:
            if self.mp.position() >= self.endingPosition:
                self.mp.pause()
                self.mp.setPosition(self.startingPosition)
                self.mp.play()
                return
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
        self.duration.setText(
            "الوقت المنقضي: " + position_str +
            "، الوقت المتبقي: " + remaining_str +
            "، مدة المقطع: " + duration_str
        )
    @staticmethod
    def load_reciters():
        file_path = "data/json/reciters.json"
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    def onChangeStartingPosition(self):
        position = self.mp.position()
        self.startingPosition = position
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        winsound.Beep(400, 500)
    def onChangeEndingPosition(self):
        if self.startingPosition is not None:
            if self.startingPosition == self.mp.position():
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لا يمكن أن يكون موضع البداية هو نفس موضع النهاية")
            elif self.startingPosition > self.mp.position():
                guiTools.qMessageBox.MessageBox.view(self, "خطأ", "لا يمكن أن يكون موضع البداية أكبر من موضع النهاية")
            else:
                position = self.mp.position()
                self.endingPosition = position
                winsound.Beep(500, 500)
                self.repeatFromPositionToPosition = True
                self.mp.setPosition(self.startingPosition)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "يرجى تحديد موضع البداية أولا")
    def removePosition(self):
        self.startingPosition = None
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        winsound.Beep(300, 500)
    def onBookmarkOpened(self):
        gui.book_marcks(self, "quran").exec()
    def onAddNewBookmark(self):
        name, ok = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب اسم العلامة المرجعية")
        if ok and name:
            type = self.recitersListWidget.currentRow()
            surah = self.surahListWidget.currentRow()
            position = self.mp.position()
            functions.bookMarksManager.addNewaudioBookMark("quran", type, surah, position, name)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeaudioBookMark("quran",self.nameOfBookmark)
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم الحذف")
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")