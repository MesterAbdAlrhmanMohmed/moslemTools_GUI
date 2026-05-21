import guiTools, webbrowser
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class AboutDeveloper(qt.QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(650,300)
        self.center()
        self.setWindowTitle("عن المطور")
        self.info = guiTools.QListWidget()
        self.info.setSpacing(3)
        font = self.info.font()
        font.setBold(True)
        self.info.setFont(font)
        self.info.itemClicked.connect(self.open_link)
        self.info.addItem("عبد الرحمن محمد alcoder")
        self.info.addItem("نبذة عن المطور")
        self.info.addItem("قناتي على YouTube")
        self.info.addItem("حسابي على telegram")
        self.info.addItem("حسابي على GitHub")
        self.info.addItem("حسابي على Facebook")
        self.info.addItem("كان أنس محمد مشاركا في هذا المشروع، جزاه الله خيرا")
        self.info_text = qt.QLabel()
        self.info_text.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_text.setText("اللهم اجعل عملنا هذا في ميزان حسناتنا وصدقة جارية لنا")
        self.info_text.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info_text.setFont(font)
        self.info_text1 = qt.QLabel()
        self.info_text1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_text1.setText("اللهم اجعل ثواب هذا البرنامج\nصدقة جارية عني،\nوعن كل مَن اغتبته أو آذيته،\nأو أخطأت في حقه بقصد أو بغير قصد،\nواغفر لي ولهم")
        self.info_text1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info_text1.setFont(font)
        main_layout = qt.QHBoxLayout()
        labels_layout = qt.QVBoxLayout()
        labels_layout.addStretch()
        labels_layout.addWidget(self.info_text)
        labels_layout.addSpacing(20)
        labels_layout.addWidget(self.info_text1)
        labels_layout.addStretch()
        main_layout.addWidget(self.info, 4)
        main_layout.addLayout(labels_layout, 3)
        self.setLayout(main_layout)
    def open_link(self):
        current_item = self.info.currentItem()
        if current_item:
            text = current_item.text()
            if text == "نبذة عن المطور":
                guiTools.MessageBox.view(self, "نبذة عن المطور", "نبذة عن المطور:\nعبد الرحمن محمد، باحث في علم مقارنة الأديان والمخطوطات التاريخية.\n\nالتخصص الفكري والبحثي:\nمتخصص في دراسة وتحليل العقائد والتشريعات وتاريخها اللاهوتي، وتتركز مؤلفاته وبحوثه المتعمقة على تفكيك وفحص العقيدة المسيحية والتفاسير الكنسية من جهة، وعلى التأصيل والدفاع عن الدين الإسلامي وبيان حقائقه من جهة أخرى.\n\nالمجال التقني والبرمجي:\nيعمل كمطور برمجيات بلغة بايثون (Python) ومدرس لأساسيات علوم الحاسب، حيث يركز على هندسة وتطوير النظم البرمجية والتطبيقات المكتبية المتقدمة وأتمتة معالجة البيانات.\n\nالبيانات الشخصية والهدف:\nهو مِن مواليد 21 سبتمبر 2005، يجمع في مسيرته بين الكفاءة التقنية والشغف العقائدي؛ مدفوعاً برؤية غايتها خدمة الدين الإسلامي، ونشر الوعي الفكري، والدفاع عن الهوية الإسلامية بأسلوب علمي، أكاديمي، ومنهجي رصين، مستمسكاً بحب الله ورسله وتفنيد الشبهات بالدليل والبرهان.")
            elif text == "قناتي على YouTube":
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