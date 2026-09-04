import os
import winsound
import pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
import custom_errors
import guiTools
import settings
from settings import settings_handler
import ujson as json

with open("data/json/files/all_moton_reciters.json", "r", encoding="utf-8") as file:
    moton_reciters = json.load(file)

from .context_menu import MotonPlayerContextMenuMixin
from .navigation_display import MotonPlayerNavigationDisplayMixin
from .merger_saver import MotonPlayerMergerSaverMixin
from .audio_player import MotonPlayerAudioMixin

class MotonPlayer(MotonPlayerContextMenuMixin, MotonPlayerNavigationDisplayMixin, MotonPlayerMergerSaverMixin, MotonPlayerAudioMixin, qt.QDialog):
    def __init__(self, parent=None, matn_name="", matn_slug="", parsed_sections=None, start_bayt=1, current_reciter_slug="", current_reciter_type="N", verses=None, verse_numbering_mode=None):
        super().__init__(parent)
        self.matn_name = matn_name
        self.matn_slug = matn_slug
        self.parsed_sections = parsed_sections
        self.current_reciter_slug = current_reciter_slug
        self.current_reciter_type = current_reciter_type
        self.show_diacritics = settings_handler.get("motonPlayer", "show_diacritics") != "False"
        self.font_is_bold = settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings_handler.get("font", "motonPlayer_size") or settings_handler.get("font", "size") or 18)
        if verse_numbering_mode is not None:
            self.verse_numbering_mode = verse_numbering_mode
        elif hasattr(parent, "verse_numbering_mode"):
            self.verse_numbering_mode = parent.verse_numbering_mode
        else:
            self.verse_numbering_mode = settings_handler.get("motonViewer", "verse_numbering_mode") or "by_chapter"

        if verses is not None:
            self.all_verses_list = list(verses)
        elif self.parsed_sections is not None:
            self.all_verses_list = []
            for sec in self.parsed_sections:
                for v in sec.get("verses", []):
                    self.all_verses_list.append(v)
        else:
            from functions.moton_data import MotonDataLoader
            loader = MotonDataLoader()
            if not self.matn_slug and self.matn_name:
                self.matn_slug = loader.get_matn_slug(self.matn_name)
            self.parsed_sections = loader.get_matn_data(self.matn_slug)
            self.all_verses_list = []
            for sec in self.parsed_sections:
                for v in sec.get("verses", []):
                    self.all_verses_list.append(v)
        self.total_verses = len(self.all_verses_list)
        self.current_index = max(0, min(start_bayt - 1, self.total_verses - 1)) if self.total_verses > 0 else 0
        self.current_bayt_num = self.all_verses_list[self.current_index]["global_num"] if (0 <= self.current_index < self.total_verses and "global_num" in self.all_verses_list[self.current_index]) else (self.current_index + 1)

        self.resize(1200, 600)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)

        self.load_reciters_data()
        self.init_ui()
        self.init_audio()
        self.init_merger_saver()

        self.update_display_text()
        qt2.QTimer.singleShot(0, self.on_play)

    def get_bayt_by_global_num(self, global_num):
        for v in self.all_verses_list:
            if v.get("global_num") == global_num:
                return v
        return None

    def load_reciters_data(self):
        from functions.moton_data import get_moton_reciters_for_matn, get_all_moton_reciters
        reciters_list = get_moton_reciters_for_matn(self.matn_slug)
        self.available_reciters = []
        for r_ar, r_slug, r_type, r_url in reciters_list:
            self.available_reciters.append((r_ar, r_slug, r_type))

        all_reciters_info = get_all_moton_reciters().get("reciters", {})

        if self.available_reciters:
            if not self.current_reciter_slug:
                saved_reciter = (
                    settings_handler.get("moton_player_reciters", self.matn_slug) or
                    settings_handler.get("moton_player_reciters", "default") or
                    settings_handler.get("moton_reciters", self.matn_slug) or
                    settings_handler.get("moton_reciters", "default")
                )
                if saved_reciter and saved_reciter in [r[1] for r in self.available_reciters]:
                    self.current_reciter_slug = saved_reciter
            if self.current_reciter_slug in [r[1] for r in self.available_reciters]:
                self.current_reciter_ar = all_reciters_info.get(self.current_reciter_slug, self.current_reciter_slug)
                for r in self.available_reciters:
                    if r[1] == self.current_reciter_slug:
                        self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = r
                        break
            else:
                self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = self.available_reciters[0]
        else:
            self.current_reciter_ar = ""
            self.current_reciter_slug = ""
            self.current_reciter_type = "N"

    def init_ui(self):
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.text = guiTools.QReadOnlyTextEdit(viewer_name="motonPlayer")
        option = self.text.document().defaultTextOption()
        option.setAlignment(qt2.Qt.AlignmentFlag.AlignRight)
        option.setTextDirection(qt2.Qt.LayoutDirection.RightToLeft)
        self.text.document().setDefaultTextOption(option)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.setFocus()
        self.update_font_size()
        main_layout.addWidget(self.text, 1)

        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setRange(0, 100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")

        self.time_label = guiTools.QNavigableLabel()
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Preferred)

        progress_time_layout = qt.QVBoxLayout()
        progress_time_layout.addWidget(self.media_progress)
        progress_time_layout.addWidget(self.time_label)
        main_layout.addLayout(progress_time_layout)

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
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        merge_layout.addWidget(self.resume_download_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        main_layout.addWidget(self.merge_widget)

        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)

        main_layout.addWidget(self.font_laybol)
        main_layout.addWidget(self.show_font)

        controls_layout = qt.QHBoxLayout()
        controls_layout.setSpacing(10)

        self.N_bayt = guiTools.QPushButton("البيت التالي")
        self.N_bayt.setAutoDefault(False)
        self.N_bayt.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_bayt.clicked.connect(self.onNextBayt)
        self.N_bayt.setAccessibleDescription("alt زائد السهم الأيمن")

        self.PPS = guiTools.QPushButton("تشغيل")
        self.PPS.setAutoDefault(False)
        self.PPS.setAccessibleDescription("space")
        self.PPS.clicked.connect(self.on_play)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")

        self.P_bayt = guiTools.QPushButton("البيت السابق")
        self.P_bayt.setAutoDefault(False)
        self.P_bayt.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_bayt.clicked.connect(self.onPreviousBayt)
        self.P_bayt.setAccessibleDescription("alt زائد السهم الأيسر")

        self.changeCurrentReciterButton = guiTools.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.setAutoDefault(False)
        self.changeCurrentReciterButton.clicked.connect(self.on_change_reciter)
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus R")

        self.mergeButton = guiTools.QPushButton("دمج الأبيات")
        self.mergeButton.setAutoDefault(False)
        self.mergeButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.mergeButton.clicked.connect(self.merge_all_verses)
        self.mergeButton.setAccessibleDescription("control plus alt plus d")

        self.saveAllButton = guiTools.QPushButton("حفظ الأبيات")
        self.saveAllButton.setAutoDefault(False)
        self.saveAllButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.saveAllButton.clicked.connect(self.save_all_verses_audio)
        self.saveAllButton.setAccessibleDescription("control plus alt plus h")

        controls_layout.addWidget(self.changeCurrentReciterButton)
        controls_layout.addWidget(self.P_bayt)
        controls_layout.addWidget(self.PPS)
        controls_layout.addWidget(self.N_bayt)
        controls_layout.addWidget(self.mergeButton)
        controls_layout.addWidget(self.saveAllButton)
        main_layout.addLayout(controls_layout)

        qt1.QShortcut("alt+right", self).activated.connect(self.onNextBayt)
        qt1.QShortcut("alt+left", self).activated.connect(self.onPreviousBayt)
        qt1.QShortcut("space", self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+shift+r", self).activated.connect(self.on_change_reciter)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.merge_all_verses)
        qt1.QShortcut("ctrl+alt+h", self).activated.connect(self.save_all_verses_audio)
        qt1.QShortcut("ctrl+h", self).activated.connect(self.save_current_bayt_audio)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.on_goto_bayt_dialog)
        qt1.QShortcut("ctrl+x", self).activated.connect(self.on_toggle_diacritics)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_bayt)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("escape", self).activated.connect(self.close_window)

    def on_change_reciter(self):
        if not self.available_reciters:
            guiTools.speak("لا يتوفر قراء مسجلين لهذا المتن")
            return
        self.was_playing = (self.media.playbackState() == self.media.PlaybackState.PlayingState)
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")
        menu = guiTools.QCustomContextMenu("اختيار القارئ", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("اختيار القارئ")
        group = qt1.QActionGroup(self)
        group.setExclusive(True)
        for r_ar, r_slug, r_type in self.available_reciters:
            action = qt1.QAction(r_ar, self)
            action.setCheckable(True)
            if r_slug == self.current_reciter_slug:
                action.setChecked(True)
            action.triggered.connect(lambda checked, rec=(r_ar, r_slug, r_type): self._set_reciter(rec))
            group.addAction(action)
            menu.addAction(action)
        menu.aboutToHide.connect(self.resume_playback)
        menu.exec(qt1.QCursor.pos())

    def _set_reciter(self, selected):
        self.media.stop()
        self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = selected
        guiTools.speak(f"تم اختيار القارئ: {self.current_reciter_ar}")
        self.was_playing = False
        self.on_play()

    def safeClose(self):
        if getattr(self, 'is_merging', False):
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_audio()
            qt2.QTimer.singleShot(100, self.close)
        else:
            self.close()

    def close_window(self):
        if getattr(self, 'is_merging', False):
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        self.stop_audio()
        self.close()

    def reject(self):
        if getattr(self, 'is_merging', False):
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        self.stop_audio()
        super().reject()

    def keyPressEvent(self, event):
        if event.key() == qt2.Qt.Key.Key_Escape:
            if getattr(self, 'is_merging', False):
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
                return
            self.close()
            return
        if event.key() == qt2.Qt.Key.Key_Menu:
            self.oncontextMenu()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if getattr(self, 'is_merging', False):
            event.ignore()
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        self.stop_audio()
        super().closeEvent(event)
