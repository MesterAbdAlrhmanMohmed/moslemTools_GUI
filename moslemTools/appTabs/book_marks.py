import gui, guiTools, functions, os, re
import ujson as json
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
        self.setWindowTitle("العلامات المرجعية")
        self.setMinimumSize(1080, 420)
        self.resize(1120, 450)
        layout = qt.QVBoxLayout(self)
        h_layout = qt.QHBoxLayout()
        self.sectian = guiTools.listBook()
        self.sectian.setSpacing(3)
        self.sectian.setFocus()
        self.sectian.setStyleSheet("color: #e0e0e0;")
        self.sectian.setAccessibleName("اختر فئة")
        self.sectian.setFont(font)
        self.sectian.setMinimumWidth(285)
        self.sectian.setMaximumWidth(310)
        h_layout.addWidget(self.sectian, 0)
        scroll_area = qt.QScrollArea()
        scroll_area.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(qt.QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.sectian.w)
        h_layout.addWidget(scroll_area, 1)
        layout.addLayout(h_layout)
        self.tabs = []
        self.results_lists = []
        self.bookMarks1 = [[] for _ in range(5)]
        categories = ["القرآن الكريم", "الأحاديث", "الكتب الإسلامية", "القصص الإسلامية", "المواضيع الإسلامية المختلفة"]
        for i, category in enumerate(categories):
            tab = qt.QWidget()
            tab_layout = qt.QVBoxLayout(tab)
            search_label = qt.QLabel(f"البحث عن علامة مرجعية في فئة {category}")
            search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar = qt.QLineEdit()
            search_bar.setAccessibleName(f"البحث عن علامة مرجعية في فئة {category}")
            search_bar.textChanged.connect(lambda text, idx=i: self.onsearch_tab(text, idx))
            search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            results = qt.QListWidget()
            results.setSpacing(3)
            results.itemActivated.connect(lambda item, idx=i: self.onItemClicked(item, idx))
            tab_layout.addWidget(search_label)
            tab_layout.addWidget(search_bar)
            tab_layout.addWidget(results)
            self.sectian.add(category, tab)
            self.tabs.append(tab)
            self.results_lists.append(results)
        self.dl = guiTools.QPushButton("حذف العلامة المرجعية المحددة")
        self.dl.setAutoDefault(False)
        self.dl.clicked.connect(self.onRemove)
        self.dl.setShortcut("Delete")
        self.dl.setAccessibleDescription("delete")
        self.dl_all_current = guiTools.QPushButton("حذف كل العلامات من الفئة الحالية")
        self.dl_all_current.setAutoDefault(False)
        self.dl_all_current.clicked.connect(self.onRemoveAllCurrentCategory)
        self.dl_all_current.setShortcut("Ctrl+Delete")
        self.dl_all_all = guiTools.QPushButton("حذف كل العلامات من كل الفئات")
        self.dl_all_all.setAutoDefault(False)
        self.dl_all_all.clicked.connect(self.onRemoveAllCategories)
        self.dl_all_all.setShortcut("Ctrl+Shift+Delete")
        self.dl_all_all.setAccessibleDescription("control plus shift plus delete")
        self.dl_all_current.setAccessibleDescription("control plus delete")
        for btn in [self.dl, self.dl_all_current, self.dl_all_all]:
            btn.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Minimum)
            btn.setMinimumHeight(40)
            btn.setStyleSheet("background-color: #5C0000; color: white; padding: 6px 8px; font-weight: bold;")
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(6)
        buttons_layout.addWidget(self.dl)
        buttons_layout.addWidget(self.dl_all_current)
        buttons_layout.addWidget(self.dl_all_all)
        layout.addLayout(buttons_layout)
        self.sectian.currentRowChanged.connect(self.onCategoryChanged)
        self.sectian.setCurrentRow(0)

    def onItemClicked(self, item, tab_index):
        try:
            if not item:
                guiTools.qMessageBox.MessageBox.error(self, "تحذير", "الرجاء تحديد علامة مرجعية لفتحها.")
                return
            if tab_index == 0:
                functions.bookMarksManager.openQuranByBookMarkName(self, item.text())
            elif tab_index == 1:
                bookName, hadeethNumber = functions.bookMarksManager.GetHadeethBookByName(item.text())
                gui.hadeeth_viewer(self, bookName, index=hadeethNumber).exec()
            elif tab_index == 2:
                bookName, pageNumber, partName = functions.bookMarksManager.GetislamicBookBookByName(item.text())
                book_path = os.path.join(os.getenv('appdata'), app.appName, "islamicBooks", bookName)
                if os.path.exists(book_path):
                    with open(book_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if partName in data:
                        partContent = data[partName]
                        gui.islamicBooks.book_viewer(self, bookName, partName, partContent, index=pageNumber).exec()
                    else:
                        guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على جزء '{partName}' في الكتاب '{bookName}'.")
                else:
                    guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على الكتاب '{bookName}' في المسار المحدد.")
            elif tab_index == 3:
                functions.bookMarksManager.getStoryBookmark(self, item.text())
            elif tab_index == 4:
                functions.bookMarksManager.openIslamicTopicByBookmarkName(self, item.text())
            self.close()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح العلامة المرجعية: {e}")

    def onRemove(self):
        try:
            tab_index = self.sectian.currentRow()
            results = self.results_lists[tab_index]
            item = results.currentItem()
            if item:
                confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف هذه العلامة المرجعية؟", "نعم", "لا")
                if confirm == 0:
                    if tab_index == 0:
                        functions.bookMarksManager.removeQuranBookMark(item.text())
                    elif tab_index == 1:
                        functions.bookMarksManager.removeAhadeethBookMark(item.text())
                    elif tab_index == 2:
                        functions.bookMarksManager.removeislamicBookBookMark(item.text())
                    elif tab_index == 3:
                        functions.bookMarksManager.removeStoriesBookMark(item.text())
                    elif tab_index == 4:
                        functions.bookMarksManager.removeIslamicTopicBookMark(item.text())
                    guiTools.speak("تم حذف العلامة المرجعية")
                    self.onCategoryChanged(tab_index)
            else:
                pass
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف العلامة المرجعية: {e}")

    def onRemoveAllCurrentCategory(self):
        try:
            tab_index = self.sectian.currentRow()
            category_name = self.sectian.item(tab_index).text()
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", f"هل تريد حذف كل علامات '{category_name}'؟", "نعم", "لا")
            if confirm == 0:
                if tab_index == 0:
                    functions.bookMarksManager.removeAllQuranBookMarks()
                elif tab_index == 1:
                    functions.bookMarksManager.removeAllAhadeethBookMarks()
                elif tab_index == 2:
                    functions.bookMarksManager.removeAllIslamicBookBookMarks()
                elif tab_index == 3:
                    functions.bookMarksManager.removeAllStoriesBookMarks()
                elif tab_index == 4:
                    functions.bookMarksManager.removeAllIslamicTopicsBookMarks()
                guiTools.speak(f"تم حذف جميع العلامات المرجعية من فئة {category_name}")
                self.onCategoryChanged(tab_index)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ: {e}")

    def onRemoveAllCategories(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل تريد حذف كل العلامات؟", "نعم", "لا")
            if confirm == 0:
                functions.bookMarksManager.removeAllBookMarks()
                guiTools.speak("تم حذف جميع العلامات المرجعية")
                for i in range(5):
                    self.onCategoryChanged(i)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ: {e}")

    def onCategoryChanged(self, index):
        results = self.results_lists[index]
        results.clear()
        self.bookMarks1[index] = []
        try:
            bookMarksData = functions.bookMarksManager.openBookMarksFile()
            type_key = ""
            if index == 0: type_key = "quran"
            elif index == 1: type_key = "ahadeeth"
            elif index == 2: type_key = "islamicBooks"
            elif index == 3: type_key = "stories"
            elif index == 4: type_key = "islamicTopics"
            if type_key and type_key in bookMarksData:
                for item in bookMarksData[type_key]:
                    self.bookMarks1[index].append(item["name"])
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء تحميل العلامات: {e}")
            self.bookMarks1[index] = []
        results.addItems(self.bookMarks1[index])

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern).lower()
        return [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text).lower()]

    def onsearch_tab(self, text, tab_index):
        results = self.results_lists[tab_index]
        results.clear()
        if text:
            result = self.search(text, self.bookMarks1[tab_index])
            results.addItems(result)
        else:
            results.addItems(self.bookMarks1[tab_index])
