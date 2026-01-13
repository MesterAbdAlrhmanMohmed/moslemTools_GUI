import guiTools,functions,gui,subprocess,os,sys
from . import settings_handler, app, tabs
from .tabs import audioSettings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt
class settings(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        self.resize(590,430)
        self.center()
        self.setWindowTitle("الإعدادات")
        self.p = p                
        layout = qt.QVBoxLayout()
        self.sectian_l=qt.QLabel("اختر قسم")
        layout.addWidget(self.sectian_l,alignment=Qt.AlignmentFlag.AlignCenter)
        self.sectian = guiTools.ComboBook()
        self.sectian.setFocus()
        font = qt1.QFont()
        font.setBold(True)
        self.sectian.setStyleSheet("color: #e0e0e0;")
        self.sectian.setAccessibleName("اختر قسم")
        self.sectian.setFont(font)
        layout.addWidget(self.sectian)
        layout.addWidget(self.sectian.w)
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
        self.fontSettings = tabs.FontSettings()
        self.sectian.add("إعدادات نوع الخط وحجمه للعارضات", self.fontSettings)
        self.tafaseerSettings = tabs.TafaseerSettings()
        self.sectian.add("إعدادات التفسير والترجمة لتبويبة القرآن الكريم مكتوب", self.tafaseerSettings)
        self.prayerTimesSettings = tabs.PrayerTimesSettings(self)
        self.sectian.add("إعدادات الأذان", self.prayerTimesSettings)
        self.locationSettings=tabs.LocationSettings(self)
        self.sectian.add("إعدادات تحديد الموقع الجغرافي لمواقيت الصلاة",self.locationSettings)
        self.quranPlayerTimes = tabs.QuranPlayerSettings(self)
        self.sectian.add("إعدادات مشغل القرآن لتبويبة القرآن الكريم مكتوب", self.quranPlayerTimes)
        self.sectian.add("إعدادات التحديثات", self.update)
        self.athkar = tabs.AthkarSettings()
        self.sectian.add("إعدادات الأذكار العشوائية", self.athkar)
        self.audioSettings = audioSettings.AudioSettings(self)
        self.sectian.add("إعدادات تحديد كرت الصوت", self.audioSettings)
        self.sectian.add("تحميل موارد", tabs.Download())
        restoar = tabs.Restoar(self)
        self.sectian.add("النسخ الاحتياطي والاستعادة", restoar)
        buttonsLayout.addWidget(self.ok)
        buttonsLayout.addWidget(self.defolt)
        buttonsLayout.addWidget(self.cancel)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)
    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    def fok(self):
        restart_required = 0
        original_font_bold = settings_handler.get("font", "bold")
        original_font_size = settings_handler.get("font", "size")
        
        # Save Audio Settings
        settings_handler.set("audio", "global", self.audioSettings.global_combo.currentText())
        settings_handler.set("audio", "quran_text", self.audioSettings.features["quran_text"].currentText())
        settings_handler.set("audio", "quran_audio", self.audioSettings.features["quran_audio"].currentText())
        settings_handler.set("audio", "stories", self.audioSettings.features["stories"].currentText())
        settings_handler.set("audio", "broadcasts", self.audioSettings.features["broadcasts"].currentText())
        settings_handler.set("audio", "adhan", self.audioSettings.features["adhan"].currentText())
        settings_handler.set("audio", "athkar", self.audioSettings.features["athkar"].currentText())
        settings_handler.set("audio", "random_athkar", self.audioSettings.features["random_athkar"].currentText())

        settings_handler.set("g", "exitDialog", str(self.layout1.ExitDialog.isChecked()))
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
        except:
            pass
        try:
            settings_handler.set("translation", "translation", functions.translater.translations[self.tafaseerSettings.selecttranslation.currentText()])
        except:
            pass
        settings_handler.set("athkar", "voice", str(self.athkar.voiceSelection.currentIndex()))
        settings_handler.set("athkar", "text", str(self.athkar.textSelection.currentIndex()))
        settings_handler.set("athkar", "playAtStartup", str(self.athkar.playAtStartup.isChecked()))
        settings_handler.set("athkar", "playBasmalaAtStartup", str(self.athkar.playBasmalaAtStartup.isChecked()))
        settings_handler.set("quranPlayer", "times", str(self.quranPlayerTimes.times.value()))
        settings_handler.set("quranPlayer", "duration", self.quranPlayerTimes.duration.text())
        settings_handler.set("prayerTimes", "adaanReminder", str(self.prayerTimesSettings.adaanReminder.isChecked()))
        settings_handler.set("update", "autoCheck", str(self.update.update_autoDect.isChecked()))
        settings_handler.set("athkar", "voiceVolume", str(self.athkar.voiceVolume.value()))
        settings_handler.set("quranPlayer", "replay", str(self.quranPlayerTimes.replay.isChecked()))
        settings_handler.set("update", "beta", str(self.update.update_beta.isChecked()))
        settings_handler.set("prayerTimes", "playPrayerAfterAdhaan", str(self.prayerTimesSettings.playPrayerAfterAdhaan.isChecked()))
        new_font_bold = str(self.fontSettings.bold_checkbox.isChecked())
        new_font_size = str(self.fontSettings.font_size_spinbox.value())
        settings_handler.set("font", "bold", new_font_bold)
        settings_handler.set("font", "size", new_font_size)
        
        # Save Audio Settings
        settings_handler.set("audio", "global", self.audioSettings.global_combo.currentText())
        settings_handler.set("audio", "quran_text", self.audioSettings.features["quran_text"].currentText())
        settings_handler.set("audio", "quran_audio", self.audioSettings.features["quran_audio"].currentText())
        settings_handler.set("audio", "stories", self.audioSettings.features["stories"].currentText())
        settings_handler.set("audio", "broadcasts", self.audioSettings.features["broadcasts"].currentText())
        settings_handler.set("audio", "adhan", self.audioSettings.features["adhan"].currentText())
        settings_handler.set("audio", "athkar", self.audioSettings.features["athkar"].currentText())
        settings_handler.set("audio", "random_athkar", self.audioSettings.features["random_athkar"].currentText())

        if original_font_bold != new_font_bold or original_font_size != new_font_size:
            restart_required = 1
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
        mb = guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد إعادة تعيين إعداداتك؟ إذا قمت بالنقر على إعادة تعيين، سيعيد البرنامج التشغيل لإكمال إعادة التعيين.","إعادة التعيين وإعادة التشغيل","إلغاء")
        if mb==0:
            os.remove(os.path.join(os.getenv('appdata'), app.appName, "settings.ini"))
            os.execl(sys.executable, sys.executable, *sys.argv)
    def fcancel(self):
        self.close()
    def cbts(self, string):
        return True if string == "True" else False
def formatDuration(sectionName: str, keyName: str):
    value = int(settings_handler.get(sectionName, keyName))
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