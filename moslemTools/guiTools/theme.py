import os
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_TABS_DIR = os.path.join(BASE_DIR, "data", "icons", "tabs")
ICONS_SETTINGS_DIR = os.path.join(BASE_DIR, "data", "icons", "settings")

TAB_ICONS_MAP = {
    "مواقيت الصلاة والتاريخ": "prayer_times.png",
    "القرآن الكريم مكتوب": "quran_read.png",
    "القرآن الكريم صوتي": "quran_listen.png",
    "متابع الختمة القرآنية": "khatmah.png",
    "الأحاديث النبوية والقدسية": "hadith.png",
    "الباحث في القرآن والأحاديث": "search.png",
    "اسأل الذكاء الاصطناعي": "ai_chat.png",
    "لعبة الأسئلة الإسلامية": "questions_game.png",
    "الكتب الإسلامية": "islamic_books.png",
    "المتون الإسلامية": "islamic_moton.png",
    "إذاعات الراديو الإسلامية": "broadcasts.png",
    "الأذكار والأدعية": "athkar.png",
    "السبحة الإلكترونية": "sibha.png",
    "أسماء الله الحُسْنى": "names_of_allah.png",
    "القصص الإسلامية": "prophet_stories.png",
    "مواضيع إسلامية مختلفة": "islamic_topics.png",
    "محول التاريخ": "date_converter.png",
    "المزيد من الخيارات": "more_options.png"
}

SETTINGS_SECTION_ICONS_MAP = {
    "الإعدادات الأساسية": "sec_basic.png",
    "إعدادات تبويبات البرنامج": "sec_tabs.png",
    "إعدادات العارضات": "sec_viewers.png",
    "إعدادات التذكيرات والأذكار": "sec_reminders.png",
    "إعدادات الأذان ومواقيت الصلاة": "sec_prayer.png",
    "إعدادات تبويبة القرآن الكريم مكتوب": "sec_quran.png",
    "إعدادات تبويبة المتون الإسلامية": "sec_moton.png",
    "إعدادات التحديث والبيانات": "sec_data.png"
}

SETTINGS_ITEM_ICONS_MAP = {
    "الإعدادات العامة": "general.png",
    "إعدادات تبويبة بدء التشغيل": "startup.png",
    "إعدادات إخفاء وإظهار التبويبات": "hidden_tabs.png",
    "إعدادات ترتيب تبويبات البرنامج": "tabs_order.png",
    "إعدادات ترتيب التبويبات": "tabs_order.png",
    "إعدادات التذكير بالمناسبات واسم المستخدم": "user_name.png",
    "إعدادات نوع الخط وحجمه للعارضات": "font.png",
    "إعدادات نوع الخط وحجمه": "font.png",
    "إعدادات صوت تقليب الصفحات في العارضات": "page_sound.png",
    "إعدادات صوت تقليب الصفحات": "page_sound.png",
    "إعدادات التذكير بالورد اليومي": "khatmah_reminder.png",
    "إعدادات تحديد الموقع الجغرافي لمواقيت الصلاة": "location.png",
    "إعدادات تحديد الموقع الجغرافي": "location.png",
    "إعدادات الأذان": "adhan.png",
    "إعدادات اختيار قارئ القرآن آية بآية": "quran_reciters.png",
    "إعدادات التفسير والترجمة لتبويبة القرآن الكريم مكتوب": "tafaseer.png",
    "إعدادات التفسير والترجمة": "tafaseer.png",
    "إعدادات مشغل القرآن لتبويبة القرآن الكريم مكتوب": "quran_player.png",
    "إعدادات مشغل القرآن": "quran_player.png",
    "إعدادات عرض الآيات في عارض القرآن الكريم": "quran_display.png",
    "إعدادات عرض الآيات": "quran_display.png",
    "إعدادات البحث": "search.png",
    "إعدادات اختيار القارئ للمتون الإسلامية": "moton_reciters.png",
    "إعدادات اختيار القارئ": "moton_reciters.png",
    "إعدادات مشغل المتون الإسلامية": "moton_player.png",
    "إعدادات مشغل المتون": "moton_player.png",
    "إعدادات عرض الأبيات في عارض المتون الإسلامية": "moton_display.png",
    "إعدادات عرض الأبيات": "moton_display.png",
    "إعدادات الأذكار العشوائية": "athkar.png",
    "إعدادات فنار (الذكاء الاصطناعي)": "fanar.png",
    "إعدادات تحديد كرت الصوت": "audio.png",
    "إعدادات التحديثات": "update.png",
    "تحميل موارد": "download.png",
    "النسخ الاحتياطي والاستعادة": "backup.png"
}

_icon_cache = {}

