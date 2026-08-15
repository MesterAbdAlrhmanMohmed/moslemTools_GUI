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


class BookNavigationDisplayMixin:
    def next_book(self):
        if self.is_search_view:
            if hasattr(self, 'total_result_pages') and self.total_result_pages > 1:
                next_page = 1 if self.current_result_page >= self.total_result_pages else self.current_result_page + 1
                winsound.PlaySound("data/sounds/next_page.wav", 1)
                self.fetch_result_page(next_page)
            return
        self.index = 0 if self.index == len(self.data) - 1 else self.index + 1
        self.text.setText(self.data[self.index])
        self.update_font_size()
        guiTools.speak(str(self.index + 1))
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/next_page.wav", 1)

    def previous_book(self):
        if self.is_search_view:
            if hasattr(self, 'total_result_pages') and self.total_result_pages > 1:
                prev_page = self.total_result_pages if self.current_result_page <= 1 else self.current_result_page - 1
                winsound.PlaySound("data/sounds/previous_page.wav", 1)
                self.fetch_result_page(prev_page)
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
