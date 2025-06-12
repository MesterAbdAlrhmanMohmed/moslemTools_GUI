import guiTools, requests, json, os,gui,functions
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    def __init__(self, url, filepath):
        super().__init__()
        self.url = url
        self.filepath = filepath
    def run(self):
        response = requests.get(self.url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        with open(self.filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress_percent = int((downloaded_size / total_size) * 100)
                    self.progress.emit(progress_percent)
            self.finished.emit()
class StoryPlayer(qt.QWidget):
    def __init__(self):
        super().__init__()        
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
        self.bookmarksPosition=None
        self.isAMustToGoToBookmark=False
        self.categories_data = self.load_categories()
        self.categoriesLabel = qt.QLabel("اختيار فئة")
        self.categoriesLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.categorySearchLabel = qt.QLabel("ابحث عن فئة")
        self.categorySearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.categorySearchEdit = qt.QLineEdit()
        self.categorySearchEdit.setAccessibleName("ابحث عن فئة")
        self.categorySearchEdit.setObjectName("categorySearch")
        self.categoriesListWidget = guiTools.QListWidget()
        self.categoriesListWidget.itemSelectionChanged.connect(self.on_category_selected)        
        self.storiesLabel = qt.QLabel("القصص")
        self.storiesLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.storySearchLabel = qt.QLabel("ابحث عن قصة")
        self.storySearchLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.storySearchEdit = qt.QLineEdit()
        self.storySearchEdit.setAccessibleName("ابحث عن قصة")
        self.storySearchEdit.setObjectName("storiesSearch")
        self.storiesListWidget = guiTools.QListWidget()
        self.storiesListWidget.clicked.connect(self.play_selected_story)        
        self.categorySearchEdit.textChanged.connect(self.category_onsearch)
        self.storySearchEdit.textChanged.connect(self.story_onsearch)        
        self.categoriesList = list(self.categories_data.keys())
        self.categoriesList.sort()
        self.categoriesListWidget.addItems(self.categoriesList)        
        self.progressBar = qt.QProgressBar()
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progressBar.setVisible(False)
        self.mp = QMediaPlayer()
        self.au = QAudioOutput()
        self.mp.setAudioOutput(self.au)        
        self.openBookmarks=qt.QPushButton("العلامات المرجعية")
        self.openBookmarks.setDefault(True)
        self.openBookmarks.clicked.connect(self.onBookmarkOpened)
        self.openBookmarks.setShortcut("ctrl+shift+b")
        self.openBookmarks.setAccessibleDescription("control plus shift plus b")
        self.openBookmarks.setFixedSize(150,40)
        self.play_all_to_end = qt.QPushButton("تشغيل كل القصص من بداية القصة المركز عليها الى النهاية")
        self.play_all_to_end.setAccessibleDescription("control plus A")
        self.play_all_to_end.setCheckable(True)
        self.play_all_to_end.setDefault(True)
        self.play_all_to_end.setShortcut("ctrl+a")
        self.play_all_to_end.toggled.connect(lambda checked: self.update_button_style(self.play_all_to_end, checked))
        self.play_all_to_end.toggled.connect(self.handle_play_all_toggled)        
        self.play_all_to_start = qt.QPushButton("تشغيل كل القصص من بداية القصة المركز عليها الى البداية")
        self.play_all_to_start.setAccessibleDescription("control plus shift plus A")
        self.play_all_to_start.setCheckable(True)
        self.play_all_to_start.setDefault(True)
        self.play_all_to_start.setShortcut("ctrl+shift+a")
        self.play_all_to_start.toggled.connect(lambda checked: self.update_button_style(self.play_all_to_start, checked))
        self.play_all_to_start.toggled.connect(self.handle_play_all_start_toggled)        
        self.repeat_story_button = qt.QPushButton("تكرار تشغيل القصة المحددة")
        self.repeat_story_button.setAccessibleDescription("control plus R")
        self.repeat_story_button.setCheckable(True)
        self.repeat_story_button.setDefault(True)
        self.repeat_story_button.setShortcut("ctrl+r")
        self.repeat_story_button.toggled.connect(lambda checked: self.update_button_style(self.repeat_story_button, checked))
        self.repeat_story_button.toggled.connect(self.handle_repeat_toggled)        
        self.Slider = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Slider.setRange(0, 100)
        self.Slider.setAccessibleName("الوقت المنقدي")
        self.Slider.setTracking(True)
        self.Slider.valueChanged.connect(self.set_position_from_slider)
        self.Slider.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.Slider.customContextMenuRequested.connect(self.onAddNewBookmark)
        self.mp.durationChanged.connect(self.update_slider)
        self.mp.positionChanged.connect(self.update_slider)        
        self.duration = qt.QLabel()
        self.duration.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.duration.setAccessibleDescription("مدة المقطع")
        self.duration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.mp.mediaStatusChanged.connect(self.handle_media_status_changed)        
        self.dl_all_app = qt.QPushButton("تحميل جميع القصص المتاحة لهذه الفئة في التطبيق")
        self.dl_all_app.setDefault(True)
        self.dl_all_app.clicked.connect(self.download_all_stories_to_app)
        self.dl_all = qt.QPushButton("تحميل جميع القصص المتاحة لهذه الفئة في الجهاز")
        self.dl_all.setDefault(True)
        self.dl_all.clicked.connect(self.download_all_stories_to_device)
        self.delete = qt.QPushButton("حذف كل القصص للفئة الحالية من التطبيق")
        self.delete .setStyleSheet("background-color: #8B0000; color: white;")
        self.delete.setDefault(True)
        self.delete.setVisible(False)
        self.delete.clicked.connect(lambda: self.delete_story())        
        self.user_guide=qt.QPushButton("دليل الاختصارات")
        self.user_guide.setDefault(True)
        self.user_guide.setShortcut("ctrl+f1")
        self.user_guide.setAccessibleDescription("control plus f1")
        self.user_guide.setFixedSize(150,40)
        self.user_guide.clicked.connect(lambda: guiTools.TextViewer(self,"دليل الاختصارات","ctrl+s: إيقاف\nspace: التشغيل والإيقاف المؤقت\nalt زائد السهم الأيمن: التقديم السريع لمدة 5 ثواني\nalt زائد السهم الأيسر: الترجيع السريع لمدة 5 ثواني\nalt زائد السهم الأعلى: التقديم السريع لمدة 10 ثواني\nalt زائد السهم الأسفل: الترجيع السريع لمدة 10 ثواني\nctrl زائد السهم الأيمن: التقديم السريع لمدة 30 ثانية\nctrl زائد السهم الأيسر: الترجيع السريع لمدة 30 ثانية\nctrl زائد السهم الأعلى: التقديم السريع لمدة دقيقة\nctrl زائد السهم الأسفل: الترجيع  السريع لمدة دقيقة\nctrl زائد رقم: الانتقال الى موضع محدد من المقطع, مثلا ctrl+10 الانتقال الى 10% من المقطع\nshift زائد السهم الأعلى: رفع الصوت\nshift زائد السهم الأسفل: خفض الصوت\nالضغط على زر التطبيقات على شريط مدة المقطع يسمح بإضافة علامة مرجعية للموضع الحالي\nctrl+shift+b: فتح نافذة العلامات المرجعية\nctrl+f1: دليل الاختصارات").exec())
        categoriesLayout = qt.QVBoxLayout()
        categoriesLayout.addWidget(self.categoriesLabel)
        categoriesLayout.addWidget(self.categorySearchLabel)
        categoriesLayout.addWidget(self.categorySearchEdit)
        categoriesLayout.addWidget(self.categoriesListWidget)        
        storiesLayout = qt.QVBoxLayout()
        storiesLayout.addWidget(self.storiesLabel)
        storiesLayout.addWidget(self.storySearchLabel)
        storiesLayout.addWidget(self.storySearchEdit)
        storiesLayout.addWidget(self.storiesListWidget)        
        topLayout = qt.QHBoxLayout()
        topLayout.addLayout(categoriesLayout)
        topLayout.addLayout(storiesLayout)        
        layout = qt.QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addWidget(self.dl_all_app)
        layout.addWidget(self.delete)
        layout.addWidget(self.dl_all)        
        layout.addWidget(self.Slider)
        layout.addWidget(self.play_all_to_end)
        layout.addWidget(self.play_all_to_start)
        layout.addWidget(self.repeat_story_button)
        layout.addWidget(self.progressBar)
        layout1=qt.QHBoxLayout()        
        layout1.addWidget(self.user_guide)
        layout1.addWidget(self.duration)
        layout1.addWidget(self.openBookmarks)
        layout.addLayout(layout1)
        self.setLayout(layout)        
        if self.categoriesListWidget.count() > 0:
            self.categoriesListWidget.setCurrentRow(0)
            self.on_category_selected()            
        self.storiesListWidget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.storiesListWidget.customContextMenuRequested.connect(self.open_context_menu)    
    def update_button_style(self, button, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
        else:
            button.setStyleSheet("")    
    def handle_play_all_toggled(self, checked):
        self.mp.stop()
        if checked:
            self.play_all_to_start.setEnabled(False)
            self.repeat_story_button.setEnabled(False)
            if self.storiesListWidget.currentRow() == -1 and self.storiesListWidget.count() > 0:
                self.storiesListWidget.setCurrentRow(0)
            self.play_selected_story()
        else:
            self.play_all_to_start.setEnabled(True)
            self.repeat_story_button.setEnabled(True)    
    def handle_play_all_start_toggled(self, checked):
        self.mp.stop()
        if checked:
            self.play_all_to_end.setEnabled(False)
            self.repeat_story_button.setEnabled(False)
            if self.storiesListWidget.currentRow() == -1 and self.storiesListWidget.count() > 0:
                self.storiesListWidget.setCurrentRow(self.storiesListWidget.count() - 1)
            self.play_selected_story()
        else:
            self.play_all_to_end.setEnabled(True)
            self.repeat_story_button.setEnabled(True)    
    def handle_repeat_toggled(self, checked):
        if checked:
            self.play_all_to_end.setEnabled(False)
            self.play_all_to_start.setEnabled(False)
        else:
            self.play_all_to_end.setEnabled(True)
            self.play_all_to_start.setEnabled(True)    
    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_story_button.isChecked():
                self.mp.setPosition(0)
                self.play_selected_story()
            elif self.play_all_to_end.isChecked():
                self.play_next_in_list()
            elif self.play_all_to_start.isChecked():
                self.play_previous_in_list()    
    def play_next_in_list(self):
        current_row = self.storiesListWidget.currentRow()
        if current_row < self.storiesListWidget.count() - 1:
            self.storiesListWidget.setCurrentRow(current_row + 1)
            self.play_selected_story()
        else:
            self.play_all_to_end.setChecked(False)    
    def play_previous_in_list(self):
        current_row = self.storiesListWidget.currentRow()
        if current_row > 0:
            self.storiesListWidget.setCurrentRow(current_row - 1)
            self.play_selected_story()
        else:
            self.play_all_to_start.setChecked(False)    
    def delete_story(self, story_name=None):
        selected_category_item = self.categoriesListWidget.currentItem()
        if not selected_category_item:
            return
        category = selected_category_item.text()
        category_folder = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category)
        try:
            if story_name:
                story_path = os.path.join(category_folder, f"{story_name}.mp3")
                if os.path.exists(story_path):
                    confirm = guiTools.QQuestionMessageBox.view(
                        self,
                        "تأكيد الحذف",
                        "هل أنت متأكد أنك تريد حذف القصة المحددة؟",
                        "نعم","لا")
                    if confirm == 0:
                        try:
                            os.remove(story_path)
                            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف القصة بنجاح.")
                        except PermissionError:
                            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف القصة. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
            else:
                if os.path.exists(category_folder):
                    confirm = guiTools.QQuestionMessageBox.view(
                        self,
                        "تأكيد الحذف",
                        "هل أنت متأكد أنك تريد حذف جميع القصص؟",
                        "نعم","لا")
                    if confirm == 0:
                        for file in os.listdir(category_folder):
                            if file.endswith(".mp3"):
                                try:
                                    os.remove(os.path.join(category_folder, file))
                                except PermissionError:
                                    guiTools.qMessageBox.MessageBox.error(
                                        self,
                                        "خطأ",
                                        "تعذر حذف بعض الملفات. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج"
                                    )
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف جميع القصص بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ غير متوقع", str(e))
        self.check_all_stories_downloaded()    
    def check_all_stories_downloaded(self):
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            category = selected_category_item.text()
            category_folder = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category)
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
            return None
        category = selected_category_item.text()
        selected_item = self.storiesListWidget.currentItem()
        if not selected_item:
            return None
        story_name = selected_item.text()
        story_path = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category, f"{story_name}.mp3")        
        action = qt.QWidgetAction(self)
        btn = qt.QPushButton("حذف القصة المحددة من التطبيق")
        btn.setStyleSheet("background-color: #8B0000; color: white;")
        btn.setDefault(True)    
        btn.clicked.connect(lambda: self.delete_story(story_name))
        action.setDefaultWidget(btn)    
        if os.path.exists(story_path):
            return action
        else:
            return None
    def download_selected_story_to_app(self):
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storiesListWidget.currentItem()
            if selected_item:
                url = self.categories_data[category][selected_item.text()]
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category)
                os.makedirs(audio_folder, exist_ok=True)
                filepath = os.path.join(audio_folder, f"{selected_item.text()}.mp3")
                if self.is_audio_downloaded(filepath):
                    guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "القصة محملة بالفعل.")
                    return
                self.progressBar.setVisible(True)
                self.download_thread = DownloadThread(url, filepath)
                self.download_thread.progress.connect(self.progressBar.setValue)
                self.download_thread.finished.connect(self.download_story_complete)
                self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تحميل المقطع: " + str(e))    
    def download_all_stories_to_app(self):
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            self.files_to_download = [
                (file_name, url)
                for file_name, url in self.categories_data.get(category, {}).items()
                if not self.is_audio_downloaded(
                    os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category, f"{file_name}.mp3")
                )
            ]
            self.current_file_index = 0
            if not self.files_to_download:
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "جميع القصص محملة بالفعل")
                return
            response = guiTools.QQuestionMessageBox.view(
                self,
                "تأكيد التحميل",
                "هل تريد تحميل جميع القصص المتاحة لهذه الفئة؟",
                "نعم","لا")
            if response == 0:
                app_folder = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category)
                os.makedirs(app_folder, exist_ok=True)
                self.save_folder = app_folder
                self.download_next_story_to_app()
            else:
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء العملية", "تم إلغاء تحميل القصص.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء بدء التحميل: " + str(e))    
    def is_audio_downloaded(self, filepath):
        return os.path.exists(filepath)    
    def download_next_story_to_app(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.download_thread = DownloadThread(url, filepath)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.download_next_story_to_app)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل جميع القصص بنجاح.")    
    def download_story_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل القصة بنجاح.")    
    def download_all_stories_to_device(self):
        selected_category_item = self.categoriesListWidget.currentItem()
        if not selected_category_item:
            return
        category_name = selected_category_item.text()
        self.files_to_download = list(self.categories_data.get(category_name, {}).items())
        self.current_file_index = 0
        save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ القصص")
        if not save_folder:
            return
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل",
            "هل أنت متأكد من تحميل جميع القصص؟",
            "نعم","لا")
        if response == 0:
            self.save_folder = save_folder
            self.download_next_story()
        else:
            guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء التحميل.")    
    def download_next_story(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = f"{self.save_folder}/{file_name}.mp3"
            self.current_file_index += 1
            self.download_thread = DownloadThread(url, filepath)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            guiTools.qMessageBox.MessageBox.view(self, "تم التحميل", "تم تحميل جميع القصص.")    
    def update_progress(self, progress_percent):
        self.progressBar.setValue(progress_percent)    
    def download_finished(self):
        self.progressBar.setVisible(True)
        self.download_next_story()
    def download_complete(self):
        self.progressBar.setVisible(False)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل القصة")
    def on_category_selected(self):
        self.mp.stop()
        self.storiesListWidget.clear()
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            category = selected_category_item.text()
            for story, link in self.categories_data[category].items():
                self.storiesListWidget.addItem(story)
            self.check_all_stories_downloaded()
    def search(self, search_text, data):
        return [item for item in data if search_text in item.lower()]    
    def category_onsearch(self):
        search_text = self.categorySearchEdit.text().lower()
        self.categoriesListWidget.clear()
        result = self.search(search_text, self.categoriesList)
        self.categoriesListWidget.addItems(result)    
    def story_onsearch(self):
        search_text = self.storySearchEdit.text().lower()
        self.storiesListWidget.clear()
        selected_category_item = self.categoriesListWidget.currentItem()
        if selected_category_item:
            category = selected_category_item.text()
            story_list = list(self.categories_data[category].keys())
        else:
            story_list = []
        result = self.search(search_text, story_list)
        self.storiesListWidget.addItems(result)    
    def play_selected_story(self):
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storiesListWidget.currentItem()
            if selected_item:
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category)
                audio_path = os.path.join(audio_folder, selected_item.text() + ".mp3")
                if os.path.exists(audio_path):
                    self.mp.setSource(qt2.QUrl.fromLocalFile(audio_path))
                    self.mp.play()
                else:
                    url = self.categories_data[category][selected_item.text()]
                    self.mp.setSource(qt2.QUrl(url))
                    self.mp.play()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تشغيل المقطع:" + str(e))    
    def download_selected_story(self):
        try:
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            selected_item = self.storiesListWidget.currentItem()
            if selected_item:
                url = self.categories_data[category][selected_item.text()]
                filepath, _ = qt.QFileDialog.getSaveFileName(self, "save story", "", "Audio Files (*.mp3)")
                if filepath:
                    self.progressBar.setVisible(True)
                    self.download_thread = DownloadThread(url, filepath)
                    self.download_thread.progress.connect(self.progressBar.setValue)
                    self.download_thread.finished.connect(self.download_complete)
                    self.download_thread.start()
        except:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ ما")        
    def open_context_menu(self, position):
        menu=qt.QMenu(self)
        menu.setAccessibleName("خيارات القصة")
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        play_action = qt1.QAction("تشغيل القصة المحددة", self)
        play_action.triggered.connect(self.play_selected_story)
        menu.addAction(play_action)
        selected_item = self.storiesListWidget.currentItem()
        if selected_item:
            story_name = selected_item.text()
            selected_category_item = self.categoriesListWidget.currentItem()
            if not selected_category_item:
                return
            category = selected_category_item.text()
            story_path = os.path.join(os.getenv('appdata'), app.appName, "audio_stories", category, f"{story_name}.mp3")
            if not os.path.exists(story_path):
                download_app_action = qt1.QAction("تحميل القصة المحددة في التطبيق", self)
                download_app_action.triggered.connect(self.download_selected_story_to_app)
                menu.addAction(download_app_action)
            download_device_action = qt1.QAction("تحميل القصة المحددة في الجهاز", self)
            download_device_action.triggered.connect(self.download_selected_story)
            menu.addAction(download_device_action)
        delete_option = self.check_current_story_downloaded()
        if delete_option:
            menu.addAction(delete_option)
        addNewBookmarkAction=qt1.QAction("إضافة علامة مرجعية",self)
        menu.addAction(addNewBookmarkAction)
        addNewBookmarkAction.triggered.connect(self.onAddNewBookmark)
        menu.exec(self.storiesListWidget.viewport().mapToGlobal(position))    
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
    def increase_volume(self):
        current_volume = self.au.volume()
        new_volume = current_volume + 0.10
        self.au.setVolume(new_volume)
    def decrease_volume(self):
        current_volume = self.au.volume()
        new_volume = current_volume - 0.10
        self.au.setVolume(new_volume)
    def set_position_from_slider(self, value):
        duration = self.mp.duration()
        new_position = int((value / 100) * duration)
        self.mp.setPosition(new_position)
    def update_slider(self):
        if self.isAMustToGoToBookmark and self.mp.position()>=3000:
            self.isAMustToGoToBookmark=False
            self.mp.setPosition(self.bookmarksPosition)
        try:
            self.Slider.blockSignals(True)
            self.Slider.setValue(int((self.mp.position() / self.mp.duration()) * 100))
            self.Slider.blockSignals(False)
            self.time_VA()
        except:
            self.duration.setText("خطأ في الحصول على مدة المقطع")
    def time_VA(self):
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
    def load_categories():
        file_path = "data/json/files/all_audio_stories.json"
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    def onBookmarkOpened(self):
        gui.book_marcks(self,"stories").exec()
    def onAddNewBookmark(self):
        name,ok=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب اسم العلامة المرجعية")
        if ok:
            type=self.categoriesListWidget.currentRow()
            surah=self.storiesListWidget.currentRow()
            position=self.mp.position()
            functions.bookMarksManager.addNewaudioBookMark("stories",type,surah,position,name)