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
        self.is_finished = False
        self.choice = choice        
        self.setWindowFlags(self.windowFlags() & ~qt2.Qt.WindowType.WindowCloseButtonHint)        
        self.thread = Thread(path, choice)
        self.thread.objects.finish.connect(self.onFinished)
        qt2.QThreadPool.globalInstance().start(self.thread)
    def onFinished(self, state):
        self.is_finished = True
        if state:
            if self.choice == 0:                
                guiTools.MessageBox.view(self, "تم", "تم نسخ الإعدادات بنجاح")
            else:                                
                mb = guiTools.QQuestionMessageBox.view(self,"تم تحديث الإعدادات","يجب عليك إعادة تشغيل البرنامج لتطبيق التغييرات. هل تريد إعادة التشغيل الآن؟","إعادة التشغيل الآن","إعادة التشغيل لاحقا")
                if mb == 0:
                    subprocess.Popen([sys.executable] + sys.argv)
                    sys.exit()
        self.accept()
    def closeEvent(self, event):
        if not self.is_finished:            
            if self.choice == 0:
                message = "لا يمكن إغلاق النافذة حتى يكتمل النسخ."
            else:
                message = "لا يمكن إغلاق النافذة حتى تكتمل الاستعادة."                        
            guiTools.MessageBox.error(self, "تحذير", message)
            event.ignore()
        else:
            event.accept()
    def keyPressEvent(self, event):
        if event.key() == qt2.Qt.Key.Key_Escape:
            if not self.is_finished:                
                if self.choice == 0:
                    message = "لا يمكن إلغاء العملية حتى يكتمل النسخ."
                else:
                    message = "لا يمكن إلغاء العملية حتى تكتمل الاستعادة."                                
                guiTools.MessageBox.error(self, "تحذير", message)                
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
class Thread(qt2.QRunnable):
    def __init__(self, path, choice):
        super().__init__()
        self.path = path
        self.choice = choice
        self.objects = Objects()
    def run(self):
        try:
            if self.choice == 0:
                with zipfile.ZipFile(os.path.join(self.path, settings_handler.appName + ".zip"), "w") as zipf:
                    appdata_path = os.path.join(os.getenv('appdata'), settings_handler.appName)
                    for root, dirs, files in os.walk(appdata_path):
                        for filename in files:
                            filePath = os.path.join(root, filename)
                            zipf.write(filePath, os.path.relpath(filePath, appdata_path))
            else:
                appdata_path = os.path.join(os.getenv('appdata'), settings_handler.appName)
                if os.path.exists(appdata_path):
                    shutil.rmtree(appdata_path)
                with zipfile.ZipFile(self.path) as zfile:
                    zfile.extractall(appdata_path)
            self.objects.finish.emit(True)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.objects.finish.emit(False)
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
        path = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد الحفظ")
        if path:
            GUIForThread(self, path, 0).exec()
    def onrestoar(self):
        path, _ = qt.QFileDialog.getOpenFileName(self, "اختر ملف الاستعادة", "", "Zip Files (*.zip)")
        if path:
            GUIForThread(self, path, 1).exec()