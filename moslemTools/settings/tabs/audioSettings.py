import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QMediaDevices
import guiTools
class AudioSettings(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)        
        self.layout = qt.QVBoxLayout()
        self.setLayout(self.layout)        
        self.devices_list = ["الافتراضي"] + [d.description() for d in QMediaDevices.audioOutputs()]
        self.global_options = self.devices_list + ["مخصص"]                
        def create_row(label_text, combo_name, is_global=False):
            row_layout = qt.QHBoxLayout()
            label = qt.QLabel(label_text)
            combo = qt.QComboBox()
            combo.addItems(self.global_options if is_global else self.devices_list)
            combo.setAccessibleName(label_text)            
            row_layout.addWidget(combo)
            row_layout.addWidget(label)
            row_layout.addStretch()
            self.layout.addLayout(row_layout)
            return combo        
        self.global_combo = create_row("تحديد كارت الصوت لكل البرنامج", "global", is_global=True)
        self.global_combo.currentIndexChanged.connect(self.on_global_change)        
        self.features = {}                
        feature_map = [
            ("تحديد كارت الصوت لتشغيل الآيات في تبويبة القرآن الكريم مكتوب", "quran_text"),
            ("تحديد كارت الصوت لتشغيل السور في تبويبة القرآن الكريم صوتي", "quran_audio"),
            ("تحديد كارت الصوت لتشغيل القصص", "stories"),
            ("تحديد كارت الصوت لتشغيل الإذاعات الإسلامية", "broadcasts"),
            ("تحديد كارت الصوت لتشغيل الأذان وما يتعلق به", "adhan"),
            ("تحديد كارت الصوت لتشغيل الأذكار والأدعية", "athkar"),
            ("تحديد كارت الصوت لتشغيل الأذكار العشوائية والبسملة", "random_athkar"),
        ]
        for label, key in feature_map:
            combo = create_row(label, key)
            self.features[key] = combo                    
        self.note_label = qt.QLabel("لتغيير كارت الصوت لباقي العناصر، يرجى اختيار 'مخصص' من قائمة 'تحديد كارت الصوت لكل البرنامج'")
        self.note_label.setStyleSheet("color: gray; font-style: italic;")
        self.note_label.setVisible(False)
        self.layout.addWidget(self.note_label)        
        self.layout.addStretch()        
        self.load_settings()
    def load_settings(self):                
        from settings import settings_handler                
        global_val = settings_handler.get("audio", "global")
        if not global_val: global_val = "الافتراضي"        
        index = self.global_combo.findText(global_val)
        if index >= 0:
            self.global_combo.setCurrentIndex(index)
        else:
            self.global_combo.setCurrentIndex(0)        
        for key, combo in self.features.items():
            val = settings_handler.get("audio", key)
            if not val: val = "الافتراضي"
            index = combo.findText(val)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                combo.setCurrentIndex(0)                
        self.on_global_change(self.global_combo.currentIndex())
    def on_global_change(self, index):
        selected_text = self.global_combo.currentText()
        is_custom = selected_text == "مخصص" or selected_text == "Custom"        
        self.note_label.setVisible(not is_custom)        
        for combo in self.features.values():
            combo.setEnabled(is_custom)
            if not is_custom:                                                                
                pass