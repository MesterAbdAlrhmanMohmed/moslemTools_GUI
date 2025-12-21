import gui,guiTools,functions,os,json,re
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import threading
class Worker(qt2.QObject):
    finished = qt2.pyqtSignal()
    data_ready = qt2.pyqtSignal(list)
    def __init__(self):
        super().__init__()
    def refresh_books(self):
        try:
            functions.islamicBooks.reload_books()
            book_list = list(functions.islamicBooks.books.keys())
            self.data_ready.emit(book_list)
        except Exception as e:
            print(f"Error in refresh thread: {e}")
        finally:
            self.finished.emit()
class DeleteWorker(qt2.QObject):
    finished = qt2.pyqtSignal()
    deletion_complete = qt2.pyqtSignal(bool)
    def __init__(self, itemText):
        super().__init__()
        self.itemText = itemText
    def delete_book(self):
        try:
            name=functions.islamicBooks.books[self.itemText]
            os.remove(os.path.join(os.getenv('appdata'),app.appName,"islamicBooks",name))
            functions.islamicBooks.reload_books()
            self.deletion_complete.emit(True)
        except Exception as e:
            print(f"Error during deletion: {e}")
            self.deletion_complete.emit(False)
        finally:
            self.finished.emit()
class LoaderThread(qt2.QThread):
    data_loaded = qt2.pyqtSignal(list)
    def __init__(self):
        super().__init__()
    def run(self):
        try:
            book_list = list(functions.islamicBooks.books.keys())
            self.data_loaded.emit(book_list)
        except Exception as e:
            print(f"Error loading books: {e}")
            self.data_loaded.emit([])
class IslamicBooks(qt.QWidget):
    def __init__(self):
        super().__init__()                
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        layout=qt.QVBoxLayout(self)                
        self.worker = None        
        self.delete_worker = None
        self.loader_thread = None
        qt1.QShortcut("f5",self).activated.connect(self.start_threaded_refresh)        
        serch=qt.QLabel("البحث عن كتاب")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)        
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("البحث عن كتاب")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)        
        self.list_of_abook=guiTools.QListWidget()
        self.list_of_abook.setSpacing(3)
        self.list_of_abook.itemClicked.connect(self.open)
        layout.addWidget(self.list_of_abook)        
        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText("في حالة تحميل كتاب جديد, يرجى إعادة تحميل قائمة الكتب بالضغت على زر F5")
        layout.addWidget(self.info)        
        self.info1=qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("تنبيه هام , مطور البرنامج غير مسؤول عن محتوى هذه الكتب")                
        self.info2=qt.QLabel()
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info2.setText("لحذف أي كتاب تم تحميله, نستخدم زر الحذف أو زر التطبيقات أو click الأيمن")
        layout.addWidget(self.info2)
        layout.addWidget(self.info1)        
        self.info3=qt.QLabel()
        self.info3.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info3.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info3.setText("يمكنكم تحميل المزيد من تحميل موارد إضافية من الإعدادات")    
        layout.addWidget(self.info3)
        self.list_of_abook.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_abook.customContextMenuRequested.connect(self.onDelete)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)
        self.is_loaded = False
    def showEvent(self, event):
        super().showEvent(event)
        if not self.is_loaded:
            self.list_of_abook.clear()
            self.list_of_abook.addItem("جاري تحميل قائمة الكتب...")
            if self.loader_thread is None:
                self.loader_thread = LoaderThread()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()
    def on_data_loaded(self, book_list):
        self.list_of_abook.clear()
        self.list_of_abook.addItems(book_list)
        self.is_loaded = True
    def start_threaded_refresh(self):
        if self.worker is None:
            self.worker = Worker()
            self.worker.data_ready.connect(self.handle_data_ready)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(lambda: setattr(self, 'worker', None))            
            thread = threading.Thread(target=self.worker.refresh_books)
            thread.daemon = True
            thread.start()    
    def handle_data_ready(self, book_list):
        self.list_of_abook.clear()
        self.list_of_abook.addItems(book_list)
        self.list_of_abook.setFocus()    
    def start_threaded_delete(self, itemText):
        if self.delete_worker is None:
            self.delete_worker = DeleteWorker(itemText)
            self.delete_worker.deletion_complete.connect(self.handle_deletion_complete)
            self.delete_worker.finished.connect(self.delete_worker.deleteLater)
            self.delete_worker.finished.connect(lambda: setattr(self, 'delete_worker', None))
            thread = threading.Thread(target=self.delete_worker.delete_book)
            thread.daemon = True
            thread.start()
    def handle_deletion_complete(self, success):
        if success:
            self.list_of_abook.clear()
            self.list_of_abook.addItems(functions.islamicBooks.books.keys())
            guiTools.speak("تم الحذف")
        else:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف الملف ")
    def onDelete(self):
        selectedItem=self.list_of_abook.currentItem()
        if selectedItem:
            itemText=selectedItem.text()
            if itemText=="حياة الصحابة":
                guiTools.qMessageBox.MessageBox.error(self,"تنبيه","لا يمكنك حذف هذا الكتاب ")
            else:
                question=guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد حذف هذا الكتاب","نعم","لا")
                if question==0:
                    self.start_threaded_delete(itemText)
    def open(self):
        try:
            with open(os.path.join(os.getenv('appdata'),app.appName,"islamicBooks",functions.islamicBooks.books[self.list_of_abook.currentItem().text()]),"r",encoding="utf-8") as f:
                data=json.load(f)    
                bookName=functions.islamicBooks.books[self.list_of_abook.currentItem().text()]
                if len(list(data.keys()))==1:
                    partName=list(data.keys())[0]
                    gui.islamicBooks.book_viewer(self,bookName,partName,data[partName]).exec()
                else:
                    gui.islamicBooks.PartSelection(self,bookName,data).exec()
        except Exception as error:
            print(error)
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر فتح الملف ")    
    def refresh(self):
        self.start_threaded_refresh()    
    def search(self,pattern,text_list):    
        tashkeel_pattern=re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')        
        normalized_pattern=tashkeel_pattern.sub('', pattern)        
        matches=[
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]        
        return matches            
    def onsearch(self):
        search_text=self.search_bar.text().lower()
        self.list_of_abook.clear()
        result=self.search(search_text,list(functions.islamicBooks.books.keys()))
        self.list_of_abook.addItems(result)