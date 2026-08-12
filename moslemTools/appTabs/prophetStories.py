import gui, guiTools, re
import ujson as json
from settings import settings_handler, app
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class ProphetStories(qt.QWidget):
    def __init__(self):
        super().__init__()
        font=qt1.QFont()
        font.setBold(True)
        self.setFont(font)

        top_controls_layout = qt.QHBoxLayout()

        cat_v_layout = qt.QVBoxLayout()
        selectCategoryLabel = qt.QLabel("اختر قسم")
        selectCategoryLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        selectCategoryLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.selectCategory = qt.QComboBox()
        self.selectCategory.setAccessibleName("اختر قسم")
        self.selectCategory.addItems(["قصص الأنبياء", "قصص القرآن الكريم"])
        self.selectCategory.setStyleSheet("font-size: 14px; font-weight: bold;")
        cat_v_layout.addWidget(selectCategoryLabel, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        cat_v_layout.addWidget(self.selectCategory, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        view_mode_v_layout = qt.QVBoxLayout()
        self.view_mode_label = qt.QLabel("طريقة عرض العناصر")
        self.view_mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.view_mode_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.view_mode_combo = qt.QComboBox()
        self.view_mode_combo.setAccessibleName("طريقة عرض العناصر")
        self.view_mode_combo.addItems(["عمودي", "شبكي"])
        self.view_mode_combo.setStyleSheet("font-size: 14px; font-weight: bold;")
        grid_enabled = settings_handler.get("prophet_stories", "grid_view") == "True"
        self.view_mode_combo.setCurrentIndex(1 if grid_enabled else 0)
        view_mode_v_layout.addWidget(self.view_mode_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        view_mode_v_layout.addWidget(self.view_mode_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        top_controls_layout.addStretch(1)
        top_controls_layout.addLayout(cat_v_layout)
        top_controls_layout.addSpacing(20)
        top_controls_layout.addLayout(view_mode_v_layout)
        top_controls_layout.addStretch(1)

        self.stories = {}
        self.list_of_aProphetStories = guiTools.QListWidget()
        self.list_of_aProphetStories.setSpacing(3)
        self.list_of_aProphetStories.setFont(font)
        self.list_of_aProphetStories.itemClicked.connect(self.open)
        layout = qt.QVBoxLayout(self)
        layout.addLayout(top_controls_layout)
        serch = qt.QLabel("البحث عن قصة")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن قصة")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.selectCategory.currentIndexChanged.connect(self.onCategoryChanged)
        self.selectCategory.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.selectCategory))
        self.view_mode_combo.currentIndexChanged.connect(self.on_view_mode_changed)
        self.view_mode_combo.currentIndexChanged.connect(lambda: self.adjust_combo_width(self.view_mode_combo))
        self.onCategoryChanged(self.selectCategory.currentIndex())
        self.on_view_mode_changed(self.view_mode_combo.currentIndex())
        layout.addWidget(self.list_of_aProphetStories)

    def adjust_combo_width(self, combo, extra_padding=50):
        if not combo or combo.count() == 0:
            return
        fm = qt1.QFontMetrics(combo.font())
        current_text = combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        combo.setFixedWidth(text_width + extra_padding)

    def adjust_all_combos_width(self):
        for combo in (self.selectCategory, self.view_mode_combo):
            if combo and combo.count() > 0:
                self.adjust_combo_width(combo)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_all_combos_width()

    def update_grid_size(self):
        if self.view_mode_combo.currentIndex() != 1:
            return
        fm = self.list_of_aProphetStories.fontMetrics()
        max_w = 0
        for i in range(self.list_of_aProphetStories.count()):
            txt = self.list_of_aProphetStories.item(i).text()
            w = fm.horizontalAdvance(txt) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(txt).width()
            if w > max_w:
                max_w = w
        cell_w = max(200, max_w + 60)
        cell_h = max(60, fm.height() * 2 + 20)
        self.list_of_aProphetStories.setGridSize(qt2.QSize(cell_w, cell_h))

    def on_view_mode_changed(self, index):
        is_grid = (index == 1)
        settings_handler.set("prophet_stories", "grid_view", "True" if is_grid else "False")
        if is_grid:
            self.list_of_aProphetStories.setStyleSheet("""
                QListWidget::item {
                    padding: 10px 18px;
                    margin: 4px;
                    border-radius: 6px;
                }
                QListWidget::item:selected {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
                QListWidget::item:focus {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
            """)
            self.list_of_aProphetStories.setViewMode(qt.QListView.ViewMode.IconMode)
            self.list_of_aProphetStories.setResizeMode(qt.QListView.ResizeMode.Adjust)
            self.update_grid_size()
            self.list_of_aProphetStories.setSpacing(6)
        else:
            self.list_of_aProphetStories.setStyleSheet("")
            self.list_of_aProphetStories.setViewMode(qt.QListView.ViewMode.ListMode)
            self.list_of_aProphetStories.setResizeMode(qt.QListView.ResizeMode.Fixed)
            self.list_of_aProphetStories.setGridSize(qt2.QSize())
            self.list_of_aProphetStories.setSpacing(3)

    def open(self):
        gui.StoryViewer(self,
                        self.stories[self.list_of_aProphetStories.currentItem().text()],
                        self.selectCategory.currentIndex(),
                        self.list_of_aProphetStories.currentItem().text(),self.stories).exec()

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches

    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.list_of_aProphetStories.clear()
        result = self.search(search_text, list(self.stories.keys()))
        self.list_of_aProphetStories.addItems(result)
        self.update_grid_size()

    def onCategoryChanged(self, index):
        if index == 0:
            with open("data/json/prophetStories.json", "r", encoding="utf-8-sig") as file:
                self.stories = json.load(file)
        elif index == 1:
            with open("data/json/quranStories.json", "r", encoding="utf-8-sig") as file:
                self.stories = json.load(file)
        self.list_of_aProphetStories.clear()
        self.list_of_aProphetStories.addItems(list(self.stories.keys()))
        self.update_grid_size()
