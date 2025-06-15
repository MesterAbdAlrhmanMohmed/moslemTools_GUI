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