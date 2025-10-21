import gui,guiTools,os,json,re,shutil
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class Athker(qt.QWidget):
    def __init__(self):        
        super().__init__()                
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)    
        with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
            self.data = json.load(data)        
        self.all_athkars_data = self.data
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
        self.athkars1 = []
        for athker in self.data:
            self.athkerList.setSpacing(3)
            self.athkars1.append(athker["name"])
        self.athkerList.clicked.connect(lambda:gui.AthkerDialog(self,self.athkerList.currentItem().text(),self.data[self.athkerList.currentRow()]["content"]).exec())        
        self.athkerList.addItems(self.athkars1)
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
        with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
            self.data = json.load(data)
        self.all_athkars_data = self.data
        self.athkerList.clear()
        self.athkars1 = []
        for athker in self.data:
            self.athkars1.append(athker["name"])
        self.athkerList.addItems(self.athkars1)