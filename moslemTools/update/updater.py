import os,shutil,subprocess,requests,settings,guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class DownloadUpdateObjects(qt2.QObject):
    progress=qt2.pyqtSignal(int)
    installing=qt2.pyqtSignal(str)
    finish=qt2.pyqtSignal(str)
    download=qt2.pyqtSignal(bool)
class DownloadUpdateThread(qt2.QRunnable):
    def __init__ (self,URL):
        super().__init__()
        self.URL=URL
        self.object=DownloadUpdateObjects()
        self.path=os.path.join(os.getenv('appdata'),settings.settings_handler.appName,"update")
        self.downloading=True
        self.object.download.connect(self.is_download)
    def is_download(self,value):
        self.downloading=value
    def run(self):
        Name=os.path.join(self.path,self.URL.split("/")[-1])
        try:
            if os.path.exists(self.path):
                shutil.rmtree(self.path)
        except:
            self.object.finish.emit("error")
            return
        os.makedirs(self.path)
        try:
            with requests.get(self.URL,stream=True)as r:
                if r.status_code!=200:
                    self.object.finish.emit("error")
                    return
                size=r.headers.get("content-length")
                try:
                    size=int(size)
                except TypeError:
                    self.object.finish.emit("error")
                    return
                recieved=0
                progress=0
                with open(Name,"wb") as file:
                    for pk in r.iter_content(1024):
                        if not self.downloading:
                            file.close()
                            self.object.finish.emit("cancelled")
                        file.write(pk)
                        recieved+=len(pk)
                        progress=int((recieved/size)*100)
                        self.object.progress.emit(progress)
                self.object.installing.emit("yes")
        except:
            self.object.finish.emit("error")
        self.object.finish.emit(Name)
class DownloadUpdateGUI(qt.QDialog):
    def __init__(self,p,URL):
        super().__init__(p)
        self.setWindowTitle("جاري التحديث")         
        self.resize(300,100)
        layout=qt.QVBoxLayout(self)
        self.state=qt.QLabel("يجري الآن تحميل التحديث")
        self.state.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.state.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.state)
        self.downloading=qt.QProgressBar()
        self.downloading.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.downloading.setRange(0,100)
        self.downloading.setAccessibleName("حالة التحميل")
        self.downloading.setValue(0)
        layout.addWidget(self.downloading)
        self.cancel=qt.QPushButton("إلغاء")
        self.cancel.setStyleSheet("background-color: #0000AA; color: white;")
        layout.addWidget(self.cancel)
        self.thread=qt2.QThreadPool(self)
        self.run=DownloadUpdateThread(URL)
        self.run.object.progress.connect(self.change)
        self.run.object.installing.connect(self.Installation)
        self.run.object.finish.connect(self.finish)
        self.thread.start(self.run)
        self.cancel.clicked.connect(self.cancelBTN)
    def Installation(self,choice):
        if choice=="yes":
            self.state.setText("جاري التثبيت")
            self.downloading.setValue(0)
    def change(self,progress):
        self.downloading.setValue(progress)
    def finish(self,c):
        if c=="error":
            guiTools.qMessageBox.MessageBox.view(self,"خطأ","خطأ أثناء التحميل الرجاء المحاولة لاحقا")
            self.close()
        elif c=="cancelled":
            self.close()
        else:
            subprocess.Popen([c, "/SILENT", "/NOCANCEL", "/SUPPRESSMSGBOXES", "/NORESTART"])
            qt.QApplication.exit()
    def cancelBTN(self):
        self.run.object.download.emit(False)