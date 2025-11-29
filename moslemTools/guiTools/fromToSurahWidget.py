import functions, gui, guiTools, os, json, requests, subprocess
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import settings_handler
from settings.app import appName
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
            command = [
                self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_filepath,
                "-ar", "44100", "-ac", "2", "-b:a", "192k", self.output_file
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
class FromToSurahWidget(qt.QDialog):
    def __init__(self, p, index:int):
        super().__init__()
        self.p = p
        self.index = index
        self.original_height = 300
        self.merge_ui_height = 450
        self.resize(300, self.original_height)                 
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)         
        item_name = ""
        if index == 0:
            self.surahs = functions.quranJsonControl.getSurahs()
            self.setWindowTitle("تحديد سور القرآن الكريم")
            item_name = "السورة"
        elif index == 1:
            self.surahs = functions.quranJsonControl.getPage()
            self.setWindowTitle("تحديد صفحات القرآن الكريم")
            item_name = "الصفحة"
        elif index == 2:
            self.surahs = functions.quranJsonControl.getJuz()
            self.setWindowTitle("تحديد أجزاء القرآن الكريم")
            item_name = "الجزء"
        elif index == 3:
            self.surahs = functions.quranJsonControl.getHezb()
            self.setWindowTitle("تحديد أرباع القرآن الكريم")
            item_name = "الربع"
        elif index == 4:
            self.surahs = functions.quranJsonControl.getHizb()
            self.setWindowTitle("تحديد أحزاب القرآن الكريم")
            item_name = "الحزب"
        
        self.label_from_surah = qt.QLabel(f"من {item_name}")
        self.combo_from_surah = qt.QComboBox()
        self.combo_from_surah.setAccessibleName(f"من {item_name}")
        self.combo_from_surah.addItems(self.surahs.keys())
        self.combo_from_surah.setFont(font)        
        self.label_from_verse = qt.QLabel("من الآية")
        self.spin_from_verse = qt.QSpinBox()
        self.spin_from_verse.setAccessibleName("من الآية")
        self.spin_from_verse.setFont(font)        
        self.label_to_surah = qt.QLabel(f"إلى {item_name}")
        self.combo_to_surah = qt.QComboBox()
        self.combo_to_surah.setAccessibleName(f"إلى {item_name}")
        self.combo_to_surah.addItems(self.surahs.keys())
        self.combo_to_surah.setFont(font)
        self.label_to_verse = qt.QLabel("إلى الآية")
        self.spin_to_verse = qt.QSpinBox()
        self.spin_to_verse.setAccessibleName("إلى الآية")
        self.spin_to_verse.setFont(font)
        self.go = guiTools.QPushButton("خيارات")
        self.go.setStyleSheet("""
        QPushButton {
            background-color: #1e7e34; color: white; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold;
        }
        QPushButton:hover { background-color: #19692c; }
        """)
        self.go.setFont(font)        
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_feedback_label.setWordWrap(True)        
        self.merge_progress_bar = qt.QProgressBar()        
        self.merge_action_button = guiTools.QPushButton("إلغاء الدمج")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
        self.merge_action_button.clicked.connect(self.handle_merge_action)        
        merge_layout = qt.QVBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)        
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)        
        
        # Start of Layout changes for spacing and alignment
        h_layout1 = qt.QHBoxLayout()
        h_layout1.setSpacing(10) # Increased spacing to 10
        h_layout1.addWidget(self.combo_from_surah) 
        h_layout1.addWidget(self.label_from_surah) 
        h_layout1.addStretch() 

        h_layout2 = qt.QHBoxLayout()
        h_layout2.setSpacing(10) # Increased spacing to 10
        h_layout2.addWidget(self.spin_from_verse) 
        h_layout2.addWidget(self.label_from_verse) 
        h_layout2.addStretch() 

        h_layout3 = qt.QHBoxLayout()
        h_layout3.setSpacing(10) # Increased spacing to 10
        h_layout3.addWidget(self.combo_to_surah) 
        h_layout3.addWidget(self.label_to_surah) 
        h_layout3.addStretch() 
        
        h_layout4 = qt.QHBoxLayout()
        h_layout4.setSpacing(10) # Increased spacing to 10
        h_layout4.addWidget(self.spin_to_verse) 
        h_layout4.addWidget(self.label_to_verse) 
        h_layout4.addStretch() 

        self.controls_widget = qt.QWidget()
        controls_layout = qt.QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        controls_layout.addLayout(h_layout1)
        controls_layout.addLayout(h_layout2)
        controls_layout.addLayout(h_layout3)
        controls_layout.addLayout(h_layout4)
        controls_layout.addWidget(self.go)
        
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(0) 
        main_layout.setContentsMargins(15, 15, 15, 15) # Increased margins to 15
        main_layout.addWidget(self.controls_widget)
        main_layout.addWidget(self.merge_widget)
        # End of Layout changes
        
        self.combo_from_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.combo_to_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.spin_from_verse.valueChanged.connect(self.validate_verse_ranges)
        self.spin_to_verse.valueChanged.connect(self.validate_verse_ranges)
        self.go.clicked.connect(self.onGo)            
        self.update_spin_boxes(set_to_verse_to_max=True)                
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onOpen)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.onListenActionTriggert)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.onTafseerActionTriggered)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.onTranslationActionTriggered)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.onIarabActionTriggered)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.onMergeActionTriggered)
        qt1.QShortcut("escape", self).activated.connect(self.close)
    def update_spin_boxes(self, set_to_verse_to_max=False):        
        self.spin_from_verse.blockSignals(True)
        self.spin_to_verse.blockSignals(True)
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()        
        if to_surah_index < from_surah_index:
            self.combo_to_surah.setCurrentIndex(from_surah_index)
            to_surah_index = from_surah_index
        surah_from_text = self.combo_from_surah.currentText()
        surah_to_text = self.combo_to_surah.currentText()        
        num_verses_from = len(self.surahs[surah_from_text][1].split("\n")) if len(self.surahs[surah_from_text]) > 1 else 1
        num_verses_to = len(self.surahs[surah_to_text][1].split("\n")) if len(self.surahs[surah_to_text]) > 1 else 1        
        self.spin_from_verse.setRange(1, num_verses_from)
        self.spin_to_verse.setRange(1, num_verses_to)        
        if self.spin_from_verse.value() > num_verses_from or self.spin_from_verse.value() < 1:
            self.spin_from_verse.setValue(1)
        if set_to_verse_to_max or self.spin_to_verse.value() > num_verses_to or self.spin_to_verse.value() < 1:
            self.spin_to_verse.setValue(num_verses_to)                
        self.spin_from_verse.blockSignals(False)
        self.spin_to_verse.blockSignals(False)                
        self.validate_verse_ranges()
    def validate_verse_ranges(self):
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()
        from_verse_val = self.spin_from_verse.value()
        to_verse_val = self.spin_to_verse.value()        
        if from_surah_index == to_surah_index:            
            if to_verse_val < from_verse_val:
                self.spin_to_verse.blockSignals(True)
                self.spin_to_verse.setValue(from_verse_val)
                self.spin_to_verse.blockSignals(False)                
        elif from_surah_index > to_surah_index:
             self.combo_to_surah.setCurrentIndex(from_surah_index)
             self.update_spin_boxes(set_to_verse_to_max=True)
    def get_range_label(self):
        from_item = self.combo_from_surah.currentText()
        to_item = self.combo_to_surah.currentText()
        from_ayah = self.spin_from_verse.value()
        to_ayah = self.spin_to_verse.value()
        item_type = ""
        if self.index == 0: item_type = "سورة"
        elif self.index == 1: item_type = "الصفحة"
        elif self.index == 2: item_type = "الجزء"
        elif self.index == 3: item_type = "الربع"
        elif self.index == 4: item_type = "الحزب"    
        if from_item == to_item:
            return f"من {item_type} {from_item} آية {from_ayah} إلى آية {to_ayah}"
        else:
            return f"من {item_type} {from_item} آية {from_ayah} إلى {item_type} {to_item} آية {to_ayah}"
    def _get_selected_ayahs(self):
        self.validate_verse_ranges() 
        return functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )    
    def onOpen(self):
        result = self._get_selected_ayahs()
        label = self.get_range_label()
        gui.QuranViewer(self.p, "\n".join(result), 5, label, enableNextPreviouseButtons=False, enableBookmarks=False).exec()            
    def onGo(self):
        menu = qt.QMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("خيارات")
        menu.setFont(font)         
        readAction = qt1.QAction("قراءة", self)
        readAction.setShortcut("ctrl+o")
        readAction.triggered.connect(self.onOpen)
        menu.addAction(readAction)
        menu.setDefaultAction(readAction)        
        listenAction = qt1.QAction("تشغيل", self)
        listenAction.setShortcut("ctrl+p")
        listenAction.triggered.connect(self.onListenActionTriggert)
        menu.addAction(listenAction)        
        tafseerAction = qt1.QAction("تفسير", self)
        tafseerAction.setShortcut("ctrl+t")
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        menu.addAction(tafseerAction)        
        translationAction = qt1.QAction("ترجمة", self)
        translationAction.setShortcut("ctrl+l")
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        menu.addAction(translationAction)        
        iarabAction = qt1.QAction("إعراب", self)
        iarabAction.setShortcut("ctrl+i")
        iarabAction.triggered.connect(self.onIarabActionTriggered)
        menu.addAction(iarabAction)        
        menu.addSeparator()
        mergeAction = qt1.QAction("دمج الآيات", self)
        mergeAction.setShortcut("ctrl+alt+d")
        mergeAction.triggered.connect(self.onMergeActionTriggered)
        menu.addAction(mergeAction)    
        menu.exec(qt1.QCursor.pos())
    def onListenActionTriggert(self):
        result = self._get_selected_ayahs()
        label = self.get_range_label()
        gui.QuranPlayer(self.p, "\n".join(result), 0, 5, label).exec()
    def onTafseerActionTriggered(self):
        result = self._get_selected_ayahs()
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض التفسير.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.TafaseerViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        result = self._get_selected_ayahs()
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الترجمة.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.translationViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self.p, "إعراب", result).exec()    
    def _get_current_reciter_name(self):
        return list(reciters.keys())[self.currentReciter]
    def _create_ayah_filename(self, ayah_text):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            return f"{surah_str}{ayah_str}.mp3"
        except:
            return None
    def handle_merge_action(self):
        if self.is_merging and self.merge_phase == 'merging':
            self.confirm_and_cancel_merge()
    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء",
            "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
    def onMergeActionTriggered(self):
        if self.is_merging: return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return    
        all_ayahs_text = self._get_selected_ayahs()
        if not all_ayahs_text:
            guiTools.qMessageBox.MessageBox.error(self, "تحذير", "لا توجد آيات في النطاق المحدد للدمج.")
            return
        self.merge_list.clear()
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        reciter_name = self._get_current_reciter_name()
        reciter_url_base = reciters[reciter_name]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), appName, "reciters", reciter_folder_name)    
        ayahs_to_download = []
        for ayah_text in all_ayahs_text:
            ayah_filename = self._create_ayah_filename(ayah_text)
            if not ayah_filename: continue
            local_path = os.path.join(reciter_local_path_base, ayah_filename)
            ayah_info = {"filename": ayah_filename, "url": reciter_url_base + ayah_filename, "local_path": local_path}
            self.merge_list.append(ayah_info)
            if not os.path.exists(local_path):
                ayahs_to_download.append(ayah_info)        
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\n"
                               "سيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق النافذة**.\n"
                               "بعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\n"
                               "هل أنت متأكد أنك تريد المتابعة؟")
        else:
            confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\n"
                               "ستبدأ عملية الدمج الآن. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق النافذة حتى انتهاء العملية.\n\n"
                               "هل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0: return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename: return
        self.set_ui_for_merge(True)
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()
    def process_next_in_merge_queue(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
            return
        next_item_to_download = next((item for item in self.merge_list if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads), None)    
        if next_item_to_download:
            self.merge_phase = 'downloading'
            self.merge_action_button.hide()
            self.merge_feedback_label.setText("جاري تحميل الآيات المطلوبة...")
            self.merge_progress_bar.show()            
            output_dir = os.path.dirname(self.current_merge_output_path)
            safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
            download_path = os.path.join(output_dir, f"temp_{safe_filename}")            
            self.current_download_url = next_item_to_download['url']
            self.download_thread = DownloadThread(self.current_download_url, download_path)
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
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", 
                "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
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
        self.controls_widget.setEnabled(not is_active)
        if is_active:
            self.setFixedHeight(self.merge_ui_height)
            self.merge_widget.setVisible(True)
            self.merge_feedback_label.setText("جاري التحضير لعملية الدمج...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
        else:
            self.merge_widget.setVisible(False)
            self.setFixedHeight(self.original_height)
    def closeEvent(self, event):
        if self.is_merging:
            if self.merge_phase == 'downloading':
                guiTools.qMessageBox.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء تحميل الآيات. الرجاء الانتظار.")
                event.ignore()
            elif self.merge_phase == 'merging':
                reply = guiTools.QQuestionMessageBox.view(self, "تأكيد", "عملية الدمج قيد التشغيل. هل تريد إلغاءها والخروج؟", "نعم", "لا")
                if reply == 0:
                    self.cancellation_requested = True
                    if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                        self.merge_thread.stop()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            super().closeEvent(event)