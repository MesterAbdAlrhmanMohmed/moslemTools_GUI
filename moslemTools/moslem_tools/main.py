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
    App.setStyle('Fusion')
    current_theme = settings_handler.get("g", "theme") or "dark"
    if current_theme == "light":
        light_palette = qt1.QPalette()
        light_palette.setColor(qt1.QPalette.ColorRole.Window, qt1.QColor("#F5F5F5"))
        light_palette.setColor(qt1.QPalette.ColorRole.WindowText, qt1.QColor("#1E1E1E"))
        light_palette.setColor(qt1.QPalette.ColorRole.Base, qt1.QColor("#FFFFFF"))
        light_palette.setColor(qt1.QPalette.ColorRole.AlternateBase, qt1.QColor("#E5E5E5"))
        light_palette.setColor(qt1.QPalette.ColorRole.ToolTipBase, qt1.QColor("#FFFFFF"))
        light_palette.setColor(qt1.QPalette.ColorRole.ToolTipText, qt1.QColor("#1E1E1E"))
        light_palette.setColor(qt1.QPalette.ColorRole.Text, qt1.QColor("#1E1E1E"))
        light_palette.setColor(qt1.QPalette.ColorRole.Button, qt1.QColor("#E0E0E0"))
        light_palette.setColor(qt1.QPalette.ColorRole.ButtonText, qt1.QColor("#1E1E1E"))
        light_palette.setColor(qt1.QPalette.ColorRole.BrightText, qt1.QColor("#FF0000"))
        light_palette.setColor(qt1.QPalette.ColorRole.Highlight, qt1.QColor("#0078D7"))
        light_palette.setColor(qt1.QPalette.ColorRole.HighlightedText, qt1.QColor("#FFFFFF"))
        App.setPalette(light_palette)
    else:
        dark_palette = qt1.QPalette()
        dark_palette.setColor(qt1.QPalette.ColorRole.Window, qt1.QColor("121212"))
        dark_palette.setColor(qt1.QPalette.ColorRole.WindowText, qt1.QColor("#E0E0E0"))
        dark_palette.setColor(qt1.QPalette.ColorRole.Base, qt1.QColor("#1E1E1E"))
        dark_palette.setColor(qt1.QPalette.ColorRole.AlternateBase, qt1.QColor("#2C2C2C"))
        dark_palette.setColor(qt1.QPalette.ColorRole.ToolTipBase, qt1.QColor("#2C2C2C"))
        dark_palette.setColor(qt1.QPalette.ColorRole.ToolTipText, qt1.QColor("#E0E0E0"))
        dark_palette.setColor(qt1.QPalette.ColorRole.Text, qt1.QColor("#E0E0E0"))
        dark_palette.setColor(qt1.QPalette.ColorRole.Button, qt1.QColor("#2C2C2C"))
        dark_palette.setColor(qt1.QPalette.ColorRole.ButtonText, qt1.QColor("#E0E0E0"))
        dark_palette.setColor(qt1.QPalette.ColorRole.BrightText, qt1.QColor("#FF0000"))
        dark_palette.setColor(qt1.QPalette.ColorRole.Highlight, qt1.QColor("#3A9FF5"))
        dark_palette.setColor(qt1.QPalette.ColorRole.HighlightedText, qt1.QColor("#000000"))
        App.setPalette(dark_palette)
    shown = run_startup_checks()
    shared = qt2.QSharedMemory("com.MTC.moslemTools")
    window = main(shown)
    if shared.attach() or not shared.create(1):
        guiTools.qMessageBox.MessageBox.error(window, "تنبيه", "البرنامج يعمل بالفعل\nلإظهار البرنامج نستخدم الاختصار windows + alt + h أو نقوم بإظهاره من قائمة علبة النظان system tray")
        sys.exit(0)
    App.aboutToQuit.connect(lambda: shared.detach())
    window.show()
    sys.exit(App.exec())


if __name__ == "__main__":
    main_app()
