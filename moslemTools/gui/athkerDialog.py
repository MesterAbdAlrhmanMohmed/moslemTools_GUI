import time,winsound,pyperclip,os,settings,json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
import guiTools
from functions import audio_manager
class AthkerDialog (qt.QDialog):
    def __init__(self,p,title:str,athkerList:list):
        super().__init__(p)        
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)        
        self.setWindowTitle(title)
        layout=qt.QVBoxLayout(self)        
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.media=QMediaPlayer(self)
        self.apply_speed()
        self.audioOutput=QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("athkar"))
        self.media.setAudioOutput(self.audioOutput)
        self.media.setSource(qt2.QUrl.fromLocalFile("data/sounds/001001.mp3"))
        self.media.play()
        time.sleep(0.5)        
        self.media.stop()
        self.athkerList=athkerList
        self.inex=0
        self.athkerViewer=guiTools.QReadOnlyTextEdit(viewer_name="athkerDialog")                                        
        self.athkerViewer.setText(self.athkerList[self.inex]["text"])
        self.athkerViewer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkerViewer.customContextMenuRequested.connect(self.OnContextMenu)    
        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0, 100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.media_progress.setAccessibleName("التحكم في تقدم المقطع")
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.time_label = qt.QLabel()        
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setVisible(False)
        progress_time_layout = qt.QHBoxLayout()
        progress_time_layout.addWidget(self.media_progress, 3)
        progress_time_layout.addWidget(self.time_label)        
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.N_theker=guiTools.QPushButton("التالي")
        self.N_theker.setAutoDefault(False)
        self.N_theker.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_theker.clicked.connect(self.onNextThker)
        self.N_theker.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=guiTools.QPushButton("تشغيل")
        self.PPS.clicked.connect(self.onPlay)
        self.PPS.setAutoDefault(False)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.PPS.setAccessibleDescription("space")
        self.P_thekr=guiTools.QPushButton("السابق")        
        self.P_thekr.setAutoDefault(False)
        self.P_thekr.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_thekr.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_thekr.clicked.connect(self.onPreviousThker)
        layout.addWidget(self.athkerViewer)
        layout.addLayout(progress_time_layout)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout1=qt.QHBoxLayout()
        layout1.addWidget(self.P_thekr)
        layout1.addWidget(self.PPS)        
        layout1.addWidget(self.N_theker)
        layout.addLayout(layout1)        
        self.update_font_size()
        qt1.QShortcut("alt+right",self).activated.connect(self.onNextThker)
        qt1.QShortcut("alt+left",self).activated.connect(self.onPreviousThker)
        qt1.QShortcut("space",self).activated.connect(self.onPlay)
        qt1.QShortcut("escape",self).activated.connect(lambda:self.closeEvent(None))        
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)                
        qt1.QShortcut("shift+up",self).activated.connect(self.volume_up)
        qt1.QShortcut("shift+down",self).activated.connect(self.volume_down)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))
    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)    
    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            position = self.media.position()
            duration = self.media.duration()
            if duration > 0:                
                progress_value = int((position / duration) * 100)
                self.media_progress.setValue(progress_value)                                
                self.update_time_label(position, duration)            
            self.media_progress.blockSignals(False)
        except:
            pass        
    def update_time_label(self, position, duration):        
        position_sec = position // 1000
        duration_sec = duration // 1000                
        remaining_sec = duration_sec - position_sec                
        position_str = f"{position_sec // 60}:{position_sec % 60:02d}"
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        remaining_str = f"{remaining_sec // 60}:{remaining_sec % 60:02d}"                
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | المدة الإجمالية: {duration_str}")
    def on_state(self, state):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)
            self.PPS.setText("تشغيل")            
    def onPlay(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.pause()
            self.PPS.setText("تشغيل")
        else:            
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3")):
                url=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3"))
            else:
                url=qt2.QUrl(self.athkerList[self.inex]["audio"])
            if url != self.media.source():
                self.media.setSource(url)
            self.media_progress.setVisible(True)
            self.time_label.setVisible(True)
            self.PPS.setText("إيقاف مؤقت")
            qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.media.play()))            
    def closeEvent (self,event):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.stop()        
            qt2.QTimer.singleShot(100,self.close)
        else:
            self.close()        
    def onNextThker(self):
        self.media.stop()
        self.media_progress.setVisible(False)
        self.time_label.setVisible(False)
        self.PPS.setText("تشغيل")
        if self.inex+1==len(self.athkerList):
            self.inex=0
            winsound.Beep(1000,200)
        else:
            self.inex+=1
        self.athkerViewer.setText(self.athkerList[self.inex]["text"])
        self.update_font_size()
        winsound.PlaySound("data/sounds/next_page.wav",1)        
    def onPreviousThker(self):
        self.media.stop()
        self.media_progress.setVisible(False)
        self.time_label.setVisible(False)
        self.PPS.setText("تشغيل")
        if self.inex==0:
            self.inex=len(self.athkerList)-1
            winsound.Beep(1000,200)
        else:
            self.inex-=1
        self.athkerViewer.setText(self.athkerList[self.inex]["text"])
        self.update_font_size()
        winsound.PlaySound("data/sounds/previous_page.wav",1)                
    def OnContextMenu(self):                        
        self.was_playing = self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState                
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")            
        menu = qt.QMenu(self)
        boldFont = qt1.QFont()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        speed_menu = menu.addMenu("سرعة التشغيل")
        speed_menu.setFont(boldFont)
        current_speed = self.load_speed()
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            action = speed_menu.addAction(f"{s}x")
            action.setCheckable(True)
            action.setChecked(abs(current_speed - s) < 0.01)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))        
        save = qt1.QAction("حفظ كملف نصي", self)
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)
        menu.addAction(save)        
        print_action = qt1.QAction("طباعة", self)
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        menu.addAction(print_action)        
        copy_all = qt1.QAction("نسخ النص كاملا", self)
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        menu.addAction(copy_all)        
        copy_selected_text = qt1.QAction("نسخ النص المحدد", self)
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_line)
        menu.addAction(copy_selected_text)        
        menu.aboutToHide.connect(self.resume_playback)        
        menu.exec(qt1.QCursor.pos())    
    def resume_playback(self):
        if hasattr(self, 'was_playing') and self.was_playing and not self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")            
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.athkerViewer.print(printer)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def save_text_as_txt(self):
        try:
            file_dialog=qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name=file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    text=self.athkerViewer.toPlainText()
                    file.write(text)                
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def increase_font_size(self):
        if self.show_font.value() < 100:
            self.show_font.setValue(self.show_font.value() + 1)
    def decrease_font_size(self):
        if self.show_font.value() > 1:
            self.show_font.setValue(self.show_font.value() - 1)
    def update_font_size(self):
        cursor=self.athkerViewer.textCursor()
        self.athkerViewer.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.athkerViewer.setCurrentFont(font)        
        self.athkerViewer.setTextCursor(cursor)        
    def copy_line(self):
        try:
            cursor=self.athkerViewer.textCursor()
            if cursor.hasSelection():
                selected_text=cursor.selectedText()
                pyperclip.copy(selected_text)                
                guiTools.speak("تم نسخ النص المحدد بنجاح")
                winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def copy_text(self):
        try:
            text=self.athkerViewer.toPlainText()
            pyperclip.copy(text)            
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
            winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def volume_up(self):
        self.audioOutput.setVolume(self.audioOutput.volume()+0.10)        
    def volume_down(self):
        self.audioOutput.setVolume(self.audioOutput.volume()-0.10)
    def load_speed(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("athkerDialog", 1.0)
        except:
            pass
        return 1.0
    def save_speed(self, speed):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    pass
            data["athkerDialog"] = speed
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            pass
    def change_speed(self, speed):
        self.save_speed(speed)
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)
    def apply_speed(self):
        speed = self.load_speed()
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)
    def t10(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.1))
    def t20(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.2))
    def t30(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.3))
    def t40(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.4))
    def t50(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.5))
    def t60(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.6))
    def t70(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.7))
    def t80(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.8))
    def t90(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.9))