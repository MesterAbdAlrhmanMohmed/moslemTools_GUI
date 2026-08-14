from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
import re
from gui.quranViewer.threads import SearchModeDialog


class SearchThread(qt2.QThread):
    batch_ready = qt2.pyqtSignal(dict, int, bool)

    def __init__(self, data, search_term, ignore_tashkeel, ignore_hamza, ignore_symbols):
        super().__init__()
        self.data = data
        self.search_term = search_term
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols

    def run(self):
        def remove_tashkeel(text):
            return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

        def normalize_hamza(text):
            return re.sub(r'[أإآ]', 'ا', text)

        def remove_symbols(text):
            return re.sub(r'[^\w\s]', '', text)

        def normalize(text):
            normalized_text = text
            if self.ignore_tashkeel:
                normalized_text = remove_tashkeel(normalized_text)
            if self.ignore_hamza:
                normalized_text = normalize_hamza(normalized_text)
            if self.ignore_symbols:
                normalized_text = remove_symbols(normalized_text)
            return normalized_text

        normalized_pattern = normalize(self.search_term)
        results_by_page = {}
        total_results = 0
        first_batch_emitted = False

        for page_idx, page_content in enumerate(self.data):
            lines = page_content.splitlines()
            page_matches = []
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    continue
                if normalized_pattern in normalize(line):
                    page_matches.append((line_idx, line))
            if page_matches:
                results_by_page[page_idx] = page_matches
                total_results += len(page_matches)
                if not first_batch_emitted and total_results >= 100:
                    self.batch_ready.emit(dict(results_by_page), total_results, False)
                    first_batch_emitted = True

        self.batch_ready.emit(results_by_page, total_results, True)


