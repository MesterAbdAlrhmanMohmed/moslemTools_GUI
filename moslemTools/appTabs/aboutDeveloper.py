import guiTools, webbrowser
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class AboutDeveloper(qt.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.setWindowTitle("عن المطور")
        self.info = guiTools.QListWidget()
        font = self.info.font()
        font.setBold(True)
        self.info.setFont(font)
        self.info.itemClicked.connect(self.open_link)
        self.info.addItem("عبد الرحمن محمد alcoder")
        self.info.addItem("قناتي على YouTube")
        self.info.addItem("حسابي على telegram")
        self.info.addItem("حسابي على GitHub")
        self.info_text = qt.QLabel()
        self.info_text.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_text.setText("اللهم اجعل عملي هذا في ميزان حسناتي وصدقة جارية لي")
        self.info_text.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info_text.setFont(font)
        layout = qt.QVBoxLayout()
        layout.addWidget(self.info)
        layout.addWidget(self.info_text)
        self.setLayout(layout)
    def open_link(self):
        current_item = self.info.currentItem()
        if current_item:
            text = current_item.text()
            if text == "قناة عبد الرحمن على YouTube":
                webbrowser.open("https://youtube.com/@alcoder01?feature=shared")
            elif text == "حساب عبد الرحمن على telegram":
                webbrowser.open("https://t.me/P1_1_1")
            elif text == "حساب عبد الرحمن على GitHub":
                webbrowser.open("https://github.com/MesterAbdAlrhmanMohmed")