import sys,subprocess
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from settings import *
class ExitApp(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        self.resize(200,100)
        self.setWindowTitle("الخروج من {} محاورة".format(app.name))
        self.p=p
        self.cancel1=False
        lec="ماذا تريد أن تفعل?"
        label=qt.QLabel(lec)        
        self.exit=qt.QComboBox()
        self.exit.setAccessibleName(lec)
        font=qt1.QFont()
        font.setBold(True)
        self.exit.addItems(["إخفاء", "خروج", "إعادة تشغيل"])
        self.exit.setFont(font)
        self.ok=qt.QPushButton("موافق")
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.fok)        
        self.cancel=qt.QPushButton("إلغاء")
        self.ok.setStyleSheet("background-color: #008000; color: #e0e0e0;")    # أخضر
        self.cancel.setStyleSheet("background-color: #AA0000; color: #e0e0e0;")  # أحمر
        self.cancel.clicked.connect(self.fcan)
        layout=qt.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.exit)        
        buttons_layout=qt.QHBoxLayout()
        buttons_layout.addWidget(self.ok)
        buttons_layout.addWidget(self.cancel)
        layout.addLayout(buttons_layout)  # إضافة التخطيط الأفقي إلى التخطيط الرئيسي
        self.setLayout(layout)
    def fok(self):
        ec=self.exit.currentIndex()
        if ec == 0:
            self.p.hide()
            self.p.show_action.setText("إظهار البرنامج")
            self.accept()
        elif ec == 1:
            sys.exit()
        elif ec == 2:
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit()

    def fcan(self):
        self.cancel1=True
        self.close()