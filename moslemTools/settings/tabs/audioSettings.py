import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QMediaDevices
import guiTools


class AudioSettings(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = qt.QVBoxLayout()
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QComboBox {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        self.devices_list = ["افتراضي"] + [d.description() for d in QMediaDevices.audioOutputs()]
        self.global_options = self.devices_list + ["مخصص"]
        self.feature_widgets = []
        self.features = {}
        def create_row(label_text, combo_name, is_global=False):
            container = qt.QWidget()
            row_layout = qt.QHBoxLayout(container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)
            label = qt.QLabel(label_text)
            combo = qt.QComboBox()
            combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo.addItems(self.global_options if is_global else self.devices_list)
            combo.setAccessibleName(label_text)
            fm = combo.fontMetrics()
            items = self.global_options if is_global else self.devices_list
            max_w = max([fm.horizontalAdvance(text) for text in items], default=100)
            combo.setMinimumWidth(max_w + 35)
            row_layout.addWidget(combo)
            row_layout.addWidget(label)
            row_layout.addStretch()
            self.layout.addWidget(container)
            if not is_global:
                self.feature_widgets.append(container)
            return combo
        self.global_combo = create_row("تحديد كرت الصوت لكل البرنامج", "global", is_global=True)
        self.global_combo.currentIndexChanged.connect(self.on_global_change)
        feature_map = [
            ("تحديد كرت الصوت لتشغيل الآيات في عارض القرآن الكريم", "quran_viewer"),
            ("تحديد كرت الصوت لتشغيل الآيات في مشغل القرآن الكريم", "quran_player"),
            ("تحديد كرت الصوت لتشغيل السور في تبويبة القرآن الكريم صوتي", "quran_audio"),
            ("تحديد كرت الصوت لتشغيل الآيات في الباحث", "researcher"),
            ("تحديد كرت الصوت لتشغيل الإذاعات الإسلامية", "broadcasts"),
            ("تحديد كرت الصوت لتشغيل الأذان وما يتعلق به", "adhan"),
            ("تحديد كرت الصوت لتشغيل الأذكار والأدعية", "athkar"),
            ("تحديد كرت الصوت لتشغيل الأذكار العشوائية والبسملة", "random_athkar"),
            ("تحديد كرت الصوت لتشغيل الأبيات في عارض المتون", "moton_viewer"),
            ("تحديد كرت الصوت لتشغيل الأبيات في مشغل المتون", "moton_player"),
        ]
        for label, key in feature_map:
            combo = create_row(label, key)
            self.features[key] = combo
        self.note_label = qt.QLabel("لتغيير كرت الصوت لباقي العناصر، يرجى اختيار 'مخصص' من قائمة 'تحديد كرت الصوت لكل البرنامج'")
        self.note_label.setStyleSheet("color: gray; font-style: italic;")
        self.note_label.setVisible(False)
        self.layout.addWidget(self.note_label)
        self.layout.addStretch()
        self.load_settings()

    def load_settings(self):
        from settings import settings_handler
        global_val = settings_handler.get("audio", "global")
        if not global_val or global_val == "Default" or global_val == "الافتراضي": global_val = "افتراضي"
        if global_val == "Custom": global_val = "مخصص"
        index = self.global_combo.findText(global_val)
        if index >= 0:
            self.global_combo.setCurrentIndex(index)
        else:
            self.global_combo.setCurrentIndex(0)
        for key, combo in self.features.items():
            val = settings_handler.get("audio", key)
            if not val and key in ["quran_viewer", "quran_player"]:
                val = settings_handler.get("audio", "quran_text")
            if not val and key in ["moton_viewer", "moton_player"]:
                val = settings_handler.get("audio", "moton")
            if not val or val == "Default" or val == "الافتراضي": val = "افتراضي"
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
        for widget in self.feature_widgets:
            widget.setVisible(is_custom)
