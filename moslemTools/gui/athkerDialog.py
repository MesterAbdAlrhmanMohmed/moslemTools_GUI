import time,winsound,pyperclip,os,settings,shutil
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
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.athkerViewer.setFont(font)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabelself.show_font=qt.QLineEdit()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.N_theker=qt.QPushButton("الذكر التالي")
        self.N_theker.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_theker.clicked.connect(self.onNextThker)
        self.N_theker.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=qt.QPushButton("تشغيل")
        self.PPS.clicked.connect(self.onPlay)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.PPS.setAccessibleDescription("space")
        self.P_thekr=qt.QPushButton("الذكر السابق")        
        self.P_thekr.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_thekr.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_thekr.clicked.connect(self.onPreviousThker)
        layout.addWidget(self.athkerViewer)
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
    def onPlay(self):
        if self.media.isPlaying():
            self.media.pause()
            self.PPS.setText("تشغيل")
        else:            
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3")):
                url=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.windowTitle(),str(self.inex) + ".mp3"))
            else:
                url=qt2.QUrl(self.athkerList[self.inex]["audio"])
            if url==self.media.source():
                pass
            else:
                self.media.setSource(url)
            self.media.play()            
            self.PPS.setText("إيقاف مؤقت")
    def closeEvent (self,event):
        self.media.stop()        
        self.close()
    def onNextThker(self):
        self.media.stop()
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
        self.PPS.setText("تشغيل")
        if self.inex==0:
            self.inex=len(self.athkerList)-1
            winsound.Beep(1000,200)
        else:
            self.inex-=1
        self.athkerViewer.setText(self.athkerList[self.inex]["text"])
        winsound.PlaySound("data/sounds/previous_page.wav",1)        
    def OnContextMenu(self):
        menu=qt.QMenu("الخيارات",self)
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        save=menu.addAction("حفظ كملف نصي")
        save.triggered.connect(self.save_text_as_txt)
        menu.setDefaultAction(save)
        print=menu.addAction("طباعة")
        print.triggered.connect(self.print_text)
        copy_all=menu.addAction("نسخ النص كاملا")        
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text=menu.addAction("نسخ النص المحدد")
        copy_selected_text.triggered.connect(self.copy_line)
        fontMenu=qt.QMenu("حجم الخط",self)
        incressFontAction=qt1.QAction("تكبير الخط",self)
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction=qt1.QAction("تصغير الخط",self)
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        menu.addMenu(fontMenu)        
        fontMenu.setFont(boldFont)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
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
                winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text=self.athkerViewer.toPlainText()
            pyperclip.copy(text)            
            winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def volume_up(self):
        self.audioOutput.setVolume(self.audioOutput.volume()+0.10)
    def volume_down(self):
        self.audioOutput.setVolume(self.audioOutput.volume()-0.10)