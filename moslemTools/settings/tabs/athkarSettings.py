from settings import settings_handler
import guiTools
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
            QComboBox, QSpinBox, QSlider, QLineEdit {
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
        voice_row.setSpacing(15)
        self.voiceSelection_laybol = qt.QLabel("تشغيل الأذكار الصوتية كل:")
        self.voiceSelection = qt.QComboBox()
        self.voiceSelection.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
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
        volume_row.setSpacing(15)
        initial_volume = int(settings_handler.get("athkar", "voiceVolume") or 100)
        initial_volume = max(1, min(100, initial_volume))
        self.voiceVolumeLabel = qt.QLabel("مستوى صوت الأذكار:")
        self.voiceVolume = qt.QSpinBox()
        self.voiceVolume.setFont(font)
        self.voiceVolume.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.voiceVolume.setFixedWidth(80)
        self.voiceVolume.setRange(1, 100)
        self.voiceVolume.setValue(initial_volume)
        self.voiceVolume.setAccessibleName("مستوى صوت الأذكار")
        volume_row.addWidget(self.voiceVolume)
        volume_row.addWidget(self.voiceVolumeLabel)
        volume_row.addStretch()
        group_layout.addLayout(volume_row)
        text_row = qt.QHBoxLayout()
        text_row.setSpacing(15)
        self.textSelection_laybol = qt.QLabel("عرض الأذكار النصية كل:")
        self.textSelection = qt.QComboBox()
        self.textSelection.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.textSelection.setAccessibleName("عرض الأذكار النصية كل")
        self.textSelection.addItems(self.items)
        self.textSelection.setCurrentIndex(int(settings_handler.get("athkar", "text")))
        self.textSelection.setFont(font)
        text_row.addWidget(self.textSelection)
        text_row.addWidget(self.textSelection_laybol)
        text_row.addStretch()
        group_layout.addLayout(text_row)
        text_type_row = qt.QHBoxLayout()
        text_type_row.setSpacing(15)
        self.textTypeLabel = qt.QLabel("طريقة عرض الأذكار النصية:")
        self.textTypeSelection = qt.QComboBox()
        self.textTypeSelection.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.textTypeSelection.setAccessibleName("طريقة عرض الأذكار النصية")
        self.textTypeSelection.addItems(["إشعار", "نافذة رسالة"])
        try:
            self.textTypeSelection.setCurrentIndex(int(settings_handler.get("athkar", "text_type")))
        except Exception:
            self.textTypeSelection.setCurrentIndex(0)
        self.textTypeSelection.setFont(font)
        text_type_row.addWidget(self.textTypeSelection)
        text_type_row.addWidget(self.textTypeLabel)
        text_type_row.addStretch()
        group_layout.addLayout(text_type_row)
        self.playAtStartup = qt.QCheckBox("تشغيل ذكر عشوائي عند بدء تشغيل البرنامج")
        self.playAtStartup.setChecked(settings_handler.get("athkar", "playAtStartup") == "True")
        group_layout.addWidget(self.playAtStartup)
        self.playBasmalaAtStartup = qt.QCheckBox("تشغيل البسملة عند بدء تشغيل البرنامج")
        self.playBasmalaAtStartup.setChecked(settings_handler.get("athkar", "playBasmalaAtStartup") == "True")
        self.playAtStartup.clicked.connect(lambda checked: self.playBasmalaAtStartup.setChecked(False) if checked else None)
        self.playBasmalaAtStartup.clicked.connect(lambda checked: self.playAtStartup.setChecked(False) if checked else None)
        group_layout.addWidget(self.playBasmalaAtStartup)
        main_layout.addWidget(group_box)
        main_layout.addSpacing(15)
        info_layout = qt.QVBoxLayout()
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.info1 = guiTools.QNavigableLabel("لتشغيل ذكر عشوائي أو إيقافه, نستخدم الاختصار windows+alt+p")
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info2 = guiTools.QNavigableLabel("لعرض ذكر عشوائي, نستخدم الاختصار windows+alt+l")
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info = guiTools.QNavigableLabel("تنبيه هام, حتى تظل الأذكار تعمل في الخلفية, يجب إخفاء البرنامج, لا الخروج منه")
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.info1)
        info_layout.addWidget(self.info2)
        info_layout.addWidget(self.info)
        main_layout.addLayout(info_layout)
        main_layout.addStretch(1)
        self.voiceSelection.currentIndexChanged.connect(self.onVoiceSelectionChanged)
        self.onVoiceSelectionChanged(self.voiceSelection.currentIndex())
        self.textSelection.currentIndexChanged.connect(self.onTextSelectionChanged)
        self.onTextSelectionChanged(self.textSelection.currentIndex())

    def onVoiceVolumeChanged(self, value):
        pass

    def onVoiceSelectionChanged(self, index):
        is_stopped = (index == 5)
        self.voiceVolume.setVisible(not is_stopped)
        self.voiceVolumeLabel.setVisible(not is_stopped)

    def onTextSelectionChanged(self, index):
        is_stopped = (index == 5)
        self.textTypeSelection.setVisible(not is_stopped)
        self.textTypeLabel.setVisible(not is_stopped)
