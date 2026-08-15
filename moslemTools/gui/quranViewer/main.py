from guiTools import note_dialog
import functions.notesManager as notesManager
from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
from ..quranPlayer import QuranPlayer
import time, winsound, pyperclip, os, re, requests, subprocess, shutil, traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, SajdaGoToDialog, AsbabAlnozoleGoToDialog, SajdaFinderThread, AsbabAlnozoleFinderThread, SearchModeDialog, GoToCategoryDialog

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)

from .audio_player import AudioPlayerMixin
from .merger_saver import MergerSaverMixin
from .search_handler import SearchHandlerMixin
from .tafseer_and_info import TafseerAndInfoMixin
from .notes_bookmarks import NotesBookmarksMixin
from .navigation_display import NavigationDisplayMixin
from .context_menu import ContextMenuMixin


class QuranViewer(ContextMenuMixin, NavigationDisplayMixin, AudioPlayerMixin, SearchHandlerMixin, MergerSaverMixin, NotesBookmarksMixin, TafseerAndInfoMixin, qt.QDialog):
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
        self.ignore_tashkeel = settings.settings_handler.get("quran_search", "ignore_tashkeel") != "False"
        self.ignore_hamza = settings.settings_handler.get("quran_search", "ignore_hamza") != "False"
        self.ignore_symbols = settings.settings_handler.get("quran_search", "ignore_symbols") != "False"
        self.resize(1200,600)
        self.type=type
        self.category=category
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج الآيات لن تعمل.")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.save_mode = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.verse_numbering_mode = settings.settings_handler.get("quran_display", "verse_numbering_mode") or "by_surah"
        self.remove_tashkeel = settings.settings_handler.get("quran_display", "remove_tashkeel") == "True"
        self.text_cache = {"by_surah": self.original_quran_text}
        self.is_counting_sajdas = False
        self.is_counting_asbab_alnozole = False
        self.original_info_text = ""
        self.media=QMediaPlayer(self)
        self.apply_speed()
        self.audioOutput=QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("quran_text"))
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
                background-color: #0056b3; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold;
            }
            QPushButton#searchModeButton:hover { background-color: #003d80; }
            QPushButton#searchModeButton:pressed { background-color: #003d80; }
            QPushButton#clearResultsButton, QPushButton#cancelButton {
                background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#clearResultsButton:hover, QPushButton#cancelButton:hover { background-color: #c82333; }
            QPushButton#clearResultsButton:pressed, QPushButton#cancelButton:pressed { background-color: #bd2130; }
        """)
        self.text=guiTools.QReadOnlyTextEdit(viewer_name="quranViewer")
        if self.verse_numbering_mode != "by_surah" or self.remove_tashkeel:
            self._update_display_text()
        else:
            self._set_text_with_delay(text)
        self.update_font_size()
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.viewport().installEventFilter(self)
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.time_label = guiTools.QNavigableLabel()
        self.time_label.setVisible(False)
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Preferred)
        progress_time_layout = qt.QVBoxLayout()
        progress_time_layout.addWidget(self.media_progress)
        progress_time_layout.addWidget(self.time_label)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.info=guiTools.QNavigableLabel()
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
        self.search_button.setStyleSheet("background-color: #0000AA; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; min-height: 30px;")
        self.search_button.clicked.connect(self.perform_search)
        self.search_mode_button = guiTools.QPushButton("نمط البحث")
        self.search_mode_button.setObjectName("searchModeButton")
        self.search_mode_button.setStyleSheet("background-color: #28a745; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; min-height: 30px;")
        self.search_mode_button.clicked.connect(self.show_search_mode_dialog)
        self.search_mode_button.setAccessibleDescription("control plus q")
        self.search_mode_button.setAutoDefault(False)
        self.search_mode_button.setShortcut("ctrl+q")
        self.clear_results_button = guiTools.QPushButton("حذف المحتوى والعودة إلى العرض الأصلي")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.setStyleSheet("background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; min-height: 30px;")
        self.clear_results_button.clicked.connect(self.clear_search_results)
        self.clear_results_button.setAccessibleDescription("control plus delete")
        self.clear_results_button.setAutoDefault(False)
        self.clear_results_button.setShortcut("ctrl+delete")
        search_layout.addWidget(self.clear_results_button)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.search_mode_button)
        layout.addWidget(self.search_widget)
        self.search_widget.hide()
        self.clear_results_button.hide()
        self.permanent_stabilizer_bar = qt.QWidget()
        self.permanent_stabilizer_bar.setFixedHeight(0)
        self.permanent_stabilizer_bar.setAccessibleName(" ")
        self.permanent_stabilizer_bar.setAccessibleDescription(" ")
        layout.addWidget(self.permanent_stabilizer_bar)
        layout.addWidget(self.text)
        layout.addLayout(progress_time_layout)
        self.merge_feedback_label = guiTools.QNavigableLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_action_button = guiTools.QPushButton("إلغاء العملية")
        self.merge_action_button.setObjectName("cancelMergeButton")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.setMinimumHeight(35)
        self.merge_action_button.setMinimumWidth(160)
        self.merge_action_button.setMaximumWidth(210)
        self.merge_action_button.setStyleSheet("QPushButton#cancelMergeButton {background-color: #8B0000; color: white; border: 2px solid #B22222; padding: 6px 12px; border-radius: 5px; font-weight: bold;} QPushButton#cancelMergeButton:hover {background-color: #A52A2A; border-color: #FF4D4D;}")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        self.resume_download_button = guiTools.QPushButton("استئناف")
        self.resume_download_button.setAutoDefault(False)
        self.resume_download_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #0000CC;}")
        self.resume_download_button.setVisible(False)
        self.resume_download_button.clicked.connect(self.resume_current_download)
        merge_layout = qt.QHBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.resume_download_button)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        layout.addWidget(self.merge_widget)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self.options_info_label = guiTools.QNavigableLabel("لمزيد من خيارات الفئة أو الآية، نستخدم زر التطبيقات أو click الأيمن على آية من الآيات")
        self.options_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.options_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.options_info_label)
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
        self.update_nav_buttons_text()
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
            qt1.QShortcut("alt+right",self).activated.connect(self.onNext)
            qt1.QShortcut("alt+left",self).activated.connect(self.onPreviouse)
        qt1.QShortcut("ctrl+shift+q", self).activated.connect(self.toggle_search_bar)
        qt1.QShortcut("ctrl+shift+s", self).activated.connect(self._show_numbering_options)
        qt1.QShortcut("ctrl+shift+x", self).activated.connect(self.toggleTashkeelView)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.goToAyah)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+0", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)
        qt1.QShortcut("ctrl+u", self).activated.connect(self.getCurentAyahMeanings)
        qt1.QShortcut("ctrl+k", self).activated.connect(self.getCurentAyahSarf)
        qt1.QShortcut("ctrl+shift+alt+i", self).activated.connect(self.getDetailedIArabForSurah)
        qt1.QShortcut("shift+alt+e", self).activated.connect(self.getDetailedIArabFromAyahToEnd)
        qt1.QShortcut("ctrl+alt+e", self).activated.connect(self.DetailedIArabFromVersToVers)
        qt1.QShortcut("ctrl+shift+u", self).activated.connect(self.getMeaningsForSurah)
        qt1.QShortcut("shift+alt+u", self).activated.connect(self.getMeaningsFromAyahToEnd)
        qt1.QShortcut("ctrl+alt+u", self).activated.connect(self.MeaningsFromVersToVers)
        qt1.QShortcut("ctrl+shift+k", self).activated.connect(self.getSarfForSurah)
        qt1.QShortcut("shift+alt+k", self).activated.connect(self.getSarfFromAyahToEnd)
        qt1.QShortcut("ctrl+shift+alt+k", self).activated.connect(self.SarfFromVersToVers)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+shift+t", self).activated.connect(self.getTafaseerForSurah)
        qt1.QShortcut("ctrl+shift+i", self).activated.connect(self.getIArabForSurah)
        qt1.QShortcut("ctrl+shift+l", self).activated.connect(self.getTranslationForSurah)
        qt1.QShortcut("shift+alt+t", self).activated.connect(self.getTafaseerFromAyahToEnd)
        qt1.QShortcut("shift+alt+l", self).activated.connect(self.getTranslationFromAyahToEnd)
        qt1.QShortcut("shift+alt+i", self).activated.connect(self.getIArabFromAyahToEnd)
        qt1.QShortcut("shift+alt+d", self).activated.connect(self.mergeFromAyahToEnd)
        qt1.QShortcut("shift+alt+h", self).activated.connect(self.saveFromAyahToEnd)
        qt1.QShortcut("ctrl+shift+f", self).activated.connect(self.onSurahInfo)
        qt1.QShortcut("ctrl+alt+f", self).activated.connect(self.show_current_surah_info)
        qt1.QShortcut("ctrl+alt+t", self).activated.connect(self.TafseerFromVersToVers)
        qt1.QShortcut("ctrl+alt+l", self).activated.connect(self.translateFromVersToVers)
        qt1.QShortcut("ctrl+alt+i", self).activated.connect(self.IArabFromVersToVers)
        qt1.QShortcut("ctrl+alt+p", self).activated.connect(self.playFromVersToVers)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.mergeAyahs)
        qt1.QShortcut("ctrl+shift+d", self).activated.connect(self.mergeCategoryAyahs)
        qt1.QShortcut("ctrl+h", self).activated.connect(self.saveCurrentAyah)
        qt1.QShortcut("ctrl+alt+h", self).activated.connect(self.saveFromVersToVers)
        qt1.QShortcut("ctrl+shift+h", self).activated.connect(self.saveCategoryAyahs)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copyFromVersToVers)
        qt1.QShortcut("ctrl+shift+p", self).activated.connect(self.onPlayToEnd)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+x", self).activated.connect(self.removeTashkeelForAyah)
        qt1.QShortcut("ctrl+alt+j", self).activated.connect(self.showSajdaVerses)
        qt1.QShortcut("ctrl+alt+r", self).activated.connect(self.showAsbabAlnozoleVerses)

    def close_window(self):
        if getattr(self, 'is_merging', False):
            if getattr(self, 'save_mode', False):
                self.close()
            else:
                self.close()
        elif self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.stop()
            qt2.QTimer.singleShot(100,self.close)
        else:
            self.close()

    def reject(self):
        if getattr(self, 'is_merging', False):
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        super().reject()

    def keyPressEvent(self, event):
        if event.key() == qt2.Qt.Key.Key_Escape:
            if getattr(self, 'is_merging', False):
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
                return
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if getattr(self, 'is_merging', False):
            event.ignore()
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        if getattr(self, 'is_counting_sajdas', False):
            self.is_counting_sajdas = False
            if hasattr(self, 'sajda_thread') and self.sajda_thread.isRunning():
                self.sajda_thread.terminate()
        if getattr(self, 'is_counting_asbab_alnozole', False):
            self.is_counting_asbab_alnozole = False
            if hasattr(self, 'asbab_thread') and self.asbab_thread.isRunning():
                self.asbab_thread.terminate()
        self.media.stop()
        super().closeEvent(event)
