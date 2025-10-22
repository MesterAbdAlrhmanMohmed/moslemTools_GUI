from guiTools import note_dialog
import functions.notesManager as notesManager
from .changeReciter import ChangeReciter
from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
from .quranPlayer import QuranPlayer
import time, winsound, pyperclip, os, json, re, requests, subprocess, shutil
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
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
class SearchModeDialog(qt.QDialog):
    def __init__(self, parent=None, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True):
        super().__init__(parent)
        self.setWindowTitle("إعدادات نمط البحث")
        self.setFixedSize(350, 200)
        self.initial_ignore_tashkeel = ignore_tashkeel
        self.initial_ignore_hamza = ignore_hamza
        self.initial_ignore_symbols = ignore_symbols
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols
        self.init_ui()
    def init_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        self.tashkeel_checkbox = qt.QCheckBox("تجاهل التشكيل")
        self.tashkeel_checkbox.setChecked(self.initial_ignore_tashkeel)
        self.tashkeel_checkbox.setFont(bold_font)
        self.tashkeel_checkbox.stateChanged.connect(self._set_ignore_tashkeel)
        layout.addWidget(self.tashkeel_checkbox)
        self.hamza_checkbox = qt.QCheckBox("تجاهل الهمزات")
        self.hamza_checkbox.setChecked(self.initial_ignore_hamza)
        self.hamza_checkbox.setFont(bold_font)
        self.hamza_checkbox.stateChanged.connect(self._set_ignore_hamza)
        layout.addWidget(self.hamza_checkbox)
        self.symbols_checkbox = qt.QCheckBox("تجاهل الرموز والعلامات")
        self.symbols_checkbox.setChecked(self.initial_ignore_symbols)
        self.symbols_checkbox.setFont(bold_font)
        self.symbols_checkbox.stateChanged.connect(self._set_ignore_symbols)
        layout.addWidget(self.symbols_checkbox)
        layout.addStretch(1)
        buttons_layout = qt.QHBoxLayout()
        self.apply_button = guiTools.QPushButton("تطبيق التغييرات")
        self.apply_button.setObjectName("applySearchModeChangesButton")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setAutoDefault(False)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)
    def _set_ignore_tashkeel(self, state):
        self.ignore_tashkeel = bool(state)
    def _set_ignore_hamza(self, state):
        self.ignore_hamza = bool(state)
    def _set_ignore_symbols(self, state):
        self.ignore_symbols = bool(state)
    def get_settings(self):
        return {
            "ignore_tashkeel": self.ignore_tashkeel,
            "ignore_hamza": self.ignore_hamza,
            "ignore_symbols": self.ignore_symbols
        }
