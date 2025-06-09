from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class AthkarSettings(qt.QWidget):
    def __init__(self):
        super().__init__()        
        self.setStyleSheet("""            
            }
            QLabel {
                font-size: 14px;
                color: #e0e0e0;
            }
            QComboBox, QSlider, QLineEdit {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                font-size: 13px;
            }
        """)        
        self.items = ["5 دقائق", "10 دقائق", "20 دقيقة", "نصف ساعة", "ساعة", "إيقاف"]
        layout = qt.QVBoxLayout(self)        
        self.voiceSelection_laybol = qt.QLabel("تشغيل الأذكار الصوتية كل")
        self.voiceSelection_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.voiceSelection_laybol)
        self.voiceSelection = qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)
        self.voiceSelection.addItems(self.items)
        self.voiceSelection.setCurrentIndex(int(settings_handler.get("athkar", "voice")))
        self.voiceSelection.setAccessibleName("تشغيل الأذكار الصوتية كل")
        self.voiceSelection.setFont(font)
        layout.addWidget(self.voiceSelection)
        self.info1 = qt.QLineEdit()
        self.info1.setReadOnly(True)
        self.info1.setText("لتشغيل ذكر عشوائي أو إيقافه, نستخدم الاختصار windows+alt+p")
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info1)
        self.info2 = qt.QLineEdit()
        self.info2.setReadOnly(True)
        self.info2.setText("لعرض ذكر عشوائي, نستخدم الاختصار windows+alt+l")
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.voiceVolumeLabel = qt.QLabel("مستوا صوت الأذكار الصوتية")
        self.voiceVolumeLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.voiceVolumeLabel)        
        self.voiceVolume = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.voiceVolume.setAccessibleName("مستوا صوت الأذكار الصوتية")
        self.voiceVolume.setRange(0, 100)
        self.voiceVolume.setValue(int(settings_handler.get("athkar", "voiceVolume")))
        layout.addWidget(self.voiceVolume)        
        self.textSelection_laybol = qt.QLabel("عرض الأذكار النصية كل")
        self.textSelection_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.textSelection_laybol)        
        self.textSelection = qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)        
        self.textSelection.addItems(self.items)
        self.textSelection.setCurrentIndex(int(settings_handler.get("athkar", "text")))
        self.textSelection.setAccessibleName("عرض الأذكار النصية كل")
        self.textSelection.setFont(font)
        layout.addWidget(self.textSelection)
        layout.addWidget(self.info2)
        self.info = qt.QLineEdit()
        self.info.setReadOnly(True)
        self.info.setText("تنبيه هام, حتى تظل الأذكار تعمل في الخلفية, يجب إخفاء البرنامج, لا الخروج منه")
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info)