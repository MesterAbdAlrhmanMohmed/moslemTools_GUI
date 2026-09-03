from settings import settings_handler
from settings import app
import guiTools, gui, re
import win32com.client
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import os, shutil, sys
startUpPath = os.path.join(os.getenv('appdata'), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "moslemTools.lnk")


class Genral(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""
            QComboBox, QCheckBox {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
        main_layout = qt.QVBoxLayout(self)
        self.ExitDialog = qt.QCheckBox("عرض نافذة الخروج عند الخروج من البرنامج")
        self.ExitDialog.setChecked(p.cbts(settings_handler.get("g", "exitDialog")))
        main_layout.addWidget(self.ExitDialog)
        self.exit_note = guiTools.QNavigableLabel("في حالة إلغاء تحديد المربع أعلاه، سيقوم البرنامج بالإغلاق مباشرة دون عرض نافذة خيارات الخروج")
        main_layout.addWidget(self.exit_note)
        main_layout.addSpacing(18)
        self.startup = qt.QCheckBox("بدء تشغيل البرنامج عند بدء تشغيل النظام")
        self.startup.setChecked(self.check_in_startup())
        self.startup.stateChanged.connect(self.onStartupChanged)
        main_layout.addWidget(self.startup)
        main_layout.addSpacing(12)
        self.randomMessageAtStartup = qt.QCheckBox("عرض رسالة عشوائية لك عند فتح البرنامج")
        self.randomMessageAtStartup.setChecked(p.cbts(settings_handler.get("g", "randomMessageAtStartup")))
        main_layout.addWidget(self.randomMessageAtStartup)
        main_layout.addSpacing(18)
        self.current_theme = settings_handler.get("g", "theme") or "dark"
        self.themeButton = guiTools.QPushButton()
        self.update_theme_button_style()
        self.themeButton.clicked.connect(self.toggle_theme)
        main_layout.addWidget(self.themeButton)
        main_layout.addSpacing(22)

        self.tray_note = guiTools.QNavigableLabel("تنبيه هام، يمكنكم إظهار أو إخفاء البرنامج عبر استخدام الاختصار windows+alt+h أو من قائمة علبة النظام system tray")
        self.tray_note.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.tray_note.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.tray_note)
        main_layout.addSpacing(8)
        self.run_note = guiTools.QNavigableLabel("تنبيه هام، يمكنكم تشغيل البرنامج من قائمة run بكتابة الأمر (mt) أو الاختصار (ctrl+alt+m)")
        self.run_note.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.run_note.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.run_note)
        main_layout.addStretch(1)

    def add_to_startup(self):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(startUpPath)
            shortcut.TargetPath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.Description = "a shortcut for opening moslem tools when windows start"
            shortcut.Save()
        except Exception as e:
            print(e)
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر إتمام العملية")

    def check_in_startup(self):
        try:
            return os.path.exists(startUpPath)
        except Exception as e:
            return False

    def remove_from_startup(self):
        try:
            os.remove(startUpPath)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر إتمام العملية")

    def onStartupChanged(self, value):
        if self.check_in_startup():
            self.remove_from_startup()
        else:
            self.add_to_startup()


    def update_theme_button_style(self):
        if self.current_theme == "light":
            self.themeButton.setText("تفعيل الوضع الداكن")
            self.themeButton.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-weight: bold; border-radius: 6px; padding: 10px;")
        else:
            self.themeButton.setText("تفعيل الوضع الفاتح")
            self.themeButton.setStyleSheet("background-color: #ffffff; color: #1e1e1e; font-weight: bold; border-radius: 6px; padding: 10px;")

    def toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        settings_handler.set("g", "theme", new_theme)
        self.current_theme = new_theme
        self.update_theme_button_style()
        mb = guiTools.QQuestionMessageBox.view(self, "إعادة تشغيل البرنامج", "تم تغيير نمط الواجهة. يجب إعادة تشغيل البرنامج لتطبيق التغيير. هل تريد إعادة التشغيل الآن؟", "إعادة التشغيل الآن", "إعادة التشغيل لاحقاً")
        if mb == 0:
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit()
