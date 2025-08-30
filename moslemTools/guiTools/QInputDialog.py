from guiTools import QPushButton
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt

class QInputDialog(qt.QDialog):
    def __init__(self, parent, title: str, label: str, widget):
        super().__init__(parent)
        self.resize(300, 150)
        self.setWindowTitle(title)
        layout = qt.QVBoxLayout(self)
        self.label = qt.QLabel(label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.text = widget
        self.text.setAccessibleName(label)
        
        # محاذاة النص حسب نوع الودجة
        if isinstance(widget, qt.QLineEdit):
            self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif isinstance(widget, qt.QSpinBox):
            self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        self.text.textChanged.connect(self.onTextChanged)
        layout.addWidget(self.text)        
        self.OKBTN = QPushButton("موافق")
        self.OKBTN.setDisabled(True)
        self.OKBTN.clicked.connect(self.accept)
        self.OKBTN.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
            }
        """)
        self.cancelBTN = QPushButton("إلغاء")
        self.cancelBTN.clicked.connect(self.reject)
        self.cancelBTN.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
            }
        """)
        buttonsLayout = qt.QHBoxLayout()
        buttonsLayout.addWidget(self.OKBTN)
        buttonsLayout.addWidget(self.cancelBTN)        
        wrapper = qt.QHBoxLayout()
        wrapper.addLayout(buttonsLayout)
        wrapper.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(wrapper)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
    
    def closeEvent(self, event):
        self.reject()
        event.accept()
    
    def onTextChanged(self, text):
        if text.strip():
            self.OKBTN.setDisabled(False)
            self.OKBTN.setStyleSheet("""
                QPushButton {
                    background-color: #008000;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-size: 14px;
                }
            """)
        else:
            self.OKBTN.setDisabled(True)
            self.OKBTN.setStyleSheet("""
                QPushButton {
                    background-color: black;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-size: 14px;
                }
            """)
    
    @staticmethod
    def getText(parent, title: str, label: str, text: str = ""):
        dlg = QInputDialog(parent, title, label, qt.QLineEdit())
        dlg.text.setText(text)
        dlg.text.textChanged.connect(dlg.onTextChanged)
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.text.text(), True
        else:
            return "", False
    
    @staticmethod
    def getInt(parent, title: str, label: str, value: int, min: int, max: int):
        dlg = QInputDialog(parent, title, label, qt.QSpinBox())
        dlg.text.setRange(min, max)
        dlg.text.setValue(value)
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.text.value(), True
        else:
            return 0, False    
    @staticmethod
    def getSingleInt(parent, title: str, label: str, value: int):
        dlg = QInputDialog(parent, title, label, qt.QSpinBox())
        dlg.text.setValue(value)
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.text.value(), True
        else:
            return 0, False