def get_tab_icon(name):
    filename = TAB_ICONS_MAP.get(name)
    if not filename:
        return qt1.QIcon()
    if filename in _icon_cache:
        return _icon_cache[filename]
    path = os.path.join(ICONS_TABS_DIR, filename)
    icon = qt1.QIcon(path) if os.path.exists(path) else qt1.QIcon()
    _icon_cache[filename] = icon
    return icon

def get_settings_section_icon(name):
    filename = SETTINGS_SECTION_ICONS_MAP.get(name)
    if not filename:
        return qt1.QIcon()
    cache_key = f"sec_{filename}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    path = os.path.join(ICONS_SETTINGS_DIR, filename)
    icon = qt1.QIcon(path) if os.path.exists(path) else qt1.QIcon()
    _icon_cache[cache_key] = icon
    return icon

def get_settings_item_icon(name):
    filename = SETTINGS_ITEM_ICONS_MAP.get(name)
    if not filename:
        return qt1.QIcon()
    cache_key = f"item_{filename}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    path = os.path.join(ICONS_SETTINGS_DIR, filename)
    icon = qt1.QIcon(path) if os.path.exists(path) else qt1.QIcon()
    _icon_cache[cache_key] = icon
    return icon

def get_theme_palette(theme_name):
    if theme_name == "light":
        palette = qt1.QPalette()
        palette.setColor(qt1.QPalette.ColorRole.Window, qt1.QColor("#f3f3f3"))
        palette.setColor(qt1.QPalette.ColorRole.WindowText, qt1.QColor("#1f1f1f"))
        palette.setColor(qt1.QPalette.ColorRole.Base, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.AlternateBase, qt1.QColor("#f8f8f8"))
        palette.setColor(qt1.QPalette.ColorRole.ToolTipBase, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.ToolTipText, qt1.QColor("#1f1f1f"))
        palette.setColor(qt1.QPalette.ColorRole.Text, qt1.QColor("#1f1f1f"))
        palette.setColor(qt1.QPalette.ColorRole.Button, qt1.QColor("#fbfbfb"))
        palette.setColor(qt1.QPalette.ColorRole.ButtonText, qt1.QColor("#1f1f1f"))
        palette.setColor(qt1.QPalette.ColorRole.BrightText, qt1.QColor("#c42b1c"))
        palette.setColor(qt1.QPalette.ColorRole.Highlight, qt1.QColor("#0056b3"))
        palette.setColor(qt1.QPalette.ColorRole.HighlightedText, qt1.QColor("#ffffff"))
        return palette
    else:
        palette = qt1.QPalette()
        palette.setColor(qt1.QPalette.ColorRole.Window, qt1.QColor("#121212"))
        palette.setColor(qt1.QPalette.ColorRole.WindowText, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.Base, qt1.QColor("#181818"))
        palette.setColor(qt1.QPalette.ColorRole.AlternateBase, qt1.QColor("#1f1f1f"))
        palette.setColor(qt1.QPalette.ColorRole.ToolTipBase, qt1.QColor("#1c1c1c"))
        palette.setColor(qt1.QPalette.ColorRole.ToolTipText, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.Text, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.Button, qt1.QColor("#252525"))
        palette.setColor(qt1.QPalette.ColorRole.ButtonText, qt1.QColor("#ffffff"))
        palette.setColor(qt1.QPalette.ColorRole.BrightText, qt1.QColor("#ff4d4f"))
        palette.setColor(qt1.QPalette.ColorRole.Highlight, qt1.QColor("#0056b3"))
        palette.setColor(qt1.QPalette.ColorRole.HighlightedText, qt1.QColor("#ffffff"))
        return palette

