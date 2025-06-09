import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from .QReadOnlyTextEdit import QReadOnlyTextEdit
import winsound
class QQuestionMessageBox(qt.QDialog):
    def __init__(self, parent, title: str, label: str, yesLabel: str, noLabel: str):
        super().__init__(parent)
        self.result = 1
        self.resize(700, 150)
        self.setWindowTitle(title)
        main_layout = qt.QVBoxLayout(self)
        self.label = QReadOnlyTextEdit()
        self.label.setText(label)
        main_layout.addWidget(self.label)
        buttons_widget = qt.QWidget()
        buttons_layout = qt.QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(0)
        self.OKBTN = qt.QPushButton(yesLabel)
        self.OKBTN.setDefault(True)
        self.OKBTN.clicked.connect(self.onOk)
        self.OKBTN.setStyleSheet("""
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)
        self.OKBTN.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed)
        buttons_layout.addWidget(self.OKBTN)
        self.noBTN = qt.QPushButton(noLabel)
        self.noBTN.clicked.connect(self.reject)
        self.noBTN.setStyleSheet("""
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)
        self.noBTN.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed)
        buttons_layout.addWidget(self.noBTN)
        main_layout.addWidget(buttons_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
    def onOk(self):
        self.result = 0
        self.accept()
    @staticmethod
    def view(parent, title: str, label: str, yesLabel: str, noLabel: str):
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        dlg = QQuestionMessageBox(parent, title, label, yesLabel, noLabel)
        result = dlg.exec()
        return dlg.result