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
from .search_handler import BookSearchMixin
from .notes_bookmarks import BookNotesBookmarksMixin
from .export_range import BookExportRangeMixin
from .navigation_display import BookNavigationDisplayMixin
from .context_menu import BookContextMenuMixin


class book_viewer(BookContextMenuMixin, BookNavigationDisplayMixin, BookExportRangeMixin, BookNotesBookmarksMixin, BookSearchMixin, qt.QDialog):
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
        qt1.QShortcut("ctrl+shift+g", self).activated.connect(self.go_to_search_result_page)

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
        self.search_results_page_label = qt.QLabel("صفحة النتائج")
        self.search_results_page_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_results_page_label.hide()
        self.show_search_results_page = guiTools.QNavigableLabel()
        self.show_search_results_page.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_search_results_page.setAccessibleDescription("صفحة النتائج")
        self.show_search_results_page.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_search_results_page.hide()
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.search_widget)
        self.search_widget.hide()
        self.clear_results_button.hide()
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.more_options_label)
        layout.addWidget(self.search_results_page_label)
        layout.addWidget(self.show_search_results_page)
        layout.addWidget(self.book_number_laybol)
        layout.addWidget(self.show_book_number)

        self.N_search = guiTools.QPushButton("صفحة النتائج التالية")
        self.N_search.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_search.clicked.connect(self.next_book)
        self.N_search.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_search.setAutoDefault(False)
        self.P_search = guiTools.QPushButton("صفحة النتائج السابقة")
        self.P_search.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_search.clicked.connect(self.previous_book)
        self.P_search.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_search.setAutoDefault(False)
        self.P_search.hide()
        self.N_search.hide()
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.P_book)
        layout1.addWidget(self.P_search)
        layout1.addWidget(self.toggle_search_button)
        layout1.addWidget(self.N_search)
        layout1.addWidget(self.N_book)
        layout.addLayout(layout1)
        self.update_font_size()
