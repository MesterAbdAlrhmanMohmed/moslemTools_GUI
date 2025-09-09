import time,winsound,pyperclip,os,settings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
import guiTools
class AthkerDialog (qt.QDialog):
    def __init__(self,p,title:str,athkerList:list):
        super().__init__(p)        
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)        
        self.setWindowTitle(title)
        layout=qt.QVBoxLayout(self)
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.media.setAudioOutput(self.audioOutput)
        self.media.setSource(qt2.QUrl.fromLocalFile("data/sounds/001001.mp3"))
        self.media.play()
        time.sleep(0.5)        
        self.media.stop()
        self.athkerList=athkerList
        self.inex=0
        self.athkerViewer=guiTools.QReadOnlyTextEdit()                                        
        self.athkerViewer.setText(self.athkerList[self.inex]["text"])
        self.athkerViewer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkerViewer.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.athkerViewer.setFont(font)                
        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0, 100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.media_progress.setAccessibleName("شريط تتبع الصوت")                
        self.time_label = qt.QLabel()        
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setVisible(False)
        progress_time_layout = qt.QHBoxLayout()
        progress_time_layout.addWidget(self.media_progress, 3)
        progress_time_layout.addWidget(self.time_label)
        
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.N_theker=guiTools.QPushButton("الذكر التالي")
        self.N_theker.setAutoDefault(False)
        self.N_theker.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_theker.clicked.connect(self.onNextThker)
        self.N_theker.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=guiTools.QPushButton("تشغيل")
        self.PPS.clicked.connect(self.onPlay)
        self.PPS.setAutoDefault(False)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.PPS.setAccessibleDescription("space")
        self.P_thekr=guiTools.QPushButton("الذكر السابق")        
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
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
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
        if self.media.isPlaying():
            self.media.pause()
            self.PPS.setText("تشغيل")
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)
        else:            
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3")):
                url=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3"))
            else:
                url=qt2.QUrl(self.athkerList[self.inex]["audio"])
            if url == self.media.source():
                pass
            else:
                self.media.setSource(url)
            self.media.play()
            self.media_progress.setVisible(True)
            self.time_label.setVisible(True)
            self.PPS.setText("إيقاف مؤقت")            
    def closeEvent (self,event):
        self.media.stop()        
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
        winsound.PlaySound("data/sounds/previous_page.wav",1)                
    def OnContextMenu(self):                        
        self.was_playing = self.media.isPlaying()                
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")            
        menu = qt.QMenu(self)
        boldFont = qt1.QFont()
        boldFont.setBold(True)
        menu.setFont(boldFont)        
        athkar_menu = qt.QMenu("خيارات الأذكار", self)
        athkar_menu.setFont(boldFont)                
        next_action = qt1.QAction("الذكر التالي", self)
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.onNextThker)
        athkar_menu.addAction(next_action)        
        previous_action = qt1.QAction("الذكر السابق", self)
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.onPreviousThker)
        athkar_menu.addAction(previous_action)                        
        menu.addMenu(athkar_menu)                
        text_menu = qt.QMenu("خيارات النص", self)
        text_menu.setFont(boldFont)        
        save = qt1.QAction("حفظ كملف نصي", self)
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)
        text_menu.addAction(save)        
        print_action = qt1.QAction("طباعة", self)
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        text_menu.addAction(print_action)        
        copy_all = qt1.QAction("نسخ النص كاملا", self)
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        text_menu.addAction(copy_all)        
        copy_selected_text = qt1.QAction("نسخ النص المحدد", self)
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_line)
        text_menu.addAction(copy_selected_text)        
        font_menu = qt.QMenu("حجم الخط", self)
        font_menu.setFont(boldFont)        
        increase_action = qt1.QAction("تكبير الخط", self)
        increase_action.setShortcut("ctrl+=")
        increase_action.triggered.connect(self.increase_font_size)
        font_menu.addAction(increase_action)        
        decrease_action = qt1.QAction("تصغير الخط", self)
        decrease_action.setShortcut("ctrl+-")
        decrease_action.triggered.connect(self.decrease_font_size)
        font_menu.addAction(decrease_action)                
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        font_menu.addAction(set_font_size)
        menu.addMenu(text_menu)
        menu.addMenu(font_menu)                
        menu.aboutToHide.connect(self.resume_playback)        
        menu.exec(qt1.QCursor.pos())    
    def resume_playback(self):
        if hasattr(self, 'was_playing') and self.was_playing and not self.media.isPlaying():
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
        if self.font_size < 50:
            self.font_size += 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()            
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()            
    def update_font_size(self):
        cursor=self.athkerViewer.textCursor()
        self.athkerViewer.selectAll()
        font=self.athkerViewer.font()
        font.setPointSize(self.font_size)
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
    def set_font_size_dialog(self):
        try:
            size, ok = guiTools.QInputDialog.getInt(
                self,
                "تغيير حجم الخط",
                "أدخل حجم الخط (من 1 الى 50):",
                value=self.font_size,
                min=1,
                max=50
            )
            if ok:
                self.font_size = size
                self.show_font.setText(str(self.font_size))
                self.update_font_size()
                guiTools.speak(f"تم تغيير حجم الخط إلى {size}")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "حدث خطأ", str(error))