from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import os, shutil, guiTools
class PrayerTimesSettings(qt.QWidget):
    def __init__(self, p):
        super().__init__()                
        self.setStyleSheet("""           
            QCheckBox, QLineEdit, QLabel {                 
                color: #e0e0e0;
                padding: 4px;
            }
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }            
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #555;
                border-radius: 4px;                
            }            
            }
        """)        
        main_layout = qt.QVBoxLayout(self)        
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)                
        group_box = qt.QGroupBox("إعدادات الأذان")
        group_layout = qt.QVBoxLayout(group_box)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(12, 15, 12, 15)                
        row1_layout = qt.QHBoxLayout()
        row1_layout.setSpacing(15)        
        self.adaanReminder = qt.QCheckBox("التنبيه بالأذان")
        self.adaanReminder.setChecked(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.adaanReminder.stateChanged.connect(self.onprayerTimesReminderCheckboxStateChanged)
        row1_layout.addWidget(self.adaanReminder)        
        self.playPrayerAfterAdhaan = qt.QCheckBox("تشغيل الدعاء بعد الأذان")
        self.playPrayerAfterAdhaan.setChecked(p.cbts(settings_handler.get("prayerTimes", "playPrayerAfterAdhaan")))
        self.playPrayerAfterAdhaan.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))                
        row1_layout.addWidget(self.playPrayerAfterAdhaan)
        row1_layout.addStretch()        
        group_layout.addLayout(row1_layout)                
        row2_layout = qt.QHBoxLayout()
        row2_layout.setSpacing(10)        
        self.beforeLabel = qt.QLabel("التنبيه قبل الأذان ب:")
        self.beforeLabel.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))                
        self.font_for_widgets=qt1.QFont()
        self.font_for_widgets.setBold(True)        
        self.before = qt.QComboBox()
        self.before.setFont(self.font_for_widgets)
        self.before.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.before.setAccessibleName("التنبيه قبل الأذان ب")                    
        self.before.addItem("15 دقيقة") 
        self.before.addItem("30 دقيقة")
        self.before.addItem("ساعة")    
        self.before.addItem("إيقاف")            
        self.before.setCurrentIndex(int(settings_handler.get("prayerTimes", "remindBeforeAdaan")))        
        row2_layout.addWidget(self.before)
        row2_layout.addWidget(self.beforeLabel)
        row2_layout.addStretch()        
        group_layout.addLayout(row2_layout)        
        row3_layout = qt.QHBoxLayout()
        row3_layout.setSpacing(10)        
        initial_volume = int(settings_handler.get("prayerTimes", "volume"))
        self.soundLevelLabel = qt.QLabel(f"مستوى صوت الأذان: {initial_volume}%")
        self.soundLevelLabel.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))                
        self.Sound_level = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Sound_level.setRange(0, 100)
        self.Sound_level.setValue(initial_volume)
        self.Sound_level.setAccessibleName("تحديد مستوى صوت الأذان")
        self.Sound_level.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))        
        self.Sound_level.valueChanged.connect(self.onSoundLevelChanged)
        row3_layout.addWidget(self.Sound_level, 2)
        row3_layout.addWidget(self.soundLevelLabel)
        group_layout.addLayout(row3_layout)                
        self.changeAdhanSound = qt.QPushButton("تغيير أصوات الأذان")
        self.changeAdhanSound.setVisible(p.cbts(settings_handler.get("prayerTimes", "adaanReminder")))
        self.changeAdhanSound.clicked.connect(self.onChangeAdhanButtonClicked)
        group_layout.addWidget(self.changeAdhanSound, 0, qt2.Qt.AlignmentFlag.AlignRight)        
        main_layout.addWidget(group_box)
        main_layout.addStretch()                    
    def onSoundLevelChanged(self, value):        
        self.soundLevelLabel.setText(f"مستوى صوت الأذان: {value}%")        
    def onprayerTimesReminderCheckboxStateChanged(self, state):        
        is_checked = bool(state)
        self.playPrayerAfterAdhaan.setVisible(is_checked)
        self.changeAdhanSound.setVisible(is_checked)        
        self.before.setVisible(is_checked)
        self.beforeLabel.setVisible(is_checked)
        self.soundLevelLabel.setVisible(is_checked)
        self.Sound_level.setVisible(is_checked)                
    def onChangeAdhanButtonClicked(self):
        contextMenu = qt.QMenu("اختر صلاة لتغيير صوت أذانها", self)
        font = qt1.QFont()
        font.setBold(True)
        contextMenu.setFont(font)
        contextMenu.setAccessibleName("اختر صلاة لتغيير صوت أذانها")
        prayers = [
            ("الفجر", "fajr"),
            ("الظهر", "dhuhr"),
            ("العصر", "asr"),
            ("المغرب", "maghrib"),
            ("العشاء", "isha")
        ]        
        for prayer_name, prayer_key in prayers:
            prayerAction = qt1.QAction(prayer_name, self)
            prayerAction.triggered.connect(lambda checked, key=prayer_key: self.onPrayerSelected(key))
            contextMenu.addAction(prayerAction)        
        contextMenu.setFocus()
        mouse_position = qt1.QCursor.pos()
        contextMenu.exec(mouse_position)                
    def onPrayerSelected(self, prayer_key):        
        soundMenu = qt.QMenu("اختر صوت", self)        
        soundMenu.setAccessibleName("اختر صوت")
        font1 = qt1.QFont()
        font1.setBold(True)
        soundMenu.setFont(font1)
        default = qt1.QAction("الصوت الافتراضي", self)
        default.triggered.connect(lambda: self.onDefaultActionTriggered(prayer_key))
        soundMenu.addAction(default)        
        chooseFromDevice = qt1.QAction("اختر من الجهاز", self)
        chooseFromDevice.triggered.connect(lambda: self.onChooseFromDevice(prayer_key))
        soundMenu.addAction(chooseFromDevice)        
        soundMenu.setFocus()
        mouse_position = qt1.QCursor.pos()
        soundMenu.exec(mouse_position)            
    def onDefaultActionTriggered(self, prayer_key):        
        default_file = "fajr.mp3" if prayer_key == "fajr" else "genral.mp3"
        path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", default_file)        
        try:                        
            if os.path.exists(path):
                os.remove(path)                        
            shutil.copy(os.path.join("data/sounds/adaan/", default_file), path)                        
            settings_handler.set("adhanSounds", prayer_key, default_file)            
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم استعادة الصوت الافتراضي بنجاح.")
        except Exception as e: 
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")                
    def onChooseFromDevice(self, prayer_key):        
        fileDialog = qt.QFileDialog(self, "اختر ملف صوتي")
        fileDialog.setFileMode(qt.QFileDialog.FileMode.ExistingFile)
        fileDialog.setNameFilter("ملفات الصوت (*.mp3 *.wav *.wma *.aac *.m4a *.flac *.ogg *.opus *.ape *.mpga *.alac *.wv *.mka *.aiff *.au *.dss *.iff *.m4r *.m4b *.midi *.mid *.ac3 *.tta *.m3u *.amr *.awb *.caf *.mod *.s3m *.xm *.it *.ra *.rm *.bwf *.rf64 *.pcm *.asf *.dvf *.msv *.qcp *.slk *.vox *.voc *.snd *.adx *.aif *.aifc *.ast *.brstm *.dts *.gsm *.m4p *.mp1 *.mp2 *.mus *.sb0 *.smp *.spx *.w64 *.xma *.ac3 *.dct *.ec3 *.mka *.mlp *.ofr *.tak *.thd *.tta *.wv)")
        if fileDialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            try:
                selected_file = fileDialog.selectedFiles()[0]                
                if not selected_file:
                    return                
                file_ext = os.path.splitext(selected_file)[1]                                
                new_filename = f"{prayer_key}{file_ext}"
                path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", new_filename)                                
                existing_files = os.listdir(os.path.join(os.getenv('appdata'), settings_handler.appName, "addan"))
                for file in existing_files:
                    if file.startswith(prayer_key):
                        os.remove(os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", file))                                
                shutil.copy(selected_file, path)                                
                settings_handler.set("adhanSounds", prayer_key, new_filename)                
                guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تغيير صوت الأذان بنجاح.")
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")