def get_theme_stylesheet(theme_name):
    if theme_name == "light":
        return """
            * {
                font-family: "Segoe UI Variable Text", "Segoe UI", "Tajawal", "Cairo", Arial, sans-serif;
            }
            QMainWindow, QDialog {
                background-color: #f3f3f3;
                color: #1f1f1f;
            }
            QWidget {
                color: #1f1f1f;
            }
            QPushButton {
                background-color: #fbfbfb;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: bold;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #b5b5b5;
            }
            QPushButton:pressed {
                background-color: #e5e5e5;
                border-color: #999999;
            }
            QPushButton:focus {
                border: 1px solid #777777;
            }
            QPushButton:disabled {
                background-color: #f3f3f3;
                color: #9e9e9e;
                border-color: #e5e5e5;
            }
            QPushButton#moreOptionsButton {
                background-color: #0056b3;
                color: #ffffff;
                border: 1px solid #004494;
            }
            QPushButton#moreOptionsButton:hover {
                background-color: #004085;
                border-color: #004085;
            }
            QPushButton#moreOptionsButton:pressed {
                background-color: #002752;
                border-color: #002752;
            }
            QComboBox {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                min-height: 24px;
            }
            QComboBox:hover {
                background-color: #fcfcfc;
                border-color: #a8a8a8;
            }
            QComboBox:focus {
                border: 2px solid #0056b3;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #555555;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #0056b3;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #0056b3;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QListWidget {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                margin: 2px 2px;
                border-radius: 6px;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #eaeaea;
                color: #1f1f1f;
            }
            QListWidget::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
                padding: 6px 10px;
                selection-background-color: #0056b3;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #0056b3;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 9px;
                margin: 2px 0 2px 0;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9e9e9e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 9px;
                margin: 0 2px 0 2px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #9e9e9e;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
            QTabWidget::pane {
                border: 1px solid #d1d1d1;
                border-radius: 8px;
                background-color: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #eaeaea;
                color: #4b4b4b;
                padding: 9px 20px;
                border: 1px solid #d1d1d1;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 3px;
                font-weight: bold;
                min-width: 90px;
            }
            QTabBar::tab:hover {
                background: #f2f2f2;
                color: #1f1f1f;
            }
            QTabBar::tab:selected {
                background: #0056b3;
                color: #ffffff;
                border-color: #0056b3;
            }
            QMenu {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 8px;
                padding: 6px 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QMenu::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #e5e5e5;
                margin: 4px 8px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #d1d1d1;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0056b3;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0056b3;
                border: 2px solid #ffffff;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #004085;
            }
            QGroupBox {
                border: 1px solid #d1d1d1;
                border-radius: 8px;
                margin-top: 14px;
                padding: 14px 10px 10px 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
                color: #0056b3;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #0056b3;
            }
            QCheckBox::indicator:checked {
                background-color: #0056b3;
                border-color: #0056b3;
                image: none;
            }
            QToolTip {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
                padding: 5px 8px;
            }
        """
    else:
        return """
            * {
                font-family: "Segoe UI Variable Text", "Segoe UI", "Tajawal", "Cairo", Arial, sans-serif;
            }
            QMainWindow, QDialog {
                background-color: #121212;
                color: #ffffff;
            }
            QWidget {
                color: #ffffff;
            }
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #383838;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: bold;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #323232;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
                border-color: #2a2a2a;
            }
            QPushButton:focus {
                border: 1px solid #555555;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border-color: #282828;
            }
            QPushButton#moreOptionsButton {
                background-color: #0056b3;
                color: #ffffff;
                border: 1px solid #004494;
            }
            QPushButton#moreOptionsButton:hover {
                background-color: #004085;
                border-color: #004085;
            }
            QPushButton#moreOptionsButton:pressed {
                background-color: #002752;
                border-color: #002752;
            }
            QComboBox {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #383838;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                min-height: 24px;
            }
            QComboBox:hover {
                background-color: #2d2d2d;
                border-color: #4a4a4a;
            }
            QComboBox:focus {
                border: 2px solid #0056b3;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cccccc;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #383838;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #0056b3;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #0056b3;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QListWidget {
                background-color: #181818;
                color: #ffffff;
                border: 1px solid #2c2c2c;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                margin: 2px 2px;
                border-radius: 6px;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #262626;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #181818;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 10px;
                selection-background-color: #0056b3;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #0056b3;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 9px;
                margin: 2px 0 2px 0;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 9px;
                margin: 0 2px 0 2px;
            }
            QScrollBar::handle:horizontal {
                background: #333333;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
            QTabWidget::pane {
                border: 1px solid #2c2c2c;
                border-radius: 8px;
                background-color: #181818;
                top: -1px;
            }
            QTabBar::tab {
                background: #202020;
                color: #cccccc;
                padding: 9px 20px;
                border: 1px solid #2c2c2c;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 3px;
                font-weight: bold;
                min-width: 90px;
            }
            QTabBar::tab:hover {
                background: #2a2a2a;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background: #0056b3;
                color: #ffffff;
                border-color: #0056b3;
            }
            QMenu {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #303030;
                border-radius: 8px;
                padding: 6px 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QMenu::item:selected {
                background-color: #0056b3;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #2c2c2c;
                margin: 4px 8px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #2e2e2e;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0056b3;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #0056b3;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
                border-color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #2c2c2c;
                border-radius: 8px;
                margin-top: 14px;
                padding: 14px 10px 10px 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
                color: #5ba2e6;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #444444;
                border-radius: 4px;
                background-color: #252525;
            }
            QCheckBox::indicator:hover {
                border-color: #0056b3;
            }
            QCheckBox::indicator:checked {
                background-color: #0056b3;
                border-color: #0056b3;
                image: none;
            }
            QToolTip {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 5px 8px;
            }
        """

def apply_theme(app, theme_name=None):
    if theme_name is None:
        from settings import settings_handler
        theme_name = settings_handler.get("g", "theme") or "dark"
    app.setStyle("Fusion")
    palette = get_theme_palette(theme_name)
    app.setPalette(palette)
    stylesheet = get_theme_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
