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
from .threads import SearchThread


class BookSearchMixin:
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
        if not self.search_widget.isVisible():
            return
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

        self.search_thread = SearchThread(self.bookName, self.part, search_term, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols, page_num=1, limit=100)
        self.search_thread.batch_ready.connect(self.on_search_batch_ready)
        self.search_thread.start()

    def fetch_result_page(self, page_num):
        search_term = self.search_input.text().strip()
        if not search_term:
            return
        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            return
        self.search_button.setEnabled(False)
        self.search_button.setStyleSheet("background-color: gray; color: white;")
        guiTools.speak(f"جاري تحميل صفحة النتائج {page_num}")
        self.search_thread = SearchThread(self.bookName, self.part, search_term, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols, page_num=page_num, limit=100)
        self.search_thread.batch_ready.connect(self.on_search_batch_ready)
        self.search_thread.start()

    def on_search_batch_ready(self, results_by_page, total_results, total_book_pages, is_finished, page_num=1, total_pages=1):
        if not results_by_page:
            if is_finished:
                self.search_button.setEnabled(True)
                self.search_button.setStyleSheet("")
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على نتائج")
            return

        self.is_search_view = True
        self.current_result_page = page_num
        self.total_result_pages = total_pages
        self.total_search_results = total_results

        self.P_book.hide()
        self.N_book.hide()
        self.toggle_search_button.hide()
        self.book_number_laybol.hide()
        self.show_book_number.hide()
        self.clear_results_button.show()
        if total_pages > 1:
            self.P_search.show()
            self.N_search.show()
            self.search_results_page_label.show()
            self.show_search_results_page.setText(f"{page_num} من {total_pages}")
            self.show_search_results_page.show()
        else:
            self.P_search.hide()
            self.N_search.hide()
            self.search_results_page_label.hide()
            self.show_search_results_page.hide()

        res_str = self.format_arabic_count(total_results, "نتيجة واحدة", "نتيجتين", "نتائج", "نتيجة")
        book_pages_str = self.format_arabic_count(total_book_pages, "صفحة واحدة من الكتاب", "صفحتين من الكتاب", "صفحات من الكتاب", "صفحة من الكتاب")
        result_pages_str = self.format_arabic_count(total_pages, "صفحة نتائج واحدة", "صفحتين نتائج", "صفحات نتائج", "صفحة نتائج")

        header = f"تم العثور على {res_str} في {book_pages_str}"
        if total_pages > 1:
            header += f"، وتم تقسيم النتائج إلى {result_pages_str}"


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
        else:
            guiTools.speak(f"تم تحميل صفحة النتائج {page_num}")

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
        self.P_search.hide()
        self.N_search.hide()
        self.search_results_page_label.hide()
        self.show_search_results_page.hide()
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

    def go_to_search_result_page(self):
        if not self.is_search_view or not hasattr(self, 'total_result_pages') or self.total_result_pages <= 1:
            winsound.Beep(440, 200)
            guiTools.speak("لا توجد صفحات نتائج متعددة للذهاب إليها")
            return
        page, OK = guiTools.QInputDialog.getInt(self, "الذهاب إلى صفحة نتائج", "أكتب رقم صفحة النتائج", self.current_result_page, 1, self.total_result_pages)
        if OK:
            self.fetch_result_page(page)
