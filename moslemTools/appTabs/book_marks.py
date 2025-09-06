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
        self.setWindowTitle("العلامات المرجعية")
        self.setMinimumWidth(800)                
        self.tabWidget = qt.QTabWidget()
        self.tabWidget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background: #2b2b2b;
                color: white;
                padding: 10px 20px;
                border: 1px solid #444;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin: 2px;
                min-width: 100px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: white;
                border: 1px solid #0078d7;
            }
            QTabBar::tab:hover {
                background: #3a3a3a;
            }
        """)                
        self.tabs = []
        self.results_lists = []
        self.bookMarks1 = [[] for _ in range(4)]        
        categories = ["القرآن الكريم", "الأحاديث", "الكتب الإسلامية", "القصص الإسلامية"]
        for i, category in enumerate(categories):
            tab = qt.QWidget()
            tab_layout = qt.QVBoxLayout(tab)            
            search_label = qt.QLabel("بحث")
            search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar = qt.QLineEdit()
            search_bar.setPlaceholderText("بحث ...")
            search_bar.textChanged.connect(lambda text, idx=i: self.onsearch_tab(text, idx))
            search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)            
            results = qt.QListWidget()            
            results.itemActivated.connect(lambda item, idx=i: self.onItemClicked(item, idx))            
            tab_layout.addWidget(search_label)
            tab_layout.addWidget(search_bar)
            tab_layout.addWidget(results)            
            self.tabWidget.addTab(tab, category)
            self.tabs.append(tab)
            self.results_lists.append(results)        
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.tabWidget)        
        self.dl = guiTools.QPushButton("حذف العلامة المرجعية المحددة")
        self.dl.setAutoDefault(False)
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
        self.dl.setShortcut("Delete")
        self.dl.setAccessibleDescription("delete")                        
        self.dl_all_current = guiTools.QPushButton("حذف كل العلامات من الفئة الحالية")
        self.dl_all_current.setAutoDefault(False)
        self.dl_all_current.setStyleSheet("""
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
        self.dl_all_current.clicked.connect(self.onRemoveAllCurrentCategory)
        self.dl_all_current.setShortcut("Ctrl+Delete")
        self.dl_all_current.setAccessibleDescription("control plus delete")                        
        self.dl_all_all = guiTools.QPushButton("حذف كل العلامات من كل الفئات")
        self.dl_all_all.setAutoDefault(False)
        self.dl_all_all.setStyleSheet("""
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
        self.dl_all_all.clicked.connect(self.onRemoveAllCategories)
        self.dl_all_all.setShortcut("Ctrl+Shift+Delete")
        self.dl_all_all.setAccessibleDescription("control+shift plus delete")                
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.addWidget(self.dl)
        buttons_layout.addWidget(self.dl_all_current)
        buttons_layout.addWidget(self.dl_all_all)
        layout.addLayout(buttons_layout)                         
        self.tabWidget.currentChanged.connect(self.onCategoryChanged)                
        self.onCategoryChanged(0)            
    def onItemClicked(self, item, tab_index):
        try:
            results = self.results_lists[tab_index]
            if item: 
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
                            guiTools.qMessageBox.MessageBox.warning(self, "خطأ", f"لم يتم العثور على جزء '{partName}' في الكتاب '{bookName}'.")
                    else:
                        guiTools.qMessageBox.MessageBox.warning(self, "خطأ", f"لم يتم العثور على الكتاب '{bookName}' في المسار المحدد.")
                elif tab_index == 3:
                    functions.bookMarksManager.getStoryBookmark(self, item.text())
                self.close()
            else:
                guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "الرجاء تحديد علامة مرجعية لفتحها.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح العلامة المرجعية: {e}")    
    def onRemove(self):
        try:
            tab_index = self.tabWidget.currentIndex()
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
                    guiTools.speak("تم حذف العلامة المرجعية")
                    self.onCategoryChanged(tab_index)
            else:
                guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "الرجاء تحديد علامة مرجعية للحذف.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف العلامة المرجعية: {e}")    
    def onRemoveAllCurrentCategory(self):
        try:
            tab_index = self.tabWidget.currentIndex()
            category_name = self.tabWidget.tabText(tab_index)
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", f"هل أنت متأكد أنك تريد حذف جميع العلامات المرجعية من فئة '{category_name}'؟ هذا الإجراء لا يمكن التراجع عنه.", "نعم", "لا")
            if confirm == 0: 
                if tab_index == 0:
                    functions.bookMarksManager.removeAllQuranBookMarks()
                elif tab_index == 1:
                    functions.bookMarksManager.removeAllAhadeethBookMarks()
                elif tab_index == 2:
                    functions.bookMarksManager.removeAllIslamicBookBookMarks()
                elif tab_index == 3:
                    functions.bookMarksManager.removeAllStoriesBookMarks()
                guiTools.speak(f"تم حذف جميع العلامات المرجعية من فئة {category_name}")
                self.onCategoryChanged(tab_index)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع العلامات المرجعية من الفئة الحالية: {e}")    
    def onRemoveAllCategories(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل أنت متأكد أنك تريد حذف جميع العلامات المرجعية من كل الفئات؟ هذا الإجراء لا يمكن التراجع عنه.", "نعم", "لا")
            if confirm == 0: 
                functions.bookMarksManager.removeAllBookMarks()
                guiTools.speak("تم حذف جميع العلامات المرجعية من كل الفئات")
                for i in range(4):
                    self.onCategoryChanged(i)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع العلامات المرجعية من كل الفئات: {e}")    
    def onCategoryChanged(self, index):
        results = self.results_lists[index]
        results.clear()
        self.bookMarks1[index] = []
        try:            
            bookMarksData = functions.bookMarksManager.openBookMarksFile()
            type_key = "" 
            if index == 0:
                type_key = "quran"
            elif index == 1:
                type_key = "ahadeeth"
            elif index == 2:
                type_key = "islamicBooks"
            elif index == 3:
                type_key = "stories"                     
            if type_key in bookMarksData:
                for item in bookMarksData[type_key]:
                    self.bookMarks1[index].append(item["name"])
        except json.JSONDecodeError:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "خطأ في قراءة ملف العلامات المرجعية (تنسيق JSON غير صالح).")
            self.bookMarks1[index] = []
        except Exception as e: 
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء تحميل العلامات المرجعية: {e}")
            self.bookMarks1[index] = []        
        results.addItems(self.bookMarks1[index])    
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern.lower() in tashkeel_pattern.sub('', text).lower() 
        ]
        return matches        
    def onsearch_tab(self, text, tab_index):
        results = self.results_lists[tab_index]
        results.clear()
        if text:
            result = self.search(text, self.bookMarks1[tab_index])
            results.addItems(result)
        else:
            results.addItems(self.bookMarks1[tab_index])