import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler


class _SettingProxy:
    def __init__(self, getter):
        self._getter = getter

    def isChecked(self):
        return self._getter()


class SearchSettings(qt.QWidget):
    VIEWERS = [
        ("quran_search", "عارض القرآن الكريم"),
        ("researcher_search", "تبويبة الباحث في القرآن والأحاديث"),
        ("islamic_books_search", "عارض الكتب الإسلامية"),
    ]

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                min-height: 36px;
            }
            QCheckBox {
                font-size: 14px;
            }
        """)
        self._updating_ui = False
        self.settings_data = {
            "quran_search": {
                "ignore_tashkeel": settings_handler.get("quran_search", "ignore_tashkeel") != "False",
                "ignore_hamza": settings_handler.get("quran_search", "ignore_hamza") != "False",
                "ignore_symbols": settings_handler.get("quran_search", "ignore_symbols") != "False",
            },
            "researcher_search": {
                "ignore_tashkeel": settings_handler.get("researcher_search", "ignore_tashkeel") != "False",
                "ignore_hamza": settings_handler.get("researcher_search", "ignore_hamza") != "False",
                "ignore_symbols": settings_handler.get("researcher_search", "ignore_symbols") != "False",
            },
            "islamic_books_search": {
                "ignore_tashkeel": settings_handler.get("islamic_books_search", "ignore_tashkeel") != "False",
                "ignore_hamza": settings_handler.get("islamic_books_search", "ignore_hamza") != "False",
                "ignore_symbols": settings_handler.get("islamic_books_search", "ignore_symbols") != "False",
            },
        }

        self.quran_tashkeel_checkbox = _SettingProxy(lambda: self.settings_data["quran_search"]["ignore_tashkeel"])
        self.quran_hamza_checkbox = _SettingProxy(lambda: self.settings_data["quran_search"]["ignore_hamza"])
        self.quran_symbols_checkbox = _SettingProxy(lambda: self.settings_data["quran_search"]["ignore_symbols"])

        self.researcher_tashkeel_checkbox = _SettingProxy(lambda: self.settings_data["researcher_search"]["ignore_tashkeel"])
        self.researcher_hamza_checkbox = _SettingProxy(lambda: self.settings_data["researcher_search"]["ignore_hamza"])
        self.researcher_symbols_checkbox = _SettingProxy(lambda: self.settings_data["researcher_search"]["ignore_symbols"])

        self.islamic_books_tashkeel_checkbox = _SettingProxy(lambda: self.settings_data["islamic_books_search"]["ignore_tashkeel"])
        self.islamic_books_hamza_checkbox = _SettingProxy(lambda: self.settings_data["islamic_books_search"]["ignore_hamza"])
        self.islamic_books_symbols_checkbox = _SettingProxy(lambda: self.settings_data["islamic_books_search"]["ignore_symbols"])

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)

        viewer_layout = qt.QHBoxLayout()
        viewer_layout.setSpacing(10)
        viewer_layout.addStretch(1)

        self.viewer_combo = qt.QComboBox()
        self.viewer_combo.setFont(font)
        self.viewer_combo.setAccessibleName("تحديد العارض")
        for key, name in self.VIEWERS:
            self.viewer_combo.addItem(name, key)

        self.viewer_label = qt.QLabel("تحديد العارض:")
        self.viewer_label.setFont(font)
        self.viewer_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)

        viewer_layout.addWidget(self.viewer_combo)
        viewer_layout.addWidget(self.viewer_label)
        viewer_layout.addStretch(1)
        layout.addLayout(viewer_layout)
        layout.addSpacing(10)

        self.tashkeel_checkbox = qt.QCheckBox("تجاهل التشكيل")
        self.tashkeel_checkbox.setFont(font)
        self.tashkeel_checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.tashkeel_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.hamza_checkbox = qt.QCheckBox("تجاهل الهمزات")
        self.hamza_checkbox.setFont(font)
        self.hamza_checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.hamza_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.symbols_checkbox = qt.QCheckBox("تجاهل الرموز والعلامات")
        self.symbols_checkbox.setFont(font)
        self.symbols_checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.symbols_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        self.viewer_combo.currentIndexChanged.connect(self.on_viewer_changed)
        self.on_viewer_changed(0)
        self.adjust_combo_width()

    def adjust_combo_width(self, index=None):
        fm = self.viewer_combo.fontMetrics()
        current_text = self.viewer_combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        self.viewer_combo.setFixedWidth(text_width + 65)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_combo_width()

    def on_viewer_changed(self, index):
        self.adjust_combo_width()
        current_key = self.viewer_combo.currentData()
        if not current_key or current_key not in self.settings_data:
            return
        data = self.settings_data[current_key]
        self._updating_ui = True
        self.tashkeel_checkbox.setChecked(data["ignore_tashkeel"])
        self.hamza_checkbox.setChecked(data["ignore_hamza"])
        self.symbols_checkbox.setChecked(data["ignore_symbols"])
        self._updating_ui = False

    def on_checkbox_changed(self):
        if self._updating_ui:
            return
        current_key = self.viewer_combo.currentData()
        if not current_key or current_key not in self.settings_data:
            return
        self.settings_data[current_key]["ignore_tashkeel"] = self.tashkeel_checkbox.isChecked()
        self.settings_data[current_key]["ignore_hamza"] = self.hamza_checkbox.isChecked()
        self.settings_data[current_key]["ignore_symbols"] = self.symbols_checkbox.isChecked()
