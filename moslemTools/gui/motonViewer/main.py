import os
import re
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
from functions.moton_data import MotonDataLoader, get_all_moton_reciters
from functions import audio_manager, text_actions

with open("data/json/files/all_moton_reciters.json", "r", encoding="utf-8") as file:
    moton_reciters = json.load(file)
from .context_menu import MotonContextMenuMixin
from .notes_bookmarks import MotonNotesBookmarksMixin
from .search_handler import MotonSearchHandlerMixin
from .merger_saver import MotonMergerSaverMixin
from .navigation_display import MotonNavigationDisplayMixin
from .audio_player import MotonAudioPlayerMixin

class MotonViewer(MotonContextMenuMixin, MotonNotesBookmarksMixin, MotonSearchHandlerMixin, MotonMergerSaverMixin, MotonNavigationDisplayMixin, MotonAudioPlayerMixin, qt.QDialog):
    def __init__(self, parent=None, matn_name="", chapter_index=0, chapter_title="", is_full_matn=False, index=None):
        super().__init__(parent)
        self.matn_name = matn_name
        self.chapter_index = chapter_index
        self.chapter_title = chapter_title
        self.is_full_matn = is_full_matn
        self.initial_bayt_index = index
        self.data_loader = MotonDataLoader()
        self.matn_slug = self.data_loader.get_matn_slug(self.matn_name)
        self.parsed_sections = []
        self.total_verses = 0
        self.available_reciters = []
        self.current_reciter_slug = ""
        self.current_reciter_ar = ""
        self.current_reciter_type = "N"

        self.resize(1200, 600)
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

        self.load_reciters_data()
        self.parse_matn_file()

        self.text = guiTools.QReadOnlyTextEdit(viewer_name="motonViewer")
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.viewport().installEventFilter(self)

        self.init_navigation_display()
        self.init_audio_player()
        self.init_merger_saver()
        self.init_search_handler()
        self.init_ui()

        self._update_display_text()
        if self.initial_bayt_index is not None:
            self._go_to_specific_bayt(self.initial_bayt_index)

    def showEvent(self, event):
        super().showEvent(event)
        if self.initial_bayt_index is not None:
            self._go_to_specific_bayt(self.initial_bayt_index)
            self.initial_bayt_index = None
        else:
            self.text.setFocus()

    def format_title_text(self):
        if self.is_full_matn:
            return self.matn_name
        clean_chapter = re.sub(r'\s*\(\s*[^)]+\s*\)', '', self.chapter_title).strip()
        clean_matn = self.matn_name if self.matn_name.startswith("متن ") else f"متن {self.matn_name}"
        return f"{clean_chapter}: من {clean_matn}"

    def load_reciters_data(self):
        from functions.moton_data import get_moton_reciters_for_matn
        reciters_list = get_moton_reciters_for_matn(self.matn_slug)
        self.available_reciters = []
        for r_ar, r_slug, r_type, r_url in reciters_list:
            self.available_reciters.append((r_ar, r_slug, r_type))

        if self.available_reciters:
            saved_reciter = (
                settings_handler.get("moton_viewer_reciters", self.matn_slug) or
                settings_handler.get("moton_viewer_reciters", "default") or
                settings_handler.get("moton_reciters", self.matn_slug) or
                settings_handler.get("moton_reciters", "default")
            )
            matched = False
            if saved_reciter:
                for r in self.available_reciters:
                    if r[1] == saved_reciter or r[0] == saved_reciter:
                        self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = r
                        matched = True
                        break
            if not matched:
                self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = self.available_reciters[0]
        else:
            self.current_reciter_ar = ""
            self.current_reciter_slug = ""
            self.current_reciter_type = "N"

    def convert_arabic_digits(self, num_str):
        mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        return num_str.translate(mapping)

    def parse_matn_file(self):
        from functions.moton_data import get_matn_text
        content = get_matn_text(self.matn_slug)
        if not content:
            return

        sections = re.split(r"\*{3,}", content)
        sec_data = sections[1:] if len(sections) > 1 else [sections[0]]
        self.parsed_sections = []
        global_bayt_counter = 0

        for s_idx, s in enumerate(sec_data):
            lines = [l.strip() for l in s.strip().split("\n") if l.strip()]
            if not lines:
                continue
            def format_ch(match):
                raw_s = match.group(1)
                mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                cnt = int(raw_s.translate(mapping))
                return f"({text_actions.format_arabic_bayt_count(cnt)})"
            has_raw_num = bool(re.search(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', lines[0]))
            title = re.sub(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', format_ch, lines[0]) if has_raw_num else lines[0]
            verse_lines = lines[1:] if len(sections) > 1 else lines
            verses = []
            i = 0
            while i < len(verse_lines):
                line = verse_lines[i]
                m = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))(.*)", line)
                if m:
                    raw_s = m.group(1) or m.group(2) or m.group(3)
                    raw_num = int(self.convert_arabic_digits(raw_s))
                    sadr = m.group(4).strip()
                    if i + 1 < len(verse_lines):
                        next_l = verse_lines[i + 1]
                        m_next = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))", next_l)
                        if not m_next:
                            ajuz = next_l.strip()
                            i += 2
                        else:
                            ajuz = ""
                            i += 1
                    else:
                        ajuz = ""
                        i += 1
                    global_bayt_counter += 1
                    verses.append({
                        "global_num": global_bayt_counter,
                        "chapter_bayt_num": len(verses) + 1,
                        "raw_num": raw_num,
                        "sadr": sadr,
                        "ajuz": ajuz,
                        "chapter_title": title,
                        "chapter_index": s_idx
                    })
                else:
                    i += 1
            if not has_raw_num and verses:
                title = f"{lines[0]} ({text_actions.format_arabic_bayt_count(len(verses))})"
                for v in verses:
                    v["chapter_title"] = title
            self.parsed_sections.append({"title": title, "verses": verses})
        self.total_verses = global_bayt_counter

    def init_ui(self):
        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0, 100)
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

        self.info = guiTools.QNavigableLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText(self.format_title_text())

        layout = qt.QVBoxLayout(self)

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

        self.clear_results_button = guiTools.QPushButton("حذف المحتوى والعودة إلى العرض الأصلي")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.setStyleSheet("background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; min-height: 30px;")
        self.clear_results_button.clicked.connect(self.clear_search_results)
        self.clear_results_button.setAccessibleDescription("control plus delete")
        self.clear_results_button.setAutoDefault(False)

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
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        merge_layout.addWidget(self.resume_download_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        layout.addWidget(self.merge_widget)

        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)

        info_label_text = "لمزيد من خيارات المتن أو البيت، نستخدم زر التطبيقات أو click الأيمن على بيت من الأبيات" if self.is_full_matn else "لمزيد من خيارات الباب أو البيت، نستخدم زر التطبيقات أو click الأيمن على بيت من الأبيات"
        self.options_info_label = guiTools.QNavigableLabel(info_label_text)
        self.options_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.options_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.options_info_label)
        layout.addWidget(self.info)

        buttonsLayout = qt.QHBoxLayout()
        self.changeCurrentReciterButton = guiTools.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.setAutoDefault(False)
        self.changeCurrentReciterButton.clicked.connect(self.on_change_reciter)
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus r")
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        buttonsLayout.addWidget(self.changeCurrentReciterButton)

        if not self.is_full_matn:
            self.previous = guiTools.QPushButton("الباب السابق")
            self.previous.setAutoDefault(False)
            self.previous.clicked.connect(self.onPreviouse)
            self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
            self.previous.setStyleSheet("background-color: #0000AA; color: white;")

            self.changeCategory = guiTools.QPushButton("تغيير الباب")
            self.changeCategory.setAutoDefault(False)
            self.changeCategory.setStyleSheet("background-color: #0000AA; color: white;")
            self.changeCategory.setAccessibleDescription("control plus alt plus g")
            self.changeCategory.clicked.connect(self.onChangeCategory)

            self.next = guiTools.QPushButton("الباب التالي")
            self.next.setAutoDefault(False)
            self.next.clicked.connect(self.onNext)
            self.next.setAccessibleDescription("alt زائد السهم الأيمن")
            self.next.setStyleSheet("background-color: #0000AA; color: white;")

            buttonsLayout.addWidget(self.previous)
            buttonsLayout.addWidget(self.changeCategory)
            buttonsLayout.addWidget(self.next)

            qt1.QShortcut("alt+right", self).activated.connect(self.onNext)
            qt1.QShortcut("alt+left", self).activated.connect(self.onPreviouse)
            qt1.QShortcut("ctrl+alt+g", self).activated.connect(self.onChangeCategory)

        search_btn_text = "البحث في المتن" if self.is_full_matn else "البحث في الباب"
        self.toggle_search_button = guiTools.QPushButton(search_btn_text)
        self.toggle_search_button.setAutoDefault(False)
        self.toggle_search_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.toggle_search_button.clicked.connect(self.toggle_search_bar)
        self.toggle_search_button.setAccessibleDescription("control plus shift plus q")

        self.numbering_button = guiTools.QPushButton("طريقة عرض الأبيات")
        self.numbering_button.setAutoDefault(False)
        self.numbering_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.numbering_button.setAccessibleDescription("control plus shift plus s")
        self.numbering_button.clicked.connect(self._show_numbering_options)

        buttonsLayout.addWidget(self.toggle_search_button)
        buttonsLayout.addWidget(self.numbering_button)
        layout.addLayout(buttonsLayout)
        qt1.QShortcut("ctrl+shift+r", self).activated.connect(self.on_change_reciter)
        qt1.QShortcut("ctrl+shift+q", self).activated.connect(self.toggle_search_bar)
        qt1.QShortcut("ctrl+q", self).activated.connect(self.show_search_mode_dialog)
        qt1.QShortcut("ctrl+delete", self).activated.connect(self.clear_search_results)
        qt1.QShortcut("ctrl+shift+s", self).activated.connect(self._show_numbering_options)
        qt1.QShortcut("ctrl+x", self).activated.connect(lambda: self.handle_invalid_line_action() if not self.get_bayt_at_cursor() else self.removeTashkeelForBayt())
        qt1.QShortcut("ctrl+shift+x", self).activated.connect(lambda: self.handle_invalid_line_action() if not self.get_bayt_at_cursor() else self.toggleTashkeelView())
        qt1.QShortcut("space", self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.goToBayt)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+a", self).activated.connect(lambda: self.handle_invalid_line_action() if not self.get_bayt_at_cursor() else text_actions.copy_all_text(self, self.text))
        qt1.QShortcut("ctrl+s", self).activated.connect(lambda: self.handle_invalid_line_action() if not self.get_bayt_at_cursor() else text_actions.save_text_file(self, self.text, f"{self.matn_name}.txt"))
        qt1.QShortcut("ctrl+p", self).activated.connect(lambda: self.handle_invalid_line_action() if not self.get_bayt_at_cursor() else text_actions.print_text_content(self, self.text))
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+shift+p", self).activated.connect(self.playFromBaytToEnd)
        qt1.QShortcut("ctrl+alt+p", self).activated.connect(self.playFromVersToVers)
        qt1.QShortcut("ctrl+shift+d", self).activated.connect(self.mergeCategoryBayts)
        qt1.QShortcut("shift+alt+d", self).activated.connect(self.mergeFromBaytToEnd)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.mergeBayts)
        qt1.QShortcut("ctrl+shift+h", self).activated.connect(self.saveCategoryBayts)
        qt1.QShortcut("shift+alt+h", self).activated.connect(self.saveFromBaytToEnd)
        qt1.QShortcut("ctrl+alt+h", self).activated.connect(self.saveFromVersToVers)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copyFromVersToVers)
        qt1.QShortcut("escape", self).activated.connect(self.close_window)

    def copy_current_selection(self):
        cursor = self.text.textCursor()
        if cursor.hasSelection():
            pyperclip.copy(cursor.selectedText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النص المحدد")
        else:
            b = self.get_bayt_at_cursor()
            if not b:
                self.handle_invalid_line_action()
                return
            self.copy_bayt(b)

    def on_change_reciter(self):
        if not self.available_reciters:
            guiTools.speak("لا يتوفر قراء مسجلين لهذا المتن")
            return
        self.pause_for_action()
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
        menu.aboutToHide.connect(self.resume_after_action)
        menu.exec(qt1.QCursor.pos())

    def _set_reciter(self, selected):
        changed = (selected[1] != self.current_reciter_slug)
        self.current_reciter_ar, self.current_reciter_slug, self.current_reciter_type = selected
        guiTools.speak(f"تم اختيار القارئ: {self.current_reciter_ar}")
        if changed and getattr(self, 'was_playing_before_action', False):
            self.stop_audio()
            self.was_playing_before_action = False
            self.on_play()

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
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if getattr(self, 'is_merging', False):
            event.ignore()
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكن إغلاق النافذة أثناء العملية الجارية.")
            return
        self.stop_audio()
        super().closeEvent(event)
