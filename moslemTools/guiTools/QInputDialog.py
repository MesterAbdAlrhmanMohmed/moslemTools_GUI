import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt
class QInputDialog(qt.QDialog):
    def __init__(self, parent, title: str, label: str,widget):
        super().__init__(parent)
        self.resize(300, 150)
        self.setWindowTitle(title)
        layout = qt.QVBoxLayout(self)
        self.label = qt.QLabel(label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.text = widget
        self.text.setAccessibleName(label)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.textChanged.connect(self.onTextChanged)
        layout.addWidget(self.text)
        buttonsLayout = qt.QHBoxLayout()
        self.OKBTN = qt.QPushButton("موافق")
        self.OKBTN.setStyleSheet("""
            background-color: black;
            color: white;
        """)
        self.OKBTN.setDisabled(True)
        self.OKBTN.setDefault(True)
        self.OKBTN.clicked.connect(self.accept)
        buttonsLayout.addWidget(self.OKBTN)
        self.cancelBTN = qt.QPushButton("إلغاء")
        self.cancelBTN.setStyleSheet("""
            background-color: #8B0000;
            color: white;
        """)
        self.cancelBTN.clicked.connect(self.reject)
        buttonsLayout.addWidget(self.cancelBTN)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
        layout.addLayout(buttonsLayout)
    def closeEvent(self, event):
        self.reject()
        event.accept()
    def onTextChanged(self, text):        
        if text.strip():
            self.OKBTN.setDisabled(False)
            self.OKBTN.setStyleSheet("""
                background-color: green;
                color: white;
            """)
        else:
            self.OKBTN.setDisabled(True)
            self.OKBTN.setStyleSheet("""
                background-color: black;
                color: white;
            """)
    @staticmethod
    def getText(parent, title: str, label: str, text: str = ""):
        dlg = QInputDialog(parent, title, label,qt.QLineEdit())
        dlg.text.setText(text)
        dlg.text.textChanged.connect(dlg.onTextChanged)
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.text.text(), True
        else:
            return "", False
    @staticmethod
    def getInt(parent, title: str, label: str, value:int,min:int,max:int):
        dlg = QInputDialog(parent, title, label,qt.QSpinBox())
        dlg.text.setRange(min,max)
        dlg.text.setValue(value)        
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.text.value(), True
        else:
            return 0, False