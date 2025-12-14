import gui.translationViewer
import gui, guiTools, functions, re, os, json, requests, subprocess
from settings.app import appName
from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)
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
class PreMergeCheckThread(qt2.QThread):
    finished = qt2.pyqtSignal(list, list, str, str)
    error = qt2.pyqtSignal(str)
    def __init__(self, all_ayahs_text, current_reciter, reciters_data, current_item_text, current_type_index):
        super().__init__()
        self.all_ayahs_text = all_ayahs_text
        self.current_reciter = current_reciter
        self.reciters_data = reciters_data
        self.current_item_text = current_item_text
        self.current_type_index = current_type_index
    def _create_ayah_filename(self, ayah_text):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text, self.current_item_text, self.current_type_index)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            return f"{surah_str}{ayah_str}.mp3"
        except:
            return None
    def run(self):
        try:
            reciter_name = list(self.reciters_data.keys())[self.current_reciter]
            reciter_url_base = self.reciters_data[reciter_name]
            reciter_folder_name = reciter_url_base.split("/")[-3]
            reciter_local_path_base = os.path.join(os.getenv('appdata'), appName, "reciters", reciter_folder_name)
            merge_list = []
            ayahs_to_download = []
            for ayah_text in self.all_ayahs_text:
                ayah_filename = self._create_ayah_filename(ayah_text)
                if not ayah_filename: continue
                local_path = os.path.join(reciter_local_path_base, ayah_filename)
                ayah_info = {"filename": ayah_filename, "url": reciter_url_base + ayah_filename, "local_path": local_path}
                merge_list.append(ayah_info)
                if not os.path.exists(local_path):
                    ayahs_to_download.append(ayah_info)
            self.finished.emit(merge_list, ayahs_to_download, reciter_name, reciter_local_path_base)
        except Exception as e:
            self.error.emit(f"حدث خطأ أثناء التحضير للدمج: {str(e)}")
