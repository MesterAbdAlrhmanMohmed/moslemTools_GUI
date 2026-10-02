from custom_errors import *
import sys
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools
from settings import settings_handler, app
from .main_window import main
from .startup_checks import run_startup_checks


def main_app():
    App = qt.QApplication(sys.argv)
    default_font = qt1.QFont()
    default_font.setBold(True)
    App.setFont(default_font)
    App.setApplicationDisplayName(app.name)
    App.setApplicationName(app.name)
    App.setApplicationVersion(str(app.version))
    App.setOrganizationName(app.creater)
    App.setWindowIcon(qt1.QIcon("data/icons/app_icon.ico"))
    guiTools.theme.apply_theme(App)
    shown = run_startup_checks()
    shared = qt2.QSharedMemory("com.MTC.moslemTools")
    window = main(shown)
    if shared.attach() or not shared.create(1):
        guiTools.qMessageBox.MessageBox.error(window, "تنبيه", "البرنامج يعمل بالفعل\nلإظهار البرنامج نستخدم الاختصار windows + alt + h أو نقوم بإظهاره من قائمة علبة النظان system tray")
        sys.exit(0)
    App.shared_memory = shared
    App.aboutToQuit.connect(lambda: shared.detach())
    window.show()
    window.more_options_button.setFocus()
    sys.exit(App.exec())


if __name__ == "__main__":
    main_app()