class book_viewer(qt.QDialog):
    def __init__(self, p, book_name, partName: str, content: list, index: int = 0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.data = content
        self.index = index
        self.bookName = book_name
        self.part = partName
        self.is_search_view = False
        self.search_line_map = {}
        self.ignore_tashkeel = settings.settings_handler.get("islamic_books_search", "ignore_tashkeel") != "False"
        self.ignore_hamza = settings.settings_handler.get("islamic_books_search", "ignore_hamza") != "False"
        self.ignore_symbols = settings.settings_handler.get("islamic_books_search", "ignore_symbols") != "False"
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("alt+right", self).activated.connect(self.next_book)
        qt1.QShortcut("alt+left", self).activated.connect(self.previous_book)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.go_to_book)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copy_page_range)
        qt1.QShortcut("ctrl+alt+s", self).activated.connect(self.save_page_range_as_txt)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.save_page_range_as_docx)
        qt1.QShortcut("ctrl+shift+q", self).activated.connect(self.toggle_search_bar)
        qt1.QShortcut("ctrl+delete", self).activated.connect(self.clear_search_results)
        qt1.QShortcut("ctrl+q", self).activated.connect(self.show_search_mode_dialog)
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
        self.resize(1200, 600)
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
        self.search_mode_button.clicked.connect(self.show_search_mode_dialog)
        self.search_mode_button.setAccessibleDescription("control plus q")
        self.search_mode_button.setAutoDefault(False)
        self.clear_results_button = guiTools.QPushButton("حذف المحتوى والعودة إلى العرض الأصلي")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.clicked.connect(self.clear_search_results)
        self.clear_results_button.setAccessibleDescription("control plus delete")
        self.clear_results_button.setAutoDefault(False)
        search_layout.addWidget(self.clear_results_button)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.search_mode_button)
        self.text = guiTools.QReadOnlyTextEdit(viewer_name="bookViewer")
        self.text.setText(self.data[self.index])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
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
        self.more_options_label = guiTools.QNavigableLabel("لمزيد من الخيارات، نستخدم زر التطبيقات أو click الأيمن")
        self.more_options_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.more_options_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.N_book = guiTools.QPushButton("الصفحة التالية")
        self.N_book.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_book.clicked.connect(self.next_book)
        self.N_book.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_book.setAutoDefault(False)
        self.P_book = guiTools.QPushButton("الصفحة السابقة")
        self.P_book.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_book.clicked.connect(self.previous_book)
        self.P_book.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_book.setAutoDefault(False)
        self.toggle_search_button = guiTools.QPushButton("البحث في المحتوى المعروض")
        self.toggle_search_button.setAutoDefault(False)
        self.toggle_search_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.toggle_search_button.clicked.connect(self.toggle_search_bar)
        self.toggle_search_button.setAccessibleDescription("control plus shift plus q")
        self.book_number_laybol = qt.QLabel("رقم الصفحة")
        self.book_number_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_book_number = guiTools.QNavigableLabel()
        self.show_book_number.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_book_number.setAccessibleDescription("رقم الصفحة")
        self.show_book_number.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.search_widget)
        self.search_widget.hide()
        self.clear_results_button.hide()
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.more_options_label)
        layout.addWidget(self.book_number_laybol)
        layout.addWidget(self.show_book_number)
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.P_book)
        layout1.addWidget(self.toggle_search_button)
        layout1.addWidget(self.N_book)
        layout.addLayout(layout1)
        self.update_font_size()

    def toggle_search_bar(self):
        if self.search_widget.isVisible():
            self.search_widget.hide()
            self.toggle_search_button.setText("البحث في المحتوى المعروض")
            guiTools.speak("تم إخفاء شريط البحث")
            self.text.setFocus()
        else:
            self.search_widget.show()
            self.toggle_search_button.setText("إخفاء شريط البحث")
            self.search_input.setFocus()

    def show_search_mode_dialog(self):
        dialog = SearchModeDialog(self, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        dialog.setStyleSheet("""
            QPushButton#applySearchModeChangesButton {
                background-color: #28a745; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#applySearchModeChangesButton:hover { background-color: #218838; }
            QPushButton#applySearchModeChangesButton:pressed { background-color: #218838; }
            QPushButton#cancelButton {
                background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton#cancelButton:hover { background-color: #c82333; }
            QPushButton#cancelButton:pressed { background-color: #bd2130; }
        """)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            settings_values = dialog.get_settings()
            self.ignore_tashkeel = settings_values["ignore_tashkeel"]
            self.ignore_hamza = settings_values["ignore_hamza"]
            self.ignore_symbols = settings_values["ignore_symbols"]
            guiTools.speak("تم تطبيق إعدادات البحث بنجاح")
        else:
            guiTools.speak("تم إلغاء التغييرات")

    def format_arabic_count(self, count, singular, dual, plural_3_10, plural_11_plus):
        if count == 1:
            return singular
        elif count == 2:
            return dual
        elif 3 <= count % 100 <= 10:
            return f"{count} {plural_3_10}"
        else:
            return f"{count} {plural_11_plus}"

    def perform_search(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return

        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            return

        self._search_spoken = False
        self.search_button.setEnabled(False)
        self.search_button.setStyleSheet("background-color: gray; color: white;")
        guiTools.speak("جاري البحث")

        self.search_thread = SearchThread(self.data, search_term, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        self.search_thread.batch_ready.connect(self.on_search_batch_ready)
        self.search_thread.start()

    def on_search_batch_ready(self, results_by_page, total_results, is_finished):
        if not results_by_page:
            if is_finished:
                self.search_button.setEnabled(True)
                self.search_button.setStyleSheet("")
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على نتائج")
            return

        self.is_search_view = True
        self.P_book.hide()
        self.N_book.hide()
        self.toggle_search_button.hide()
        self.book_number_laybol.hide()
        self.show_book_number.hide()
        self.clear_results_button.show()

        res_str = self.format_arabic_count(total_results, "نتيجة واحدة", "نتيجتين", "نتائج", "نتيجة")
        pages_str = self.format_arabic_count(len(results_by_page), "صفحة واحدة", "صفحتين", "صفحات", "صفحة")
        header = f"عدد نتائج البحث {res_str} في {pages_str}"

        display_lines = [header, ""]
        self.search_line_map = {}

        is_first_page = True
        for page_idx, page_matches in results_by_page.items():
            if not is_first_page:
                display_lines.append("")
            is_first_page = False
            page_res_count_str = self.format_arabic_count(len(page_matches), "نتيجة واحدة", "نتيجتين", "نتائج", "نتيجة")
            display_lines.append(f"الصفحة {page_idx + 1}: {page_res_count_str}")
            for res_idx, (line_idx, line_text) in enumerate(page_matches, start=1):
                result_title_line_idx = len(display_lines)
                display_lines.append(f"النتيجة رقم {res_idx}")
                self.search_line_map[result_title_line_idx] = (page_idx, line_idx, line_text)

                result_content_line_idx = len(display_lines)
                display_lines.append(line_text)
                self.search_line_map[result_content_line_idx] = (page_idx, line_idx, line_text)

        if not hasattr(self, '_search_spoken') or not self._search_spoken:
            guiTools.speak(header)
            self._search_spoken = True

        self.text.setText("\n".join(display_lines))
        self.update_font_size()

        if is_finished:
            self.search_button.setEnabled(True)
            self.search_button.setStyleSheet("")

    def clear_search_results(self):
        if not self.is_search_view:
            return
        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
        self.search_button.setEnabled(True)
        self.search_button.setStyleSheet("")
        self._search_spoken = False
        self.is_search_view = False
        self.search_line_map = {}
        self.clear_results_button.hide()
        self.search_input.clear()
        self.P_book.show()
        self.N_book.show()
        self.toggle_search_button.show()
        self.book_number_laybol.show()
        self.show_book_number.show()
        self.text.setText(self.data[self.index])
        self.update_font_size()
        self.text.setFocus()
        guiTools.speak("تمت العودة إلى العرض الأصلي")

    def go_to_search_result_target(self, target_data):
        page_idx, line_idx, line_text = target_data
        self.clear_search_results()
        self.index = page_idx
        self.text.setText(self.data[self.index])
        self.update_font_size()
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")

        doc = self.text.document()
        block = doc.findBlockByNumber(line_idx)
        if block.isValid():
            cursor = qt1.QTextCursor(block)
            self.text.setTextCursor(cursor)
            self.text.ensureCursorVisible()

        winsound.PlaySound("data/sounds/next_page.wav", 1)
        guiTools.speak(f"الصفحة {self.index + 1}")

    def OnContextMenu(self):
        if self.is_search_view:
            menu = qt.QMenu("الخيارات", self)
            boldFont = menu.font()
            boldFont.setBold(True)
            menu.setFont(boldFont)
            menu.setAccessibleName("الخيارات")

            cursor = self.text.textCursor()
            current_line_idx = cursor.blockNumber()

            if current_line_idx in self.search_line_map:
                target_data = self.search_line_map[current_line_idx]
                go_action = menu.addAction("الذهاب إلى الصفحة والنتيجة")
                go_action.setShortcut("ctrl+g")
                go_action.triggered.connect(lambda: self.go_to_search_result_target(target_data))

                text_options_menu = qt.QMenu("خيارات النص", self)
                text_options_menu.setFont(boldFont)
                save_action = text_options_menu.addAction("حفظ كملف نصي")
                save_action.setShortcut("ctrl+s")
                save_action.triggered.connect(self.save_text_as_txt)
                print_action = text_options_menu.addAction("طباعة")
                print_action.setShortcut("ctrl+p")
                print_action.triggered.connect(self.print_text)
                copy_all_action = text_options_menu.addAction("نسخ النص كاملاً")
                copy_all_action.setShortcut("ctrl+a")
                copy_all_action.triggered.connect(self.copy_text)
                copy_selected_action = text_options_menu.addAction("نسخ النص المحدد")
                copy_selected_action.setShortcut("ctrl+c")
                copy_selected_action.triggered.connect(self.copy_line)
                menu.addMenu(text_options_menu)
            else:
                save_action = menu.addAction("حفظ كملف نصي")
                save_action.setShortcut("ctrl+s")
                save_action.triggered.connect(self.save_text_as_txt)
                print_action = menu.addAction("طباعة")
                print_action.setShortcut("ctrl+p")
                print_action.triggered.connect(self.print_text)
                copy_all_action = menu.addAction("نسخ النص كاملاً")
                copy_all_action.setShortcut("ctrl+a")
                copy_all_action.triggered.connect(self.copy_text)
                copy_selected_action = menu.addAction("نسخ النص المحدد")
                copy_selected_action.setShortcut("ctrl+c")
                copy_selected_action.triggered.connect(self.copy_line)

            menu.exec(self.mapToGlobal(self.cursor().pos()))
            return

        menu = qt.QMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        book_menu = qt.QMenu("خيارات الصفحة", self)
        book_menu.setFont(boldFont)
        next_action = book_menu.addAction("الصفحة التالية")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.next_book)
        previous_action = book_menu.addAction("الصفحة السابقة")
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.previous_book)
        go_action = book_menu.addAction("الذهاب إلى صفحة")
        go_action.setShortcut("ctrl+g")
        go_action.triggered.connect(self.go_to_book)
        menu.addMenu(book_menu)
        book_options_menu = qt.QMenu("خيارات الكتاب", self)
        book_options_menu.setFont(boldFont)
        copy_range_action = book_options_menu.addAction("نسخ محتوى الكتاب")
        copy_range_action.setShortcut("ctrl+alt+c")
        copy_range_action.triggered.connect(self.copy_page_range)
        save_txt_range_action = book_options_menu.addAction("حفظ محتوى الكتاب كملف نصي")
        save_txt_range_action.setShortcut("ctrl+alt+s")
        save_txt_range_action.triggered.connect(self.save_page_range_as_txt)
        save_docx_range_action = book_options_menu.addAction("حفظ محتوة الكتاب كملف Word")
        save_docx_range_action.setShortcut("ctrl+alt+d")
        save_docx_range_action.triggered.connect(self.save_page_range_as_docx)
        menu.addMenu(book_options_menu)
        text_options_menu = qt.QMenu("خيارات النص", self)
        text_options_menu.setFont(boldFont)
        save_action = text_options_menu.addAction("حفظ كملف نصي")
        save_action.setShortcut("ctrl+s")
        save_action.triggered.connect(self.save_text_as_txt)
        print_action = text_options_menu.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all_action = text_options_menu.addAction("نسخ النص كاملاً")
        copy_all_action.setShortcut("ctrl+a")
        copy_all_action.triggered.connect(self.copy_text)
        copy_selected_action = text_options_menu.addAction("نسخ النص المحدد")
        copy_selected_action.setShortcut("ctrl+c")
        copy_selected_action.triggered.connect(self.copy_line)
        menu.addMenu(text_options_menu)
        book_position = {"bookName": self.bookName,"partName": self.part,"pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", book_position)
        if note_exists:
            note_action = qt1.QAction("عرض ملاحظة الصفحة الحالية", self)
            note_action.setShortcut("ctrl+o")
            note_action.triggered.connect(lambda: self.onNoteAction(book_position))
            book_menu.addAction(note_action)
            delete_note_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف ملاحظة الصفحة الحالية:  ctrl+shift+n")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+shift+n")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_button.clicked.connect(lambda: self.onDeleteNote(book_position))
            delete_note_action.setDefaultWidget(delete_button)
            book_menu.addAction(delete_note_action)
        else:
            note_action = qt1.QAction("إضافة ملاحظة للصفحة الحالية", self)
            note_action.setShortcut("ctrl+n")
            note_action.triggered.connect(lambda: self.onAddNote(book_position))
            book_menu.addAction(note_action)
        state, self.nameOfBookmark = functions.bookMarksManager.getIslamicBookBookmarkName(self.bookName, self.index)
        if state:
            delete_bookmark_action = qt.QWidgetAction(self)
            delete_bookmark_button = qt.QPushButton("حذف العلامة المرجعية للصفحة الحالية: ctrl+b")
            delete_bookmark_button.setDefault(True)
            delete_bookmark_button.setShortcut("ctrl+b")
            delete_bookmark_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_bookmark_button.clicked.connect(self.onRemoveBookmark)
            delete_bookmark_action.setDefaultWidget(delete_bookmark_button)
            book_menu.addAction(delete_bookmark_action)
        else:
            add_bookmark_action = qt1.QAction("إضافة علامة مرجعية للصفحة الحالية", self)
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)
            book_menu.addAction(add_bookmark_action)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def get_page_range(self):
        start_page, ok1 = guiTools.QInputDialog.getInt(self, "بداية النطاق", "أدخل رقم صفحة البداية:", value=self.index + 1, min=1, max=len(self.data))
        if not ok1:
            return None, None
        end_page, ok2 = guiTools.QInputDialog.getInt(self, "نهاية النطاق", f"أدخل رقم صفحة النهاية (1-{len(self.data)}):", value=len(self.data), min=1, max=len(self.data))
        if not ok2:
            return None, None
        if start_page > end_page:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "صفحة البداية لا يمكن أن تكون أكبر من صفحة النهاية")
            return None, None
        return start_page, end_page

    def copy_page_range(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        content = ""
        for i in range(start-1, end):
            content += self.data[i] + "\n\n"
        try:
            pyperclip.copy(content)
            winsound.Beep(1000, 100)
            guiTools.qMessageBox.MessageBox.view(self, "تم النسخ", f"تم نسخ المحتوى من الصفحة {start} إلى الصفحة {end}")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في النسخ", str(e))

    def save_page_range_as_txt(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    for i in range(start-1, end):
                        file.write(self.data[i] + "\n\n")
                guiTools.speak(f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))

    def save_page_range_as_docx(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Word Documents (*.docx);;All Files (*)")
            file_dialog.setDefaultSuffix("docx")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                doc = Document()
                for i in range(start-1, end):
                    p = doc.add_paragraph(self.data[i])
                    if i < end-1:
                        doc.add_page_break()
                doc.save(file_name)
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف Word")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))

    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()

    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("islamicBooks", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()

    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("islamicBooks", name)
        if existing_note is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("islamicBooks", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")

    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("islamicBooks", new_name)
            if existing_note is not None:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("islamicBooks", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")

    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()

    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("islamicBooks", note["name"])
                guiTools.speak("تم حذف الملاحظة")

    def onAddOrRemoveNote(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)

    def onViewNote(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الصفحة")

    def print_text(self):
        functions.text_actions.print_text_content(self, self.text)

    def save_text_as_txt(self):
        functions.text_actions.save_text_file(self, self.text)

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def update_font_size(self):
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)

    def copy_line(self):
        functions.text_actions.copy_current_selection(self, self.text)

    def copy_text(self):
        functions.text_actions.copy_all_text(self, self.text)

    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getIslamicBookBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
            functions.bookMarksManager.addNewislamicBookBookMark(self.bookName, self.part, self.index, name)
            guiTools.speak("تمت إضافة العلامة المرجعية")

    def onRemoveBookmark(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", "نعم", "لا")
            if confirm == 0:
                functions.bookMarksManager.removeislamicBookBookMark(self.nameOfBookmark)
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف العلامة المرجعية")

    def onAddOrRemoveBookmark(self):
        state, self.nameOfBookmark = functions.bookMarksManager.getIslamicBookBookmarkName(self.bookName, self.index)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()

    def next_book(self):
        if self.is_search_view:
            return
        self.index = 0 if self.index == len(self.data) - 1 else self.index + 1
        self.text.setText(self.data[self.index])
        self.update_font_size()
        guiTools.speak(str(self.index + 1))
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/next_page.wav", 1)

    def previous_book(self):
        if self.is_search_view:
            return
        self.index = len(self.data) - 1 if self.index == 0 else self.index - 1
        self.text.setText(self.data[self.index])
        self.update_font_size()
        guiTools.speak(str(self.index + 1))
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/previous_page.wav", 1)

    def go_to_book(self):
        if self.is_search_view:
            cursor = self.text.textCursor()
            current_line_idx = cursor.blockNumber()
            if current_line_idx in self.search_line_map:
                target_data = self.search_line_map[current_line_idx]
                self.go_to_search_result_target(target_data)
            else:
                winsound.Beep(440, 200)
                guiTools.speak("قم بالتركيز على نتيجة أولا")
        else:
            book, OK = guiTools.QInputDialog.getInt(self, "الذهاب إلى صفحة", "أكتب رقم الصفحة", self.index + 1, 1, len(self.data))
            if OK:
                self.index = book - 1
                self.text.setText(self.data[self.index])
                self.update_font_size()
                self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")

    def onDeleteNoteShortcut(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
