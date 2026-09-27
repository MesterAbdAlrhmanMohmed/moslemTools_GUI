import re
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import guiTools


class MotonFavoritesWidget(qt.QWidget):
    def __init__(self, data_loader, favorites_manager, on_toggle_fav_callback):
        super().__init__()
        self.data_loader = data_loader
        self.favorites_manager = favorites_manager
        self.on_toggle_fav_callback = on_toggle_fav_callback
        self.all_moton = []
        self.all_chapters = []
        self.init_ui()

    def init_ui(self):
        layout = qt.QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        moton_layout = qt.QVBoxLayout()
        moton_layout.setSpacing(10)
        self.moton_label = qt.QLabel("المتون المفضلة")
        self.moton_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        self.moton_label.setFont(font)

        self.moton_search = qt.QLineEdit()
        self.moton_search.setPlaceholderText("البحث عن متن")
        self.moton_search.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.moton_search.textChanged.connect(self.filter_moton)

        self.moton_list = guiTools.QListWidget()
        self.moton_list.setSpacing(5)
        self.moton_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.moton_list.itemSelectionChanged.connect(self.on_moton_selected)
        self.moton_list.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.moton_list.customContextMenuRequested.connect(self.on_moton_context_menu)

        moton_layout.addWidget(self.moton_label)
        moton_layout.addWidget(self.moton_search)
        moton_layout.addWidget(self.moton_list)

        self.chapters_container = qt.QWidget()
        chapters_layout = qt.QVBoxLayout(self.chapters_container)
        chapters_layout.setContentsMargins(0, 0, 0, 0)
        chapters_layout.setSpacing(10)
        self.chapters_label = qt.QLabel("اختيار باب")
        self.chapters_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.chapters_label.setFont(font)

        self.chapters_search = qt.QLineEdit()
        self.chapters_search.setPlaceholderText("البحث عن باب")
        self.chapters_search.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.chapters_search.textChanged.connect(self.filter_chapters)

        self.chapters_list = guiTools.QListWidget()
        self.chapters_list.setSpacing(5)
        self.chapters_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.chapters_list.itemActivated.connect(self.on_chapter_activated)

        chapters_layout.addWidget(self.chapters_label)
        chapters_layout.addWidget(self.chapters_search)
        chapters_layout.addWidget(self.chapters_list)

        layout.addLayout(moton_layout, 1)
        layout.addWidget(self.chapters_container, 1)

        self.refresh_favorites()

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[ؗ-ًؚ-ْٰ]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches

    def refresh_favorites(self):
        favs = self.favorites_manager.favorites
        self.all_moton = list(favs) if favs else []
        self.filter_moton()

    def filter_moton(self):
        query = self.moton_search.text().lower().strip()
        current_selected = self.get_current_matn()
        if not self.all_moton:
            self.chapters_container.hide()
            self.moton_list.blockSignals(True)
            self.moton_list.clear()
            self.moton_list.addItem("لا توجد متون في قائمة المفضلة")
            self.moton_list.setCurrentRow(0)
            self.moton_list.blockSignals(False)
            self.on_moton_selected()
            return

        if query:
            filtered = self.search(query, self.all_moton)
        else:
            filtered = list(self.all_moton)

        self.moton_list.blockSignals(True)
        self.moton_list.clear()
        if filtered:
            self.chapters_container.show()
            self.moton_list.addItems(filtered)
            if current_selected and current_selected in filtered:
                self.moton_list.setCurrentRow(filtered.index(current_selected))
            else:
                self.moton_list.setCurrentRow(0)
        else:
            self.chapters_container.hide()
            self.moton_list.addItem("لا توجد متون مطابقة للبحث")
            self.moton_list.setCurrentRow(0)
        self.moton_list.blockSignals(False)
        self.on_moton_selected()

    def on_moton_selected(self):
        selected_item = self.moton_list.currentItem()
        if not selected_item or selected_item.text() in ["لا توجد متون في قائمة المفضلة", "لا توجد متون مطابقة للبحث", "لا يوجد متون في قائمة المفضلة"]:
            self.all_chapters = []
            self.chapters_list.clear()
            self.chapters_container.hide()
            return
        self.chapters_container.show()
        matn_name = selected_item.text()
        chapters = self.data_loader.get_matn_chapters(matn_name)
        self.all_chapters = list(chapters) if chapters else []
        self.filter_chapters()

    def filter_chapters(self):
        query = self.chapters_search.text().lower().strip()
        current_selected = self.get_current_chapter()
        if query:
            filtered = self.search(query, self.all_chapters)
        else:
            filtered = list(self.all_chapters)

        self.chapters_list.blockSignals(True)
        self.chapters_list.clear()
        if filtered:
            self.chapters_list.addItems(filtered)
            if current_selected and current_selected in filtered:
                self.chapters_list.setCurrentRow(filtered.index(current_selected))
            else:
                self.chapters_list.setCurrentRow(0)
        self.chapters_list.blockSignals(False)

    def on_chapter_activated(self, item):
        if not item:
            return
        matn_name = self.get_current_matn()
        if not matn_name or matn_name in ["لا يوجد متون في قائمة المفضلة", "لا توجد متون في قائمة المفضلة", "لا توجد متون مطابقة للبحث"]:
            return
        if item.text() in ["لا يوجد متون في قائمة المفضلة", "لا توجد متون في قائمة المفضلة", "لا توجد أبواب لعرضها"]:
            return
        from gui.motonViewer import MotonViewer
        chapter_title = item.text()
        is_full = (chapter_title == "عرض المتن كاملا") or chapter_title.startswith("المتن كاملا")
        row = self.all_chapters.index(chapter_title) if chapter_title in self.all_chapters else self.chapters_list.row(item)
        viewer = MotonViewer(self, matn_name=matn_name, chapter_index=row, chapter_title=chapter_title, is_full_matn=is_full)
        viewer.exec()

    def on_moton_context_menu(self, pos):
        item = (self.moton_list.itemAt(pos) if pos is not None else None) or self.moton_list.currentItem()
        if item and item.text() and item.text() not in ["لا يوجد متون في قائمة المفضلة", "لا توجد متون في قائمة المفضلة", "لا توجد متون مطابقة للبحث"]:
            self.on_toggle_fav_callback(item.text())

    def get_current_matn(self):
        item = self.moton_list.currentItem()
        if item and item.text() not in ["لا يوجد متون في قائمة المفضلة", "لا توجد متون في قائمة المفضلة", "لا توجد متون مطابقة للبحث"]:
            return item.text()
        return ""

    def get_current_chapter(self):
        item = self.chapters_list.currentItem()
        if item and item.text() not in ["لا يوجد متون في قائمة المفضلة", "لا توجد متون في قائمة المفضلة", "لا توجد أبواب لعرضها"]:
            return item.text()
        return ""
