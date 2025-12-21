import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler
class FontSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: Arial;
            }
            QCheckBox, QLabel {
                font-size: 14px;
            }
            QSpinBox {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        main_layout = qt.QVBoxLayout(self)
        main_layout.addStretch()
        self.bold_checkbox = qt.QCheckBox("خط عريض (Bold)")
        self.bold_checkbox.setChecked(settings_handler.get("font", "bold") == "True")
        self.bold_checkbox.stateChanged.connect(self.update_checkbox_font)
        self.update_checkbox_font()
        main_layout.addWidget(self.bold_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(10)        
        font_size_layout = qt.QHBoxLayout()
        font_size_label = qt.QLabel("حجم الخط")
        self.font_size_spinbox = qt.QSpinBox()
        self.font_size_spinbox.setRange(1, 100)
        self.font_size_spinbox.setValue(int(settings_handler.get("font", "size")))
        self.font_size_spinbox.setFixedWidth(80)
        self.font_size_spinbox.setAccessibleName("حجم الخط")
        font_size_layout.addStretch()
        font_size_layout.addWidget(self.font_size_spinbox)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addStretch()    
        main_layout.addLayout(font_size_layout)                        
        main_layout.addStretch()        
        self.setLayout(main_layout)
    def update_checkbox_font(self):
        font = self.bold_checkbox.font()
        font.setBold(self.bold_checkbox.isChecked())
        self.bold_checkbox.setFont(font)