from .QPushButton import QPushButton
if not isinstance(QPushButton, type):
    QPushButton = QPushButton.QPushButton
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from .QNavigableLabelAsTextEdit import QNavigableLabelAsTextEdit
if not isinstance(QNavigableLabelAsTextEdit, type):
    QNavigableLabelAsTextEdit = QNavigableLabelAsTextEdit.QNavigableLabelAsTextEdit
import winsound


class MessageBox(qt.QDialog):
    def __init__(self, parent, title: str, label: str):
        super().__init__(parent)
        self.setMinimumSize(500, 200)
        self.resize(900, 350)
        self.setWindowTitle(title)
        self.center()
        layout = qt.QVBoxLayout(self)
        self.label = QNavigableLabelAsTextEdit(label, parent=self, viewer_name="qMessageBox")
        layout.addWidget(self.label)
        self.OKBTN = QPushButton("موافق")
        self.OKBTN.setDefault(True)
        self.OKBTN.clicked.connect(self.accept)
        self.OKBTN.setStyleSheet("""
            QPushButton {
                background-color: #0056b3;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #004085;
            }
            QPushButton:pressed {
                background-color: #002752;
            }
        """)
        self.OKBTN.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed)
        layout.addWidget(self.OKBTN, alignment=qt2.Qt.AlignmentFlag.AlignLeft)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
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