class Quran(qt.QWidget):
    def __init__(self):
        super().__init__()
        qt1.QShortcut("ctrl+p",self).activated.connect(self.onListenActionTriggert)
        qt1.QShortcut("ctrl+t",self).activated.connect(self.onTafseerActionTriggered)
        qt1.QShortcut("ctrl+l",self).activated.connect(self.onTranslationActionTriggered)
        qt1.QShortcut("ctrl+i",self).activated.connect(self.onIarabActionTriggered)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.onMergeActionTriggered)
        self.infoData = []
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.setStyleSheet("QWidget{color:#f0f0f0;font:bold 12px;}QLineEdit{background-color:#3e3e3e;border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QComboBox,QLabel{border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QLineEdit:focus{border:1px solid #0078d7;}QComboBox QAbstractItemView::item:selected{background-color:blue;color:white;}QPushButton{background-color:#0056b3;color:white;border:none;border-radius:5px;padding:5px;}QPushButton:hover{background-color:#003d80;}QPushButton#customButton{background-color:#008000;color:white;border:none;}QPushButton#customButton:hover{background-color:#006600;}QPushButton#cancelMergeButton{background-color:#dc3545;color:white;font-weight:bold;}QPushButton#cancelMergeButton:hover{background-color:#c82333;}QListWidget{background-color:#000000;border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QListWidget::item:selected{background-color:red;}QMenu{background-color:#3e3e3e;color:#f0f0f0;}QMenu::item:selected{background-color:#0078d7;}")
        browse_layout = qt.QHBoxLayout()
        browse_layout.setSpacing(10)
        layout1=qt.QVBoxLayout()
        self.by = qt.QLabel("التصفح ب")
        self.by.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout1.addWidget(self.by)
        self.type = qt.QComboBox()
        self.type.setFixedWidth(100)
        self.type.setAccessibleName("التصفح ب")
        self.type.addItems(["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"])
        self.type.currentIndexChanged.connect(self.onTypeChanged)
        layout1.addWidget(self.type)
        self.custom = guiTools.QPushButton("التصفح المخصص")
        self.custom.setMaximumHeight(30)
        self.custom.setMaximumWidth(160)
        self.custom.setObjectName("customButton")
        self.custom.setShortcut("ctrl+c")
        self.custom.setAccessibleDescription("control plus c")
        self.custom.clicked.connect(self.onCostumBTNClicked)
        self.custom.setMaximumWidth(150)
        self.custom.setMaximumHeight(150)
        layout2=qt.QVBoxLayout()
        layout2.addWidget(self.custom)
        browse_layout.addLayout(layout1)
        browse_layout.addLayout(layout2)
        layout.addLayout(browse_layout)
        self.serch = qt.QLabel("البحث عن محتوى فئة")
        self.serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن محتوى فئة")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.info = guiTools.QListWidget()
        self.info.setSpacing(3)
        font=qt1.QFont()
        font.setBold(True)
        self.info.setFont(font)
        self.info.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.info.customContextMenuRequested.connect(self.onContextMenu)
        self.info.itemActivated.connect(self.onItemTriggered)
        layout.addWidget(self.info)
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_action_button = guiTools.QPushButton("إلغاء الدمج")
        self.merge_action_button.setObjectName("cancelMergeButton")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        merge_layout = qt.QHBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        layout.addWidget(self.merge_widget)
        guide_layout = qt.QHBoxLayout()
        self.info_of_quran= guiTools.QPushButton("معلومات عن المصحف")
        self.info_of_quran.setShortcut("ctrl+shift+q")
        self.info_of_quran.setAccessibleDescription("control plus shift plus Q")
        self.info_of_quran.setFixedSize(150, 40)
        self.info_of_quran.clicked.connect(lambda: guiTools.TextViewer(self, "معلومات عن المصحف", ("معلومات عامة عن مصحف المدينة برواية حفص عن عاصم:\nعدد السور: 114 سورة (86 مكية + 28 مدنية).\nعدد الآيات: 6236 آية (بحسب رواية حفص، دون احتساب البسملة في السور ما عدا سورة الفاتحة).\nعدد الأجزاء: 30 جزءًا.\nعدد الأحزاب: 60 حزبًا.\nعدد الأرباع: 240 ربعًا (4 أرباع في الحزب، 8 أرباع في الجزء).\nعدد السجدات التلاوية: 15 سجدة.\nعدد الصفحات (في مصحف المدينة العادي): حوالي 604 صفحة.\n\nملاحظات:\nعدد الكلمات تقريبي، حوالي 77430 كلمة حسب طرق العد الطباعية.\nعدد الحروف تقريبي، يتراوح بين 320000 و324000 حرف حسب احتساب النقاط والحركات.\nعدد الركوعات تقريبي (558 ركوعاً)، وهو رقم متداول حسب تقسيم السور في الطبعات.\n\nكل الأرقام المدونة تمثل الطبعة الرسمية لمصحف المدينة برواية حفص عن عاصم، الصادرة عن مجمع الملك فهد لطباعة المصحف الشريف.")).exec())
        self.info1 = qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setText("لخيارات عنصر الفئة, نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        guide_layout.addWidget(self.info1)
        guide_layout.addWidget(self.info_of_quran)
        layout.addLayout(guide_layout)
        self.onTypeChanged(0)
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches
    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.info.clear()
        result = self.search(search_text, self.infoData)
        self.info.addItems(result)
    def onItemTriggered(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        
        selected_item_text = self.info.currentItem().text()
        
        try:
            correct_index = list(result.keys()).index(selected_item_text)
        except ValueError:
            correct_index = self.info.currentRow()

        gui.QuranViewer(self, result[selected_item_text][1], index, selected_item_text, enableNextPreviouseButtons=True, typeResult=result, CurrentIndex=correct_index).exec()
    def onTypeChanged(self, index: int):
        self.info.clear()
        self.infoData = []
        if index == 0:
            self.infoData = list(functions.quranJsonControl.getSurahs().keys())
        elif index == 1:
            for i in range(1, 605):
                self.infoData.append(str(i))
        elif index == 2:
            for i in range(1, 31):
                self.infoData.append(str(i))
        elif index == 3:
            for i in range(1, 241):
                self.infoData.append(str(i))
        elif index == 4:
            for i in range(1, 61):
                self.infoData.append(str(i))
        self.info.addItems(self.infoData)
    def getResult(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        return result[self.info.currentItem().text()][1]
    def onContextMenu(self):
        menu = qt.QMenu(self)
        menu.setAccessibleName("خيارات عنصر الفئة")
        menu.setFocus()
        listenAction = qt1.QAction("تشغيل", self)
        listenAction.setShortcut("ctrl+p")
        menu.addAction(listenAction)
        listenAction.triggered.connect(self.onListenActionTriggert)
        menu.setDefaultAction(listenAction)
        tafseerAction = qt1.QAction("تفسير", self)
        tafseerAction.setShortcut("ctrl+t")
        menu.addAction(tafseerAction)
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        translationAction = qt1.QAction("ترجمة", self)
        translationAction.setShortcut("ctrl+l")
        menu.addAction(translationAction)
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        iarabAction = qt1.QAction("إعراب", self)
        iarabAction.setShortcut("ctrl+i")
        menu.addAction(iarabAction)
        iarabAction.triggered.connect(self.onIarabActionTriggered)
        menu.addSeparator()
        mergeAction = qt1.QAction("دمج الآيات", self)
        mergeAction.setShortcut("ctrl+alt+d")
        menu.addAction(mergeAction)
        mergeAction.triggered.connect(self.onMergeActionTriggered)
        menu.exec(qt1.QCursor.pos())
    def onListenActionTriggert(self):
        if not self.info.currentItem():
            return
        result = self.getResult()
        gui.QuranPlayer(self, result, 0, self.type.currentIndex(), self.info.currentItem().text()).exec()
    def onTafseerActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.TafaseerViewer(self, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.translationViewer(self, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self, "إعراب", result).exec()
    def onCostumBTNClicked(self):
        categories=["من سورة الى سورة", "من صفحة الى صفحة", "من جزء الى جزء", "من ربع الى ربع", "من حزب الى حزب"]
        menu=qt.QMenu("اختر فئة",self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        for category in categories:
            action=qt1.QAction(category,self)
            menu.addAction(action)
            action.triggered.connect(self.onCostumBTNRequested)
        menu.exec(qt1.QCursor.pos())
        menu.setFont(font)
    def onCostumBTNRequested(self):
        categories=["من سورة الى سورة", "من صفحة الى صفحة", "من جزء الى جزء", "من ربع الى ربع", "من حزب الى حزب"]
        index=categories.index(self.sender().text())
        guiTools.FromToSurahWidget(self,index).exec()
    def _get_current_reciter_name(self):
        return list(reciters.keys())[self.currentReciter]
    def _create_ayah_filename(self, ayah_text):
        category = self.info.currentItem().text()
        type_index = self.type.currentIndex()
        Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text, category, type_index)
        surah_str = str(surah).zfill(3)
        ayah_str = str(Ayah).zfill(3)
        return f"{surah_str}{ayah_str}.mp3"
    def handle_merge_action(self):
        if self.is_merging and self.merge_phase == 'merging':
            self.confirm_and_cancel_merge()
        elif self.is_merging and self.merge_phase == 'preparing':
            self.cancellation_requested = True
            if hasattr(self, 'pre_merge_thread') and self.pre_merge_thread.isRunning():
                self.pre_merge_thread.terminate()
            self.on_merge_finished(False, "تم إلغاء عملية التحضير من قبل المستخدم.")
    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
    def onMergeActionTriggered(self):
        if not self.info.currentItem():
            return
        if self.is_merging:
            return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        all_ayahs_text = self.getResult().split("\n")
        self.merge_list.clear()
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات المطلوبة...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(all_ayahs_text, self.currentReciter, reciters, self.info.currentItem().text(), self.type.currentIndex())
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()
    def on_pre_merge_check_finished(self, merge_list, ayahs_to_download, reciter_name, reciter_local_path_base):
        if self.cancellation_requested: return
        self.merge_list = merge_list
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
        else:
            confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن. يمكنك إلغاء عملية الدمج ولكن لا يمكنك التفاعل مع الواجهة حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_merge(False)
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.set_ui_for_merge(False)
            return
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()
    def process_next_in_merge_queue(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
            return
        output_dir = os.path.dirname(self.current_merge_output_path)
        next_item_to_download = None
        for item in self.merge_list:
            if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads:
                next_item_to_download = item
                break
        if next_item_to_download:
            self.merge_phase = 'downloading'
            self.merge_action_button.hide()
            self.merge_feedback_label.setText("جاري تحميل الآيات المطلوبة...")
            self.merge_progress_bar.show()
            url = next_item_to_download['url']
            safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
            download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.current_download_url = url
            self.download_thread = DownloadThread(url, download_path)
            self.download_thread.progress.connect(self.merge_progress_bar.setValue)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            self.finalize_and_execute_merge()
    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()
    def finalize_and_execute_merge(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية قبل بدء الدمج.")
            return
        self.merge_action_button.show()
        files_for_ffmpeg = []
        self.files_to_delete_after_merge.clear()
        output_dir = os.path.dirname(self.current_merge_output_path)
        for item in self.merge_list:
            if os.path.exists(item["local_path"]):
                files_for_ffmpeg.append(item["local_path"])
            else:
                safe_filename = "".join(c for c in item['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"temp_{safe_filename}")
                if os.path.exists(temp_path):
                    files_for_ffmpeg.append(temp_path)
                    if temp_path not in self.files_to_delete_after_merge:
                        self.files_to_delete_after_merge.append(temp_path)
                else:
                    self.on_merge_finished(False, f"خطأ: الملف المؤقت للآية لم يتم العثور عليه: {item['filename']}")
                    return
        if len(files_for_ffmpeg) != len(self.merge_list):
            self.on_merge_finished(False, "لم يتم العثور على جميع الملفات المطلوبة للدمج.")
            return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)
    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.merge_phase = 'merging'
        self.merge_feedback_label.setText(f"جاري دمج {len(self.merge_list)} آيات...")
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()
    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.merge_phase = 'idle'
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try: os.remove(self.current_merge_output_path)
                except: pass
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم دمج الآيات بنجاح.")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
            if reply == 0:
                for f_path in self.files_to_delete_after_merge:
                    if os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass
        self.set_ui_for_merge(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets_to_disable = [self.by, self.type, self.custom, self.serch, self.search_bar, self.info, self.info_of_quran, self.info1]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير لعملية الدمج...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)