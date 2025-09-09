import json,os,requests,re,guiTools,functions
import guiTools,gui,settings,settings,functions
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class SelectItem(qt.QDialog):
    def __init__(self,p,fileName:str,dirName):
        super().__init__(p)
        self.resize(900,500)
        self.data={}
        self.dirName=dirName
        layout=qt.QVBoxLayout(self)
        serch=qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.item=guiTools.QListWidget()        
        font=qt1.QFont()
        font.setBold(True)
        self.item.setFont(font)
        layout.addWidget(self.item)        
        self.item.clicked.connect(lambda:StartDownloading(self,self.data[self.item.currentItem().text()],self.dirName).exec())            
        self.fileName=fileName
        self.onLoad()
    def onLoad(self):
        try:
            url = "https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/refs/heads/main/moslemTools/data/json/files/" + self.fileName
            r=requests.get(url)
            if r.status_code==200:
                jsonContent=r.json()
                with open("data/json/files/" + self.fileName,"w",encoding="utf-8") as file:
                    json.dump(jsonContent,file,ensure_ascii=False,indent=4)
                downloadedData=[]
                if self.fileName=="all_tafaseers.json":
                    downloadedData=list(functions.tafseer.tafaseers.keys())
                elif self.fileName=="all_translater.json":
                    downloadedData=list(functions.translater.translations.keys())
                elif self.fileName=="all_ahadeeth.json":
                    downloadedData=list(functions.ahadeeth.ahadeeths.keys())
                elif self.fileName=="all_islamic_books.json":
                    downloadedData=list(functions.islamicBooks.books.keys())
                for data in downloadedData:
                    del jsonContent[data]
                self.data=jsonContent
                self.item.addItems(self.data)
            else:
                guiTools.qMessageBox.MessageBox.error(self,"تنبيه","حدث خطأ أثناء تحميل البيانات")
                self.close()
        except:
            guiTools.qMessageBox.MessageBox.error(self,"تنبيه","حدث خطأ أثناء تحميل البيانات")
            self.accept()
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
        self.item.clear()
        result=self.search(search_text,list(self.data.keys()))
        self.item.addItems(result)
class DownloadThread(qt2.QThread):
    progress=qt2.pyqtSignal(int)
    finished=qt2.pyqtSignal(bool)
    def __init__(self,fileName:str,DIRName:str):
        super().__init__()
        self.fileName=fileName
        self.DIRName=DIRName        
    def run (self):
        try:
            url = "https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/refs/heads/main/moslemTools/data/json/" + self.DIRName + "/" + self.fileName
            with requests.get(url,stream=True) as r:
                if r.status_code==200:
                    total_size=int(r.headers.get('content-length', 0))
                    downloaded_size=0                    
                    with open(os.path.join(os.getenv('appdata'),settings.app.appName,self.DIRName,self.fileName),"wb") as file:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                file.write(chunk)
                                downloaded_size+=len(chunk)
                                progress_percent=int((downloaded_size / total_size) * 100)
                                self.progress.emit(progress_percent)                                
                    functions.tafseer.setTafaseer()
                    functions.translater.settranslation()
                    functions.ahadeeth.setahadeeth()
                    self.finished.emit(True)                
                else:
                    self.finished.emit(False)    
        except:
            self.finished.emit(False)    
class StartDownloading(qt.QDialog):
    def __init__(self,p,FileName:str,DIRName:str):
        super().__init__(p)
        self.fileName=FileName
        self.DIRName=DIRName
        layout=qt.QVBoxLayout(self)
        self.progressBar=qt.QProgressBar()        
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.progressBar)
        self.cancel=guiTools.QPushButton("إلغاء")
        self.cancel.setStyleSheet("background-color: #0000AA; color: #e0e0e0;")
        self.cancel.clicked.connect(self.close)
        layout.addWidget(self.cancel)
        self.thread=DownloadThread(FileName,DIRName)
        self.thread.finished.connect(self.onFinished)
        self.thread.progress.connect(self.onProgreesBarChanged)
        self.thread.start()
        qt1.QShortcut("escape",self).activated.connect(self.close)
    def closeEvent(self, a0):
        result=guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد إلغاء العملية","نعم","لا")
        if result==0:
            self.thread.terminate()
            functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'),settings.app.appName,self.DIRName,self.fileName))
            a0.accept()
        else:
            a0.ignore()
    def onFinished(self,state):
        if state:
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم تحميل بنجاح")
            self.accept()
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","حدث خطأ أثناء التحميل")
            self.close()
    def onProgreesBarChanged(self,value):
        self.progressBar.setValue(value)