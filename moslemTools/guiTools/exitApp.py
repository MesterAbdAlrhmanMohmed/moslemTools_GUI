import sys
import subprocess
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import app
from .QNavigableLabelAsTextEdit import QNavigableLabelAsTextEdit
if not isinstance(QNavigableLabelAsTextEdit, type):
    QNavigableLabelAsTextEdit = QNavigableLabelAsTextEdit.QNavigableLabelAsTextEdit
from .QPushButton import QPushButton
if not isinstance(QPushButton, type):
    QPushButton = QPushButton.QPushButton


class ExitApp(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        self.p = p
        self.cancel1 = False
        self.setMinimumSize(500, 200)
        self.resize(900, 350)
        self.setWindowTitle("خيارات تشغيل البرنامج")
        self.center()
        layout = qt.QVBoxLayout(self)
        content = (
            "خيارات تشغيل البرنامج:\n\n"
            "1. إيقاف تشغيل البرنامج:\n"
            "يُستخدم لإغلاق البرنامج تماماً وإنهاء كافة عملياته وإجراءاته.\n\n"
            "2. إخفاء البرنامج:\n"
            "يُستخدم إذا كنت تريد أن تظل الأذكار والأذان والإجراءات التي تعمل في الخلفية قيد التشغيل، مع عدم عرض نافذة البرنامج على الشاشة.\n\n"
            "3. إعادة تشغيل البرنامج:\n"
            "يُستخدم لإعادة تشغيل البرنامج في حالة اكتشاف أي أخطاء تتطلب إعادة التشغيل."
        )
        self.text_edit = QNavigableLabelAsTextEdit(content)
        layout.addWidget(self.text_edit)
        buttons_layout = qt.QHBoxLayout()
        self.btn_exit = QPushButton("إيقاف تشغيل البرنامج")
        self.btn_exit.setDefault(False)
        self.btn_exit.setAutoDefault(False)
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #8B1A1A;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #A02828;
            }
            QPushButton:pressed {
                background-color: #661010;
            }
        """)
        self.btn_exit.clicked.connect(self.on_exit)
        self.btn_hide = QPushButton("إخفاء البرنامج")
        self.btn_hide.setDefault(False)
        self.btn_hide.setAutoDefault(False)
        self.btn_hide.setStyleSheet("""
            QPushButton {
                background-color: #0056b3;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #003d80;
            }
            QPushButton:pressed {
                background-color: #002b5c;
            }
        """)
        self.btn_hide.clicked.connect(self.on_hide)
        self.btn_restart = QPushButton("إعادة تشغيل البرنامج")
        self.btn_restart.setDefault(False)
        self.btn_restart.setAutoDefault(False)
        self.btn_restart.setStyleSheet("""
            QPushButton {
                background-color: #006400;
                color: #e0e0e0;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #008000;
            }
            QPushButton:pressed {
                background-color: #004d00;
            }
        """)
        self.btn_restart.clicked.connect(self.on_restart)
        buttons_layout.addWidget(self.btn_exit)
        buttons_layout.addWidget(self.btn_hide)
        buttons_layout.addWidget(self.btn_restart)
        layout.addLayout(buttons_layout)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
        qt1.QShortcut("Alt+F4", self).activated.connect(self.reject)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def on_exit(self):
        app.exit = False
        app_instance = qt.QApplication.instance()
        if app_instance:
            app_instance.quit()
        import os
        os._exit(0)

    def on_hide(self):
        if self.p:
            self.p.hide()
            if hasattr(self.p, "show_action"):
                self.p.show_action.setText("إظهار البرنامج")
        self.accept()

    def on_restart(self):
        if hasattr(self.p, "restart_application"):
            self.p.restart_application()
        else:
            app.exit = False
            try:
                shared = qt2.QSharedMemory("com.MTC.moslemTools")
                shared.attach()
                shared.detach()
            except Exception:
                pass
            if getattr(sys, 'frozen', False):
                args = [sys.executable] + sys.argv[1:]
            else:
                args = [sys.executable] + sys.argv
            subprocess.Popen(args)
            app_instance = qt.QApplication.instance()
            if app_instance:
                app_instance.quit()
            import os
            os._exit(0)

    def on_back(self):
        self.cancel1 = True
        self.reject()

    def reject(self):
        self.cancel1 = True
        super().reject()
