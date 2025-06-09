import guiTools, update
import zipfile
import sys
import os, shutil
from settings import settings_handler, app
import PyQt6.QtWidgets as qt
import sys
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt
class Update(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""            
            }
            QCheckBox {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
            }
            QPushButton {
                background-color: #0000AA; /* اللون الأزرق من شاشة الموت */
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
            }
        """)
        UpdateLayout = qt.QVBoxLayout(self)
        self.update_autoDect = qt.QCheckBox("تحقق تلقائيًا من التحديثات عند بدء البرنامج")
        self.update_autoDect.setChecked(p.cbts(settings_handler.get("update", "autoCheck")))
        UpdateLayout.addWidget(self.update_autoDect)
        self.update_beta = qt.QCheckBox("تحميل التحديثات التجريبية")
        self.update_beta.setChecked(p.cbts(settings_handler.get("update", "beta")))
        UpdateLayout.addWidget(self.update_beta)
        self.update_check = qt.QPushButton("التحقق من وجود تحديثات")
        self.update_check.clicked.connect(lambda: update.check(self))
        UpdateLayout.addWidget(self.update_check)