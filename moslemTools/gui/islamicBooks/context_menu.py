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


class BookContextMenuMixin:
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

            if hasattr(self, 'total_result_pages') and self.total_result_pages > 1:
                go_res_page_action = menu.addAction("الذهاب إلى صفحة نتائج")
                go_res_page_action.setShortcut("ctrl+shift+g")
                go_res_page_action.triggered.connect(self.go_to_search_result_page)


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
