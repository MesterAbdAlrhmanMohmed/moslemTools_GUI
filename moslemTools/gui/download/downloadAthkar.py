from functions import quranJsonControl
import json,os,requests,gettext,re
import guiTools,gui,settings,settings,functions
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class SelectAthkar(qt.QDialog):
    def __init__(self,p):
        super().__init__(p)
        self.resize(900,500)
        layout=qt.QVBoxLayout(self)
        serch=qt.QLabel("البحث عن فئة أذكار")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("البحث عن فئة أذكار")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
            self.reciterData=json.load(data)
        self.reciters=guiTools.QListWidget()
        font=qt1.QFont()
        font.setBold(True)
        self.reciters.setFont(font)
        self.reciterData1=[]
        for athker in self.reciterData:
            self.reciterData1.append(athker["name"])
        self.reciters.clicked.connect(lambda:DownloadReciter(self,self.reciterData[self.reciters.currentRow()]["content"],self.reciters.currentItem().text()).exec())
        self.reciters.addItems(self.reciterData1)
        layout.addWidget(self.reciters)
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
        self.reciters.clear()
        result=self.search(search_text,list(self.reciterData1))
        self.reciters.addItems(result)

class downloadObjects(qt2.QObject):
    progress=qt2.pyqtSignal(int)
    downloaded=qt2.pyqtSignal(int)
    pauseDownloading=qt2.pyqtSignal(str)
    finch=qt2.pyqtSignal(bool)
class downloadThread(qt2.QRunnable):
    def __init__(self,p,url,name):
        super().__init__()        
        self.objects=downloadObjects()
        self.name=name
        self.url=url
        self.pause=False
        self.objects.pauseDownloading.connect(self.on_pause)        
    def on_pause(self,s):
        self.pause=True
    def  run(self):
        try:
            count=0
            for item in self.url:
                if not self.pause:
                    if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar")):
                        os.makedirs(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar"))
                    if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name)):
                        os.makedirs(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name))
                    file=str(self.url.index(item)) + ".mp3"
                    if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name,file)):
                        count+=1
                        self.objects.downloaded.emit(count)
                    else:
                        with requests.get(item["audio"],stream=True) as r:
                            if r.status_code!=200:
                                self.objects.finch.emit(False)
                                return
                            size=r.headers.get("content-length")
                            try:
                                size=int(size)
                            except TypeError:
                                self.objects.finch.emit(False)
                                return
                            recieved=0
                            progress=0
                            with open(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name,file),"wb") as file:
                                for pk in r.iter_content(1024):
                                    file.write(pk)
                                    recieved+=len(pk)
                                    progress=int((recieved/size)*100)
                                    self.objects.progress.emit(progress)
                        count+=1
                        self.objects.downloaded.emit(count)
            self.objects.finch.emit(True)
        except Exception as e:
            print(e)
            self.objects.finch.emit(False)
class DownloadReciter(qt.QDialog):
    def __init__(self,p,url,name):
        super().__init__(p)                         
        self.setWindowTitle("جاري التحميل")        
        qt1.QShortcut("escape",self).activated.connect(lambda:self.run.objects.pauseDownloading.emit("a"))
        self.progress=qt.QProgressBar()
        self.downloaded=qt.QSpinBox()
        self.downloaded.setAccessibleName("عدد الأذكار التي تم تحميلها")
        self.downloaded.setRange(0,7000)
        self.downloaded.setReadOnly(True)
        self.pause=guiTools.QPushButton("إيقاف مؤقت")
        self.pause.setStyleSheet("background-color: #0000AA; color: white;")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.progress)
        layout.addWidget(qt.QLabel("عدد الأذكار التي تم تحميلها"))
        layout.addWidget(self.downloaded)
        layout.addWidget(self.pause)
        thread=qt2.QThreadPool(self)
        self.run=downloadThread(self,url,name)
        self.run.objects.finch.connect(self.on)
        self.run.objects.progress.connect(self.on_progress)
        self.run.objects.downloaded.connect(self.on_downloaded)
        thread.start(self.run)
        self.pause.clicked.connect(lambda:self.run.objects.pauseDownloading.emit("a"))
    def closeEvent(self,event):
        self.run.objects.pauseDownloading.emit("a")
    def on(self,state):
        if state==True:
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم التحميل بنجاح")
            self.close()
        else:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعظر التحميل")
            self.close()
    def on_progress(self,progress):
        self.progress.setValue(progress)
    def on_downloaded(self,count):
        self.downloaded.setValue(count)