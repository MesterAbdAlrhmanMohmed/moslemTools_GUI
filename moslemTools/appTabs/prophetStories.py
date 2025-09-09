import gui, guiTools, re, json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class ProphetStories(qt.QWidget):
    def __init__(self):
        super().__init__()        
        category_layout = qt.QHBoxLayout()
        category_layout.addStretch(1)
        selectCategoryLabel = qt.QLabel("اختر قسم")
        selectCategoryLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        selectCategoryLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.selectCategory = qt.QComboBox()
        self.selectCategory.setAccessibleName("اختر قسم")
        self.selectCategory.addItems(["قصص الأنبياء", "قصص القرآن الكريم"])
        self.selectCategory.setStyleSheet("font-size: 14px; font-weight: bold;")
        category_layout.addWidget(self.selectCategory, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        category_layout.addWidget(selectCategoryLabel, alignment=qt2.Qt.AlignmentFlag.AlignCenter)        
        category_layout.addStretch(1)
        self.stories = {}
        font=qt1.QFont()
        font.setBold(True)        
        self.list_of_aProphetStories = guiTools.QListWidget()
        self.list_of_aProphetStories.setFont(font)
        self.list_of_aProphetStories.itemClicked.connect(self.open)        
        layout = qt.QVBoxLayout(self)
        layout.addLayout(category_layout)        
        serch = qt.QLabel("البحث عن قصة")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)        
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن قصة")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)        
        self.selectCategory.currentIndexChanged.connect(self.onCategoryChanged)
        self.onCategoryChanged(self.selectCategory.currentIndex())
        layout.addWidget(self.list_of_aProphetStories)        
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
    def onCategoryChanged(self, index):
        if index == 0:
            with open("data/json/prophetStories.json", "r", encoding="utf-8-sig") as file:
                self.stories = json.load(file)
        elif index == 1:
            with open("data/json/quranStories.json", "r", encoding="utf-8-sig") as file:
                self.stories = json.load(file)
        self.list_of_aProphetStories.clear()
        self.list_of_aProphetStories.addItems(list(self.stories.keys()))