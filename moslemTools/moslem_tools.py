import sys
from custome_errors import *
sys.excepthook = my_excepthook
import update,guiTools,json,random,os,shutil,datetime,webbrowser,requests,keyboard,pyperclip,winsound
from hijri_converter import Gregorian
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from appTabs import *
try:
    updatePath = os.path.join(os.getenv('appdata'), settings_handler.appName, "update")
    if os.path.exists(updatePath):
        shutil.rmtree(updatePath)
except:
    pass
class main(qt.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(app.name + "الإصدار:" + str(app.version))
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.setWindowFlag(qt2.Qt.WindowType.WindowMinimizeButtonHint, False)
        guiTools.speak("مرحبا بك في moslem tools, جاري تشغيل البرنامج, الرجاء الانتظار.")
        keyboard.add_hotkey("alt+windows+p", self.random_audio_theker)
        keyboard.add_hotkey("alt+windows+l", self.show_random_theker)
        keyboard.add_hotkey("ctrl+alt+h", self.check_app_show_or_not)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(int(settings_handler.get("athkar", "voiceVolume")) / 100)
        self.media_player.setAudioOutput(self.audio_output)
        self.timer = qt2.QTimer(self)
        self.timer.timeout.connect(self.random_audio_theker)
        layout = qt.QVBoxLayout()
        self.info = qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout1=qt.QHBoxLayout()
        layout1.addWidget(self.info)
        layout2=qt.QVBoxLayout()
        layout.addLayout(layout1)
        layout1.addLayout(layout2)
        self.viewInfoTextEdit()
        content_layout = qt.QHBoxLayout()
        self.list_widget = guiTools.listBook()
        self.list_widget.currentItemChanged.connect(self.onToolChanged)
        self.quranPlayer = QuranPlayer()
        self.storiesPlayer = StoryPlayer()
        tabs = [
            (prayer_times(self), "مواقيت الصلاة والتاريخ"),
            (Quran(), "القرآن الكريم مكتوب"),
            (self.quranPlayer, "القرآن الكريم صوتي"),
            (QuranRecitations(), "قراءات القرآن الكريم"),
            (hadeeth(), "الأحاديث النبوية والقدسية"),
            (IslamicBooks(), "الكتب الإسلامية"),
            (ProphetStories(), "القصص الإسلامية المكتوبة"),
            (self.storiesPlayer, "القصص الإسلامية الصوتية"),
            (Albaheth(), "الباحث في القرآن والأحاديث"),
            (protcasts(), "الإذاعات الإسلامية"),
            (Athker(), "الأذكار والأدعية"),
            (sibha(), "سبحة إلكترونية"),
            (NamesOfAllah(), "أسماء الله الحُسْنى"),
            (DateConverter(), "محول التاريخ")
        ]
        for widget_class, label in tabs:
            self.list_widget.add(label, widget_class)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        fm = qt1.QFontMetrics(self.list_widget.font())
        max_width = 0
        for i in range(self.list_widget.count()):
            item_text = self.list_widget.item(i).text()
            text_width = fm.boundingRect(item_text).width()
            if text_width > max_width:
                max_width = text_width
        max_width += 40
        self.list_widget.setFixedWidth(max_width)
        content_layout.addWidget(self.list_widget)
        content_layout.addWidget(self.list_widget.w, 1)
        layout.addLayout(content_layout)
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        font = qt1.QFont()
        font.setBold(True)
        moreOptionsMenu = menubar.addMenu("المزيد من الخيارات")
        action_settings = qt1.QAction("الإعدادات", self)
        action_settings.setShortcut("f3")
        action_settings.triggered.connect(lambda: settings(self).exec())
        moreOptionsMenu.addAction(action_settings)
        action_bookMark = qt1.QAction("العلامات المرجعية", self)
        action_bookMark.setShortcut("ctrl+b")
        action_bookMark.triggered.connect(lambda: book_marcks(self).exec())
        moreOptionsMenu.addAction(action_bookMark)
        action_whats_new = qt1.QAction("ما الجديد في هذا الإصدار", self)
        action_whats_new.setShortcut("ctrl+w")
        action_whats_new.triggered.connect(self.whats_new_funktion)
        moreOptionsMenu.addAction(action_whats_new)
        action_viewLastMessage = qt1.QAction("إظهار آخر رسالة من المطور", self)
        action_viewLastMessage.setShortcut("ctrl+m")
        action_viewLastMessage.triggered.connect(self.onViewLastMessageButtonClicked)
        moreOptionsMenu.addAction(action_viewLastMessage)
        action_user_guide = qt1.QAction("دليل المستخدم", self)
        action_user_guide.setShortcut("f1")
        action_user_guide.triggered.connect(self.open_user_g_window)
        moreOptionsMenu.addAction(action_user_guide)
        action_about_devs = qt1.QAction("عن المطور", self)
        action_about_devs.setShortcut("f2")
        action_about_devs.triggered.connect(self.open_developers_window)
        moreOptionsMenu.addAction(action_about_devs)
        action_release_date = qt1.QAction("تاريخ نشر البرنامج", self)
        action_release_date.setShortcut("ctrl+d")
        action_release_date.triggered.connect(lambda: guiTools.MessageBox.view(self, "تاريخ نشر البرنامج", "غير معروف حتى الآن"))
        moreOptionsMenu.addAction(action_release_date)
        GitHub_action=qt1.QAction("رابط مستودع البرنامج على GitHub", self)
        GitHub_action.setShortcut("ctrl+shift+q")
        GitHub_action.triggered.connect(lambda: webbrowser.open("https://github.com/MesterAbdAlrhmanMohmed/moslemTools_GUI"))
        moreOptionsMenu.addAction(GitHub_action)
        donateAction=qt1.QAction("تبرع",self)
        moreOptionsMenu.addAction(donateAction)
        donateAction.triggered.connect(self.OnDonation)
        donateAction.setShortcut("ctrl+shift+d")        
        action_delete_program_data = qt1.QAction("حذف بيانات البرنامج لإلغاء تثبيته", self)
        action_delete_program_data.triggered.connect(self.delete_program_data_with_confirmation)
        moreOptionsMenu.addAction(action_delete_program_data)                
        moreOptionsMenu.setFont(font)
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
        self.show_action.setShortcut("ctrl+alt+h")
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
        self.a=qt2.QTimer.singleShot(0, self._restore)
        guiTools.messageHandler.check(self)
        if settings_handler.get("update", "autoCheck") == "True":
            update.check(self, message=False)
    def check_app_show_or_not(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
    def _restore(self):
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.show_action.setText("إظهار البرنامج")
        else:
            self.show()
            self.show_action.setText("إخفاء البرنامج")
    def show_random_theker(self):
        with open("data/json/text_athkar.json", "r", encoding="utf_8") as f:
            data = json.load(f)
        random_theckr = random.choice(data)
        guiTools.SendNotification("ذكر عشوائي", random_theckr)
    def notification_random_thecker(self):
        self.TIMER1.stop()
        if formatDuration("athkar", "text") != 0:
            self.TIMER1.start(formatDuration("athkar", "text"))
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
        if self.media_player.isPlaying():
            self.media_player.stop()
            return
        folder_path = r"data\sounds\athkar"
        sound_files = [f for f in os.listdir(folder_path) if f.endswith(('.ogg'))]
        if sound_files:
            chosen_file = random.choice(sound_files)
            file_path = os.path.join(folder_path, chosen_file)
            self.media_player.setSource(qt2.QUrl.fromLocalFile(file_path))
            self.media_player.play()
    def open_user_g_window(self):
        webbrowser.open("https://drive.google.com/file/d/1GLp5kR6SIY2OhXfc6bZXjWn5beRflsEP/view?usp=drivesdk")
    def open_developers_window(self):
        self.developers_window = AboutDeveloper()
        self.developers_window.show()
    def viewInfoTextEdit(self):
        try:
            hijri_date_obj = Gregorian.today().to_hijri()
            current_gregorian_weekday = datetime.datetime.now().weekday()
            if current_gregorian_weekday == 4:
                self.info.setText("جمعة مباركة")
            elif current_gregorian_weekday == 0:
                self.info.setText("صيام يوم الإثنين سنة\nعن النبي صل الله عليه وسلم")
            elif current_gregorian_weekday == 3:
                self.info.setText("صيام يوم الخميس سنة\nعن النبي صل الله عليه وسلم")                        
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 1:
                self.info.setText("كل عام وأنتم بخير بمناسبة رأس السنة الهجرية الجديدة")
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 10:
                self.info.setText("صيام عاشوراء مستحب عن النبي صل الله عليه وسلم")        
            elif hijri_date_obj.month == 7 and hijri_date_obj.day == 27:
                self.info.setText("ذكرى الإسراء والمعراج")        
            elif hijri_date_obj.month == 8 and hijri_date_obj.day == 15:
                self.info.setText("ليلة النصف من شعبان، يستحب فيها الدعاء")
            elif hijri_date_obj.month == 8:
                self.info.setText("يستحب الصيام في شهر شعبان")
            elif hijri_date_obj.month == 9 and hijri_date_obj.day >= 21 and hijri_date_obj.day <= 29:
                self.info.setText("العشر الأواخر من رمضان، الله يرزقكم فضل ليلة القدر")
            elif hijri_date_obj.month == 9:
                self.info.setText("رمضان كريم")        
            elif hijri_date_obj.month == 10 and hijri_date_obj.day == 1:
                self.info.setText("عيد فطر مبارك")
            elif hijri_date_obj.month == 10:
                self.info.setText("صيام الست أيام البيض في شهر شوال، وهي سنة عن النبي صل الله عليه وسلم")        
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 9:
                self.info.setText("صيام يوم عرفة، صيام يغفر ذنوب السنة الماضية والسنة القادمة")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 10:
                self.info.setText("عيد أضحى مبارك")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [11, 12, 13]:
                self.info.setText("أيام التشريق، أيام أكل وشرب وذكر لله")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [1, 2, 3, 4, 5, 6, 7, 8]:
                self.info.setText("صيام العشر الأوائل من ذي الحجة سنة عن النبي صل الله عليه وسلم")        
            elif hijri_date_obj.day in [13, 14, 15]:
                self.info.setText("صيام الأيام القمرية سنة عن النبي صل الله عليه وسلم")        
            else:
                self.info.setText("لا تَنْسى ذِكْر الله")
        except Exception as e:
            print(f"حدث خطأ: {e}")
            self.info.setText("لا تَنْسى ذِكْر الله")
    def onViewLastMessageButtonClicked(self):
        with open(os.path.join(os.getenv('appdata'), settings_handler.appName, "message.json"), "r", encoding="utf-8") as file:
            data = json.load(file)
        guiTools.TextViewer(self, "آخر رسالة من المطور", data["message"]).exec()
    def whats_new_funktion(self):
        try:
            r = requests.get(f"https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/{settings_handler.appName}/main/{app.appdirname}/update/app.json")
            info = r.json()
            guiTools.TextViewer(self, "ما الجديد", info["what is new"]).exec()
        except Exception as e:
            print(e)
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشلت عملية جلب المعلومات, الرجاء الإتصال بالإنترنت")
    def onToolChanged(self,index):
        self.quranPlayer.mp.stop()
        self.storiesPlayer.mp.stop()
    def OnDonation(self):
        guiTools.MessageBox.view(self,"تنبيه","في حالة التبرع الرجاء إرسال صورة للتحويل على حساب Telegram الخاص بي، حتى لا تختلط التحويلات الخاطئة بالتحويلات المقصودة")
        menu=qt.QMenu("اختر طريقة",self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("اختر طريقة")
        menu.setFocus()
        vodafone_cash_action=qt1.QAction("نسخ رقم vodafone cash",self)
        vodafone_cash_action.triggered.connect(self.VFC)
        menu.addAction(vodafone_cash_action)
        instaPayAction=qt1.QAction("نسخ رابط حساب InstaPay",self)
        menu.addAction(instaPayAction)
        instaPayAction.triggered.connect(self.instaPay)
        menu.setFont(font)
        menu.exec(qt1.QCursor.pos())
    def instaPay(self):
        pyperclip.copy("https://ipn.eg/S/av369852/instapay/23Mu5Z")
        winsound.Beep(1000, 100)    
    def VFC(self):
        pyperclip.copy("+201022701463")
        guiTools.MessageBox.view(self,"تنبيه","تم نسخ رقم vodafone cash لكن هذا الرقم للتحويلات فقط، يمنع الإتصال بهذا الرقم أو مراسلته بأي شكل")
    def delete_program_data_with_confirmation(self):    
        confirm = guiTools.QQuestionMessageBox.view(
            self,
            "تأكيد الحذف النهائي لبيانات البرنامج",
            "تحذير هام:\nأنت على وشك حذف جميع بيانات برنامج moslem tools نهائيًا من جهازك بما في ذلك الإعدادات وكل شيئ متعلق بالبرنامج\nهذه العملية لا يمكن التراجع عنها وستؤدي إلى فقدان دائم لجميع البيانات\nهل أنت متأكد تمامًا أنك تريد المتابعة وحذف مجلد البرنامج بالكامل؟",
            "نعم، احذف البرنامج",
            "لا، إلغاء"
        )
        if confirm == 0:
            try:
                roaming_path = os.path.join(os.getenv('appdata'))
                target_folder_path = os.path.join(roaming_path, 'moslemTools_GUI')
                if os.path.exists(target_folder_path) and os.path.isdir(target_folder_path):
                    shutil.rmtree(target_folder_path)
                    guiTools.MessageBox.view(
                        self,
                        "تم الحذف بنجاح",
                        "تم حذف مجلد moslemTools_GUI وجميع بيانات البرنامج بنجاح\nالآن يمكنك إلغاء تثبيت البرنامج"
                    )
                    qt.QApplication.quit()
                else:
                    guiTools.MessageBox.view(
                        self,
                        "المجلد غير موجود",
                        f"المجلد '{target_folder_path}' غير موجود أو ليس مجلدًا. لا توجد بيانات لحذفها."
                    )
            except OSError as e:
                guiTools.MessageBox.error(
                    self,
                    "خطأ في الحذف",
                    f"حدث خطأ أثناء محاولة حذف المجلد: {e}\n\nيرجى التأكد من أن البرنامج ليس قيد التشغيل في الخلفية أو أن لديك الأذونات اللازمة."
                )
            except Exception as e:
                guiTools.MessageBox.error(
                    self,
                    "خطأ غير متوقع",
                    f"حدث خطأ غير متوقع: {e}"
                )
        else:
            return
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
shared=qt2.QSharedMemory("com.MTC.moslemTools")
window = main()
if shared.attach() or not shared.create(1):
    guiTools.qMessageBox.MessageBox.error(window,"تنبيه","البرنامج يعمل بالفعل")
    sys.exit(0)
App.aboutToQuit.connect(lambda: shared.detach())
window.show()
App.exec()