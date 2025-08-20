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
        self.Category_label = qt.QLabel("اختيار الفئة")
        self.Category_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.Category = qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)
        self.Category.addItem("القرآن الكريم")
        self.Category.addItem("الأحاديث")
        self.Category.addItem("الكتب الإسلامية")
        self.Category.addItem("القصص الإسلامية")
        self.Category.setAccessibleName("اختيار الفئة")
        self.Category.setFont(font)        
        self.results = qt.QListWidget()
        self.results.itemActivated.connect(self.onItemClicked)                
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
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.dl)
        layout1.addWidget(self.dl_all_current)
        layout1.addWidget(self.dl_all_all)
        layout.addLayout(layout1)         
        self.Category.currentIndexChanged.connect(self.onCategoryChanged)
        self.onCategoryChanged(0)
        self.bookMarks1 = []        
    def onItemClicked(self):
        try:
            if self.results.currentItem(): 
                if self.Category.currentIndex() == 0:
                    functions.bookMarksManager.openQuranByBookMarkName(self, self.results.currentItem().text())
                elif self.Category.currentIndex() == 1:
                    bookName, hadeethNumber = functions.bookMarksManager.GetHadeethBookByName(self.results.currentItem().text())
                    gui.hadeeth_viewer(self, bookName, index=hadeethNumber).exec()
                elif self.Category.currentIndex() == 2:
                    bookName, pageNumber, partName = functions.bookMarksManager.GetislamicBookBookByName(self.results.currentItem().text())
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
                elif self.Category.currentIndex() == 3:
                    functions.bookMarksManager.getStoryBookmark(self, self.results.currentItem().text())
                self.close()
            else:
                guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "الرجاء تحديد علامة مرجعية لفتحها.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح العلامة المرجعية: {e}")
    def onRemove(self):
        try:
            if self.results.currentItem(): 
                confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف هذه العلامة المرجعية؟", "نعم", "لا")
                if confirm == 0: 
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
            else:
                guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "الرجاء تحديد علامة مرجعية للحذف.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف العلامة المرجعية: {e}")
    def onRemoveAllCurrentCategory(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل أنت متأكد أنك تريد حذف جميع العلامات المرجعية من الفئة الحالية؟ هذا الإجراء لا يمكن التراجع عنه.", "نعم", "لا")
            if confirm == 0: 
                current_category_index = self.Category.currentIndex()
                category_name = self.Category.currentText()             
                if current_category_index == 0:
                    functions.bookMarksManager.removeAllQuranBookMarks()
                elif current_category_index == 1:
                    functions.bookMarksManager.removeAllAhadeethBookMarks()
                elif current_category_index == 2:
                    functions.bookMarksManager.removeAllIslamicBookBookMarks()
                elif current_category_index == 3:
                    functions.bookMarksManager.removeAllStoriesBookMarks()
                guiTools.speak(f"تم حذف جميع العلامات المرجعية من فئة {category_name}")
                self.onCategoryChanged(current_category_index)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع العلامات المرجعية من الفئة الحالية: {e}")
    def onRemoveAllCategories(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل أنت متأكد أنك تريد حذف جميع العلامات المرجعية من كل الفئات؟ هذا الإجراء لا يمكن التراجع عنه.", "نعم", "لا")
            if confirm == 0: 
                functions.bookMarksManager.removeAllBookMarks()
                guiTools.speak("تم حذف جميع العلامات المرجعية من كل الفئات")
                self.onCategoryChanged(self.Category.currentIndex()) 
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع العلامات المرجعية من كل الفئات: {e}")
    def onCategoryChanged(self, index):
        self.results.clear()
        self.bookMarks1 = []
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
                    self.bookMarks1.append(item["name"])
        except json.JSONDecodeError:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "خطأ في قراءة ملف العلامات المرجعية (تنسيق JSON غير صالح).")
            self.bookMarks1 = []
        except Exception as e: 
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء تحميل العلامات المرجعية: {e}")
            self.bookMarks1 = []        
        self.results.addItems(self.bookMarks1)
        self.search_bar.clear()        
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern.lower() in tashkeel_pattern.sub('', text).lower() 
        ]
        return matches    
    def onsearch(self):
        search_text = self.search_bar.text() 
        self.results.clear()
        if search_text:
            result = self.search(search_text, self.bookMarks1)
            self.results.addItems(result)
        else:
            self.results.addItems(self.bookMarks1)