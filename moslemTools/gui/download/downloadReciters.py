import json,os,requests,re,time,socket
from functions import quranJsonControl
import guiTools,gui,settings,settings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class SelectReciter(qt.QDialog):
    def __init__(self,p):
        super().__init__(p)
        self.resize(900,500)
        layout=qt.QVBoxLayout(self)
        serch=qt.QLabel("البحث عن قارئ")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("البحث عن قارئ")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.reciterData=gui.reciters
        self.reciters=guiTools.QListWidget()
        self.reciters.setSpacing(3)
        font=qt1.QFont()
        font.setBold(True)
        self.reciters.setFont(font)
        self.reciters.addItems(self.reciterData.keys())
        self.reciters.clicked.connect(lambda:DownloadReciter(self,self.reciterData[self.reciters.currentItem().text()]).exec())
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
        result=self.search(search_text,list(self.reciterData.keys()))
        self.reciters.addItems(result)
class downloadObjects(qt2.QObject):
    progress=qt2.pyqtSignal(int)
    downloaded=qt2.pyqtSignal(int)
    pauseDownloading=qt2.pyqtSignal(str)
    finch=qt2.pyqtSignal(bool)
    network_error=qt2.pyqtSignal(str)
class downloadThread(qt2.QThread):
    def __init__(self,p,url):
        super().__init__(p)                
        self.objects=downloadObjects()
        self.url=url
        self.is_paused=False
        self.is_cancelled=False
        self.current_file=None
        self.objects.pauseDownloading.connect(self.cancel)
    def resume(self):
        self.is_paused=False
    def cancel(self):
        self.is_cancelled=True
        self.is_paused=False
    def run(self):
        try:
            count=0
            base_dir=os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",self.url.split("/")[-3])
            os.makedirs(base_dir,exist_ok=True)
            for key,value in quranJsonControl.data.items():
                for ayah in value["ayahs"]:
                    if self.is_cancelled:
                        return
                    file_name=self.on_set(key,ayah["numberInSurah"])
                    file_path=os.path.join(base_dir,file_name)
                    self.current_file=file_path
                    if os.path.exists(file_path):
                        count+=1
                        self.objects.downloaded.emit(count)
                        continue
                    downloaded_current=False
                    while not downloaded_current and not self.is_cancelled:
                        while self.is_paused and not self.is_cancelled:
                            self.msleep(200)
                        if self.is_cancelled:
                            return
                        try:
                            with requests.get(self.url + file_name,stream=True,timeout=(5,5)) as r:
                                if r.status_code!=200:
                                    self.objects.finch.emit(False)
                                    return
                                size=r.headers.get("content-length")
                                try:
                                    size=int(size)
                                except (TypeError, ValueError):
                                    size=0
                                recieved=0
                                progress=0
                                with open(file_path,"wb") as f:
                                    for pk in r.iter_content(1024):
                                        if self.is_cancelled:
                                            break
                                        f.write(pk)
                                        recieved+=len(pk)
                                        if size>0:
                                            progress=int((recieved/size)*100)
                                            self.objects.progress.emit(progress)
                                if self.is_cancelled:
                                    if os.path.exists(file_path):
                                        try:
                                            os.remove(file_path)
                                        except Exception:
                                            pass
                                    return
                            downloaded_current=True
                            count+=1
                            self.objects.downloaded.emit(count)
                        except (requests.exceptions.RequestException, Exception) as e:
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                except Exception:
                                    pass
                            if self.is_cancelled:
                                return
                            self.is_paused=True
                            self.objects.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")
            if not self.is_cancelled:
                self.objects.finch.emit(True)
        except Exception as e:
            print(e)
            self.objects.finch.emit(False)
    def on_set(self,surah,Ayah):
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"
class DownloadReciter(qt.QDialog):
    def __init__(self,p,url):
        super().__init__(p)                         
        self.resize(300,100)
        self.setWindowTitle("جاري التحميل")        
        qt1.QShortcut("escape",self).activated.connect(self.close)
        self.lay=qt.QLabel("عدد الآيات التي تم تحميلها")
        self.lay.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.progress=qt.QProgressBar()
        self.downloaded=qt.QSpinBox()
        self.downloaded.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.downloaded.setAccessibleName("عدد الآيات التي تم تحميلها")
        self.downloaded.setRange(0,7000)
        self.downloaded.setReadOnly(True)
        self.pause=guiTools.QPushButton("إيقاف مؤقت")
        self.pause.setStyleSheet("background-color: #0000AA; color: white;")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.progress)
        layout.addWidget(self.lay)
        layout.addWidget(self.downloaded)
        layout.addWidget(self.pause)
        self.run=downloadThread(self,url)
        self.run.objects.finch.connect(self.on)
        self.run.objects.progress.connect(self.on_progress)
        self.run.objects.downloaded.connect(self.on_downloaded)
        self.run.objects.network_error.connect(self.on_network_error)
        self.run.start()
        self.pause.clicked.connect(self.on_pause_clicked)
    def check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5).close()
            return True
        except Exception:
            try:
                socket.create_connection(("1.1.1.1", 53), timeout=1.5).close()
                return True
            except Exception:
                try:
                    requests.head("https://www.google.com", timeout=1.5)
                    return True
                except Exception:
                    return False
    def on_pause_clicked(self):
        if self.run.is_paused or self.pause.text() == "استئناف":
            if not self.check_internet():
                self.pause.setText("استئناف")
                self.pause.setAccessibleName("استئناف")
                guiTools.speak("لا يوجد اتصال بالإنترنت، يرجى التأكد من الاتصال أولاً")
                guiTools.qMessageBox.MessageBox.error(self, "خطأ في الاتصال", "لا يوجد اتصال بالإنترنت، يرجى التأكد من الاتصال أولاً ثم الضغط على زر الاستئناف.")
                return
            self.pause.setText("إيقاف مؤقت")
            self.pause.setAccessibleName("إيقاف مؤقت")
            guiTools.speak("تم استئناف التحميل")
            self.run.resume()
        else:
            self.close()
    def on_network_error(self,msg):
        self.pause.setText("استئناف")
        self.pause.setAccessibleName("استئناف")
        guiTools.speak("تم إيقاف التحميل مؤقتاً بسبب انقطاع الاتصال بالإنترنت")
        guiTools.qMessageBox.MessageBox.error(self,"انقطاع الاتصال",msg)
    def closeEvent(self,event):
        if self.run and self.run.isRunning():
            self.run.cancel()
            self.run.terminate()
            self.run.wait(200)
            if self.run.current_file and os.path.exists(self.run.current_file):
                try:
                    os.remove(self.run.current_file)
                except Exception:
                    pass
        event.accept()
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