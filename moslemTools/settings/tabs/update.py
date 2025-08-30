import update,guiTools
from settings import settings_handler
import PyQt6.QtWidgets as qt
class Update(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""            
            }
            QCheckBox {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
                margin: 0; /* إزالة الهوامش الخارجية */
            }
            QPushButton {
                background-color: #0000AA; /* اللون الأزرق من شاشة الموت */
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 8px 20px;
                margin: 0; /* إزالة الهوامش الخارجية */
                border-radius: 4px;
                font-size: 14px;
            }
        """)                
        UpdateLayout = qt.QVBoxLayout(self)        
        UpdateLayout.setSpacing(0)
        UpdateLayout.setContentsMargins(0, 0, 0, 0)                
        self.update_autoDect = qt.QCheckBox("تحقق تلقائيًا من التحديثات عند بدء البرنامج")
        self.update_autoDect.setChecked(p.cbts(settings_handler.get("update", "autoCheck")))
        UpdateLayout.addWidget(self.update_autoDect)        
        self.update_beta = qt.QCheckBox("تحميل التحديثات التجريبية")
        self.update_beta.setChecked(p.cbts(settings_handler.get("update", "beta")))
        UpdateLayout.addWidget(self.update_beta)                        
        button_container = qt.QWidget()
        button_layout = qt.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)        
        self.update_check = qt.QPushButton("التحقق من وجود تحديثات")
        self.update_check.clicked.connect(lambda: update.check(self))
        button_layout.addStretch()
        button_layout.addWidget(self.update_check)                
        UpdateLayout.addWidget(button_container)