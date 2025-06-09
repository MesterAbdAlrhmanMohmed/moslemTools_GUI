from .changeReciter import ChangeReciter
from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
import time,gettext,os,json,winsound
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)
class QuranPlayer(qt.QDialog):
    def __init__(self,p,text,index:int,type,category,enableBookMarks=True):
        super().__init__(p)                                
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.currentReciter=int(settings.settings_handler.get("g","reciter"))
        self.enableBookmarks=enableBookMarks
        self.resize(1200,600)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.type=type
        self.times=int(settings.settings_handler.get("quranPlayer","times"))
        self.currentTime=1
        self.category=category
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.media.setAudioOutput(self.audioOutput)
        self.media.setSource(qt2.QUrl.fromLocalFile("data/sounds/001001.mp3"))
        self.media.play()
        time.sleep(0.5)
        self.media.stop()
        self.media.mediaStatusChanged.connect(self.on_state)
        self.index=index-1        
        self.quranText=text.split("\n")
        self.text=guiTools.QReadOnlyTextEdit()
        self.text.setText(text[index-1])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.text.setFocus()
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        self.text.setFont(font)        
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.media_progress.setAccessibleName("التحكم في تقدم الآية")
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLineEdit()
        self.show_font.setReadOnly(True)
        self.show_font.setAccessibleName("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))        
        self.N_aya=qt.QPushButton("الآيا التالية")
        self.N_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_aya.clicked.connect(self.onNextAyah)
        self.N_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_aya.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=qt.QPushButton("تشغيل")
        self.PPS.setAccessibleDescription("space")
        self.PPS.clicked.connect(self.on_play)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya=qt.QPushButton("الآيا السابقة")
        self.P_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya.clicked.connect(self.onPreviousAyah)
        self.P_aya.setAccessibleDescription("alt زائد السهم الأيسر")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.media_progress)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout1=qt.QHBoxLayout()
        layout1.addWidget(self.P_aya)
        layout1.addWidget(self.PPS)        
        layout1.addWidget(self.N_aya)
        self.changeCurrentReciterButton=qt.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.clicked.connect(self.onChangeRecitersContextMenuRequested)
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCurrentReciterButton.setShortcut("ctrl+shift+r")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus R")
        layout1.addWidget(self.changeCurrentReciterButton)

        layout.addLayout(layout1)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.gotoayah)
        qt1.QShortcut("alt+right",self).activated.connect(self.onNextAyah)
        qt1.QShortcut("alt+left",self).activated.connect(self.onPreviousAyah)
        qt1.QShortcut("escape",self).activated.connect(self.close)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("shift+up",self).activated.connect(self.volume_up)
        qt1.QShortcut("shift+down",self).activated.connect(self.volume_down)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)        
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        self.on_play()
    def OnContextMenu(self):
        if self.media.isPlaying():
            self.media.pause()
            self.PPS.setText("تشغيل")
        menu=qt.QMenu("الخيارات",self)
        menu.setAccessibleName("الخيارات")
        aya=qt.QMenu("خيارات الآية",self)
        GoToAya=qt1.QAction("الذهاب الى آيا",self)
        GoToAya.setShortcut("ctrl+g")
        aya.addAction(GoToAya)
        aya.setDefaultAction(GoToAya)
        GoToAya.triggered.connect(self.gotoayah)
        aya_info=qt1.QAction("معلومات الآيا الحالية",self)
        aya_info.setShortcut("ctrl+f")
        aya.addAction(aya_info)
        aya_info.triggered.connect(self.getAyahInfo)
        aya_trans=qt1.QAction("ترجمة الآيا الحالية",self)
        aya_trans.setShortcut("ctrl+l")
        aya.addAction(aya_trans)
        aya_trans.triggered.connect(self.getCurentAyahTranslation)
        aya_tafsseer=qt1.QAction("تفسير الآيا الحالية",self)
        aya_tafsseer.setShortcut("ctrl+t")
        aya.addAction(aya_tafsseer)
        aya_tafsseer.triggered.connect(self.getCurentAyahTafseer)
        aya_arab=qt1.QAction("إعراب الآيا الحالية",self)
        aya_arab.setShortcut("ctrl+i")
        aya.addAction(aya_arab)
        aya_arab.triggered.connect(self.getCurentAyahIArab)        
        aya_tanzeel=qt1.QAction("أسباب نزول الآيا الحالية",self)
        aya_tanzeel.setShortcut("ctrl+r")
        aya.addAction(aya_tanzeel)
        aya_tanzeel.triggered.connect(self.getCurrentAyahTanzel)        
        state,self.nameOfBookmark=functions.bookMarksManager.getQuranBookmarkName(self.type,self.category,self.index,isPlayer=True)
        if state:
            removeBookmarkAction=qt1.QAction("حذف العلامة المرجعية",self)
            removeBookmarkAction.setShortcut("ctrl+b")
            aya.addAction(removeBookmarkAction)
            removeBookmarkAction.triggered.connect(self.onRemoveBookmark)
        else:
            addNewBookMark=qt1.QAction("إضافة علامة مرجعية",self)
            addNewBookMark.setShortcut("ctrl+b")
            aya.addAction(addNewBookMark)
            addNewBookMark.triggered.connect(self.onAddBookMark)
            addNewBookMark.setEnabled(self.enableBookmarks)
        Previous_aya=qt1.QAction("الآيا السابقة",self)
        Previous_aya.setShortcut("alt+left")
        aya.addAction(Previous_aya)
        Previous_aya.triggered.connect(self.onPreviousAyah)
        next_aya=qt1.QAction("الآيا التالية",self)
        next_aya.setShortcut("alt+right")
        aya.addAction(next_aya)
        next_aya.triggered.connect(self.onNextAyah)
        menu.setFocus()
        fontMenu=qt.QMenu("حجم الخط",self)
        incressFontAction=qt1.QAction("تكبير الخط",self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction=qt1.QAction("تصغير الخط",self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        menu.addMenu(aya)
        menu.addMenu(fontMenu)        
        menu.exec(self.mapToGlobal(self.cursor().pos()))
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
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=self.text.font()
        font.setPointSize(self.font_size)
        self.text.setCurrentFont(font)        
        self.text.setTextCursor(cursor)
    def on_set(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"
    def on_play(self):
        if not self.media.isPlaying():
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set())):
                path=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set()))
            else:
                path=qt2.QUrl(reciters[self.getCurrentReciter()] + self.on_set())
            if not self.media.source()==path:
                self.media.setSource(path)
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
        else:
            self.media.pause()
            self.PPS.setText("تشغيل")
    def gotoayah(self):
        self.media.stop()
        number,ok=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية",self.index+1,1,len(self.quranText))
        if ok:
            self.currentTime=1
            self.index=number-1
            self.text.setText(self.quranText[self.index])
            self.update_font_size()
            self.on_play()
    def onNextAyah(self):
        self.currentTime=1
        if self.index+1==len(self.quranText):
            self.index=0
        else:
            self.index+=1
        self.text.setText(self.quranText[self.index])
        self.update_font_size()
        self.media.stop()
        self.on_play()
    def onPreviousAyah(self):
        self.currentTime=1
        if self.index==0:
            self.index=len(self.quranText)-1
        else:
            self.index-=1
        self.text.setText(self.quranText[self.index])
        self.update_font_size()
        self.media.stop()
        self.on_play()
    def getcurrentAyahText(self):
        return self.text.toPlainText()
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            if self.times==self.currentTime:
                if settings.settings_handler.get("quranPlayer","replay")=="False":
                    if not self.index+1==len(self.quranText):
                        qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
                    else:
                        self.PPS.setText("تشغيل")
                        self.index=0
                        self.text.setText(self.quranText[self.index])
                else:
                    qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
            else:
                self.currentTime+=1
                qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.media.play)
    def getCurrentReciter(self):
        index=self.currentReciter
        name=list(reciters.keys())[index]
        return name
    def getCurentAyahTafseer(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
    def closeEvent(self,event):
        self.media.stop()
        self.close()
    def getCurentAyahIArab(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        guiTools.TextViewer(self,"إعراب",result).exec()
    def getCurrentAyahTanzel(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            guiTools.TextViewer(self,"اسباب النزول",result).exec()
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
    def getAyahInfo(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} رقم السورة {} {} رقم الآية في المصحف {} الجزء {} الربع {} الصفحة {} {}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
    def getCurentAyahTranslation(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        translationViewer(self,AyahNumber,AyahNumber).exec()    
    def onAddBookMark(self):
        if self.enableBookmarks==False:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا يمكن وضع علامة مرجعية عند تصفح القرآن بشكلا مخصص")
            return
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            functions.bookMarksManager.addNewQuranBookMark(self.type,self.category,self.index,True,name)
    def volume_up(self):
        self.audioOutput.setVolume(self.audioOutput.volume()+0.10)
    def volume_down(self):
        self.audioOutput.setVolume(self.audioOutput.volume()-0.10)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeQuranBookMark(self.nameOfBookmark)
            winsound.Beep(1000,100)
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state,self.nameOfBookmark=functions.bookMarksManager.getQuranBookmarkName(self.type,self.category,self.index,isPlayer=True)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)
    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            self.media_progress.setValue(int((self.media.position() / self.media.duration()) * 100))
            self.media_progress.blockSignals(False)
        except:
            pass
    def onChangeRecitersContextMenuRequested(self):
        self.media.stop()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.on_play()