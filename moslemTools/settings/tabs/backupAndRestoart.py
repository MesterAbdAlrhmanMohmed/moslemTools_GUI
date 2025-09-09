import guiTools,zipfile,subprocess,sys,os, shutil
from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class GUIForThread(qt.QDialog):
    def __init__(self, p, path, choice):
        super().__init__(p)
        self.resize(500, 500)
        self.setWindowTitle("جاري إتمام العملية . يرجى الانتظار ...")
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: Arial;
            }
        """)
        self.thread = Thread(path, choice)
        self.thread.objects.finish.connect(self.onFinished)
        qt2.QThreadPool(self).start(self.thread)
        self.choice = choice
    def onFinished(self, state):
        if state:
            if self.choice == 0:
                guiTools.qMessageBox.MessageBox.view(self, "تم", "تم نسخ الإعدادات بنجاح")
            else:
                mb = guiTools.QQuestionMessageBox.view(self,"تم تحديث الإعدادات","يجب عليك إعادة تشغيل البرنامج لتطبيق التغييرات. هل تريد إعادة التشغيل الآن؟","إعادة التشغيل الآن","إعادة التشغيل لاحقا")
                if mb==0:                    
                    subprocess.Popen([sys.executable] + sys.argv)
                    sys.exit()
        self.close()
class Thread(qt2.QRunnable):
    def __init__(self, path, choice):
        super().__init__()
        self.path = path
        self.choice = choice
        self.objects = Objects()
    def run(self):
        if self.choice == 0:
            with zipfile.ZipFile(os.path.join(self.path, settings_handler.appName + ".zip"), "w") as zipf:
                for root, dirs, files in os.walk(os.path.join(os.getenv('appdata'), settings_handler.appName)):
                    for filename in files:
                        filePath = os.path.join(root, filename)
                        zipf.write(filePath, os.path.relpath(filePath, os.path.join(os.getenv('appdata'), settings_handler.appName)))
        else:
            shutil.rmtree(os.path.join(os.getenv('appdata'), settings_handler.appName))
            with zipfile.ZipFile(self.path) as zfile:
                zfile.extractall(os.path.join(os.getenv('appdata'), settings_handler.appName))
        self.objects.finish.emit(True)
class Objects(qt2.QObject):
    finish = qt2.pyqtSignal(bool)
class Restoar(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: Arial;
            }
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0000CC;
            }
        """)
        layout = qt.QVBoxLayout(self)
        layout.addStretch()        
        self.createCopy = qt.QPushButton("نسخ الإعدادات والملفات احتياطيا")
        self.createCopy.setFixedWidth(250)
        layout.addWidget(self.createCopy, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        self.createCopy.clicked.connect(self.onbackup)        
        self.restoar = qt.QPushButton("استعادة الإعدادات والملفات")
        self.restoar.setFixedWidth(250)
        layout.addWidget(self.restoar, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.restoar.clicked.connect(self.onrestoar)        
        layout.addStretch()
        self.p = p
    def onbackup(self):
        fileDialog = qt.QFileDialog(self.p)
        fileDialog.setFileMode(qt.QFileDialog.FileMode.Directory)
        if fileDialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            GUIForThread(self, fileDialog.selectedFiles()[0], 0).exec()
    def onrestoar(self):
        fileDialog = qt.QFileDialog(self.p)
        if fileDialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            GUIForThread(self, fileDialog.selectedFiles()[0], 1).exec()