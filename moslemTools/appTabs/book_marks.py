import gui, guiTools, functions, json, os, re
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class book_marcks(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.resize(300, 300)
        self.setWindowTitle("العلامات المرجعية")
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.Category_label = qt.QLabel("إختيار الفئة")
        self.Category_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.Category = qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)
        self.Category.addItem("القرآن الكريم")
        self.Category.addItem("الأحاديث")
        self.Category.addItem("الكتب الإسلامية")
        self.Category.addItem("القصص الإسلامية")
        self.Category.setAccessibleName("إختيار الفئة")
        self.Category.setFont(font)
        self.results = qt.QListWidget()
        self.results.itemActivated.connect(self.onItemClicked)
        self.dl = qt.QPushButton("حذف العلامة المرجعية")
        self.dl.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
        """)
        self.dl.clicked.connect(self.onRemove)
        layout = qt.QVBoxLayout(self)
        serch = qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.Category_label)
        layout.addWidget(self.Category)
        layout.addWidget(serch)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.results)
        layout.addWidget(self.dl)
        self.Category.currentIndexChanged.connect(self.onCategoryChanged)
        self.onCategoryChanged(0)
        qt1.QShortcut("delete", self).activated.connect(self.onRemove)
    def onItemClicked(self):
        if self.Category.currentIndex() == 0:
            functions.bookMarksManager.openQuranByBookMarkName(self, self.results.currentItem().text())
        elif self.Category.currentIndex() == 1:
            bookName, hadeethNumber = functions.bookMarksManager.GetHadeethBookByName(self.results.currentItem().text())
            gui.hadeeth_viewer(self, bookName, index=hadeethNumber).exec()
        elif self.Category.currentIndex() == 2:
            bookName, pageNumber, partName = functions.bookMarksManager.GetislamicBookBookByName(self.results.currentItem().text())
            with open(os.path.join(os.getenv('appdata'), app.appName, "islamicBooks", bookName), "r", encoding="utf-8") as f:
                data = json.load(f)
            partContent = data[partName]
            gui.islamicBooks.book_viewer(self, bookName, partName, partContent, index=pageNumber).exec()
        elif self.Category.currentIndex() == 3:
            functions.bookMarksManager.getStoryBookmark(self, self.results.currentItem().text())
        self.close()
    def onRemove(self):
        try:
            if self.Category.currentIndex() == 0:
                functions.bookMarksManager.removeQuranBookMark(self.results.currentItem().text())
            elif self.Category.currentIndex() == 1:
                functions.bookMarksManager.removeAhadeethBookMark(self.results.currentItem().text())
            elif self.Category.currentIndex() == 2:
                functions.bookMarksManager.removeislamicBookBookMark(self.results.currentItem().text())
            elif self.Category.currentIndex() == 3:
                functions.bookMarksManager.removeStoriesBookMark(self.results.currentItem().text())
            guiTools.speak("تم حذف العلامة المرجعية")
            self.onCategoryChanged(self.Category.currentIndex())
        except:
            guiTools.qMessageBox.MessageBox.error(self, "تحذير", "حدث خطأ أثناء حذف العلامة المرجعية")
    def onCategoryChanged(self, index):
        bookMarksData = functions.bookMarksManager.openBookMarksFile()
        if index == 0:
            type = "quran"
        elif index == 1:
            type = "ahadeeth"
        elif index == 2:
            type = "islamicBooks"
        elif index == 3:
            type = "stories"
        self.results.clear()
        self.bookMarks1 = []
        try:
            for item in bookMarksData[type]:
                self.bookMarks1.append(item["name"])
        except:
            pass
        self.results.addItems(self.bookMarks1)
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches
    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.results.clear()
        result = self.search(search_text, self.bookMarks1)
        self.results.addItems(result)