class QuranViewer(qt.QDialog):
    def __init__(self,p,text:str,type:int,category,index=0,enableNextPreviouseButtons=False,typeResult=[],CurrentIndex=0,enableBookmarks=True):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.currentReciter=int(settings.settings_handler.get("g","reciter"))
        self.nameOfBookmark=""
        self.enableBookmarks=enableBookmarks
        self.type=type
        self.enableNextPreviouseButtons=enableNextPreviouseButtons
        self.typeResult=typeResult
        self.CurrentIndex=CurrentIndex
        self.initial_ayah_index = index
        self.context_menu_active = False
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_ayah_index = None
        self.was_playing_before_action = False
        self.original_quran_text = text
        self.is_search_view = False
        self.initial_enableBookmarks = enableBookmarks
        self.ignore_tashkeel = True
        self.ignore_hamza = True
        self.ignore_symbols = True
        self.resize(1200,600)
        self.type=type
        self.category=category
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج الآيات لن تعمل.")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.verse_numbering_mode = "by_surah"
        self.text_cache = {"by_surah": self.original_quran_text}
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.media.setAudioOutput(self.audioOutput)
        self.media.setSource(qt2.QUrl.fromLocalFile("data/sounds/001001.mp3"))
        self.media.play()
        time.sleep(0.5)
        self.media.stop()
        self.media.mediaStatusChanged.connect(self.on_state)
        self.quranText=text
        self.setStyleSheet("""
            QPushButton#startButton, QPushButton#applySearchModeChangesButton {
                background-color: #28a745; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#startButton:hover, QPushButton#applySearchModeChangesButton:hover { background-color: #218838; }
            QPushButton#startButton:pressed, QPushButton#applySearchModeChangesButton:pressed { background-color: #218838; }
            QPushButton#searchModeButton {
                background-color: #0056b3; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#searchModeButton:hover { background-color: #003d80; }
            QPushButton#searchModeButton:pressed { background-color: #003d80; }
            QPushButton#clearResultsButton, QPushButton#cancelButton {
                background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#clearResultsButton:hover, QPushButton#cancelButton:hover { background-color: #c82333; }
            QPushButton#clearResultsButton:pressed, QPushButton#cancelButton:pressed { background-color: #bd2130; }
        """)
        self.text=guiTools.QReadOnlyTextEdit()
        self._set_text_with_delay(text)
        self.update_font_size()
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.viewport().installEventFilter(self)
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media_progress.setAccessibleName("التحكم في تقدم الآية")
        self.time_label = qt.QLabel()
        self.time_label.setVisible(False)
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        progress_time_layout = qt.QHBoxLayout()
        progress_time_layout.addWidget(self.media_progress)
        progress_time_layout.addWidget(self.time_label)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        if self.type == 5 and isinstance(self.category, str):
            self.info.setText(self.category)
        else:
            if self.typeResult:
                formatted_name = self.format_category_name(self.type, list(self.typeResult.keys())[self.CurrentIndex])
                self.info.setText(formatted_name)
            else:
                self.info.setText("")
        layout=qt.QVBoxLayout(self)
        self.search_widget = qt.QWidget()
        search_layout = qt.QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 5, 0, 5)
        self.search_input = qt.QLineEdit()
        self.search_input.setPlaceholderText("أكتب محتوى البحث هنا...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_button = guiTools.QPushButton("البحث")
        self.search_button.setObjectName("startButton")
        self.search_button.setAutoDefault(False)
        self.search_button.clicked.connect(self.perform_search)
        self.search_mode_button = guiTools.QPushButton("نمط البحث")
        self.search_mode_button.setObjectName("searchModeButton")
        self.search_mode_button.setShortcut("ctrl+q")
        self.search_mode_button.setAutoDefault(False)
        self.search_mode_button.clicked.connect(self.show_search_mode_dialog)
        self.search_mode_button.setAccessibleDescription("control plus q")
        self.clear_results_button = guiTools.QPushButton("حذف المحتوى والعودة الى العرض الأصلي")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.setShortcut("ctrl+delete")
        self.clear_results_button.setAutoDefault(False)
        self.clear_results_button.clicked.connect(self.clear_search_results)
        self.clear_results_button.setAccessibleDescription("control plus delete")
        search_layout.addWidget(self.clear_results_button)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.search_mode_button)
        layout.addWidget(self.search_widget)
        self.search_widget.hide()
        self.clear_results_button.hide()
        layout.addWidget(self.text)
        layout.addLayout(progress_time_layout)
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_action_button = guiTools.QPushButton("إلغاء الدمج")
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
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.info)
        buttonsLayout=qt.QHBoxLayout()
        self.next=guiTools.QPushButton("التالي")
        self.next.setAutoDefault(False)
        self.next.clicked.connect(self.onNext)
        self.next.setVisible(enableNextPreviouseButtons)
        self.next.setShortcut("alt+right")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCategory=guiTools.QPushButton("تغيير الفئة")
        self.changeCategory.setAutoDefault(False)
        self.changeCategory.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCategory.setShortcut("ctrl+alt+g")
        self.changeCategory.setAccessibleDescription("control plus alt plus g")
        self.changeCategory.setVisible(enableNextPreviouseButtons)
        self.changeCategory.clicked.connect(self.onChangeCategory)
        self.previous=guiTools.QPushButton("السابق")
        self.previous.setAutoDefault(False)
        self.previous.clicked.connect(self.onPreviouse)
        self.previous.setShortcut("alt+left")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.setVisible(enableNextPreviouseButtons)
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCurrentReciterButton=guiTools.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.setAutoDefault(False)
        self.changeCurrentReciterButton.clicked.connect(self.onChangeRecitersContextMenuRequested)
        self.changeCurrentReciterButton.setShortcut("ctrl+shift+r")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus r")
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.toggle_search_button = guiTools.QPushButton("البحث في المحتوى المعروض")
        self.toggle_search_button.setAutoDefault(False)
        self.toggle_search_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.toggle_search_button.clicked.connect(self.toggle_search_bar)
        self.toggle_search_button.setAccessibleDescription("control plus shift plus q")
        self.numbering_button = guiTools.QPushButton("طريقة عرض الآيات")
        self.numbering_button.setAutoDefault(False)
        self.numbering_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.numbering_button.setAccessibleDescription("control plus shift plus s")
        self.numbering_button.clicked.connect(self._show_numbering_options)
        buttonsLayout.addWidget(self.changeCurrentReciterButton)
        buttonsLayout.addWidget(self.previous)
        buttonsLayout.addWidget(self.changeCategory)
        buttonsLayout.addWidget(self.next)
        buttonsLayout.addWidget(self.toggle_search_button)
        buttonsLayout.addWidget(self.numbering_button)
        layout.addLayout(buttonsLayout)
        if not self.initial_ayah_index == 0:
            QTimer.singleShot(501, self._set_initial_ayah_position)
        if enableNextPreviouseButtons:
            qt1.QShortcut("ctrl+shift+g",self).activated.connect(self.goToCategory)
            qt1.QShortcut("escape",self).activated.connect(self.close_window)
        qt1.QShortcut("ctrl+shift+q", self).activated.connect(self.toggle_search_bar)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.goToAyah)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)        
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+shift+t", self).activated.connect(self.getTafaseerForSurah)
        qt1.QShortcut("ctrl+shift+i", self).activated.connect(self.getIArabForSurah)
        qt1.QShortcut("ctrl+shift+l", self).activated.connect(self.getTranslationForSurah)
        qt1.QShortcut("ctrl+shift+f", self).activated.connect(self.onSurahInfo)
        qt1.QShortcut("ctrl+alt+t", self).activated.connect(self.TafseerFromVersToVers)
        qt1.QShortcut("ctrl+alt+l", self).activated.connect(self.translateFromVersToVers)
        qt1.QShortcut("ctrl+alt+i", self).activated.connect(self.IArabFromVersToVers)
        qt1.QShortcut("ctrl+alt+p", self).activated.connect(self.playFromVersToVers)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.mergeAyahs)
        qt1.QShortcut("ctrl+shift+c", self).activated.connect(self.copyFromVersToVers)
        qt1.QShortcut("ctrl+shift+p", self).activated.connect(self.onPlayToEnd)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        qt1.QShortcut("ctrl+shift+s", self).activated.connect(self._show_numbering_options)
    def close_window(self):
        if self.media.isPlaying():
            self.media.stop()
            qt2.QTimer.singleShot(100,self.close)
        else:
            self.close()
    def _is_invalid_search_line(self):
        if self.is_search_view and self.text.toPlainText().startswith("عدد نتائج البحث"):
            if self.text.textCursor().blockNumber() < 2:
                return True
        return False
    def _handle_invalid_search_line_action(self):
        winsound.Beep(440, 200)
        guiTools.speak("لا يمكن تنفيذ هذا الإجراء على هذا السطر")
    def _show_numbering_options(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_ayah_index = self.getCurrentAyah()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        self.pause_for_action()
        menu = qt.QMenu(self)
        action_group = qt1.QActionGroup(self)
        action_group.setExclusive(True)
        by_surah_action = qt1.QAction("إظهار الأرقام بحسب السورة (افتراضي)", self, checkable=True)
        by_surah_action.setChecked(self.verse_numbering_mode == "by_surah")
        by_surah_action.triggered.connect(lambda: self._set_numbering_mode("by_surah"))
        cumulative_action = qt1.QAction("إظهار الأرقام بحسب الفئة", self, checkable=True)
        cumulative_action.setChecked(self.verse_numbering_mode == "cumulative")
        cumulative_action.triggered.connect(lambda: self._set_numbering_mode("cumulative"))
        quran_wide_action = qt1.QAction("إظهار الأرقام بحسب القرآن كاملا", self, checkable=True)
        quran_wide_action.setChecked(self.verse_numbering_mode == "quran_wide")
        quran_wide_action.triggered.connect(lambda: self._set_numbering_mode("quran_wide"))
        none_action = qt1.QAction("إخفاء أرقام الآيات", self, checkable=True)
        none_action.setChecked(self.verse_numbering_mode == "none")
        none_action.triggered.connect(lambda: self._set_numbering_mode("none"))
        action_group.addAction(by_surah_action)
        action_group.addAction(cumulative_action)
        action_group.addAction(quran_wide_action)
        action_group.addAction(none_action)
        menu.addAction(by_surah_action)
        menu.addAction(cumulative_action)
        menu.addAction(quran_wide_action)
        menu.addAction(none_action)
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(qt1.QCursor.pos())
    def _set_numbering_mode(self, mode):
        if self.verse_numbering_mode == mode:
            return
        self.verse_numbering_mode = mode
        self._update_display_text()
    def _update_display_text(self):
        if self.verse_numbering_mode in self.text_cache:
            formatted_text = self.text_cache[self.verse_numbering_mode]
        else:
            lines = self.original_quran_text.split('\n')
            new_lines = []
            if not lines or not self.original_quran_text.strip():
                formatted_text = self.original_quran_text
            elif self.verse_numbering_mode == "none":
                for line in lines:
                    new_lines.append(re.sub(r' \(\d+\)$', '', line))
                formatted_text = "\n".join(new_lines)
            elif self.verse_numbering_mode == "cumulative":
                start_cumulative_num = -1
                try:
                    first_line = ""
                    for line in lines:
                        if line.strip():
                            first_line = line
                            break
                    if first_line:
                        base_text = re.sub(r'\s*\(\d+\)$', '', first_line)
                        _, _, _, _, start_cumulative_num = functions.quranJsonControl.getAyah(base_text, self.category, self.type)
                except Exception as e:
                    print(f"Error getting starting cumulative number: {e}")
                    start_cumulative_num = -1
                if start_cumulative_num != -1:
                    current_cumulative_num = start_cumulative_num
                    for line in lines:
                        if not line.strip():
                            new_lines.append(line)
                            continue
                        base_text = re.sub(r'\s*\(\d+\)$', '', line)
                        new_lines.append(f"{base_text} ({current_cumulative_num})")
                        current_cumulative_num += 1
                    formatted_text = "\n".join(new_lines)
                else:
                    formatted_text = self.original_quran_text
            elif self.verse_numbering_mode == "quran_wide":
                for line in lines:
                    if not line.strip():
                        new_lines.append(line)
                        continue
                    try:
                        _, _, _, _, ayah_number_in_quran = functions.quranJsonControl.getAyah(line, self.category, self.type)
                        base_text = re.sub(r'\s*\(\d+\)$', '', line)
                        new_lines.append(f"{base_text} ({ayah_number_in_quran})")
                    except Exception as e:
                        print(f"Could not get Quran-wide number for line: '{line}'. Error: {e}")
                        new_lines.append(line)
                formatted_text = "\n".join(new_lines)
            else:
                formatted_text = self.original_quran_text
            self.text_cache[self.verse_numbering_mode] = formatted_text
        self.quranText = formatted_text
        self._set_text_with_delay(formatted_text)
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
    def _handle_search_view_restriction(self):
        winsound.Beep(440, 200)
        guiTools.speak("هذا الخيار غير متاح في وضع البحث أو التصفح المخصص")
    def mergeAyahs(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        total_ayahs = len(self.quranText.split("\n"))
        start_ayah, ok1 = guiTools.QInputDialog.getInt(self, "تحديد بداية الدمج", "من الآية رقم:", self.getCurrentAyah() + 1, 1, total_ayahs)
        if not ok1:
            self.resume_after_action()
            return
        end_ayah, ok2 = guiTools.QInputDialog.getInt(self, "تحديد نهاية الدمج", "إلى الآية رقم:", total_ayahs, start_ayah, total_ayahs)
        if not ok2:
            self.resume_after_action()
            return
        self.merge_list.clear()
        reciter_url_base = reciters[self.getCurrentReciter()]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
        ayahs_to_download = []
        for i in range(start_ayah - 1, end_ayah):
            ayah_filename = self.on_set(i)
            if not ayah_filename: continue
            local_path = os.path.join(reciter_local_path_base, ayah_filename)
            ayah_info = {
                "index": i, "filename": ayah_filename,
                "url": reciter_url_base + ayah_filename,
                "local_path": local_path
            }
            self.merge_list.append(ayah_info)
            if not os.path.exists(local_path):
                ayahs_to_download.append(ayah_info)
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (
                f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\n"
                "سيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\n"
                "بعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\n"
                "هل أنت متأكد أنك تريد المتابعة؟"
            )
        else:
            confirm_message = (
                "جميع الآيات المحددة جاهزة للدمج.\n"
                "ستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\n"
                "هل تريد المتابعة؟"
            )
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.resume_after_action()
            return
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
        self.resume_after_action()
    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets_to_disable = [
            self.text, self.search_widget, self.next, self.previous,
            self.changeCategory, self.changeCurrentReciterButton, self.toggle_search_button
        ]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير لعملية الدمج...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
        else:
            self.merge_action_button.setStyleSheet("")
    def toggle_search_bar(self):
        if self.search_widget.isVisible():
            self.search_widget.hide()
            self.toggle_search_button.setText("البحث في المحتوى المعروض")
            guiTools.speak("تم إخفاء شريط البحث")
        else:
            self.search_widget.show()
            self.toggle_search_button.setText("إخفاء شريط البحث")
            self.search_input.setFocus()
    def show_search_mode_dialog(self):
        self.pause_for_action()
        dialog = SearchModeDialog(self, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            settings_values = dialog.get_settings()
            self.ignore_tashkeel = settings_values["ignore_tashkeel"]
            self.ignore_hamza = settings_values["ignore_hamza"]
            self.ignore_symbols = settings_values["ignore_symbols"]
            guiTools.speak("تم تطبيق إعدادات البحث بنجاح")
        else:
            guiTools.speak("تم إلغاء التغييرات")
        self.resume_after_action()
    def search(self, pattern, text_list):
        def remove_tashkeel(text):
            return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        def normalize_hamza(text):
            return re.sub(r'[أإآ]', 'ا', text)
        def normalize(text):
            normalized_text = text
            if self.ignore_tashkeel:
                normalized_text = remove_tashkeel(normalized_text)
            if self.ignore_hamza:
                normalized_text = normalize_hamza(normalized_text)
            return normalized_text
        normalized_pattern = normalize(pattern)
        return [text for text in text_list if normalized_pattern in normalize(text)]
    def perform_search(self):
        search_term = self.search_input.text()
        if not search_term:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        source_text_list = self.original_quran_text.split('\n')
        results = self.search(search_term, source_text_list)
        if results:
            self.is_search_view = True
            self.numbering_button.setVisible(False)
            self.enableBookmarks = False
            header = f"عدد نتائج البحث: {len(results)}"
            guiTools.speak(header)
            display_text = [header, ""] + results
            self.quranText = "\n".join(results)
            self.text.setText("\n".join(display_text))
            self.update_font_size()
            self.clear_results_button.show()
            if self.media.isPlaying():
                self.media.stop()
        else:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على نتائج")
    def clear_search_results(self):
        self.is_search_view = False
        self.numbering_button.setVisible(True)
        self.enableBookmarks = self.initial_enableBookmarks
        self.quranText = self.original_quran_text
        self.text.setText(self.original_quran_text)
        self.update_font_size()
        self.clear_results_button.hide()
        self.search_input.clear()
        guiTools.speak("تمت العودة إلى العرض الأصلي")
    def format_category_name(self, category_type, category_value):
        if category_type == 0:
            return category_value
        elif category_type == 1:
            return f"الصفحة {category_value}"
        elif category_type == 2:
            return f"الجزء {category_value}"
        elif category_type == 3:
            return f"الربع {category_value}"
        elif category_type == 4:
            return f"الحزب {category_value}"
        return category_value
    def pause_for_action(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False
    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()
    def _set_text_with_delay(self, full_text):
        self.saved_text = full_text
        lines = full_text.split('\n')
        initial_text_chunk = '\n'.join(lines[:40])
        self.text.setText(initial_text_chunk)
        self.update_font_size()
        if len(lines) > 40:
            qt2.QTimer.singleShot(500, self._display_full_content)
    def _display_full_content(self):
        if not hasattr(self, 'context_menu_active') or not self.context_menu_active:
            self.text.setText(self.saved_text)
            self.update_font_size()
    def restore_after_menu(self):
        self.context_menu_active = False
        lines = self.saved_text.split('\n')
        self.text.setText('\n'.join(lines[:40]))
        self.update_font_size()
        self.text.setUpdatesEnabled(True)
        if len(lines) > 40:
            QTimer.singleShot(500, self.restore_full_content)
        if self.saved_cursor_position is not None:
            cursor = self.text.textCursor()
            cursor.setPosition(self.saved_cursor_position)
            self.text.setTextCursor(cursor)
        self.resume_after_action()
    def restore_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
            self.update_font_size()
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
    def eventFilter(self, obj, event):
        if obj == self.text.viewport() and \
            event.type() == qt2.QEvent.Type.MouseButtonPress and \
            event.button() == qt2.Qt.MouseButton.LeftButton:
            cursor = self.text.cursorForPosition(event.position().toPoint())
            self.text.setTextCursor(cursor)
            self.on_play()
            return True
        return super().eventFilter(obj, event)
    def oncontextMenu(self):
        if self._is_invalid_search_line():
            return
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_ayah_index = self.getCurrentAyah()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        self.pause_for_action()
        menu = qt.QMenu("الخيارات ", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات ")
        menu.setFocus()
        ayahOptions = qt.QMenu("خيارات الآية الحالية", self)
        ayahOptions.setFont(font)
        if not self.is_search_view:
            goToAyah = qt1.QAction("الذهاب إلى آية", self)
            goToAyah.setShortcut("ctrl+g")
            ayahOptions.addAction(goToAyah)
            goToAyah.triggered.connect(lambda: QTimer.singleShot(501, self.goToAyah))
        playCurrentAyahAction = qt1.QAction("تشغيل الآية الحالية", self)
        playCurrentAyahAction.setShortcut("space")
        ayahOptions.addAction(playCurrentAyahAction)
        playCurrentAyahAction.triggered.connect(lambda: QTimer.singleShot(501, self.on_play))
        tafaserCurrentAyahAction = qt1.QAction("تفسير الآية الحالية", self)
        tafaserCurrentAyahAction.setShortcut("ctrl+t")
        ayahOptions.addAction(tafaserCurrentAyahAction)
        tafaserCurrentAyahAction.triggered.connect(lambda: QTimer.singleShot(501, self.getCurentAyahTafseer))
        IArabCurrentAyah = qt1.QAction("إعراب الآية الحالية", self)
        IArabCurrentAyah.setShortcut("ctrl+i")
        ayahOptions.addAction(IArabCurrentAyah)
        IArabCurrentAyah.triggered.connect(lambda: QTimer.singleShot(501, self.getCurentAyahIArab))
        tanzelCurrentAyahAction = qt1.QAction("أسباب نزول الآية الحالية", self)
        tanzelCurrentAyahAction.setShortcut("ctrl+r")
        ayahOptions.addAction(tanzelCurrentAyahAction)
        tanzelCurrentAyahAction.triggered.connect(lambda: QTimer.singleShot(501, self.getCurrentAyahTanzel))
        translationCurrentAyahAction = qt1.QAction("ترجمة الآية الحالية", self)
        translationCurrentAyahAction.setShortcut("ctrl+l")
        ayahOptions.addAction(translationCurrentAyahAction)
        translationCurrentAyahAction.triggered.connect(lambda: QTimer.singleShot(501, self.getCurentAyahTranslation))
        ayahInfo = qt1.QAction("معلومات الآية الحالية", self)
        ayahInfo.setShortcut("ctrl+f")
        ayahOptions.addAction(ayahInfo)
        ayahInfo.triggered.connect(lambda: QTimer.singleShot(501, self.getAyahInfo))
        copy_aya = qt1.QAction("نسخ الآية الحالية", self)
        ayahOptions.addAction(copy_aya)
        copy_aya.triggered.connect(lambda: QTimer.singleShot(501, self.copyAya))
        if self.enableBookmarks:
            state, self.nameOfBookmark = functions.bookMarksManager.getQuranBookmarkName(self.type, self.category, self.saved_ayah_index, isPlayer=False)
            if state:
                removeBookmarkAction = qt.QWidgetAction(self)
                delete_button = qt.QPushButton("حذف العلامة المرجعية للآياة الحالية: CTRL+B")
                delete_button.setDefault(True)
                delete_button.setShortcut("ctrl+b")
                delete_button.setStyleSheet("background-color: #8B0000; color: white;")
                delete_button.clicked.connect(lambda: QTimer.singleShot(501, self.onRemoveBookmark))
                removeBookmarkAction.setDefaultWidget(delete_button)
                ayahOptions.addAction(removeBookmarkAction)
            else:
                addNewBookMark = qt1.QAction("إضافة علامة مرجعية للآياة الحالية", self)
                addNewBookMark.setShortcut("ctrl+b")
                ayahOptions.addAction(addNewBookMark)
                addNewBookMark.triggered.connect(lambda: QTimer.singleShot(501, self.onAddBookMark))
            ayah_position = {
                "ayah_text": self.quranText.split("\n")[self.saved_ayah_index],
                "ayah_number": self.saved_ayah_index,
                "surah": self.category
            }
            note_exists = notesManager.getNotesForPosition("quran", ayah_position)
            if note_exists:
                note_action = qt1.QAction("عرض ملاحظة الآية الحالية", self)
                note_action.setShortcut("ctrl+o")
                note_action.triggered.connect(lambda: QTimer.singleShot(501, lambda: self.onNoteAction(ayah_position)))
                ayahOptions.addAction(note_action)
                delete_note_action = qt.QWidgetAction(self)
                delete_button = qt.QPushButton("حذف ملاحظة الآية الحالية: CTRL+SHIFT+N")
                delete_button.setDefault(True)
                delete_button.setStyleSheet("background-color: #8B0000; color: white;")
                delete_button.clicked.connect(lambda: QTimer.singleShot(501, lambda: self.onDeleteNote(ayah_position)))
                delete_note_action.setDefaultWidget(delete_button)
                ayahOptions.addAction(delete_note_action)
            else:
                note_action = qt1.QAction("إضافة ملاحظة للآية الحالية", self)
                note_action.setShortcut("ctrl+n")
                note_action.triggered.connect(lambda: QTimer.singleShot(501, lambda: self.onAddNote(ayah_position)))
                ayahOptions.addAction(note_action)
        menu.addMenu(ayahOptions)
        surahOption = qt.QMenu("خيارات الفئة", self)
        surahOption.setFont(font)
        copySurahAction = qt1.QAction("نسخ الفئة", self)
        copySurahAction.setShortcut("ctrl+a")
        surahOption.addAction(copySurahAction)
        copySurahAction.triggered.connect(lambda: QTimer.singleShot(501, self.copy_text))
        saveSurahAction = qt1.QAction("حفظ الفئة كملف نصي", self)
        saveSurahAction.setShortcut("ctrl+s")
        surahOption.addAction(saveSurahAction)
        saveSurahAction.triggered.connect(lambda: QTimer.singleShot(501, self.save_text_as_txt))
        printSurah = qt1.QAction("طباعة الفئة", self)
        printSurah.setShortcut("ctrl+p")
        surahOption.addAction(printSurah)
        printSurah.triggered.connect(lambda: QTimer.singleShot(501, self.print_text))
        SurahInfoAction = qt1.QAction("معلومات السورة", self)
        SurahInfoAction.setShortcut("ctrl+shift+f")
        surahOption.addAction(SurahInfoAction)
        SurahInfoAction.triggered.connect(lambda: QTimer.singleShot(501, self.onSurahInfo))
        playToEndActionText = "التشغيل إلى نهاية نتائج البحث" if self.is_search_view else "التشغيل إلى نهاية الفئة"
        playSurahToEnd = qt1.QAction(playToEndActionText, self)
        playSurahToEnd.setShortcut("ctrl+shift+p")
        surahOption.addAction(playSurahToEnd)
        playSurahToEnd.triggered.connect(lambda: QTimer.singleShot(501, self.onPlayToEnd))
        if not self.is_search_view:
            tafaseerSurahAction = qt1.QAction("تفسير الفئة", self)
            tafaseerSurahAction.setShortcut("ctrl+shift+t")
            surahOption.addAction(tafaseerSurahAction)
            tafaseerSurahAction.triggered.connect(lambda: QTimer.singleShot(501, self.getTafaseerForSurah))
            IArabSurah = qt1.QAction("إعراب الفئة", self)
            IArabSurah.setShortcut("ctrl+shift+i")
            surahOption.addAction(IArabSurah)
            IArabSurah.triggered.connect(lambda: QTimer.singleShot(501, self.getIArabForSurah))
            translationSurahAction = qt1.QAction("ترجمة  الفئة", self)
            translationSurahAction.setShortcut("ctrl+shift+l")
            surahOption.addAction(translationSurahAction)
            translationSurahAction.triggered.connect(lambda: QTimer.singleShot(501, self.getTranslationForSurah))
            tafseerFromVersToVersAction = qt1.QAction("التفسير من آية إلى آية")
            tafseerFromVersToVersAction.setShortcut("ctrl+alt+t")
            surahOption.addAction(tafseerFromVersToVersAction)
            tafseerFromVersToVersAction.triggered.connect(lambda: QTimer.singleShot(501, self.TafseerFromVersToVers))
            translateFromVersToVersAction = qt1.QAction("الترجمة من آية إلى آية")
            translateFromVersToVersAction.setShortcut("ctrl+alt+l")
            surahOption.addAction(translateFromVersToVersAction)
            translateFromVersToVersAction.triggered.connect(lambda: QTimer.singleShot(501, self.translateFromVersToVers))
            IArabFromVersToVersAction = qt1.QAction("الإعراب من آية إلى آية", self)
            IArabFromVersToVersAction.setShortcut("ctrl+alt+i")
            surahOption.addAction(IArabFromVersToVersAction)
            IArabFromVersToVersAction.triggered.connect(lambda: QTimer.singleShot(501, self.IArabFromVersToVers))
            copyFromVersToVersAction = qt1.QAction("نسخ من آية إلى آية", self)
            copyFromVersToVersAction.setShortcut("ctrl+shift+c")
            surahOption.addAction(copyFromVersToVersAction)
            copyFromVersToVersAction.triggered.connect(lambda: QTimer.singleShot(501, self.copyFromVersToVers))
            playFromVersToVersAction = qt1.QAction("التشغيل من آية إلى آية", self)
            playFromVersToVersAction.setShortcut("ctrl+alt+p")
            surahOption.addAction(playFromVersToVersAction)
            playFromVersToVersAction.triggered.connect(lambda: QTimer.singleShot(501, self.playFromVersToVers))
            mergeAyahsAction = qt1.QAction("دمج الآيات", self)
            mergeAyahsAction.setShortcut("ctrl+alt+d")
            surahOption.addAction(mergeAyahsAction)
            mergeAyahsAction.triggered.connect(lambda: QTimer.singleShot(501, self.mergeAyahs))
            if self.enableNextPreviouseButtons:
                goToCategoryAction = qt1.QAction("الذهاب إلى محتوى فئة", self)
                goToCategoryAction.setShortcut("ctrl+shift+g")
                goToCategoryAction.triggered.connect(lambda: QTimer.singleShot(501, self.goToCategory))
                surahOption.addAction(goToCategoryAction)
        menu.addMenu(surahOption)
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(font)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        incressFontAction.triggered.connect(lambda: QTimer.singleShot(501, self.increase_font_size))
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(lambda: QTimer.singleShot(501, self.decrease_font_size))
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(lambda: QTimer.singleShot(501, self.set_font_size_dialog))
        fontMenu.addAction(set_font_size)
        menu.addMenu(fontMenu)
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def onAddNote(self, position_data):
        self.pause_for_action()
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
        self.resume_after_action()
    def onEditNote(self, position_data, note_name):
        self.pause_for_action()
        note = notesManager.getNoteByName("quran", note_name)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="edit",
                old_name=note["name"]
            )
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
        self.resume_after_action()
    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("quran", name)
        if existing_note is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("quran", {
            "name": name,
            "content": content,
            "position_data": position_data
        })
        guiTools.speak("تمت إضافة الملاحظة")
    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("quran", new_name)
            if existing_note is not None:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {
            "name": new_name,
            "content": new_content,
            "position_data": position_data
        }
        success = notesManager.updateNote("quran", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")
    def onAddOrRemoveNote(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن إدارة الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": self.getCurrentAyah(),
            "surah": self.category
        }
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onEditNote(ayah_position, note_exists["name"])
        else:
            self.onAddNote(ayah_position)
        self.resume_after_action()
    def onViewNote(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن عرض الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": self.getCurrentAyah(),
            "surah": self.category
        }
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onNoteAction(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الآية")
        self.resume_after_action()
    def onNoteAction(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="view",
                old_name=note["name"]
            )
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
        self.resume_after_action()
    def onDeleteNote(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف",
                f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟",
                "نعم", "لا"
            )
            if confirm == 0:
                notesManager.removeNote("quran", note["name"])
                guiTools.speak("تم حذف الملاحظة")
        self.resume_after_action()
    def copyAya(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        a = self._get_line_text_for_action(self.saved_ayah_index)
        if a:
            pyperclip.copy(a)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ الآية المحددة بنجاح")
    def goToAyah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        ayah,OK=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية ",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if OK:
            cerser=self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)
            for i in range(ayah-1):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
        self.resume_after_action()
    def getCurrentAyah(self):
        if self.is_search_view and self.text.toPlainText().startswith("عدد نتائج البحث"):
            return self.text.textCursor().blockNumber() - 2
        return self.text.textCursor().blockNumber()
    def on_set(self, ayah_index=None):
        if ayah_index is None:
            ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(ayah_index)
        if not current_line:
            return None
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"
    def on_play(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.media_progress.setVisible(True)
        self.time_label.setVisible(True)
        current_ayah_index = self.getCurrentAyah()
        if current_ayah_index < 0:
            return
        file_name = self.on_set(current_ayah_index)
        if not file_name:
            return
        reciter_key = self.getCurrentReciter()
        reciter_folder = reciters[reciter_key].split("/")[-3]
        local_file_path = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder, file_name)
        if os.path.exists(local_file_path):
            path = qt2.QUrl.fromLocalFile(local_file_path)
        else:
            path = qt2.QUrl(reciters[reciter_key] + file_name)
        is_playing_this_verse = (self.media.playbackState() != QMediaPlayer.PlaybackState.StoppedState) and (self.media.source() == path)
        if is_playing_this_verse:
            if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media.pause()
            elif self.media.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.media.play()
        else:
            self.media.stop()
            self.media.setSource(path)
            self.media.play()
    def onPlayToEnd(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return        
        text_for_player = self.original_quran_text if not self.is_search_view else self.quranText
        QuranPlayer(self, text_for_player, self.getCurrentAyah(), self.type, self.category).exec()
    def getCurrentReciter(self):
        index=self.currentReciter
        name=list(reciters.keys())[index]
        return name
    def getcurrentAyahText(self):
        line = self.getCurrentAyah()
        return self._get_line_text_for_action(line) or ""
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def save_text_as_txt(self):
        try:
            file_dialog=qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name=file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    text = self.text.toPlainText()
                    file.write(text)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def increase_font_size(self):
        if self.font_size < 100:
            self.font_size += 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()
    def update_font_size(self):
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def getCurentAyahTafseer(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def getTafaseerForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def onSurahInfo(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        with open("data/json/files/all_surahs.json","r",encoding="utf-8") as file:
            data=json.load(file)
        surahInfo=data[int(surah)-1]
        numberOfAyah=surahInfo["n"]
        if surahInfo["r"]==0:
            type="مكية"
        else:
            type="مدنية"
        guiTools.qMessageBox.MessageBox.view(self,"معلومات {}".format(juz[1]),"رقم السورة {} \n عدد آياتها {} \n نوع السورة {}".format(str(surah),str(numberOfAyah),type))
        self.resume_after_action()
    def closeEvent(self, event):
        if self.is_merging:
            if self.merge_phase == 'downloading':
                guiTools.qMessageBox.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق البرنامج أثناء مرحلة تحميل الآيات. الرجاء الانتظار.")
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
            self.media.stop()
            super().closeEvent(event)
    def getCurentAyahIArab(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def getIArabForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def getCurrentAyahTanzel(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            self.text.setUpdatesEnabled(False)
            guiTools.TextViewer(self,"أسباب النزول",result).exec()
            self.text.setUpdatesEnabled(True)
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()
    def getAyahInfo(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nالجزء {} \nالربع {} \nالصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
        self.resume_after_action()
    def getCurentAyahTranslation(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def getTranslationForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def onAddBookMark(self):
        self.pause_for_action()
        if self.enableBookmarks==False:
            guiTools.qMessageBox.MessageBox.error(self,"تنبيه","لا يمكن وضع علامة مرجعية عند تصفح القرآن بشكلا مخصص")
            self.resume_after_action()
            return
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getQuranBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                self.resume_after_action()
                return
            current_ayah = self.getCurrentAyah()
            functions.bookMarksManager.addNewQuranBookMark(self.type, self.category, current_ayah, False, name)
        self.resume_after_action()
    def playFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                verses=[]
                allVerses=self.original_quran_text.split("\n")
                for vers in allVerses:
                    index=allVerses.index(vers)+1
                    if index>=FromVers and index<=toVers:
                        verses.append(vers)
                self.text.setUpdatesEnabled(False)
                QuranPlayer(self,"\n".join(verses),0,self.type,self.category).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def TafseerFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def translateFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                translationViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def IArabFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
                guiTools.TextViewer(self,"إعراب",result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()
    def _get_line_text_for_action(self, ayah_index):
        if ayah_index < 0:
            return None
        text_source = self.quranText if self.is_search_view else self.original_quran_text
        lines = text_source.split('\n')
        if ayah_index < len(lines):
            return lines[ayah_index]
        return None
    def _update_view_for_new_content(self, new_text):
        self.quranText = new_text
        self.original_quran_text = new_text
        self.text_cache = {"by_surah": self.original_quran_text}
        self._update_display_text()
    def onNext(self):
        self.pause_for_action()
        if self.CurrentIndex==len(self.typeResult)-1:
            self.CurrentIndex=0
        else:
            self.CurrentIndex+=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.category = indexs
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(formatted_name))
        self.info.setText(formatted_name)
        self.resume_after_action()
    def onPreviouse(self):
        self.pause_for_action()
        if self.CurrentIndex==0:
            self.CurrentIndex=len(self.typeResult)-1
        else:
            self.CurrentIndex-=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.category = indexs
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        winsound.PlaySound("data/sounds/previous_page.wav",1)
        guiTools.speak(str(formatted_name))
        self.info.setText(formatted_name)
        self.resume_after_action()
    def goToCategory(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        category,OK=qt.QInputDialog.getItem(self,"الذهاب إلى محتوى فئة","اختر عنصر",list(self.typeResult.keys()),self.CurrentIndex,False)
        if OK:
            self.CurrentIndex=list(self.typeResult.keys()).index(category)
            indexs=list(self.typeResult.keys())[self.CurrentIndex]
            formatted_name = self.format_category_name(self.type, indexs)
            self.category = indexs
            self.info.setText(formatted_name)
            new_text = self.typeResult[indexs][1]
            self._update_view_for_new_content(new_text)
        self.resume_after_action()
    def onChangeCategory(self):
        self.pause_for_action()
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        menu=qt.QMenu("اختر فئة",self)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        selectedCategory=qt1.QAction(categories[self.type],self)
        menu.addAction(selectedCategory)
        selectedCategory.setCheckable(True)
        selectedCategory.setChecked(True)
        selectedCategory.triggered.connect(self.ONChangeCategoryRequested)
        menu.setDefaultAction(selectedCategory)
        categories.pop(self.type)
        for category in categories:
            action=qt1.QAction(category,self)
            menu.addAction(action)
            action.triggered.connect(self.ONChangeCategoryRequested)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
        self.resume_after_action()
    def ONChangeCategoryRequested(self):
        self.pause_for_action()
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        index=categories.index(self.sender().text())
        self.type=index
        if index==0:
            result=functions.quranJsonControl.getSurahs()
        elif index==1:
            result=functions.quranJsonControl.getPage()
        elif index==2:
            result=functions.quranJsonControl.getJuz()
        elif index==3:
            result=functions.quranJsonControl.getHezb()
        elif index==4:
            result=functions.quranJsonControl.getHizb()
        self.typeResult=result
        self.CurrentIndex=0
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.info.setText(formatted_name)
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        self.resume_after_action()
    def onRemoveBookmark(self):
        self.pause_for_action()
        try:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف",
                f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟",
                "نعم", "لا"
            )
            if confirm == 0:
                functions.bookMarksManager.removeQuranBookMark(self.nameOfBookmark)
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.speak("تم حذف العلامة المرجعية")
        self.resume_after_action()
    def onAddOrRemoveBookmark(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن إدارة العلامات المرجعية في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        current_ayah = self.getCurrentAyah()
        state, self.nameOfBookmark = functions.bookMarksManager.getQuranBookmarkName(self.type, self.category, current_ayah, isPlayer=False)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
        self.resume_after_action()
    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)
    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            position = self.media.position()
            duration = self.media.duration()
            if duration > 0:
                progress_value = int((position / duration) * 100)
                self.media_progress.setValue(progress_value)
                self.update_time_label(position, duration)
            self.media_progress.blockSignals(False)
        except:
            pass
    def update_time_label(self, position, duration):
        position_sec = position // 1000
        duration_sec = duration // 1000
        remaining_sec = duration_sec - position_sec
        position_str = f"{position_sec // 60}:{position_sec % 60:02d}"
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        remaining_str = f"{remaining_sec // 60}:{remaining_sec % 60:02d}"
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)
    def onChangeRecitersContextMenuRequested(self):
        self.pause_for_action()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.resume_after_action()
    def _set_initial_ayah_position(self):
        cerser = self.text.textCursor()
        cerser.movePosition(cerser.MoveOperation.Start)
        for i in range(self.initial_ayah_index):
            cerser.movePosition(cerser.MoveOperation.Down)
        self.text.setTextCursor(cerser)
    def onDeleteNoteShortcut(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن حذف الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        current_ayah = self.getCurrentAyah()
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": current_ayah,
            "surah": self.category
        }
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onDeleteNote(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
        self.resume_after_action()
    def set_font_size_dialog(self):
        try:
            size, ok = guiTools.QInputDialog.getInt(
                self,
                "تغيير حجم الخط",
                "أدخل حجم الخط (من 1 الى 100):",
                value=self.font_size,
                min=1,
                max=100
            )
            if ok:
                self.font_size = size
                self.show_font.setText(str(self.font_size))
                self.update_font_size()
                guiTools.speak(f"تم تغيير حجم الخط إلى {size}")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "حدث خطأ", str(error))
    def copy_current_selection(self):
        try:
            cursor = self.text.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copyFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        total_ayahs = len(self.quranText.split("\n"))
        FromVers, ok = guiTools.QInputDialog.getInt(self, "نسخ من الآية", "أكتب رقم الآية للبداية:", self.getCurrentAyah() + 1, 1, total_ayahs)
        if ok:
            toVers, ok = guiTools.QInputDialog.getInt(self, "نسخ إلى الآية", "أكتب رقم الآية للنهاية:", total_ayahs, FromVers, total_ayahs)
            if ok:
                start_index = FromVers - 1
                end_index = toVers
                allVerses = self.quranText.split("\n")
                verses_to_copy = allVerses[start_index:end_index]
                if verses_to_copy:
                    text_to_copy = "\n".join(verses_to_copy)
                    pyperclip.copy(text_to_copy)
                    winsound.Beep(1000, 100)
                    guiTools.speak(f"تم نسخ {len(verses_to_copy)} آيات بنجاح")
                else:
                    guiTools.speak("لم يتم تحديد آيات للنسخ")
        self.resume_after_action()