import gui,guiTools,functions,os,re
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class hadeeth(qt.QWidget):
    def __init__(self):
        super().__init__()                
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        qt1.QShortcut("f5",self).activated.connect(self.refresh)
        self.list_of_ahadeeth=guiTools.QListWidget()
        self.list_of_ahadeeth.setFont(font)
        self.list_of_ahadeeth.addItems(functions.ahadeeth.ahadeeths.keys())
        self.list_of_ahadeeth.itemClicked.connect(self.open)
        layout=qt.QVBoxLayout(self)
        serch=qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_of_ahadeeth)
        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText("في حالة تحميل كتاب جديد, يرجى إعادة تحميل قائمة الكتب بالضغت على زر F5")
        layout.addWidget(self.info)
        self.info1=qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("لحذف أي كتاب تم تحميله, نستخدم زر الحذف أو زر التطبيقات")
        layout.addWidget(self.info1)
        self.list_of_ahadeeth.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_ahadeeth.customContextMenuRequested.connect(self.onDelete)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)
    def onDelete(self):
        selectedItem=self.list_of_ahadeeth.currentItem()
        if selectedItem:
            itemText=selectedItem.text()
            if itemText=="الأربعون نووية" or itemText=="الأربعون قُدسية":
                guiTools.MessageBox.error(self,"تنبيه","لا يمكنك حذف هذا الكتاب ")
            else:
                question=guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد حذف هذا الكتاب","نعم","لا")
                if question==0:
                    name=functions.ahadeeth.ahadeeths[itemText]
                    os.remove(os.path.join(os.getenv('appdata'),app.appName,"ahadeeth",name))
                    functions.ahadeeth.setahadeeth()
                    self.list_of_ahadeeth.clear()
                    self.list_of_ahadeeth.addItems(functions.ahadeeth.ahadeeths.keys())
                    guiTools.speak("تم الحذف")
    def open(self):
        gui.hadeeth_viewer(self,functions.ahadeeth.ahadeeths[self.list_of_ahadeeth.currentItem().text()]).exec()
    def refresh(self):
        functions.ahadeeth.setahadeeth()
        self.list_of_ahadeeth.clear()
        self.list_of_ahadeeth.addItems(functions.ahadeeth.ahadeeths.keys())
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
        self.list_of_ahadeeth.clear()
        result=self.search(search_text,list(functions.ahadeeth.ahadeeths.keys()))
        self.list_of_ahadeeth.addItems(result)