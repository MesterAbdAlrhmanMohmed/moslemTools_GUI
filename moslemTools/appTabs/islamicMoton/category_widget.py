import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import guiTools

class MotonCategoryWidget(qt.QWidget):
    def __init__(self, category_index, data_loader, on_toggle_fav_callback):
        super().__init__()
        self.category_index = category_index
        self.data_loader = data_loader
        self.on_toggle_fav_callback = on_toggle_fav_callback
        self.init_ui()

    def init_ui(self):
        layout = qt.QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        moton_layout = qt.QVBoxLayout()
        moton_layout.setSpacing(10)
        self.moton_label = qt.QLabel("اختيار متن")
        self.moton_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        self.moton_label.setFont(font)

        self.moton_list = guiTools.QListWidget()
        self.moton_list.setSpacing(5)
        self.moton_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.moton_list.itemSelectionChanged.connect(self.on_moton_selected)
        self.moton_list.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.moton_list.customContextMenuRequested.connect(self.on_moton_context_menu)

        moton_layout.addWidget(self.moton_label)
        moton_layout.addWidget(self.moton_list)

        chapters_layout = qt.QVBoxLayout()
        chapters_layout.setSpacing(10)
        self.chapters_label = qt.QLabel("اختيار باب")
        self.chapters_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.chapters_label.setFont(font)

        self.chapters_list = guiTools.QListWidget()
        self.chapters_list.setSpacing(5)
        self.chapters_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.chapters_list.itemActivated.connect(self.on_chapter_activated)

        chapters_layout.addWidget(self.chapters_label)
        chapters_layout.addWidget(self.chapters_list)

        layout.addLayout(moton_layout, 1)
        layout.addLayout(chapters_layout, 1)

        self.populate_moton()

    def populate_moton(self):
        self.moton_list.clear()
        moton_items = self.data_loader.get_moton_for_category(self.category_index)
        if moton_items:
            self.moton_list.addItems(moton_items)
            self.moton_list.setCurrentRow(0)
            self.on_moton_selected()

    def on_moton_selected(self):
        selected_item = self.moton_list.currentItem()
        if not selected_item:
            self.chapters_list.clear()
            return
        matn_name = selected_item.text()
        chapters = self.data_loader.get_matn_chapters(matn_name)
        self.chapters_list.clear()
        if chapters:
            self.chapters_list.addItems(chapters)

    def on_chapter_activated(self, item):
        if not item:
            return
        matn_name = self.get_current_matn()
        if not matn_name:
            return
        from gui.motonViewer import MotonViewer
        chapter_title = item.text()
        is_full = (chapter_title == "عرض المتن كاملا")
        row = self.chapters_list.row(item)
        viewer = MotonViewer(self, matn_name=matn_name, chapter_index=row, chapter_title=chapter_title, is_full_matn=is_full)
        viewer.exec()

    def on_moton_context_menu(self, pos):
        item = self.moton_list.itemAt(pos) or self.moton_list.currentItem()
        if item and item.text():
            self.on_toggle_fav_callback(item.text())

    def get_current_matn(self):
        item = self.moton_list.currentItem()
        return item.text() if item else ""

    def get_current_chapter(self):
        item = self.chapters_list.currentItem()
        return item.text() if item else ""
