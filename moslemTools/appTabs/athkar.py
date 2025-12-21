import gui,guiTools,os,json,re,shutil,threading
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class AthkarLoader(qt2.QThread):
    data_loaded = qt2.pyqtSignal(list)
    def __init__(self):
        super().__init__()
    def run(self):
        try:
            with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
                athkar_data = json.load(data)
            self.data_loaded.emit(athkar_data)
        except Exception as e:
            print(f"Error loading athkar: {e}")
            self.data_loaded.emit([])
class Athker(qt.QWidget):
    def __init__(self):        
        super().__init__()                
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)    
        self.data = None
        self.all_athkars_data = []
        self.is_loaded = False
        self.loader_thread = None
        layout = qt.QVBoxLayout(self)                
        self.SL=qt.QLabel("البحث عن فئة أذكار")
        self.SL.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar = qt.QLineEdit()        
        self.search_bar.setPlaceholderText("البحث عن فئة أذكار")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.SL)
        layout.addWidget(self.search_bar)
        self.athkerList = guiTools.QListWidget()
        self.athkerList.setSpacing(3)
        self.athkerList.clicked.connect(lambda:gui.AthkerDialog(self,self.athkerList.currentItem().text(),self.data[self.athkerList.currentRow()]["content"]).exec())        
        self.athkerList.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkerList.customContextMenuRequested.connect(self.onDelete)                
        layout.addWidget(self.athkerList)        
        self.info1 = qt.QLabel()                    
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("لحذف أي نوع من الأذكار تم تحميله، نستخدم زر الحذف أو زر التطبيقات")
        layout.addWidget(self.info1)
        self.info2=qt.QLabel()
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info2.setText("يمكنكم تحميل الأذكار الصوتية لتشغيلها بدون انترنت من تحميل موارد إضافية من الإعدادات")    
        layout.addWidget(self.info2)
    def showEvent(self, event):
        super().showEvent(event)
        if not self.is_loaded:
            self.athkerList.clear()
            self.athkerList.addItem("جاري تحميل الأذكار...")
            if self.loader_thread is None:
                self.loader_thread = AthkarLoader()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()
    def on_data_loaded(self, data):
        self.data = data
        self.all_athkars_data = data
        self.athkerList.clear()
        self.athkars1 = []
        for athker in self.data:
            self.athkars1.append(athker["name"])
        self.athkerList.addItems(self.athkars1)
        self.is_loaded = True
    def onDelete(self):
        itemText = self.athkerList.currentItem()
        if itemText:
            athkar_name = itemText.text()
            path = os.path.join(os.getenv('appdata'), app.appName, "athkar", athkar_name)
            if os.path.exists(path):
                confirm = guiTools.QQuestionMessageBox.view(
                    self,
                    "تأكيد الحذف",
                    f"هل أنت متأكد أنك تريد حذف فئة الأذكار '{athkar_name}'؟",
                    "نعم",
                    "لا"
                )
                if confirm == 0:
                    try:
                        shutil.rmtree(path)
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف فئة الأذكار بنجاح.")
                        self.refresh_athkar_list()
                    except Exception as e:
                        guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف فئة الأذكار: {e}")
    def normalize_arabic_text(self, text):        
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        return tashkeel_pattern.sub('', text)
    def onsearch(self, text):
        if not self.data: return
        self.athkerList.clear()
        search_pattern = self.normalize_arabic_text(text).strip()        
        if not search_pattern:            
            self.athkerList.addItems([athker["name"] for athker in self.all_athkars_data])
            self.data = self.all_athkars_data
            return
        filtered_athkars = []
        filtered_data_for_display = []
        for athker in self.all_athkars_data:
            normalized_name = self.normalize_arabic_text(athker["name"])
            if search_pattern in normalized_name:
                filtered_athkars.append(athker["name"])
                filtered_data_for_display.append(athker)        
        self.athkerList.addItems(filtered_athkars)
        self.data = filtered_data_for_display
    def refresh_athkar_list(self):        
        self.is_loaded = False
        self.showEvent(None)