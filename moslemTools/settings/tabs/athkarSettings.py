from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class AthkarSettings(qt.QWidget):
    def __init__(self):
        super().__init__()                
        self.setStyleSheet("""
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
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)                
        group_box = qt.QGroupBox()
        group_layout = qt.QVBoxLayout(group_box)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(12, 15, 12, 15)                                
        voice_row = qt.QHBoxLayout()
        voice_row.setSpacing(10)        
        self.voiceSelection_laybol = qt.QLabel("تشغيل الأذكار الصوتية كل:")
        self.voiceSelection = qt.QComboBox()
        self.voiceSelection.setAccessibleName("تشغيل الأذكار الصوتية كل")
        self.voiceSelection.addItems(self.items)
        self.voiceSelection.setCurrentIndex(int(settings_handler.get("athkar", "voice")))                
        font = qt1.QFont()
        font.setBold(True)
        self.voiceSelection.setFont(font)        
        voice_row.addWidget(self.voiceSelection)
        voice_row.addWidget(self.voiceSelection_laybol)
        voice_row.addStretch()
        group_layout.addLayout(voice_row)                                
        volume_row = qt.QHBoxLayout()
        volume_row.setSpacing(10)        
        initial_volume = int(settings_handler.get("athkar", "voiceVolume"))
        self.voiceVolumeLabel = qt.QLabel(f"مستوى صوت الأذكار: {initial_volume}%")        
        self.voiceVolume = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.voiceVolume.setAccessibleName("مستوى صوت الأذكار")
        self.voiceVolume.setRange(0, 100)
        self.voiceVolume.setValue(initial_volume)
        self.voiceVolume.valueChanged.connect(self.onVoiceVolumeChanged)        
        volume_row.addWidget(self.voiceVolume, 2)
        volume_row.addWidget(self.voiceVolumeLabel)
        group_layout.addLayout(volume_row)                
        text_row = qt.QHBoxLayout()
        text_row.setSpacing(10)        
        self.textSelection_laybol = qt.QLabel("عرض الأذكار النصية كل:")
        self.textSelection = qt.QComboBox()
        self.textSelection.setAccessibleName("عرض الأذكار النصية كل")
        self.textSelection.addItems(self.items)
        self.textSelection.setCurrentIndex(int(settings_handler.get("athkar", "text")))
        self.textSelection.setFont(font)        
        text_row.addWidget(self.textSelection)
        text_row.addWidget(self.textSelection_laybol)
        text_row.addStretch()
        group_layout.addLayout(text_row)
        self.playAtStartup = qt.QCheckBox("تشغيل ذكر عشوائي عند بدء تشغيل البرنامج")
        self.playAtStartup.setChecked(settings_handler.get("athkar", "playAtStartup") == "True")
        group_layout.addWidget(self.playAtStartup)
        main_layout.addWidget(group_box)
        main_layout.addStretch()                                
        info_layout = qt.QVBoxLayout()
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 20, 0, 0)                
        self.info1 = qt.QLabel("لتشغيل ذكر عشوائي أو إيقافه, نستخدم الاختصار windows+alt+p")
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        self.info2 = qt.QLabel("لعرض ذكر عشوائي, نستخدم الاختصار windows+alt+l")
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        self.info = qt.QLabel("تنبيه هام, حتى تظل الأذكار تعمل في الخلفية, يجب إخفاء البرنامج, لا الخروج منه")
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("font-weight: bold;")        
        info_layout.addWidget(self.info1)
        info_layout.addWidget(self.info2)
        info_layout.addWidget(self.info)        
        main_layout.addLayout(info_layout)                        
        self.voiceSelection.currentIndexChanged.connect(self.onVoiceSelectionChanged)                
        self.onVoiceSelectionChanged(self.voiceSelection.currentIndex())
    def onVoiceVolumeChanged(self, value):        
        self.voiceVolumeLabel.setText(f"مستوى صوت الأذكار الصوتية: {value}%")    
    def onVoiceSelectionChanged(self, index):        
        is_stopped = (index == 5)                
        self.voiceVolume.setVisible(not is_stopped)
        self.voiceVolumeLabel.setVisible(not is_stopped)