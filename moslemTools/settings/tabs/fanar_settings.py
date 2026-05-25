import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools,webbrowser
from settings import settings_handler
class FanarSettings(qt.QWidget):
    def __init__(self, p=None):
        super().__init__()
        self.p = p
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #e0e0e0;
            }
            QLineEdit {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 8px;
                font-size: 13px;
                background-color: #1E1E1E;
            }
        """)        
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)                
        api_key_layout = qt.QHBoxLayout()
        self.api_key_label = qt.QLabel("مفتاح الـ API الخاص بـ فنار:")
        self.api_key_input = qt.QLineEdit()
        self.api_key_input.setEchoMode(qt.QLineEdit.EchoMode.Password)
        self.api_key_input.setText(settings_handler.get("fanar", "api_key"))
        self.api_key_input.setAccessibleName("مفتاح الـ API الخاص بـ فنار")        
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.api_key_label)
        main_layout.addLayout(api_key_layout)                
        self.get_api_button = guiTools.QPushButton("الحصول على مفتاح الـ API")
        self.get_api_button.setStyleSheet("background-color: #0000AA; color: #e0e0e0; font-weight: bold;")        
        self.get_api_button.setAutoDefault(False)
        self.get_api_button.clicked.connect(lambda: webbrowser.open("https://api.fanar.qa/request/ar"))
        main_layout.addWidget(self.get_api_button)                                        
        self.instructions_view = guiTools.QReadOnlyTextEdit()
        instructions_text = (
            "للحصول على مفتاح الـ API، اتبع التعليمات الآتية:\n\n"
            "قم بالضغط على الزر أعلاه، وسيتم توجيهك إلى صفحة ويب لكتابة بياناتك.\n"
            "اكتب اسمك، ثم بريدك الإلكتروني،\n"
            "بعدها، يمكنك كتابة أي شيء في مربع المؤسسة،\n"
            "وفي خانة حالة الاستخدام (Use case)، اكتب: برنامج إسلامي،\n"
            "ثم قم بالموافقة على الشروط والأحكام، وبعدها قم بالضغط على زر طلب.\n"
            "بعد ذلك، سيتم إرسال كود تفعيل إلى بريدك الإلكتروني، وبعد كتابته وتأكيده سيتم إرسال لك مفتاح الـ API الخاص بك."
        )
        self.instructions_view.setText(instructions_text)
        main_layout.addWidget(self.instructions_view)        
        main_layout.addStretch()