from custom_errors import *
import sys, traceback, threading
sys.excepthook = my_excepthook
threading.excepthook = lambda args: log_error_to_file("".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
import update,guiTools,random,os,shutil,datetime,webbrowser,requests,pyperclip,winsound,ctypes
from ctypes import wintypes
import ujson as json
from pynput import keyboard as p_key
from hijridate import Gregorian
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from appTabs import *
from functions import audio_manager
try:
    updatePath = os.path.join(os.getenv('appdata'), settings_handler.appName, "update")
    if os.path.exists(updatePath):
        shutil.rmtree(updatePath)
    asked_file = os.path.join(os.getenv('appdata'), settings_handler.appName, "asked_questions.json")
    if os.path.exists(asked_file):
        os.remove(asked_file)
except Exception as e:
    print(f"Error cleaning startup files: {e}")


def get_smart_display_name():
    try:
        if settings_handler.get("g", "use_name_in_occasions") != "True":
            return ""
        name_type = settings_handler.get("g", "name_type") or "custom_name"
        if name_type == "custom_name":
            custom_val = settings_handler.get("g", "user_name").strip()
            if custom_val:
                return custom_val
        elif name_type == "os_username":
            try:
                username = os.getlogin()
                if username and username.strip():
                    return username.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
        elif name_type == "personal_name":
            try:
                GetUserNameExW = ctypes.windll.secur32.GetUserNameExW
                NameDisplay = 3
                size = wintypes.DWORD(256)
                buffer = ctypes.create_unicode_buffer(size.value)
                if GetUserNameExW(NameDisplay, buffer, ctypes.byref(size)) and buffer.value.strip():
                    return buffer.value.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
            try:
                username = os.getlogin()
                generic_names = ['dell', 'hp', 'lenovo', 'user', 'admin', 'administrator', 'pc', 'com']
                if username and username.lower().strip() not in generic_names:
                    return username.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
    except Exception as e:
        print(f"Handled exception: {e}")
    return ""


class MessageCheckWorker(qt2.QObject):
    finished = qt2.pyqtSignal()

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

    def check_for_message(self):
        try:
            guiTools.messageHandler.check(self.parent_window)
        except Exception as e:
            print(f"Error checking for message in thread: {e}")
        finally:
            self.finished.emit()


class main(qt.QMainWindow):
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
        self.moreOptionsMenu = qt.QMenu(self)
        self.moreOptionsMenu.setFont(font)
        self.moreOptionsMenu.setAccessibleName("المزيد من الخيارات")
        action_settings = qt1.QAction("الإعدادات", self)
        action_settings.setShortcut("f1")
        action_settings.triggered.connect(lambda: settings(self).exec())
        self.moreOptionsMenu.addAction(action_settings)
        action_bookMark = qt1.QAction("العلامات المرجعية", self)
        action_bookMark.setShortcut("ctrl+b")
        action_bookMark.triggered.connect(lambda: book_marcks(self).exec())
        self.moreOptionsMenu.addAction(action_bookMark)
        action_notes = qt1.QAction("الملاحظات", self)
        action_notes.setShortcut("ctrl+n")
        action_notes.triggered.connect(lambda: notes.NotesDialog(self).exec())
        self.moreOptionsMenu.addAction(action_notes)
        action_random_message = qt1.QAction("رسالة لك", self)
        action_random_message.setShortcut("ctrl+shift+m")
        action_random_message.triggered.connect(self.show_random_message)
        self.moreOptionsMenu.addAction(action_random_message)
        action_whats_new = qt1.QAction("ما الجديد في آخر إصدار من البرنامج", self)
        action_whats_new.setShortcut("ctrl+w")
        action_whats_new.triggered.connect(self.whats_new_funktion)
        self.moreOptionsMenu.addAction(action_whats_new)
        action_viewLastMessage = qt1.QAction("إظهار آخر رسالة من المطور", self)
        action_viewLastMessage.setShortcut("ctrl+m")
        action_viewLastMessage.triggered.connect(self.onViewLastMessageButtonClicked)
        self.moreOptionsMenu.addAction(action_viewLastMessage)
        action_about_devs = qt1.QAction("عن المطور", self)
        action_about_devs.setShortcut("f2")
        action_about_devs.triggered.connect(self.open_developers_window)
        self.moreOptionsMenu.addAction(action_about_devs)
        action_release_date = qt1.QAction("تاريخ نشر البرنامج", self)
        action_release_date.setShortcut("ctrl+d")
        action_release_date.triggered.connect(lambda: guiTools.MessageBox.view(self, "تاريخ نشر البرنامج", "السبت 14 يُونْيُو 2025، 18 ذُو ٱلْحِجَّة 1446"))
        self.moreOptionsMenu.addAction(action_release_date)
        GitHub_action=qt1.QAction("رابط مستودع البرنامج على GitHub", self)
        GitHub_action.setShortcut("ctrl+shift+g")
        GitHub_action.triggered.connect(lambda: webbrowser.open("https://github.com/MesterAbdAlrhmanMohmed/moslemTools_GUI"))
        self.moreOptionsMenu.addAction(GitHub_action)
        youtube_action=qt1.QAction("رابط قائمة تشغيل شرح البرنامج على YouTube", self)
        youtube_action.setShortcut("ctrl+shift+y")
        youtube_action.triggered.connect(lambda: webbrowser.open("https://youtube.com/playlist?list=PLgnAXYp1AusBRcxO_JAgxq9KyLP0ET6cE&si=TzdbfdiFaDOyPbMd"))
        self.moreOptionsMenu.addAction(youtube_action)
        telegram_action=qt1.QAction("رابط القناة الرسمية للبرنامج على telegram", self)
        telegram_action.setShortcut("ctrl+shift+t")
        telegram_action.triggered.connect(lambda: webbrowser.open("https://t.me/moslem_tools"))
        self.moreOptionsMenu.addAction(telegram_action)
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
        self.tray_menu = qt.QMenu(self)
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

    def check_scheduled_khatmah_reminder(self):
        try:
            if settings_handler.get("khatmah_reminder", "enabled") != "True":
                return

            today = datetime.date.today()
            today_str = today.strftime("%Y-%m-%d")

            try:
                hour = int(settings_handler.get("khatmah_reminder", "hour") or 8)
            except Exception:
                hour = 8
            try:
                minute = int(settings_handler.get("khatmah_reminder", "minute") or 0)
            except Exception:
                minute = 0
            period = settings_handler.get("khatmah_reminder", "period") or "مساءً"

            if period == "مساءً" and hour < 12:
                h24 = hour + 12
            elif period == "صباحاً" and hour == 12:
                h24 = 0
            else:
                h24 = hour

            time_key = f"{today_str}_{h24}:{minute}"
            last_reminded_time = settings_handler.get("khatmah_reminder", "last_reminded_time")
            if last_reminded_time == time_key:
                return

            now = datetime.datetime.now()
            rem_dt = datetime.datetime(today.year, today.month, today.day, h24, minute)

            if now >= rem_dt:
                khatmah_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "khatmah.json")
                if os.path.exists(khatmah_path):
                    with open(khatmah_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("is_completed", False):
                        return

                use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
                username1 = get_smart_display_name() if use_name_enabled else ""
                gender = settings_handler.get("g", "user_gender") or "ذكر"
                is_female = (gender == "أنثى")
                if not use_name_enabled:
                    msg = "تنبيه: لقد حان موعد الورد اليومي للختمة القرآنية."
                elif is_female:
                    msg = f"تنبيه: لقد حان موعد وردكِ اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد حان موعد وردكِ اليومي للختمة القرآنية."
                else:
                    msg = f"تنبيه: لقد حان موعد وردك اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد حان موعد وردك اليومي للختمة القرآنية."

                settings_handler.set("khatmah_reminder", "last_reminded_time", time_key)
                settings_handler.set("khatmah_reminder", "last_reminded_date", today_str)
                guiTools.SendNotification("تنبيه الورد القرآني", msg)
                guiTools.MessageBox.view(self, "تنبيه الورد القرآني", msg)
        except Exception as e:
            print(f"Error in scheduled khatmah reminder: {e}")

    def play_random_basmala(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        self.audio_output.setDevice(audio_manager.get_audio_device("random_athkar"))
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.abspath(os.path.join(base_dir, "data", "sounds", "basmala"))
        if not os.path.exists(folder_path): return
        sound_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if sound_files:
            chosen_file = random.choice(sound_files)
            file_path = os.path.abspath(os.path.join(folder_path, chosen_file))
            self.media_player.setSource(qt2.QUrl.fromLocalFile(file_path))
            self.media_player.play()

    def play_startup_athkar(self):
        if settings_handler.get("athkar", "playAtStartup") == "True":
            self.random_audio_theker()
        elif settings_handler.get("athkar", "playBasmalaAtStartup") == "True":
            self.play_random_basmala()

    def start_message_check_thread(self):
        self.message_worker = MessageCheckWorker(self)
        self.message_worker.finished.connect(self.message_worker.deleteLater)
        self.message_worker.finished.connect(lambda: setattr(self, 'message_worker', None))
        thread = threading.Thread(target=self.message_worker.check_for_message)
        thread.daemon = True
        thread.start()

    def showEvent(self, event):
        super().showEvent(event)
        MF_BYCOMMAND = 0x00000000
        SC_SIZE = 0xF000
        SC_MOVE = 0xF010
        SC_MINIMIZE = 0xF020
        SC_MAXIMIZE = 0xF030
        SC_RESTORE = 0xF120
        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_SYSMENU = 0x00080000
        user32 = ctypes.windll.user32
        GetWindowLong = user32.GetWindowLongW
        SetWindowLong = user32.SetWindowLongW
        hwnd = self.winId().__int__()
        hMenu = user32.GetSystemMenu(hwnd, False)
        if hMenu:
            for cmd in (SC_SIZE, SC_MOVE, SC_MINIMIZE, SC_MAXIMIZE, SC_RESTORE):
                user32.RemoveMenu(hMenu, cmd, MF_BYCOMMAND)
            user32.DrawMenuBar(hwnd)
        style = GetWindowLong(hwnd, GWL_STYLE)
        new_style = WS_CAPTION | WS_SYSMENU
        SetWindowLong(hwnd, GWL_STYLE, new_style)
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0020)

    def _restore(self):
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.show_action.setText("إظهار البرنامج")
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.show_action.setText("إخفاء البرنامج")

    def show_random_theker(self):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "data", "json", "text_athkar.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_theckr = random.choice(data)
        if settings_handler.get("athkar", "text_type") == "1":
            guiTools.MessageBox.view(self, "ذكر عشوائي", random_theckr)
        else:
            guiTools.SendNotification("ذكر عشوائي", random_theckr)

    def show_random_message(self):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "data", "json", "QuotesMessages.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_message = random.choice(data)
        guiTools.TextViewer(self, "رسالة لك", random_message).exec()

    def notification_random_thecker(self):
        self.TIMER1.stop()
        duration = formatDuration("athkar", "text")
        if duration != 0:
            self.TIMER1.start(duration)

    def runAudioThkarTimer(self):
        self.timer.stop()
        if formatDuration("athkar", "voice") != 0:
            self.timer.start(formatDuration("athkar", "voice"))

    def closeEvent(self, event):
        if app.exit:
            if settings_handler.get("g", "exitDialog") == "True":
                m = guiTools.ExitApp(self)
                m.exec()
                if m:
                    event.ignore()
            else:
                self.close()
        else:
            self.close()

    def random_audio_theker(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
            return
        self.audio_output.setDevice(audio_manager.get_audio_device("random_athkar"))
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.abspath(os.path.join(base_dir, "data", "sounds", "athkar"))
        if not os.path.exists(folder_path): return
        sound_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if sound_files:
            chosen_file = random.choice(sound_files)
            file_path = os.path.abspath(os.path.join(folder_path, chosen_file))
            self.media_player.setSource(qt2.QUrl.fromLocalFile(file_path))
            self.media_player.play()

    def open_developers_window(self):
        self.developers_window = AboutDeveloper()
        self.developers_window.exec()

    def viewInfoTextEdit(self):
        use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
        username1 = get_smart_display_name() if use_name_enabled else ""
        gender = settings_handler.get("g", "user_gender") or "ذكر"
        is_female = (gender == "أنثى")
        if use_name_enabled:
            ya_name = f" يا {username1}" if username1 else ""
            if is_female:
                la_tansa_comma = f"يا {username1}، لا تَنْسِ، " if username1 else "لا تَنْسِ، "
                la_tansa_no_comma = f"يا {username1} لا تَنْسِ، " if username1 else "لا تَنْسِ، "
                la_tansa_direct = f"يا {username1}، لا تَنْسِ " if username1 else "لا تَنْسِ "
                la_tansa_direct_no_comma = f"يا {username1} لا تَنْسِ " if username1 else "لا تَنْسِ "
                default_dhikr = f"لا تَنْسِ يا {username1} ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم" if username1 else "لا تَنْسِ ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
            else:
                la_tansa_comma = f"يا {username1}، لا تَنْسَ، " if username1 else "لا تَنْسَ، "
                la_tansa_no_comma = f"يا {username1} لا تَنْسَ، " if username1 else "لا تَنْسَ، "
                la_tansa_direct = f"يا {username1}، لا تَنْسَ " if username1 else "لا تَنْسَ "
                la_tansa_direct_no_comma = f"يا {username1} لا تَنْسَ " if username1 else "لا تَنْسَ "
                default_dhikr = f"لا تَنْسَ يا {username1} ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم" if username1 else "لا تَنْسَ ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
        else:
            ya_name = ""
            la_tansa_comma = ""
            la_tansa_no_comma = ""
            la_tansa_direct = ""
            la_tansa_direct_no_comma = ""
            default_dhikr = "ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
        try:
            hijri_date_obj = Gregorian.today().to_hijri()
            current_gregorian_weekday = datetime.datetime.now().weekday()
            if current_gregorian_weekday == 4:
                self.info.setText(f"جمعة مباركة{ya_name}، تشغيل أو قراءة سورة الكهف في هذا اليوم سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 9:
                if 21 <= hijri_date_obj.day <= 29:
                    if not use_name_enabled:
                        self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزق الجميع فضل ليلة القدر، ولا تنسوني من صالح الدعاء، وجزاكم الله خيرا.")
                    elif is_female:
                        self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزقكِ فضل ليلة القدر، ولا تنسيني من صالح دعائكِ، وجزاكِ الله خيراً.")
                    else:
                        if username1:
                            self.info.setText(f"العشر الأواخر من رمضان، الله يرزقك فضل ليلة القدر يا {username1}، لا تنساني من صالح دعاءك، وجزاك الله خيرا.")
                        else:
                            self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزق الجميع فضل ليلة القدر، ولا تنسوني من صالح الدعاء، وجزاكم الله خيرا.")
                else:
                    self.info.setText(f"رمضان كريم{ya_name}")
            elif hijri_date_obj.month == 10 and hijri_date_obj.day == 1:
                self.info.setText(f"عيد فطر مبارك{ya_name}")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 10:
                self.info.setText(f"عيد أضحى مبارك{ya_name}")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [11, 12, 13]:
                self.info.setText("أيام التشريق، أيام أكل وشرب وذكر لله")
            elif current_gregorian_weekday == 0:
                self.info.setText(f"{la_tansa_no_comma}صيام يوم الإثنين، سنة عن النبي صلى الله عليه وسلم")
            elif current_gregorian_weekday == 3:
                self.info.setText(f"{la_tansa_no_comma}صيام يوم الخميس، سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 1:
                if not use_name_enabled:
                    self.info.setText("كل عام وأنتم بخير بمناسبة رأس السنة الهجرية الجديدة")
                elif is_female:
                    self.info.setText(f"كل عام وأنتِ بخير{ya_name} بمناسبة رأس السنة الهجرية الجديدة")
                else:
                    self.info.setText(f"كل عام وأنتَ بخير{ya_name} بمناسبة رأس السنة الهجرية الجديدة")
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 10:
                self.info.setText(f"{la_tansa_no_comma}صيام عاشوراء، مستحب عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 7 and hijri_date_obj.day == 27:
                self.info.setText("ذكرى الإسراء والمعراج")
            elif hijri_date_obj.month == 8 and hijri_date_obj.day == 15:
                if is_female:
                    self.info.setText(f"{la_tansa_comma}ليلة النصف من شعبان، يستحب فيها الدعاء")
                else:
                    self.info.setText(f"{la_tansa_no_comma}ليلة النصف من شعبان، يستحب فيها الدعاء")
            elif hijri_date_obj.month == 8:
                self.info.setText(f"{la_tansa_no_comma}يستحب الصيام في شهر شعبان")
            elif hijri_date_obj.month == 10:
                if is_female:
                    self.info.setText(f"{la_tansa_direct}صيام الست أيام البيض في شهر شوال، وهي سنة عن النبي صلى الله عليه وسلم")
                else:
                    self.info.setText(f"{la_tansa_no_comma}صيام الست أيام البيض في شهر شوال، وهي سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 9:
                self.info.setText(f"{la_tansa_direct_no_comma}صيام يوم عرفة، صيام يغفر ذنوب السنة الماضية والسنة القادمة")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [1, 2, 3, 4, 5, 6, 7, 8]:
                self.info.setText(f"{la_tansa_comma}صيام العشر الأوائل من ذي الحجة سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.day in [13, 14, 15]:
                self.info.setText(f"{la_tansa_comma}صيام الأيام القمرية، سنة عن النبي صلى الله عليه وسلم")
            else:
                self.info.setText(default_dhikr)
        except Exception as e:
            print(f"حدث خطأ: {e}")
            self.info.setText(default_dhikr)

    def onViewLastMessageButtonClicked(self):
        with open(os.path.join(os.getenv('appdata'), settings_handler.appName, "message.json"), "r", encoding="utf-8") as file:
            data = json.load(file)
        guiTools.TextViewer(self, "آخر رسالة من المطور", data["message"]).exec()

    def whats_new_funktion(self):
        try:
            r = requests.get(f"https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/{settings_handler.appName}/main/{app.appdirname}/update/app.json")
            info = r.json()
            guiTools.TextViewer(self, "ما الجديد في آخر إصدار من البرنامج", info["what is new"]).exec()
        except Exception as e:
            print(e)
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشلت عملية جلب المعلومات, الرجاء الإتصال بالإنترنت")

    def onToolChanged(self, current, previous):
        self.quranPlayer.mp.pause()
        self.researcher.media_player.pause()

    def adjust_list_widget_width(self, index=None):
        fm = qt1.QFontMetrics(self.list_widget.font())
        current_text = self.list_widget.currentText()
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        self.list_widget.setFixedWidth(text_width + 65)

    def open_error_log_file(self):
        log_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "error.log")
        if not os.path.exists(log_path):
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                print(f"Handled exception: {e}")
        try:
            os.startfile(log_path)
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ", f"تعذر فتح ملف السجل: {e}")


def check_missed_khatmah_alert(parent_window=None):
    try:
        if settings_handler.get("khatmah_reminder", "enabled") != "True":
            return False
        if settings_handler.get("khatmah_reminder", "missed_alert") == "False":
            return False

        khatmah_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "khatmah.json")
        if not os.path.exists(khatmah_path):
            data = {
                "has_khatmah": True,
                "target_days": 30,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": 20,
                "completed_pages": 0,
                "is_completed": False
            }
        else:
            with open(khatmah_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        if data.get("is_completed", False):
            return False

        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")

        try:
            hour = int(settings_handler.get("khatmah_reminder", "hour") or 8)
        except Exception:
            hour = 8
        try:
            minute = int(settings_handler.get("khatmah_reminder", "minute") or 0)
        except Exception:
            minute = 0
        period = settings_handler.get("khatmah_reminder", "period") or "مساءً"

        if period == "مساءً" and hour < 12:
            h24 = hour + 12
        elif period == "صباحاً" and hour == 12:
            h24 = 0
        else:
            h24 = hour

        missed_key = f"{today_str}_{h24}:{minute}"
        if (data.get("last_missed_alert_key") == missed_key or 
            settings_handler.get("khatmah_reminder", "last_reminded_time") == missed_key):
            return False

        start_date_str = data.get("start_date", today_str)
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except Exception:
            start_date = today

        days_passed = max(0, (today - start_date).days)
        daily_pages = data.get("daily_pages", 20)
        completed_pages = data.get("completed_pages", 0)

        now = datetime.datetime.now()
        rem_dt = datetime.datetime(today.year, today.month, today.day, h24, minute)

        if days_passed > 0 or now >= rem_dt:
            expected_pages = min(604, (days_passed + 1) * daily_pages)
        else:
            expected_pages = min(604, days_passed * daily_pages)

        if completed_pages < expected_pages:
            use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
            username1 = get_smart_display_name() if use_name_enabled else ""
            gender = settings_handler.get("g", "user_gender") or "ذكر"
            is_female = (gender == "أنثى")
            if not use_name_enabled:
                msg = "تنبيه: لقد فاتك موعد الورد اليومي للختمة القرآنية."
            elif is_female:
                msg = f"تنبيه: لقد فاتكِ موعد وردكِ اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد فاتكِ موعد وردكِ اليومي للختمة القرآنية."
            else:
                msg = f"تنبيه: لقد فاتك موعد وردك اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد فاتك موعد وردك اليومي للختمة القرآنية."

            guiTools.MessageBox.view(parent_window, "تنبيه فوات الورد القرآني", msg)
            data["last_missed_alert_key"] = missed_key
            data["last_missed_alert_date"] = today_str
            settings_handler.set("khatmah_reminder", "last_reminded_time", missed_key)
            settings_handler.set("khatmah_reminder", "last_reminded_date", today_str)
            try:
                with open(khatmah_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error updating khatmah json: {e}")
            return True
        return False
    except Exception as e:
        print(f"Error checking missed khatmah alert: {e}")
        return False


def show_random_quote_message(parent=None):
    try:
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "data", "json", "QuotesMessages.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_message = random.choice(data)
        guiTools.TextViewer(parent, "رسالة لك", random_message).exec()
        return True
    except Exception as e:
        print(f"Error showing random quote message: {e}")
        return False


def run_startup_checks():
    try:
        check_missed_khatmah_alert(None)
    except Exception as e:
        print(f"Error in khatmah startup alert: {e}")

    shown = False
    if settings_handler.get("update", "autoCheck") == "True":
        try:
            shown = update.check(None, message=False)
        except Exception as e:
            print(f"Error checking update at startup: {e}")
    if shown: return True
    try:
        shown = guiTools.messageHandler.check(None)
    except Exception as e:
        print(f"Error checking messages at startup: {e}")
    if shown: return True

    if settings_handler.get("g", "randomMessageAtStartup") == "True":
        try:
            show_random_quote_message(None)
            return True
        except Exception as e:
            print(f"Error showing quote message at startup: {e}")

    return False
if __name__ == "__main__":
    App = qt.QApplication([])
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
    shared=qt2.QSharedMemory("com.MTC.moslemTools")
    window = main(shown)
    if shared.attach() or not shared.create(1):
        guiTools.qMessageBox.MessageBox.error(window,"تنبيه","البرنامج يعمل بالفعل\nلإظهار البرنامج نستخدم الاختصار windows + alt + h أو نقوم بإظهاره من قائمة علبة النظان system tray")
        sys.exit(0)
    App.aboutToQuit.connect(lambda: shared.detach())
    window.show()
    App.exec()
