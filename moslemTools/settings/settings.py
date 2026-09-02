import guiTools,functions,gui,subprocess,os,sys,ctypes
from ctypes import wintypes
from . import settings_handler, app, tabs
from .tabs import audioSettings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt


class settings(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        self.setMinimumSize(1050, 500)
        self.resize(1100, 560)
        self.center()
        self.setWindowTitle("الإعدادات")
        self.p = p
        layout = qt.QVBoxLayout()
        h_layout = qt.QHBoxLayout()
        self.sectian = guiTools.listBook()
        self.sectian.setFocus()
        font = qt1.QFont()
        font.setBold(True)
        self.sectian.setStyleSheet("color: #e0e0e0;")
        self.sectian.setAccessibleName("اختر قسم")
        self.sectian.setFont(font)
        self.sectian.setMinimumWidth(360)
        h_layout.addWidget(self.sectian)
        scroll_area = qt.QScrollArea()
        scroll_area.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(qt.QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.sectian.w)
        h_layout.addWidget(scroll_area)
        layout.addLayout(h_layout)
        self.update = tabs.Update(self)
        buttonsLayout = qt.QHBoxLayout()
        self.ok = qt.QPushButton("موافق")
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.fok)
        self.ok.setStyleSheet("background-color: #006400; color: #e0e0e0; padding: 12px; font-weight: bold;")
        self.defolt = guiTools.QPushButton("استعادة الإعدادات الافتراضية")
        self.defolt.clicked.connect(self.default)
        self.defolt.setStyleSheet("background-color: #8B0000; color: #e0e0e0; padding: 12px; font-weight: bold;")
        self.cancel = guiTools.QPushButton("إلغاء")
        self.cancel.clicked.connect(self.fcancel)
        self.cancel.setStyleSheet("background-color: #333333; color: #e0e0e0; padding: 12px; font-weight: bold;")
        self.layout1 = tabs.Genral(self)
        self.sectian.add("الإعدادات العامة", self.layout1)
        self.startupTabSettings = tabs.StartupTabSettings(self)
        self.sectian.add("إعدادات تبويبة بدء التشغيل", self.startupTabSettings)
        self.userNameSettings = tabs.UserNameSettings()
        self.sectian.add("إعدادات التذكير بالمناسبات واسم المستخدم", self.userNameSettings)
        self.fontSettings = tabs.FontSettings()
        self.sectian.add("إعدادات نوع الخط وحجمه للعارضات", self.fontSettings)
        self.khatmahReminderSettings = tabs.KhatmahReminderSettings(self)
        self.sectian.add("إعدادات التذكير بالورد اليومي", self.khatmahReminderSettings)
        self.locationSettings=tabs.LocationSettings(self)
        self.sectian.add("إعدادات تحديد الموقع الجغرافي لمواقيت الصلاة",self.locationSettings)
        self.prayerTimesSettings = tabs.PrayerTimesSettings(self)
        self.sectian.add("إعدادات الأذان", self.prayerTimesSettings)
        self.tafaseerSettings = tabs.TafaseerSettings()
        self.sectian.add("إعدادات التفسير والترجمة لتبويبة القرآن الكريم مكتوب", self.tafaseerSettings)
        self.quranPlayerTimes = tabs.QuranPlayerSettings(self)
        self.sectian.add("إعدادات مشغل القرآن لتبويبة القرآن الكريم مكتوب", self.quranPlayerTimes)
        self.quranDisplaySettings = tabs.QuranDisplaySettings()
        self.sectian.add("إعدادات عرض الآيات في عارض القرآن الكريم", self.quranDisplaySettings)
        self.searchSettings = tabs.SearchSettings()
        self.sectian.add("إعدادات البحث", self.searchSettings)
        self.motonRecitersSettings = tabs.MotonRecitersSettings()
        self.sectian.add("إعدادات اختيار القارئ لتبويبة المتون الإسلامية المكتوبة", self.motonRecitersSettings)
        self.motonPlayerTimes = tabs.MotonPlayerSettings(self)
        self.sectian.add("إعدادات مشغل المتون لتبويبة المتون الإسلامية المكتوبة", self.motonPlayerTimes)
        self.motonDisplaySettings = tabs.MotonDisplaySettings()
        self.sectian.add("إعدادات عرض الأبيات في عارض المتون الإسلامية", self.motonDisplaySettings)
        self.athkar = tabs.AthkarSettings()
        self.sectian.add("إعدادات الأذكار العشوائية", self.athkar)
        self.fanarSettings = tabs.FanarSettings()
        self.sectian.add("إعدادات فنار (الذكاء الاصطناعي)", self.fanarSettings)
        self.audioSettings = audioSettings.AudioSettings(self)
        self.sectian.add("إعدادات تحديد كرت الصوت", self.audioSettings)
        self.sectian.add("إعدادات التحديثات", self.update)
        self.sectian.add("تحميل موارد", tabs.Download())
        restoar = tabs.Restoar(self)
        self.sectian.add("النسخ الاحتياطي والاستعادة", restoar)
        buttonsLayout.addWidget(self.ok)
        buttonsLayout.addWidget(self.defolt)
        buttonsLayout.addWidget(self.cancel)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)
        self.sectian.setCurrentRow(0)

    def center(self):
        primary_screen = qt1.QGuiApplication.primaryScreen()
        if primary_screen:
            frame_geometry = self.frameGeometry()
            screen_center = primary_screen.availableGeometry().center()
            frame_geometry.moveCenter(screen_center)
            self.move(frame_geometry.topLeft())

    def fok(self):
        if self.userNameSettings.use_name_checkbox.isChecked():
            selected_name_type = self.userNameSettings.get_selected_name_type()
            generic_names = ['dell', 'hp', 'lenovo', 'user', 'admin', 'administrator', 'pc', 'com']
            if selected_name_type == "custom_name":
                if not self.userNameSettings.custom_name_input.text().strip():
                    guiTools.MessageBox.view(self, "تنبيه", "مربع كتابة الاسم المخصص فارغ. يرجى كتابة اسم مخصص، أو تجربة استخدام اسم المستخدم الخاص بالجهاز، أو اسمك الشخصي.")
                    return
            elif selected_name_type == "os_username":
                has_os_name = False
                try:
                    uname = os.getlogin()
                    if uname and uname.lower().strip() not in generic_names:
                        has_os_name = True
                except Exception as e:
                    print(f"Handled exception: {e}")
                if not has_os_name:
                    guiTools.MessageBox.view(self, "تنبيه", "تعذر العثور على اسم مستخدم مخصص للجهاز (الاسم الحالي عام أو غير متاح). يرجى تجربة استخدام اسمك الشخصي، أو كتابة اسم مخصص.")
                    return
            elif selected_name_type == "personal_name":
                has_personal_name = False
                try:
                    GetUserNameExW = ctypes.windll.secur32.GetUserNameExW
                    NameDisplay = 3
                    size = wintypes.DWORD(256)
                    buffer = ctypes.create_unicode_buffer(size.value)
                    if GetUserNameExW(NameDisplay, buffer, ctypes.byref(size)) and buffer.value.strip():
                        has_personal_name = True
                except Exception as e:
                    print(f"Handled exception: {e}")
                if not has_personal_name:
                    try:
                        uname = os.getlogin()
                        if uname and uname.lower().strip() not in generic_names:
                            has_personal_name = True
                    except Exception as e:
                        print(f"Handled exception: {e}")
                if not has_personal_name:
                    guiTools.MessageBox.view(self, "تنبيه", "تعذر العثور على اسم شخصي للنظام. يرجى تجربة استخدام اسم المستخدم الخاص بالجهاز، أو كتابة اسم مخصص.")
                    return
        restart_required = 0
        original_font_bold = settings_handler.get("font", "bold")
        original_font_size = settings_handler.get("font", "size")
        original_font_wrap = settings_handler.get("font", "wrap")
        original_viewer_wraps = {key: settings_handler.get("font_wrap", key) for key, _ in self.fontSettings.VIEWERS}
        original_audio_global = settings_handler.get("audio", "global")
        original_audio_quran_viewer = settings_handler.get("audio", "quran_viewer")
        original_audio_quran_player = settings_handler.get("audio", "quran_player")
        original_audio_quran_audio = settings_handler.get("audio", "quran_audio")
        original_audio_researcher = settings_handler.get("audio", "researcher")
        original_audio_broadcasts = settings_handler.get("audio", "broadcasts")
        original_audio_adhan = settings_handler.get("audio", "adhan")
        original_audio_athkar = settings_handler.get("audio", "athkar")
        original_audio_random_athkar = settings_handler.get("audio", "random_athkar")
        original_audio_moton_viewer = settings_handler.get("audio", "moton_viewer")
        original_audio_moton_player = settings_handler.get("audio", "moton_player")
        original_use_name = settings_handler.get("g", "use_name_in_occasions")
        original_name_type = settings_handler.get("g", "name_type")
        original_user_name = settings_handler.get("g", "user_name")
        original_user_gender = settings_handler.get("g", "user_gender")
        orig_qs_tashkeel = settings_handler.get("quran_search", "ignore_tashkeel")
        orig_qs_hamza = settings_handler.get("quran_search", "ignore_hamza")
        orig_qs_symbols = settings_handler.get("quran_search", "ignore_symbols")
        orig_rs_tashkeel = settings_handler.get("researcher_search", "ignore_tashkeel")
        orig_rs_hamza = settings_handler.get("researcher_search", "ignore_hamza")
        orig_rs_symbols = settings_handler.get("researcher_search", "ignore_symbols")
        orig_ibs_tashkeel = settings_handler.get("islamic_books_search", "ignore_tashkeel")
        orig_ibs_hamza = settings_handler.get("islamic_books_search", "ignore_hamza")
        orig_ibs_symbols = settings_handler.get("islamic_books_search", "ignore_symbols")
        orig_ms_tashkeel = settings_handler.get("moton_search", "ignore_tashkeel")
        orig_ms_hamza = settings_handler.get("moton_search", "ignore_hamza")
        orig_ms_symbols = settings_handler.get("moton_search", "ignore_symbols")
        def get_audio_val(text):
            if text == "افتراضي": return "Default"
            if text == "مخصص": return "Custom"
            return text
        if (original_audio_global != get_audio_val(self.audioSettings.global_combo.currentText()) or
            original_audio_quran_viewer != get_audio_val(self.audioSettings.features["quran_viewer"].currentText()) or
            original_audio_quran_player != get_audio_val(self.audioSettings.features["quran_player"].currentText()) or
            original_audio_quran_audio != get_audio_val(self.audioSettings.features["quran_audio"].currentText()) or
            original_audio_researcher != get_audio_val(self.audioSettings.features["researcher"].currentText()) or
            original_audio_broadcasts != get_audio_val(self.audioSettings.features["broadcasts"].currentText()) or
            original_audio_adhan != get_audio_val(self.audioSettings.features["adhan"].currentText()) or
            original_audio_athkar != get_audio_val(self.audioSettings.features["athkar"].currentText()) or
            original_audio_random_athkar != get_audio_val(self.audioSettings.features["random_athkar"].currentText()) or
            original_audio_moton_viewer != get_audio_val(self.audioSettings.features["moton_viewer"].currentText()) or
            original_audio_moton_player != get_audio_val(self.audioSettings.features["moton_player"].currentText())):
            restart_required = 1
        settings_handler.set("audio", "global", get_audio_val(self.audioSettings.global_combo.currentText()))
        settings_handler.set("audio", "quran_viewer", get_audio_val(self.audioSettings.features["quran_viewer"].currentText()))
        settings_handler.set("audio", "quran_player", get_audio_val(self.audioSettings.features["quran_player"].currentText()))
        settings_handler.set("audio", "quran_audio", get_audio_val(self.audioSettings.features["quran_audio"].currentText()))
        settings_handler.set("audio", "researcher", get_audio_val(self.audioSettings.features["researcher"].currentText()))
        settings_handler.set("audio", "broadcasts", get_audio_val(self.audioSettings.features["broadcasts"].currentText()))
        settings_handler.set("audio", "adhan", get_audio_val(self.audioSettings.features["adhan"].currentText()))
        settings_handler.set("audio", "athkar", get_audio_val(self.audioSettings.features["athkar"].currentText()))
        settings_handler.set("audio", "random_athkar", get_audio_val(self.audioSettings.features["random_athkar"].currentText()))
        settings_handler.set("audio", "moton_viewer", get_audio_val(self.audioSettings.features["moton_viewer"].currentText()))
        settings_handler.set("audio", "moton_player", get_audio_val(self.audioSettings.features["moton_player"].currentText()))
        settings_handler.set("g", "exitDialog", str(self.layout1.ExitDialog.isChecked()))
        settings_handler.set("g", "startup_tab", str(self.startupTabSettings.tab_list.currentRow()))
        settings_handler.set("g", "randomMessageAtStartup", str(self.layout1.randomMessageAtStartup.isChecked()))
        settings_handler.set("g", "use_name_in_occasions", str(self.userNameSettings.use_name_checkbox.isChecked()))
        settings_handler.set("g", "name_type", self.userNameSettings.get_selected_name_type())
        settings_handler.set("g", "user_name", self.userNameSettings.custom_name_input.text().strip())
        settings_handler.set("g", "user_gender", self.userNameSettings.get_gender())
        settings_handler.set("quran_search", "ignore_tashkeel", str(self.searchSettings.quran_tashkeel_checkbox.isChecked()))
        settings_handler.set("quran_search", "ignore_hamza", str(self.searchSettings.quran_hamza_checkbox.isChecked()))
        settings_handler.set("quran_search", "ignore_symbols", str(self.searchSettings.quran_symbols_checkbox.isChecked()))
        settings_handler.set("researcher_search", "ignore_tashkeel", str(self.searchSettings.researcher_tashkeel_checkbox.isChecked()))
        settings_handler.set("researcher_search", "ignore_hamza", str(self.searchSettings.researcher_hamza_checkbox.isChecked()))
        settings_handler.set("researcher_search", "ignore_symbols", str(self.searchSettings.researcher_symbols_checkbox.isChecked()))
        settings_handler.set("islamic_books_search", "ignore_tashkeel", str(self.searchSettings.islamic_books_tashkeel_checkbox.isChecked()))
        settings_handler.set("islamic_books_search", "ignore_hamza", str(self.searchSettings.islamic_books_hamza_checkbox.isChecked()))
        settings_handler.set("islamic_books_search", "ignore_symbols", str(self.searchSettings.islamic_books_symbols_checkbox.isChecked()))
        settings_handler.set("moton_search", "ignore_tashkeel", str(self.searchSettings.moton_tashkeel_checkbox.isChecked()))
        settings_handler.set("moton_search", "ignore_hamza", str(self.searchSettings.moton_hamza_checkbox.isChecked()))
        settings_handler.set("moton_search", "ignore_symbols", str(self.searchSettings.moton_symbols_checkbox.isChecked()))
        settings_handler.set("quran_display", "verse_numbering_mode", self.quranDisplaySettings.get_selected_mode())
        settings_handler.set("quran_display", "remove_tashkeel", str(self.quranDisplaySettings.remove_tashkeel_checkbox.isChecked()))
        settings_handler.set("motonViewer", "verse_numbering_mode", self.motonDisplaySettings.get_selected_mode())
        settings_handler.set("motonViewer", "remove_tashkeel", str(self.motonDisplaySettings.remove_tashkeel_checkbox.isChecked()))
        settings_handler.set("motonPlayer", "times", str(self.motonPlayerTimes.times.value()))
        settings_handler.set("motonPlayer", "duration", self.motonPlayerTimes.duration.text())
        settings_handler.set("motonPlayer", "replay", str(self.motonPlayerTimes.replay.isChecked()))
        self.motonRecitersSettings.save_settings()
        if self.layout1.reciter.count() > 0:
             settings_handler.set("g", "reciter", str(list(gui.reciters.keys()).index(self.layout1.reciter.currentText())))
        settings_handler.set("prayerTimes","volume",str(self.prayerTimesSettings.Sound_level.value()))
        settings_handler.set("location","autoDetect",str(self.locationSettings.autoDetectLocation.isChecked()))
        settings_handler.set("location","LT1",str(self.locationSettings.LT1.value()))
        settings_handler.set("location","LT2",str(self.locationSettings.LT2.value()))
        settings_handler.set("location", "calculationMethod", str(self.locationSettings.methodCombo.currentData()))
        settings_handler.set("prayerTimes","remindBeforeAdaan",str(self.prayerTimesSettings.before.currentIndex()))
        settings_handler.set("prayerTimes", "remindAfterAdaan", str(self.prayerTimesSettings.iqamaTime.currentIndex()))
        settings_handler.set("prayerTimes", "iqamaVolume", str(self.prayerTimesSettings.iqamaVolumeSlider.value()))
        try:
            settings_handler.set("tafaseer", "tafaseer", functions.tafseer.tafaseers[self.tafaseerSettings.selectTafaseer.currentText()])
        except Exception as e:
            print(f"Handled exception: {e}")
        try:
            settings_handler.set("translation", "translation", functions.translater.translations[self.tafaseerSettings.selecttranslation.currentText()])
        except Exception as e:
            print(f"Handled exception: {e}")
        settings_handler.set("athkar", "voice", str(self.athkar.voiceSelection.currentIndex()))
        settings_handler.set("athkar", "text", str(self.athkar.textSelection.currentIndex()))
        settings_handler.set("athkar", "text_type", str(self.athkar.textTypeSelection.currentIndex()))
        settings_handler.set("athkar", "playAtStartup", str(self.athkar.playAtStartup.isChecked()))
        settings_handler.set("athkar", "playBasmalaAtStartup", str(self.athkar.playBasmalaAtStartup.isChecked()))
        settings_handler.set("quranPlayer", "times", str(self.quranPlayerTimes.times.value()))
        settings_handler.set("quranPlayer", "duration", self.quranPlayerTimes.duration.text())
        settings_handler.set("prayerTimes", "adaanReminder", str(self.prayerTimesSettings.adaanReminder.isChecked()))
        settings_handler.set("update", "autoCheck", str(self.update.update_autoDect.isChecked()))
        settings_handler.set("athkar", "voiceVolume", str(self.athkar.voiceVolume.value()))
        settings_handler.set("fanar", "api_key", self.fanarSettings.api_key_input.text())
        settings_handler.set("quranPlayer", "replay", str(self.quranPlayerTimes.replay.isChecked()))
        settings_handler.set("update", "beta", str(self.update.update_beta.isChecked()))
        settings_handler.set("prayerTimes", "playPrayerAfterAdhaan", str(self.prayerTimesSettings.playPrayerAfterAdhaan.isChecked()))
        settings_handler.set("khatmah_reminder", "enabled", str(self.khatmahReminderSettings.enable_checkbox.isChecked()))
        settings_handler.set("khatmah_reminder", "hour", str(self.khatmahReminderSettings.hour_spin.value()))
        settings_handler.set("khatmah_reminder", "minute", str(self.khatmahReminderSettings.minute_spin.value()))
        settings_handler.set("khatmah_reminder", "period", self.khatmahReminderSettings.period_combo.currentText())
        settings_handler.set("khatmah_reminder", "missed_alert", str(self.khatmahReminderSettings.missed_alert_checkbox.isChecked()))
        settings_handler.set("khatmah_reminder", "last_reminded_time", "")
        new_font_bold = str(self.fontSettings.bold_checkbox.isChecked())
        new_font_size = str(self.fontSettings.font_size_spinbox.value())
        new_font_wrap = str(self.fontSettings.select_all_checkbox.isChecked())
        settings_handler.set("font", "bold", new_font_bold)
        settings_handler.set("font", "size", new_font_size)
        settings_handler.set("font", "wrap", new_font_wrap)
        font_changed = (original_font_bold != new_font_bold or original_font_size != new_font_size or original_font_wrap != new_font_wrap)
        for key, cb in self.fontSettings.viewer_checkboxes.items():
            new_v_wrap = str(cb.isChecked())
            settings_handler.set("font_wrap", key, new_v_wrap)
            if original_viewer_wraps.get(key) != new_v_wrap:
                font_changed = True
        if font_changed:
            restart_required = 1
        new_use_name = str(self.userNameSettings.use_name_checkbox.isChecked())
        new_name_type = self.userNameSettings.get_selected_name_type()
        new_user_name = self.userNameSettings.custom_name_input.text().strip()
        new_user_gender = self.userNameSettings.get_gender()
        if original_use_name != new_use_name or original_name_type != new_name_type or original_user_name != new_user_name or original_user_gender != new_user_gender:
            restart_required = 1
        new_qs_tashkeel = str(self.searchSettings.quran_tashkeel_checkbox.isChecked())
        new_qs_hamza = str(self.searchSettings.quran_hamza_checkbox.isChecked())
        new_qs_symbols = str(self.searchSettings.quran_symbols_checkbox.isChecked())
        new_rs_tashkeel = str(self.searchSettings.researcher_tashkeel_checkbox.isChecked())
        new_rs_hamza = str(self.searchSettings.researcher_hamza_checkbox.isChecked())
        new_rs_symbols = str(self.searchSettings.researcher_symbols_checkbox.isChecked())
        new_ibs_tashkeel = str(self.searchSettings.islamic_books_tashkeel_checkbox.isChecked())
        new_ibs_hamza = str(self.searchSettings.islamic_books_hamza_checkbox.isChecked())
        new_ibs_symbols = str(self.searchSettings.islamic_books_symbols_checkbox.isChecked())
        new_ms_tashkeel = str(self.searchSettings.moton_tashkeel_checkbox.isChecked())
        new_ms_hamza = str(self.searchSettings.moton_hamza_checkbox.isChecked())
        new_ms_symbols = str(self.searchSettings.moton_symbols_checkbox.isChecked())
        if (orig_qs_tashkeel != new_qs_tashkeel or orig_qs_hamza != new_qs_hamza or orig_qs_symbols != new_qs_symbols or
            orig_rs_tashkeel != new_rs_tashkeel or orig_rs_hamza != new_rs_hamza or orig_rs_symbols != new_rs_symbols or
            orig_ibs_tashkeel != new_ibs_tashkeel or orig_ibs_hamza != new_ibs_hamza or orig_ibs_symbols != new_ibs_symbols or
            orig_ms_tashkeel != new_ms_tashkeel or orig_ms_hamza != new_ms_hamza or orig_ms_symbols != new_ms_symbols):
            restart_required = 1
        self.p.viewInfoTextEdit()
        self.p.runAudioThkarTimer()
        self.p.notification_random_thecker()
        self.p.audio_output.setVolume(int(settings_handler.get("athkar", "voiceVolume")) / 100)
        if restart_required == 1:
            mb = guiTools.QQuestionMessageBox.view(self,"تم تحديث الإعدادات","يجب عليك إعادة تشغيل البرنامج لتطبيق التغييرات. هل تريد إعادة التشغيل الآن؟","إعادة التشغيل الآن","إعادة التشغيل لاحقا")
            if mb==0:
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit()
            else:
                self.close()
        else:
            self.close()

    def default(self):
        mb = guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد إعادة تعيين إعداداتك؟\nإذا قمت بالنقر على إعادة تعيين، سيعيد البرنامج التشغيل لإكمال إعادة التعيين.","إعادة التعيين وإعادة التشغيل","إلغاء")
        if mb==0:
            os.remove(os.path.join(os.getenv('appdata'), app.appName, "settings.ini"))
            os.execl(sys.executable, sys.executable, *sys.argv)

    def fcancel(self):
        self.close()

    def cbts(self, string):
        return True if string == "True" else False


def formatDuration(sectionName: str, keyName: str):
    try:
        value = int(settings_handler.get(sectionName, keyName))
    except Exception:
        value = 0
    result = 0
    if value == 0:
        result = 300
    elif value == 1:
        result = 600
    elif value == 2:
        result = 1200
    elif value == 3:
        result = 1800
    elif value == 4:
        result = 3600
    return result * 1000
