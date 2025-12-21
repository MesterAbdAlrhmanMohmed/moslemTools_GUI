from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class QuranPlayerSettings(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""            
            QSpinBox, QLineEdit, QCheckBox, QLabel {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                font-size: 13px;
            }
        """)
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        times_layout = qt.QHBoxLayout()    
        self.times_laybol = qt.QLabel("عدد مرات تكرار الآيات")        
        self.times = qt.QSpinBox()
        self.times.setRange(1, 10)
        self.times.setValue(int(settings_handler.get("quranPlayer", "times")))
        self.times.setAccessibleName("عدد مرات تكرار الآيات")        
        self.times.setFixedWidth(80)                
        times_layout.addWidget(self.times)
        times_layout.addWidget(self.times_laybol)                
        times_layout.addStretch()        
        main_layout.addLayout(times_layout)        
        duration_layout = qt.QHBoxLayout()
        self.duration_laybol = qt.QLabel("مدة الانتظار بين التكرار بالثواني")
        self.duration_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)        
        self.duration = qt.QLineEdit()
        self.duration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.duration.setInputMask("999")
        self.duration.setText(settings_handler.get("quranPlayer", "duration"))
        self.duration.setAccessibleName("مدة الانتظار بين التكرار بالثواني")
        self.duration.setFixedWidth(80)        
        duration_layout.addWidget(self.duration)
        duration_layout.addWidget(self.duration_laybol)                
        duration_layout.addStretch()
        main_layout.addLayout(duration_layout)        
        self.replay = qt.QCheckBox("إعادة التشغيل بعد الانتهاء: في حالة اختيار التشغيل الى النهاية، أو من آية الى آية")        
        self.replay.setChecked(p.cbts(settings_handler.get("quranPlayer", "replay")))
        main_layout.addWidget(self.replay)                
        main_layout.addStretch()