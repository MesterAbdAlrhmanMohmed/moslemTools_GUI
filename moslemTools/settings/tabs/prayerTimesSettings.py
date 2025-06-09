from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import os, shutil,guiTools
class PrayerTimesSettings(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""            
            }
            QCheckBox, QLineEdit {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
            QPushButton {
                background-color: #0000AA; /* اللون الأزرق من شاشة الموت */
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
            }
        """)
        layout = qt.QVBoxLayout(self)
        self.adaanReminder = qt.QCheckBox("التنبيه بالأذان")
        self.adaanReminder.setChecked(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.adaanReminder.stateChanged.connect(self.onprayerTimesReminderCheckboxStateChanged)
        layout.addWidget(self.adaanReminder)
        self.playPrayerAfterAdhaan = qt.QCheckBox("تشغيل الدعاء بعد الأذان")
        self.playPrayerAfterAdhaan.setChecked(p.cbts(settings_handler.get("prayerTimes", "playPrayerAfterAdhaan")))
        self.playPrayerAfterAdhaan.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        layout.addWidget(self.playPrayerAfterAdhaan)
        self.before_laybol=qt.QLabel("التنبيه قبل الأذان ب")
        self.before_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.before_laybol.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        layout.addWidget(self.before_laybol)
        self.before=qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)        
        self.before.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.before.setAccessibleName("التنبيه قبل الأذان ب")
        self.before.addItem("15 دقيقة")
        self.before.addItem("30 دقيقة")
        self.before.addItem("إيقاف")
        self.before.setCurrentIndex(int(settings_handler.get("prayerTimes","remindBeforeAdaan")))
        self.before.setFont(font)
        layout.addWidget(self.before)        
        self.Sound_level_laybol=qt.QLabel("تحديد مستوى صوت الأذان")
        self.Sound_level_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.Sound_level_laybol.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        layout.addWidget(self.Sound_level_laybol)
        self.Sound_level=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Sound_level.setRange(0,100)
        self.Sound_level.setValue(int(settings_handler.get("prayerTimes","volume")))
        self.Sound_level.setAccessibleName("تحديد مستوى صوت الأذان")
        self.Sound_level.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        layout.addWidget(self.Sound_level)
        self.changeFajrSound = qt.QPushButton("تغيير صوت أذان الفجر")
        self.changeFajrSound.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.changeFajrSound.clicked.connect(lambda: self.onChangeAdaanButtonClicked("fajr.mp3"))
        layout.addWidget(self.changeFajrSound)
        self.changeAdaanSound = qt.QPushButton("تغيير صوت الأذان")
        self.changeAdaanSound.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.changeAdaanSound.clicked.connect(lambda: self.onChangeAdaanButtonClicked("genral.mp3"))
        layout.addWidget(self.changeAdaanSound)
        self.worning = qt.QLineEdit()
        self.worning.setReadOnly(True)
        self.worning.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.worning.setText("تنبيه هام, في حالة اختيار صوت للأذان من الجهاز, الرجاء اختيار ملف صوتي بامتداد .mp3")
        self.worning.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.worning)
    def onprayerTimesReminderCheckboxStateChanged(self, state):
        self.playPrayerAfterAdhaan.setVisible(state)
        self.changeAdaanSound.setVisible(state)
        self.changeFajrSound.setVisible(state)
        self.worning.setVisible(state)
        self.changeFajrSound.setVisible(state)
        self.before.setVisible(state)
        self.before_laybol.setVisible(state)
        self.Sound_level_laybol.setVisible(state)
        self.Sound_level.setVisible(state)
    def onChangeAdaanButtonClicked(self, adaanName):
        contextMenu = qt.QMenu("اختر صوت", self)
        contextMenu.setAccessibleName("اختر صوت")
        default = qt1.QAction("الأذان الإفتراضي", self)
        contextMenu.addAction(default)
        contextMenu.setDefaultAction(default)
        default.triggered.connect(lambda: self.onDefaultActionTriggered(adaanName))
        chooseFromDevice = qt1.QAction("اختر من الجهاز", self)
        contextMenu.addAction(chooseFromDevice)
        chooseFromDevice.triggered.connect(lambda: self.onChooseFromDevice(adaanName))
        contextMenu.setFocus()
        mouse_position = qt1.QCursor.pos()
        contextMenu.exec(mouse_position)
    def onDefaultActionTriggered(self, adaanName):
        path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", adaanName)
        try:
            os.remove(path)
            shutil.copy("data/sounds/adaan/" + adaanName, path)
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تغيير صوت الأذان بنجاح")
        except:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ غير متوقع")
    def onChooseFromDevice(self, adaanName):
        path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", adaanName)
        fileDialog = qt.QFileDialog(self, "اختر صوت")
        fileDialog.setDefaultSuffix("mp3")
        fileDialog.setNameFilters(["audio files(*.mp3)"])
        if fileDialog.exec() == fileDialog.DialogCode.Accepted:
            try:
                os.remove(path)
                shutil.copy(fileDialog.selectedFiles()[0], path)
                guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تغيير صوت الأذان بنجاح")
            except:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ غير متوقع")