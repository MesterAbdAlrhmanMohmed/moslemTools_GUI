from guiTools import QPushButton
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from .QReadOnlyTextEdit import QReadOnlyTextEdit
import winsound

class MessageBoxForGame(qt.QDialog):
    def __init__(self, parent, title: str, label: str):
        super().__init__(parent)
        self.resize(900, 350)
        self.setWindowTitle(title)
        self.center()
        layout = qt.QVBoxLayout(self)
        self.label = QReadOnlyTextEdit(viewer_name="qMessageBox")
        self.label.setText(label)
        layout.addWidget(self.label)
        self.OKBTN = QPushButton("موافق")
        self.OKBTN.clicked.connect(self.accept)
        self.OKBTN.setStyleSheet("""
            QPushButton {
                background-color: #0000AA; 
                color: #e0e0e0;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
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
    def error(parent, title:str, label:str, sound_enabled=True):
        if sound_enabled:
            winsound.PlaySound(r"data\sounds\game\false.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        dlg = MessageBoxForGame(parent, title, label)
        dlg.setWindowIcon(dlg.style().standardIcon(qt.QStyle.StandardPixmap.SP_MessageBoxCritical))
        result = dlg.exec()