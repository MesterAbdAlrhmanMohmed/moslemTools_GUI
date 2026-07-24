import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler

class ResearcherSearchSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)
        self.tashkeel_checkbox = qt.QCheckBox("تجاهل التشكيل")
        self.tashkeel_checkbox.setFont(font)
        self.tashkeel_checkbox.setChecked(settings_handler.get("researcher_search", "ignore_tashkeel") != "False")
        layout.addWidget(self.tashkeel_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.hamza_checkbox = qt.QCheckBox("تجاهل الهمزات")
        self.hamza_checkbox.setFont(font)
        self.hamza_checkbox.setChecked(settings_handler.get("researcher_search", "ignore_hamza") != "False")
        layout.addWidget(self.hamza_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.symbols_checkbox = qt.QCheckBox("تجاهل الرموز والعلامات")
        self.symbols_checkbox.setFont(font)
        self.symbols_checkbox.setChecked(settings_handler.get("researcher_search", "ignore_symbols") != "False")
        layout.addWidget(self.symbols_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
