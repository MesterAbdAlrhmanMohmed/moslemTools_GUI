import guiTools, webbrowser
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class AboutDeveloper(qt.QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(500,300)
        self.center()
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
        self.info.addItem("حسابي على Facebook")
        self.info.addItem("كان أنس محمد مشاركا في هذا المشروع، جزاه الله خيرا")
        font1=qt1.QFont()
        font1.setBold(True)
        self.info_text = qt.QLabel()
        self.info_text.setFont(font1)
        self.info_text.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_text.setText("اللهم اجعل عملنا هذا في ميزان حسناتنا وصدقة جارية لنا")
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
            if text == "قناتي على YouTube":
                webbrowser.open("https://youtube.com/@alcoder01?feature=shared")
            elif text == "حسابي على telegram":
                webbrowser.open("https://t.me/P1_1_1")
            elif text == "حسابي على GitHub":
                webbrowser.open("https://github.com/MesterAbdAlrhmanMohmed")
            elif text == "حسابي على Facebook":
                webbrowser.open("https://www.facebook.com/abd.alrhman.mohamed.alcoder?mibextid=ZbWKwL")
    def center(self):        
        frame_geometry = self.frameGeometry()        
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)        
        self.move(frame_geometry.topLeft())