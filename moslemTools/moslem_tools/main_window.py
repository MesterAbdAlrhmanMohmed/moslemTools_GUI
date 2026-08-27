from custom_errors import *
import sys, traceback, threading, random, os, shutil, datetime, webbrowser, requests, pyperclip, winsound, ctypes
from ctypes import wintypes
import ujson as json
from pynput import keyboard as p_key
from hijridate import Gregorian
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from appTabs import *
from functions import audio_manager
import guiTools
import update
from .display_name import get_smart_display_name
from .workers import MessageCheckWorker
from .athkar_mixin import AthkarMixin
from .khatmah_mixin import KhatmahMixin
from .messages_mixin import MessagesMixin
from .window_events_mixin import WindowEventsMixin


class main(AthkarMixin, KhatmahMixin, MessagesMixin, WindowEventsMixin, qt.QMainWindow):
    audio_sig = qt2.pyqtSignal()
    text_sig = qt2.pyqtSignal()
    toggle_sig = qt2.pyqtSignal()

    def __init__(self, startup_window_shown=False):
        super().__init__()
        self.setWindowTitle(app.name + "الإصدار:" + str(app.version))
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.setWindowFlags(qt2.Qt.WindowType.Window | qt2.Qt.WindowType.WindowCloseButtonHint | qt2.Qt.WindowType.CustomizeWindowHint)
        self.audio_sig.connect(self.random_audio_theker)
        self.text_sig.connect(self.show_random_theker)
        self.toggle_sig.connect(self.toggle_visibility)
        self.hk_listener = p_key.GlobalHotKeys({'<alt>+<cmd>+p': self.audio_sig.emit, '<alt>+<cmd>+l': self.text_sig.emit, '<cmd>+<alt>+h': self.toggle_sig.emit})
        self.hk_listener.start()
        self.info_update_timer = qt2.QTimer(self)
        self.info_update_timer.timeout.connect(self.viewInfoTextEdit)
        self.info_update_timer.start(90000)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(int(settings_handler.get("athkar", "voiceVolume")) / 100)
        self.media_player.setAudioOutput(self.audio_output)
        self.timer = qt2.QTimer(self)
        self.timer.timeout.connect(self.random_audio_theker)
        layout = qt.QVBoxLayout()
        self.info = guiTools.QNavigableLabel()
        font1=qt1.QFont()
        font1.setBold(True)
        self.info.setFont(font1)
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout1=qt.QHBoxLayout()
        layout2=qt.QVBoxLayout()
        layout.addLayout(layout1)
        layout1.addLayout(layout2)
        self.viewInfoTextEdit()
        self.list_widget = guiTools.ComboBook()
        self.list_widget.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.list_widget.setMinimumHeight(40)
        font = qt1.QFont()
        font.setBold(True)
        self.list_widget.setFont(font)
        self.list_widget.setAccessibleDescription("يمكنكم التنقل بين التبويبات باستخدام control plus tab و control plus shift plus tab، ويمكنكم فتح قائمة التبويبات من أي مكان باستخدام الاختصار control plus 0")
        self.list_widget.currentIndexChanged.connect(lambda idx: self.onToolChanged(None, None))
        self.quranPlayer = QuranPlayer()
        self.researcher = Albaheth()
        self.askAI = AskAI()
        tabs = [
    (prayer_times(self), "مواقيت الصلاة والتاريخ"),
    (Quran(), "القرآن الكريم مكتوب"),
    (self.quranPlayer, "القرآن الكريم صوتي"),
    (KhatmahTab(self), "متابع الختمة القرآنية"),
    (hadeeth(), "الأحاديث النبوية والقدسية"),
    (self.researcher, "الباحث في القرآن والأحاديث"),
    (self.askAI, "اسأل الذكاء الاصطناعي"),
    (IslamicQuestionsGame(), "لعبة الأسئلة الإسلامية"),
    (IslamicBooks(), "الكتب الإسلامية"),
    (protcasts(), "إذاعات الراديو الإسلامية"),
    (Athker(), "الأذكار والأدعية"),
    (sibha(), "السبحة الإلكترونية"),
    (NamesOfAllah(), "أسماء الله الحُسْنى"),
    (ProphetStories(), "القصص الإسلامية"),
    (IslamicTopicsTab(), "مواضيع إسلامية مختلفة"),
    (DateConverter(), "محول التاريخ"),
]
        for widget_class, label in tabs:
            scroll = qt.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(qt.QFrame.Shape.NoFrame)
            scroll.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
            scroll.horizontalScrollBar().setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
            scroll.verticalScrollBar().setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
            scroll.setWidget(widget_class)
            self.list_widget.add(label, scroll)
        try:
            start_tab = int(settings_handler.get("g", "startup_tab"))
            if 0 <= start_tab < self.list_widget.count():
                self.list_widget.setCurrentIndex(start_tab)
            else:
                self.list_widget.setCurrentIndex(0)
        except Exception:
            self.list_widget.setCurrentIndex(0)
        self.adjust_list_widget_width()
        self.list_widget.currentIndexChanged.connect(self.adjust_list_widget_width)
        layout.addWidget(self.list_widget.w, 1)
        qt1.QShortcut("ctrl+0", self).activated.connect(lambda: (self.list_widget.setFocus(), self.list_widget.showPopup()))
        self.more_options_button = qt.QPushButton("المزيد من الخيارات")
        self.more_options_button.setShortcut("ctrl+o")
        self.more_options_button.setAccessibleDescription("control plus o")
        self.more_options_button.setDefault(True)
        self.more_options_button.setStyleSheet("background-color: black; color: white;")
        fm_opts = qt1.QFontMetrics(font)
        opts_text_width = fm_opts.horizontalAdvance("المزيد من الخيارات") if hasattr(fm_opts, 'horizontalAdvance') else fm_opts.boundingRect("المزيد من الخيارات").width()
        self.more_options_button.setFixedWidth(opts_text_width + 45)
        self.more_options_button.setMinimumHeight(40)
        self.more_options_button.setFont(font)
        self.moreOptionsMenu = guiTools.QCustomContextMenu(self)
        self.moreOptionsMenu.setFont(font)
        self.moreOptionsMenu.setAccessibleName("المزيد من الخيارات")
        action_settings = qt1.QAction("الإعدادات", self)
        action_settings.setShortcut("f1")
        action_settings.triggered.connect(lambda: settings(self).exec())
        self.moreOptionsMenu.addAction(action_settings)
        bookmarks_notes_menu = guiTools.QCustomContextMenu("العلامات والملاحظات", self)
        bookmarks_notes_menu.setFont(font)
        action_bookMark = qt1.QAction("العلامات المرجعية", self)
        action_bookMark.setShortcut("ctrl+b")
        action_bookMark.triggered.connect(lambda: book_marcks(self).exec())
        bookmarks_notes_menu.addAction(action_bookMark)
        action_notes = qt1.QAction("دفتر الملاحظات", self)
        action_notes.setShortcut("ctrl+n")
        action_notes.triggered.connect(lambda: notes.NotesDialog(self).exec())
        bookmarks_notes_menu.addAction(action_notes)
        self.moreOptionsMenu.addMenu(bookmarks_notes_menu)
        messages_menu = guiTools.QCustomContextMenu("الرسائل", self)
        messages_menu.setFont(font)
        action_random_message = qt1.QAction("رسالة لك", self)
        action_random_message.setShortcut("ctrl+shift+m")
        action_random_message.triggered.connect(self.show_random_message)
        messages_menu.addAction(action_random_message)
        action_viewLastMessage = qt1.QAction("آخر رسالة من المطور", self)
        action_viewLastMessage.setShortcut("ctrl+m")
        action_viewLastMessage.triggered.connect(self.onViewLastMessageButtonClicked)
        messages_menu.addAction(action_viewLastMessage)
        self.moreOptionsMenu.addMenu(messages_menu)
        links_menu = guiTools.QCustomContextMenu("روابط البرنامج", self)
        links_menu.setFont(font)
        GitHub_action = qt1.QAction("رابط مستودع البرنامج على GitHub", self)
        GitHub_action.setShortcut("ctrl+shift+g")
        GitHub_action.triggered.connect(lambda: webbrowser.open("https://github.com/MesterAbdAlrhmanMohmed/moslemTools_GUI"))
        links_menu.addAction(GitHub_action)
        youtube_action = qt1.QAction("رابط قائمة تشغيل شرح البرنامج على YouTube", self)
        youtube_action.setShortcut("ctrl+shift+y")
        youtube_action.triggered.connect(lambda: webbrowser.open("https://youtube.com/playlist?list=PLgnAXYp1AusBRcxO_JAgxq9KyLP0ET6cE&si=TzdbfdiFaDOyPbMd"))
        links_menu.addAction(youtube_action)
        telegram_action = qt1.QAction("رابط القناة الرسمية للبرنامج على telegram", self)
        telegram_action.setShortcut("ctrl+shift+t")
        telegram_action.triggered.connect(lambda: webbrowser.open("https://t.me/moslem_tools"))
        links_menu.addAction(telegram_action)
        copy_download_link_action = qt1.QAction("نسخ رابط تحميل البرنامج", self)
        copy_download_link_action.triggered.connect(self.copy_download_link)
        links_menu.addAction(copy_download_link_action)
        self.moreOptionsMenu.addMenu(links_menu)
        action_whats_new = qt1.QAction("ما الجديد في آخر إصدار من البرنامج", self)
        action_whats_new.setShortcut("ctrl+w")
        action_whats_new.triggered.connect(self.whats_new_funktion)
        self.moreOptionsMenu.addAction(action_whats_new)
        action_release_date = qt1.QAction("تاريخ نشر البرنامج", self)
        action_release_date.setShortcut("ctrl+d")
        action_release_date.triggered.connect(lambda: guiTools.MessageBox.view(self, "تاريخ نشر البرنامج", "السبت 14 يُونْيُو 2025، 18 ذُو ٱلْحِجَّة 1446"))
        self.moreOptionsMenu.addAction(action_release_date)
        action_about_devs = qt1.QAction("عن المطور", self)
        action_about_devs.setShortcut("f2")
        action_about_devs.triggered.connect(self.open_developers_window)
        self.moreOptionsMenu.addAction(action_about_devs)
        action_error_log = qt1.QAction("فتح ملف سجل الأخطاء", self)
        action_error_log.setShortcut("ctrl+alt+e")
        action_error_log.triggered.connect(self.open_error_log_file)
        self.moreOptionsMenu.addAction(action_error_log)
        self.more_options_button.setMenu(self.moreOptionsMenu)
        layout1.addWidget(self.more_options_button)
        layout1.addWidget(self.info)
        layout1.addWidget(self.list_widget)
        w = qt.QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.tray_icon = qt.QSystemTrayIcon(self)
        self.tray_icon.setIcon(qt1.QIcon("data/icons/tray_icon.jpg"))
        self.tray_icon.setToolTip(app.name)
        self.tray_menu = guiTools.QCustomContextMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        self.tray_menu.setAccessibleName("تم فتح قائمة moslem tools")
        self.random_thecker_audio = qt1.QAction("تشغيل ذكر عشوائي")
        self.random_thecker_audio.triggered.connect(self.random_audio_theker)
        self.random_thecker_text = qt1.QAction("عرض ذكر عشوائي")
        self.random_thecker_text.triggered.connect(self.show_random_theker)
        self.show_action = qt1.QAction("إخفاء البرنامج")
        self.show_action.triggered.connect(self.toggle_visibility)
        self.close_action = qt1.QAction("إغلاق البرنامج")
        self.close_action.triggered.connect(lambda: qt.QApplication.quit())
        self.tray_menu.addAction(self.random_thecker_audio)
        self.tray_menu.addAction(self.random_thecker_text)
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.close_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.TIMER1 = qt2.QTimer(self)
        self.TIMER1.timeout.connect(self.show_random_theker)
        self.runAudioThkarTimer()
        self.notification_random_thecker()
        self.tray_menu.setFont(font)
        self.khatmah_timer = qt2.QTimer(self)
        self.khatmah_timer.timeout.connect(self.check_scheduled_khatmah_reminder)
        self.khatmah_timer.start(5000)
        qt2.QTimer.singleShot(1000, self.check_scheduled_khatmah_reminder)
        qt2.QTimer.singleShot(1000, self.play_startup_athkar)

    def copy_download_link(self):
        def run():
            try:
                r = requests.get(f"https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/{settings_handler.appName}/main/{app.appdirname}/update/app.json", timeout=10)
                info = r.json()
                pyperclip.copy(info["download"])
                guiTools.speak("تم نسخ رابط تحميل البرنامج")
                winsound.Beep(1000, 100)
            except Exception as e:
                print(e)
        threading.Thread(target=run, daemon=True).start()

