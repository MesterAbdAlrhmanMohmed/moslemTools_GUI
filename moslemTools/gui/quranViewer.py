from .changeReciter import ChangeReciter
from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
from .quranPlayer import QuranPlayer
import time,winsound,pyperclip,gettext,os,json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)
class QuranViewer(qt.QDialog):
    def __init__(self,p,text:str,type:int,category,index=0,enableNextPreviouseButtons=False,typeResult=[],CurrentIndex=0,enableBookmarks=True):
        super().__init__(p)        
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.currentReciter=int(settings.settings_handler.get("g","reciter"))
        self.nameOfBookmark=""
        self.enableBookmarks=enableBookmarks
        self.type=type
        self.enableNextPreviouseButtons=enableNextPreviouseButtons
        self.typeResult=typeResult
        self.CurrentIndex=CurrentIndex
        self.resize(1200,600)        
        self.type=type
        self.category=category
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.media.setAudioOutput(self.audioOutput)
        self.media.setSource(qt2.QUrl.fromLocalFile("data/sounds/001001.mp3"))
        self.media.play()
        time.sleep(0.5)
        self.media.stop()
        self.media.mediaStatusChanged.connect(self.on_state)
        self.quranText=text
        self.text=guiTools.QReadOnlyTextEdit()
        self.font_size = 12
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.text.setFont(font)
        self.text.setStyleSheet(f"font-size: {self.font_size}pt;")
        self.text.setText(text)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.viewport().installEventFilter(self)         
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setVisible(False)
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
        self.show_font.setText(str(self.font_size))         
        if enableNextPreviouseButtons:
            self.info=qt.QLineEdit()         
            self.info.setReadOnly(True)
            self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            self.info.setText(list(self.typeResult.keys())[self.CurrentIndex])
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)         
        layout.addWidget(self.media_progress)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        if enableNextPreviouseButtons:
            layout.addWidget(self.info)
        buttonsLayout=qt.QHBoxLayout()
        self.next=qt.QPushButton("التالي")
        self.next.clicked.connect(self.onNext)
        self.next.setVisible(enableNextPreviouseButtons)
        self.next.setShortcut("alt+right")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")         
        self.changeCategory=qt.QPushButton("تغيير الفئة")
        self.changeCategory.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCategory.setShortcut("ctrl+alt+g")
        self.changeCategory.setAccessibleDescription("control plus alt plus g")
        self.changeCategory.setVisible(enableNextPreviouseButtons)
        self.changeCategory.clicked.connect(self.onChangeCategory)         
        self.previous=qt.QPushButton("السابق")
        self.previous.clicked.connect(self.onPreviouse)
        self.previous.setShortcut("alt+left")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.setVisible(enableNextPreviouseButtons)
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")         
        self.changeCurrentReciterButton=qt.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.clicked.connect(self.onChangeRecitersContextMenuRequested)
        self.changeCurrentReciterButton.setShortcut("ctrl+shift+r")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus r")
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        buttonsLayout.addWidget(self.changeCurrentReciterButton)
        buttonsLayout.addWidget(self.previous)
        buttonsLayout.addWidget(self.changeCategory)
        buttonsLayout.addWidget(self.next)         
        layout.addLayout(buttonsLayout)
        if not index==0:
            cerser=self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)
            for i in range(index-1):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
        if enableNextPreviouseButtons:
            qt1.QShortcut("ctrl+shift+g",self).activated.connect(self.goToCategory)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.goToAyah)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("escape",self).activated.connect(self.close)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+shift+t", self).activated.connect(self.getTafaseerForSurah)
        qt1.QShortcut("ctrl+shift+i", self).activated.connect(self.getIArabForSurah)
        qt1.QShortcut("ctrl+shift+l", self).activated.connect(self.getTranslationForSurah)
        qt1.QShortcut("ctrl+shift+f", self).activated.connect(self.onSurahInfo)
        qt1.QShortcut("ctrl+alt+t", self).activated.connect(self.TafseerFromVersToVers)
        qt1.QShortcut("ctrl+alt+l", self).activated.connect(self.translateFromVersToVers)
        qt1.QShortcut("ctrl+alt+i", self).activated.connect(self.IArabFromVersToVers)
        qt1.QShortcut("ctrl+alt+p", self).activated.connect(self.playFromVersToVers)
        qt1.QShortcut("ctrl+shift+p", self).activated.connect(lambda: QuranPlayer(self, self.quranText, self.getCurrentAyah(), self.type, self.category, enableBookMarks=self.enableBookmarks).exec())         
    def eventFilter(self, obj, event):
        if obj == self.text.viewport() and \
            event.type() == qt2.QEvent.Type.MouseButtonPress and \
            event.button() == qt2.Qt.MouseButton.LeftButton:
            cursor = self.text.cursorForPosition(event.position().toPoint())
            self.text.setTextCursor(cursor)         
            self.on_play()
            return True
        return super().eventFilter(obj, event)
    def oncontextMenu(self):
        menu=qt.QMenu("الخيارات ",self)
        font=qt1.QFont()         
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات ")
        menu.setFocus()
        ayahOptions=qt.QMenu("خيارات الآية الحالية")
        goToAyah=qt1.QAction("الذهاب إلى آية")
        goToAyah.setShortcut("ctrl+g")
        ayahOptions.addAction(goToAyah)
        goToAyah.triggered.connect(self.goToAyah)
        ayahOptions.setDefaultAction(goToAyah)
        playCurrentAyahAction=qt1.QAction("تشغيل الآية الحالية",self)         
        playCurrentAyahAction.setShortcut("space")
        ayahOptions.addAction(playCurrentAyahAction)
        playCurrentAyahAction.triggered.connect(self.on_play)
        tafaserCurrentAyahAction=qt1.QAction("تفسير الآية الحالية",self)
        tafaserCurrentAyahAction.setShortcut("ctrl+t")
        ayahOptions.addAction(tafaserCurrentAyahAction)
        tafaserCurrentAyahAction.triggered.connect(self.getCurentAyahTafseer)
        IArabCurrentAyah=qt1.QAction("إعراب الآية الحالية",self)
        IArabCurrentAyah.setShortcut("ctrl+i")
        ayahOptions.addAction(IArabCurrentAyah)
        IArabCurrentAyah.triggered.connect(self.getCurentAyahIArab)
        tanzelCurrentAyahAction=qt1.QAction("أسباب نزول الآية الحالية",self)
        tanzelCurrentAyahAction.setShortcut("ctrl+r")
        ayahOptions.addAction(tanzelCurrentAyahAction)
        tanzelCurrentAyahAction.triggered.connect(self.getCurrentAyahTanzel)
        translationCurrentAyahAction=qt1.QAction("ترجمة الآية الحالية",self)
        translationCurrentAyahAction.setShortcut("ctrl+l")
        ayahOptions.addAction(translationCurrentAyahAction)
        translationCurrentAyahAction.triggered.connect(self.getCurentAyahTranslation)
        ayahInfo=qt1.QAction("معلومات الآية الحالية",self)
        ayahInfo.setShortcut("ctrl+f")
        ayahOptions.addAction(ayahInfo)
        ayahInfo.triggered.connect(self.getAyahInfo)         
        copy_aya=qt1.QAction("نسخ الآية الحالية",self)         
        ayahOptions.addAction(copy_aya)
        copy_aya.triggered.connect(self.copyAya)
        state,self.nameOfBookmark=functions.bookMarksManager.getQuranBookmarkName(self.type,self.category,self.getCurrentAyah(),isPlayer=False)
        if state:
            removeBookmarkAction=qt1.QAction("حذف العلامة المرجعية",self)
            removeBookmarkAction.setShortcut("ctrl+b")
            ayahOptions.addAction(removeBookmarkAction)
            removeBookmarkAction.triggered.connect(self.onRemoveBookmark)
        else:
            addNewBookMark=qt1.QAction("إضافة علامة مرجعية",self)
            addNewBookMark.setShortcut("ctrl+b")
            ayahOptions.addAction(addNewBookMark)
            addNewBookMark.triggered.connect(self.onAddBookMark)
            addNewBookMark.setEnabled(self.enableBookmarks)
        menu.addMenu(ayahOptions)
        surahOption=qt.QMenu("خيارات الفئة",self)
        copySurahAction=qt1.QAction("نسخ الفئة",self)
        copySurahAction.setShortcut("ctrl+a")
        surahOption.addAction(copySurahAction)
        surahOption.setDefaultAction(copySurahAction)
        copySurahAction.triggered.connect(self.copy_text)
        saveSurahAction=qt1.QAction("حفظ الفئة كملف نصي",self)
        saveSurahAction.setShortcut("ctrl+s")
        surahOption.addAction(saveSurahAction)
        saveSurahAction.triggered.connect(self.save_text_as_txt)
        printSurah=qt1.QAction("طباعة الفئة",self)
        printSurah.setShortcut("ctrl+p")
        surahOption.addAction(printSurah)
        printSurah.triggered.connect(self.print_text)
        tafaseerSurahAction=qt1.QAction("تفسير الفئة",self)
        tafaseerSurahAction.setShortcut("ctrl+shift+t")
        surahOption.addAction(tafaseerSurahAction)
        tafaseerSurahAction.triggered.connect(self.getTafaseerForSurah)
        IArabSurah=qt1.QAction("إعراب الفئة",self)
        IArabSurah.setShortcut("ctrl+shift+i")
        surahOption.addAction(IArabSurah)
        IArabSurah.triggered.connect(self.getIArabForSurah)
        translationSurahAction=qt1.QAction("ترجمة  الفئة",self)
        translationSurahAction.setShortcut("ctrl+shift+l")
        surahOption.addAction(translationSurahAction)
        translationSurahAction.triggered.connect(self.getTranslationForSurah)
        SurahInfoAction=qt1.QAction("معلومات السورة",self)
        SurahInfoAction.setShortcut("ctrl+shift+f")
        surahOption.addAction(SurahInfoAction)         
        SurahInfoAction.triggered.connect(self.onSurahInfo)
        tafseerFromVersToVersAction=qt1.QAction("التفسير من آية إلى آية")
        tafseerFromVersToVersAction.setShortcut("ctrl+alt+t")
        surahOption.addAction(tafseerFromVersToVersAction)
        tafseerFromVersToVersAction.triggered.connect(self.TafseerFromVersToVers)
        translateFromVersToVersAction=qt1.QAction("الترجمة من آية إلى آية")
        translateFromVersToVersAction.setShortcut("ctrl+alt+l")
        surahOption.addAction(translateFromVersToVersAction)
        translateFromVersToVersAction.triggered.connect(self.translateFromVersToVers)
        IArabFromVersToVersAction=qt1.QAction("الإعراب من آية إلى آية",self)
        IArabFromVersToVersAction.setShortcut("ctrl+alt+i")
        surahOption.addAction(IArabFromVersToVersAction)
        IArabFromVersToVersAction.triggered.connect(self.IArabFromVersToVers)
        playFromVersToVersAction=qt1.QAction("التشغيل من آية إلى آية",self)
        playFromVersToVersAction.setShortcut("ctrl+alt+p")
        surahOption.addAction(playFromVersToVersAction)
        playFromVersToVersAction.triggered.connect(self.playFromVersToVers)
        playSurahToEnd=qt1.QAction("التشغيل إلى نهاية الفئة",self)
        playSurahToEnd.setShortcut("ctrl+shift+p")
        surahOption.addAction(playSurahToEnd)
        playSurahToEnd.triggered.connect(lambda:QuranPlayer(self,self.quranText,self.getCurrentAyah(),self.type,self.category,enableBookMarks=self.enableBookmarks).exec())
        if self.enableNextPreviouseButtons:
            goToCategoryAction=qt1.QAction("الذهاب إلى محتوى فئة",self)
            goToCategoryAction.setShortcut("ctrl+shift+g")
            goToCategoryAction.triggered.connect(self.goToCategory)
            surahOption.addAction(goToCategoryAction)
        menu.addMenu(surahOption)
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
        menu.addMenu(fontMenu)
        ayahOptions.setFont(font)
        surahOption.setFont(font)
        fontMenu.setFont(font)
        menu.setFont(font)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def copyAya(self):
        a=self.getcurrentAyahText()
        pyperclip.copy(a)
        winsound.Beep(1000,100)
    def goToAyah(self):
        ayah,OK=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية ",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if OK:
            cerser=self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)
            for i in range(ayah-1):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
    def getCurrentAyah(self):
        cerser=self.text.textCursor()
        return cerser.blockNumber()
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
        self.media_progress.setVisible(True)
        if not self.media.isPlaying():
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set())):
                path=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set()))
            else:
                path=qt2.QUrl(reciters[self.getCurrentReciter()] + self.on_set())
            if not self.media.source()==path:
                self.media.stop()
                self.media.setSource(path)
            self.media.play()
        else:
            self.media.pause()
    def getCurrentReciter(self):
        index=self.currentReciter
        name=list(reciters.keys())[index]
        return name
    def getcurrentAyahText(self):
        line=self.getCurrentAyah()
        return self.quranText.split("\n")[line]
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
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
                    text = self.text.toPlainText()
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
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=self.text.font()
        font.setPointSize(self.font_size)
        self.text.setCurrentFont(font)         
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            cursor=self.text.textCursor()
            if cursor.hasSelection():
                selected_text=cursor.selectedText()
                pyperclip.copy(selected_text)                 
                winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)             
            winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def getCurentAyahTafseer(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
    def getTafaseerForSurah(self):
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
    def onSurahInfo(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        with open("data/json/files/all_surahs.json","r",encoding="utf-8") as file:
            data=json.load(file)
        surahInfo=data[int(surah)-1]
        numberOfAyah=surahInfo["n"]
        if surahInfo["r"]==0:
            type="مكية"
        else:
            type="مدنية"
        guiTools.MessageBox.view(self,"معلومات {}".format(juz[1]),"رقم السورة {} \n عدد آياتها {} \n نوع السورة {}".format(str(surah),str(numberOfAyah),type))
    def closeEvent(self,event):
        self.media.stop()
        self.close()
    def getCurentAyahIArab(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        guiTools.TextViewer(self,"إعراب",result).exec()
    def getIArabForSurah(self):
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
        guiTools.TextViewer(self,"إعراب",result).exec()
    def getCurrentAyahTanzel(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            guiTools.TextViewer(self,"أسباب النزول",result).exec()
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
    def getAyahInfo(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nالجزء {} \nالربع {} \nالصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
    def getCurentAyahTranslation(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        translationViewer(self,AyahNumber,AyahNumber).exec()
    def getTranslationForSurah(self):
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        translationViewer(self,AyahNumber1,AyahNumber2).exec()
    def onAddBookMark(self):
        if self.enableBookmarks==False:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا يمكن وضع علامة مرجعية عند تصفح القرآن بشكلا مخصص")
            return
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            functions.bookMarksManager.addNewQuranBookMark(self.type,self.category,self.getCurrentAyah(),False,name)
    def playFromVersToVers(self):
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                verses=[]
                allVerses=self.quranText.split("\n")
                for vers in allVerses:
                    index=allVerses.index(vers)+1
                    if index>=FromVers and index<=toVers:
                        verses.append(vers)
                QuranPlayer(self,"\n".join(verses),0,self.type,self.category,enableBookMarks=self.enableBookmarks).exec()
    def TafseerFromVersToVers(self):
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
    def translateFromVersToVers(self):
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                translationViewer(self,AyahNumber1,AyahNumber2).exec()
    def IArabFromVersToVers(self):
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
                guiTools.TextViewer(self,"إعراب",result).exec()
    def onNext(self):
        if self.CurrentIndex==len(self.typeResult)-1:
            self.CurrentIndex=0
        else:
            self.CurrentIndex+=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        self.quranText=self.typeResult[indexs][1]
        self.text.setText(self.quranText)
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(indexs))
        self.info.setText(indexs)
    def onPreviouse(self):
        if self.CurrentIndex==0:
            self.CurrentIndex=len(self.typeResult)-1
        else:
            self.CurrentIndex-=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        self.quranText=self.typeResult[indexs][1]
        self.text.setText(self.quranText)
        winsound.PlaySound("data/sounds/previous_page.wav",1)
        guiTools.speak(str(indexs))
        self.info.setText(indexs)
    def goToCategory(self):
        category,OK=qt.QInputDialog.getItem(self,"الذهاب إلى محتوى فئة","اختر عنصر",self.typeResult,self.CurrentIndex,True)
        if OK:
            self.CurrentIndex=list(self.typeResult.keys()).index(category)
            indexs=list(self.typeResult.keys())[self.CurrentIndex]
            self.info.setText(indexs)
            self.quranText=self.typeResult[indexs][1]
            self.text.setText(self.quranText)
    def onChangeCategory(self):
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        menu=qt.QMenu("اختر فئة",self)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        selectedCategory=qt1.QAction(categories[self.type],self)
        menu.addAction(selectedCategory)
        selectedCategory.setCheckable(True)
        selectedCategory.setChecked(True)
        selectedCategory.triggered.connect(self.ONChangeCategoryRequested)
        menu.setDefaultAction(selectedCategory)
        categories.pop(self.type)
        for category in categories:
            action=qt1.QAction(category,self)
            menu.addAction(action)
            action.triggered.connect(self.ONChangeCategoryRequested)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def ONChangeCategoryRequested(self):
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        index=categories.index(self.sender().text())
        self.type=index
        if index==0:
            result=functions.quranJsonControl.getSurahs()
        elif index==1:
            result=functions.quranJsonControl.getPage()
        elif index==2:
            result=functions.quranJsonControl.getJuz()
        elif index==3:
            result=functions.quranJsonControl.getHezb()
        elif index==4:
            result=functions.quranJsonControl.getHizb()
        self.typeResult=result
        self.CurrentIndex=0
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        self.info.setText(indexs)
        self.quranText=self.typeResult[indexs][1]
        self.text.setText(self.quranText)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeQuranBookMark(self.nameOfBookmark)
            winsound.Beep(1000,100)
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state,self.nameOfBookmark=functions.bookMarksManager.getQuranBookmarkName(self.type,self.category,self.getCurrentAyah(),isPlayer=False)
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
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
    def onChangeRecitersContextMenuRequested(self):
        self.media.stop()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())