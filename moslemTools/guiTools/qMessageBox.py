import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from .QReadOnlyTextEdit import QReadOnlyTextEdit
import winsound
class MessageBox(qt.QDialog):
    def __init__(self, parent, title: str, label: str):
        super().__init__(parent)
        self.resize(700, 150)
        self.setWindowTitle(title)        
        layout = qt.QVBoxLayout(self)
        self.label = QReadOnlyTextEdit()
        self.label.setText(label)
        layout.addWidget(self.label)        
        self.OKBTN = qt.QPushButton("موافق")
        self.OKBTN.setDefault(True)
        self.OKBTN.clicked.connect(self.accept)
        self.OKBTN.setStyleSheet("""
            QPushButton {
                background-color: #0000AA; 
                color: #e0e0e0;
                border-radius: 4px;
                padding: 8px 20px; /* تم زيادة الـpadding لجعل الزر أكبر وأوضح */
                font-size: 14px; /* حجم الخط أكبر قليلاً لجعل النص أوضح */
            }
        """)        
        self.OKBTN.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed) 
        layout.addWidget(self.OKBTN, alignment=qt2.Qt.AlignmentFlag.AlignLeft)        
        qt1.QShortcut("Escape", self).activated.connect(self.reject)    
    @staticmethod
    def view(parent, title:str, label:str):
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        dlg = MessageBox(parent, title, label)
        dlg.setWindowIcon(dlg.style().standardIcon(qt.QStyle.StandardPixmap.SP_MessageBoxInformation))
        result = dlg.exec()    
    @staticmethod
    def error(parent, title:str, label:str):
        winsound.MessageBeep(winsound.MB_ICONHAND)
        dlg = MessageBox(parent, title, label)
        dlg.setWindowIcon(dlg.style().standardIcon(qt.QStyle.StandardPixmap.SP_MessageBoxCritical))
        result = dlg.exec()