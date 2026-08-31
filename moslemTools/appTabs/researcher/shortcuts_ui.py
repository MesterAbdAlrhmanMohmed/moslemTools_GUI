import guiTools, pyperclip, winsound, functions, re, os, settings, requests, shutil
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from gui.quranViewer import QuranViewer
from gui.tafaseerViewer import TafaseerViewer
from gui.translationViewer import translationViewer
from gui.changeReciter import ChangeReciter
from .search_worker import DownloadThread, SearchModeDialog, SearchThread, RemainingThread


class ResearcherShortcutsUIMixin:
    def create_shortcuts(self):
        qt1.QShortcut(qt2.Qt.Key.Key_Space, self).activated.connect(self.on_spacebar_pressed)
        qt1.QShortcut("Ctrl+T", self).activated.connect(self.on_tafseer_shortcut)
        qt1.QShortcut("Ctrl+L", self).activated.connect(self.on_translation_shortcut)
        qt1.QShortcut("Ctrl+I", self).activated.connect(self.on_iarab_shortcut)
        qt1.QShortcut("Ctrl+E", self).activated.connect(self.on_qiraat_shortcut)
        qt1.QShortcut("Ctrl+U", self).activated.connect(self.on_meanings_shortcut)
        qt1.QShortcut("Ctrl+K", self).activated.connect(self.on_sarf_shortcut)
        qt1.QShortcut("Ctrl+R", self).activated.connect(self.on_tanzil_shortcut)
        qt1.QShortcut("Ctrl+G", self).activated.connect(self.on_goto_surah_shortcut)
        qt1.QShortcut("Ctrl+F", self).activated.connect(self.on_ayah_info_shortcut)
        qt1.QShortcut("Ctrl+H", self).activated.connect(self.on_save_shortcut)
        qt1.QShortcut("Ctrl+Shift+R", self).activated.connect(self.on_change_reciter_requested)
        qt1.QShortcut("Ctrl+C", self).activated.connect(self.copy_line)
        qt1.QShortcut("Ctrl+A", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)

    def on_shortcut_activated(self, action_func):
        cursor = self.results.textCursor()
        line_number = cursor.blockNumber() + 1
        metadata = self.search_metadata.get(line_number)
        if not metadata:
            guiTools.speak("يرجى تحديد آية أولاً لتطبيق الإجراء")
            return
        if isinstance(metadata, dict) and metadata.get("type") == "hadith":
            return
        action_func(metadata)

    def init_ui(self):
        font_combo = qt1.QFont()
        font_combo.setBold(True)
        self.serch_laibol = qt.QLabel("ابحث في")
        self.serch_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch = qt.QComboBox()
        self.serch.addItem("القرآن الكريم")
        self.serch.addItem("الأحاديث")
        self.serch.setFont(font_combo)
        self.serch.setAccessibleName("ابحث في")
        self.ahadeeth_laibol = qt.QLabel("اختيار الكتاب")
        self.ahadeeth_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.ahadeeth = qt.QComboBox()
        ahadeeth_items = ["البحث في جميع كتب الأحاديث المتاحة"] + list(functions.ahadeeth.ahadeeths.keys())
        self.ahadeeth.addItems(ahadeeth_items)
        self.ahadeeth.setFont(font_combo)
        self.ahadeeth.setAccessibleName("اختيار الكتاب")
        self.surahsList = functions.quranJsonControl.getSurahs()
        self.surahs_laybol = qt.QLabel("ابحث في")
        self.surahs_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahs = qt.QComboBox()
        self.surahs.addItems(["كل القرآن", "سور", "صفحات", "أجزاء", "أرباع", "أحزاب"])
        self.surahs.setFont(font_combo)
        self.surahs.setAccessibleName("ابحث في")
        self.surahs.activated.connect(self.on_scope_changed)
        self.specific_scope_label = qt.QLabel("اختر")
        self.specific_scope_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.specific_scope_combo = qt.QComboBox()
        self.specific_scope_combo.setFont(font_combo)
        self.specific_scope_combo.setAccessibleName("اختر القيمة")
        self.specific_scope_label.setVisible(False)
        self.specific_scope_combo.setVisible(False)
        self.current_scope = None
        self.serch.currentIndexChanged.connect(self.toggle_ahadeeth_visibility)
        self.serch.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.serch))
        self.ahadeeth.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.ahadeeth))
        self.surahs.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.surahs))
        self.specific_scope_combo.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.specific_scope_combo))
        self.serch_laibol_content = qt.QLabel("أكتب محتوى البحث")
        self.serch_laibol_content.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch_input = qt.QLineEdit()
        self.serch_input.setAccessibleName("أكتب محتوى البحث")
        self.serch_input.returnPressed.connect(self.onSearchClicked)
        self.ignore_tashkeel = settings.settings_handler.get("researcher_search", "ignore_tashkeel") != "False"
        self.ignore_hamza = settings.settings_handler.get("researcher_search", "ignore_hamza") != "False"
        self.ignore_symbols = settings.settings_handler.get("researcher_search", "ignore_symbols") != "False"
        self.search_mode_button = guiTools.QPushButton("نمط البحث")
        self.search_mode_button.setShortcut("ctrl+q")
        self.search_mode_button.setAccessibleDescription("control plus Q")
        self.search_mode_button.setObjectName("searchModeButton")
        self.search_mode_button.clicked.connect(self.show_search_mode_dialog)
        self.start = guiTools.QPushButton("البحث")
        self.start.setObjectName("startButton")
        self.start.clicked.connect(self.onSearchClicked)
        self.results = guiTools.QReadOnlyTextEdit(viewer_name="researcher")
        self.results.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.OnContextMenu)
        self.results.viewport().installEventFilter(self)
        self.save_feedback_label = qt.QLabel()
        self.save_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.save_progress_bar = qt.QProgressBar()
        self.save_action_button = guiTools.QPushButton("إلغاء العملية")
        self.save_action_button.setAutoDefault(False)
        self.save_action_button.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #A52A2A;}")
        self.save_action_button.clicked.connect(self.cancel_save)
        self.resume_download_button = guiTools.QPushButton("استئناف")
        self.resume_download_button.setAutoDefault(False)
        self.resume_download_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #0000CC;}")
        self.resume_download_button.setVisible(False)
        self.resume_download_button.clicked.connect(self.resume_current_download)
        save_layout = qt.QHBoxLayout()
        save_layout.addWidget(self.save_feedback_label)
        save_layout.addWidget(self.resume_download_button)
        save_layout.addWidget(self.save_progress_bar)
        save_layout.addWidget(self.save_action_button)
        self.save_widget = qt.QWidget()
        self.save_widget.setLayout(save_layout)
        self.save_widget.setVisible(False)
        self.player_widget = qt.QWidget()
        player_layout = qt.QVBoxLayout(self.player_widget)
        player_layout.setContentsMargins(0, 5, 0, 5)
        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.media_progress.setRange(0, 100)
        self.media_progress.valueChanged.connect(self.set_media_position)
        self.time_label = guiTools.QNavigableLabel("0 ثانية")
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Preferred)
        player_layout.addWidget(self.media_progress)
        player_layout.addWidget(self.time_label)
        self.player_widget.setVisible(False)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.clear_results_button = guiTools.QPushButton("حذف النتائج")
        self.clear_results_button.setShortcut("ctrl+del")
        self.clear_results_button.setAccessibleDescription("control plus delete")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.setDisabled(True)
        self.clear_results_button.clicked.connect(self.clear_results)
        self.loading_label = guiTools.QNavigableLabel("جاري تحميل باقي نتائج البحث")
        self.loading_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.loading_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide()
        self.more_options_label = guiTools.QNavigableLabel("لمزيد من الخيارات، نستخدم زر التطبيقات أو click الأيمن")
        self.more_options_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.more_options_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        main_layout = qt.QVBoxLayout(self)
        top_combo_layout = qt.QHBoxLayout()
        top_combo_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        top_combo_layout.setSpacing(20)

        search_layout_top = qt.QVBoxLayout()
        search_layout_top.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        search_layout_top.addWidget(self.serch_laibol, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        search_layout_top.addWidget(self.serch, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        ahadeeth_layout_top = qt.QVBoxLayout()
        ahadeeth_layout_top.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        ahadeeth_layout_top.addWidget(self.ahadeeth_laibol, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        ahadeeth_layout_top.addWidget(self.ahadeeth, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        quran_scope_layout = qt.QHBoxLayout()
        quran_scope_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        quran_scope_layout.setSpacing(15)

        surahs_vbox = qt.QVBoxLayout()
        surahs_vbox.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        surahs_vbox.addWidget(self.surahs_laybol, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        surahs_vbox.addWidget(self.surahs, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        specific_vbox = qt.QVBoxLayout()
        specific_vbox.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        specific_vbox.addWidget(self.specific_scope_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        specific_vbox.addWidget(self.specific_scope_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        quran_scope_layout.addLayout(surahs_vbox)
        quran_scope_layout.addLayout(specific_vbox)
        ahadeeth_layout_top.addLayout(quran_scope_layout)

        top_combo_layout.addLayout(search_layout_top)
        top_combo_layout.addLayout(ahadeeth_layout_top)
        main_layout.addLayout(top_combo_layout)
        main_layout.addWidget(self.serch_laibol_content)
        search_layout = qt.QHBoxLayout()
        search_layout.addWidget(self.search_mode_button)
        search_layout.addWidget(self.serch_input)
        search_layout.addWidget(self.start)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.results)
        main_layout.addWidget(self.save_widget)
        main_layout.addWidget(self.player_widget)
        bottom_layout = qt.QHBoxLayout()
        bottom_layout.addWidget(self.clear_results_button, 0)
        bottom_layout.addSpacing(15)
        font_layout = qt.QVBoxLayout()
        font_layout.addWidget(self.font_laybol)
        font_layout.addWidget(self.show_font)
        bottom_layout.addLayout(font_layout, 1)
        bottom_layout.addSpacing(20)
        options_layout = qt.QVBoxLayout()
        options_layout.addWidget(self.loading_label)
        options_layout.addWidget(self.more_options_label)
        bottom_layout.addLayout(options_layout, 1)
        main_layout.addLayout(bottom_layout)
        self.ahadeeth_laibol.hide()
        self.ahadeeth.hide()
        self.update_font_size()
        self.adjust_all_combos_width()

    def closeEvent(self, event):
        if getattr(self, 'is_saving', False):
            guiTools.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء عملية الحفظ.")
            event.ignore()
        else:
            if hasattr(self, 'remaining_thread') and self.remaining_thread and self.remaining_thread.isRunning():
                self.remaining_thread.cancel()
                self.remaining_thread.wait()
            if self.current_search_thread and self.current_search_thread.isRunning():
                self.current_search_thread.quit()
                self.current_search_thread.wait()
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
            super().closeEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.results.viewport() and event.type() == qt2.QEvent.Type.MouseButtonPress:
            if event.button() == qt2.Qt.MouseButton.LeftButton:
                cursor = self.results.cursorForPosition(event.position().toPoint())
                self.results.setTextCursor(cursor)
                line_number = cursor.blockNumber() + 1
                metadata = self.search_metadata.get(line_number)
                if metadata:
                    if isinstance(metadata, dict) and metadata.get("type") == "hadith":
                        return False
                    self.handle_play_toggle(metadata)
                    return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_all_combos_width()
