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
    batch_ready = qt2.pyqtSignal(dict, int, int, bool, int, int)

    def __init__(self, book_name, part_name, search_term, ignore_tashkeel, ignore_hamza, ignore_symbols, page_num=1, limit=100):
        super().__init__()
        self.book_name = book_name
        self.part_name = part_name
        self.search_term = search_term
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols
        self.page_num = page_num
        self.limit = limit

    def run(self):
        json_path = functions.searchIndex.get_book_json_path(self.book_name)
        if not json_path:
            self.batch_ready.emit({}, 0, 0, True, 1, 1)
            return

        db_path = functions.searchIndex.get_index_db_path(json_path)
        if not functions.searchIndex.is_index_valid(json_path, db_path):
            functions.searchIndex.build_index(json_path, db_path)

        offset = (self.page_num - 1) * self.limit
        results_by_page, total_results, total_book_pages = functions.searchIndex.query_index(
            db_path, self.part_name, self.search_term,
            self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols,
            offset=offset, limit=self.limit
        )

        total_pages = max(1, (total_results + self.limit - 1) // self.limit) if total_results > 0 else 1
        self.batch_ready.emit(results_by_page, total_results, total_book_pages, True, self.page_num, total_pages)
