import update
from settings import settings_handler
import PyQt6.QtWidgets as qt


class Update(qt.QWidget):
    def __init__(self, p):
        super().__init__()

        UpdateLayout = qt.QVBoxLayout(self)
        UpdateLayout.setSpacing(0)
        UpdateLayout.setContentsMargins(0, 0, 0, 0)
        self.update_autoDect = qt.QCheckBox("تحقق تلقائيًا من التحديثات عند بدء البرنامج")
        self.update_autoDect.setChecked(p.cbts(settings_handler.get("update", "autoCheck")))
        UpdateLayout.addWidget(self.update_autoDect)
        self.update_beta = qt.QCheckBox("تحميل التحديثات التجريبية")
        self.update_beta.setChecked(p.cbts(settings_handler.get("update", "beta")))
        UpdateLayout.addWidget(self.update_beta)
        UpdateLayout.addSpacing(10)
        button_layout = qt.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.update_check = qt.QPushButton("التحقق من وجود تحديثات")
        self.update_check.setStyleSheet("""
            QPushButton {
                background-color: #0056b3;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #004085;
            }
            QPushButton:pressed {
                background-color: #002752;
            }
        """)
        self.update_check.clicked.connect(lambda: update.check(self))
        button_layout.addStretch()
        button_layout.addWidget(self.update_check)
        button_layout.addStretch()
        UpdateLayout.addLayout(button_layout)
        UpdateLayout.addStretch()
