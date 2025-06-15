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
            self.data=json.load(data)
        layout=qt.QVBoxLayout(self)
        self.athkerList=guiTools.QListWidget()
        self.athkars1=[]
        for athker in self.data:
            self.athkars1.append(athker["name"])
        self.athkerList.clicked.connect(lambda:gui.AthkerDialog(self,self.athkerList.currentItem().text(),self.data[self.athkerList.currentRow()]["content"]).exec())        
        self.athkerList.addItems(self.athkars1)
        self.athkerList.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkerList.customContextMenuRequested.connect(self.onDelete)
        serch=qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.athkerList)
        self.info1=qt.QLabel()                    
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("لحذف أي نوع من الأذكار تم تحميله, نستخدم زر الحذف أو زر التطبيقات")
        layout.addWidget(self.info1)
    def onDelete(self):
        itemText=self.athkerList.currentItem()
        if itemText:
            reciterText=itemText.text()
            path=os.path.join(os.getenv('appdata'),app.appName,"athkar",reciterText)
            if os.path.exists(path):
                question=guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد حذف الأذكار الصوتية","نعم","لا")
                if question==0:
                    shutil.rmtree(path)
                    guiTools.speak("تم الحذف")
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
        self.athkerList.clear()
        result=self.search(search_text,self.athkars1)
        self.athkerList.addItems(result)