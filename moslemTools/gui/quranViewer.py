from guiTools import note_dialog
import functions.notesManager as notesManager
from .changeReciter import ChangeReciter
from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
from .quranPlayer import QuranPlayer
import time, winsound, pyperclip, gettext, os, json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
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
        self.initial_ayah_index = index
        self.context_menu_active = False
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_ayah_index = None
        self.was_playing_before_action = False
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
        self._set_text_with_delay(text)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.oncontextMenu)
        self.text.viewport().installEventFilter(self)                
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setVisible(False)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media_progress.setAccessibleName("التحكم في تقدم الآية")        
        self.time_label = qt.QLabel()
        self.time_label.setVisible(False)
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
        progress_time_layout = qt.QHBoxLayout()
        progress_time_layout.addWidget(self.media_progress)
        progress_time_layout.addWidget(self.time_label)        
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)        
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        if self.type == 5 and isinstance(self.category, str):
            self.info.setText(self.category)
        else:            
            if self.typeResult:
                self.info.setText(list(self.typeResult.keys())[self.CurrentIndex])
            else:
                self.info.setText("")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addLayout(progress_time_layout)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.info)
        buttonsLayout=qt.QHBoxLayout()
        self.next=guiTools.QPushButton("التالي")
        self.next.setAutoDefault(False)
        self.next.clicked.connect(self.onNext)
        self.next.setVisible(enableNextPreviouseButtons)
        self.next.setShortcut("alt+right")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCategory=guiTools.QPushButton("تغيير الفئة")
        self.changeCategory.setAutoDefault(False)
        self.changeCategory.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCategory.setShortcut("ctrl+alt+g")
        self.changeCategory.setAccessibleDescription("control plus alt plus g")
        self.changeCategory.setVisible(enableNextPreviouseButtons)
        self.changeCategory.clicked.connect(self.onChangeCategory)
        self.previous=guiTools.QPushButton("السابق")
        self.previous.setAutoDefault(False)
        self.previous.clicked.connect(self.onPreviouse)
        self.previous.setShortcut("alt+left")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.setVisible(enableNextPreviouseButtons)
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCurrentReciterButton=guiTools.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.setAutoDefault(False)
        self.changeCurrentReciterButton.clicked.connect(self.onChangeRecitersContextMenuRequested)
        self.changeCurrentReciterButton.setShortcut("ctrl+shift+r")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus r")
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        buttonsLayout.addWidget(self.changeCurrentReciterButton)
        buttonsLayout.addWidget(self.previous)
        buttonsLayout.addWidget(self.changeCategory)
        buttonsLayout.addWidget(self.next)
        layout.addLayout(buttonsLayout)
        if not self.initial_ayah_index == 0:
            QTimer.singleShot(201, self._set_initial_ayah_position)
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
        qt1.QShortcut("ctrl+shift+p", self).activated.connect(lambda: QuranPlayer(self, self.quranText, self.getCurrentAyah(), self.type, self.category).exec())
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)            
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)    
    def pause_for_action(self):        
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False    
    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()
    def _set_text_with_delay(self, full_text):        
        self.saved_text = full_text
        lines = full_text.split('\n')                
        initial_text_chunk = '\n'.join(lines[:7])
        self.text.setText(initial_text_chunk)        
        if len(lines) > 7:
            qt2.QTimer.singleShot(200, self._display_full_content)
    def _display_full_content(self):                
        if not hasattr(self, 'context_menu_active') or not self.context_menu_active:
            self.text.setText(self.saved_text)                        
    def restore_after_menu(self):
        self.context_menu_active = False
        lines = self.saved_text.split('\n')
        self.text.setText('\n'.join(lines[:7]))
        self.text.setUpdatesEnabled(True)    
        if len(lines) > 7:
            QTimer.singleShot(200, self.restore_full_content)        
        if self.saved_cursor_position is not None:
            cursor = self.text.textCursor()
            cursor.setPosition(self.saved_cursor_position)
            self.text.setTextCursor(cursor)        
        self.resume_after_action()
    def restore_full_content(self):    
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
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
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_ayah_index = self.getCurrentAyah()        
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True    
        self.pause_for_action()        
        menu = qt.QMenu("الخيارات ", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات ")
        menu.setFocus()        
        ayahOptions = qt.QMenu("خيارات الآية الحالية", self)
        ayahOptions.setFont(font)
        goToAyah = qt1.QAction("الذهاب إلى آية", self)
        goToAyah.setShortcut("ctrl+g")
        ayahOptions.addAction(goToAyah)
        goToAyah.triggered.connect(self.goToAyah)    
        playCurrentAyahAction = qt1.QAction("تشغيل الآية الحالية", self)
        playCurrentAyahAction.setShortcut("space")
        ayahOptions.addAction(playCurrentAyahAction)
        playCurrentAyahAction.triggered.connect(self.on_play)    
        tafaserCurrentAyahAction = qt1.QAction("تفسير الآية الحالية", self)
        tafaserCurrentAyahAction.setShortcut("ctrl+t")
        ayahOptions.addAction(tafaserCurrentAyahAction)
        tafaserCurrentAyahAction.triggered.connect(self.getCurentAyahTafseer)    
        IArabCurrentAyah = qt1.QAction("إعراب الآية الحالية", self)
        IArabCurrentAyah.setShortcut("ctrl+i")
        ayahOptions.addAction(IArabCurrentAyah)
        IArabCurrentAyah.triggered.connect(self.getCurentAyahIArab)    
        tanzelCurrentAyahAction = qt1.QAction("أسباب نزول الآية الحالية", self)
        tanzelCurrentAyahAction.setShortcut("ctrl+r")
        ayahOptions.addAction(tanzelCurrentAyahAction)
        tanzelCurrentAyahAction.triggered.connect(self.getCurrentAyahTanzel)    
        translationCurrentAyahAction = qt1.QAction("ترجمة الآية الحالية", self)
        translationCurrentAyahAction.setShortcut("ctrl+l")
        ayahOptions.addAction(translationCurrentAyahAction)
        translationCurrentAyahAction.triggered.connect(self.getCurentAyahTranslation)    
        ayahInfo = qt1.QAction("معلومات الآية الحالية", self)
        ayahInfo.setShortcut("ctrl+f")        
        ayahOptions.addAction(ayahInfo)
        ayahInfo.triggered.connect(self.getAyahInfo)    
        copy_aya = qt1.QAction("نسخ الآية الحالية", self)
        ayahOptions.addAction(copy_aya)
        copy_aya.triggered.connect(self.copyAya)    
        state, self.nameOfBookmark = functions.bookMarksManager.getQuranBookmarkName(self.type, self.category, self.saved_ayah_index, isPlayer=False)
        if state:
            removeBookmarkAction = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف العلامة المرجعية للآياة الحالية: CTRL+B")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+b")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")            
            delete_button.clicked.connect(self.onRemoveBookmark)
            removeBookmarkAction.setDefaultWidget(delete_button)
            ayahOptions.addAction(removeBookmarkAction)
        else:
            addNewBookMark = qt1.QAction("إضافة علامة مرجعية للآياة الحالية", self)
            addNewBookMark.setShortcut("ctrl+b")
            ayahOptions.addAction(addNewBookMark)
            addNewBookMark.triggered.connect(self.onAddBookMark)
            addNewBookMark.setEnabled(self.enableBookmarks)    
        if self.enableBookmarks:
            ayah_position = {
                "ayah_text": self.quranText.split("\n")[self.saved_ayah_index],
                "ayah_number": self.saved_ayah_index,
                "surah": self.category
            }
            note_exists = notesManager.getNotesForPosition("quran", ayah_position)
            if note_exists:
                note_action = qt1.QAction("عرض ملاحظة الآية الحالية", self)
                note_action.setShortcut("ctrl+o")
                note_action.triggered.connect(lambda: self.onNoteAction(ayah_position))
                ayahOptions.addAction(note_action)                
                delete_note_action = qt.QWidgetAction(self)
                delete_button = qt.QPushButton("حذف ملاحظة الآية الحالية: CTRL+SHIFT+N")
                delete_button.setDefault(True)                
                delete_button.setStyleSheet("background-color: #8B0000; color: white;")            
                delete_button.clicked.connect(lambda: self.onDeleteNote(ayah_position))                
                delete_note_action.setDefaultWidget(delete_button)                
                ayahOptions.addAction(delete_note_action)
            else:
                note_action = qt1.QAction("إضافة ملاحظة للآية الحالية", self)
                note_action.setShortcut("ctrl+n")
                note_action.triggered.connect(lambda: self.onAddNote(ayah_position))
                ayahOptions.addAction(note_action)        
        menu.addMenu(ayahOptions)        
        surahOption = qt.QMenu("خيارات الفئة", self)
        surahOption.setFont(font)
        copySurahAction = qt1.QAction("نسخ الفئة", self)
        copySurahAction.setShortcut("ctrl+a")
        surahOption.addAction(copySurahAction)
        copySurahAction.triggered.connect(self.copy_text)    
        saveSurahAction = qt1.QAction("حفظ الفئة كملف نصي", self)
        saveSurahAction.setShortcut("ctrl+s")
        surahOption.addAction(saveSurahAction)
        saveSurahAction.triggered.connect(self.save_text_as_txt)    
        printSurah = qt1.QAction("طباعة الفئة", self)
        printSurah.setShortcut("ctrl+p")
        surahOption.addAction(printSurah)
        printSurah.triggered.connect(self.print_text)    
        tafaseerSurahAction = qt1.QAction("تفسير الفئة", self)
        tafaseerSurahAction.setShortcut("ctrl+shift+t")
        surahOption.addAction(tafaseerSurahAction)
        tafaseerSurahAction.triggered.connect(self.getTafaseerForSurah)    
        IArabSurah = qt1.QAction("إعراب الفئة", self)
        IArabSurah.setShortcut("ctrl+shift+i")
        surahOption.addAction(IArabSurah)
        IArabSurah.triggered.connect(self.getIArabForSurah)    
        translationSurahAction = qt1.QAction("ترجمة  الفئة", self)
        translationSurahAction.setShortcut("ctrl+shift+l")
        surahOption.addAction(translationSurahAction)
        translationSurahAction.triggered.connect(self.getTranslationForSurah)    
        SurahInfoAction = qt1.QAction("معلومات السورة", self)
        SurahInfoAction.setShortcut("ctrl+shift+f")
        surahOption.addAction(SurahInfoAction)
        SurahInfoAction.triggered.connect(self.onSurahInfo)    
        tafseerFromVersToVersAction = qt1.QAction("التفسير من آية إلى آية")
        tafseerFromVersToVersAction.setShortcut("ctrl+alt+t")
        surahOption.addAction(tafseerFromVersToVersAction)
        tafseerFromVersToVersAction.triggered.connect(self.TafseerFromVersToVers)    
        translateFromVersToVersAction = qt1.QAction("الترجمة من آية إلى آية")
        translateFromVersToVersAction.setShortcut("ctrl+alt+l")
        surahOption.addAction(translateFromVersToVersAction)
        translateFromVersToVersAction.triggered.connect(self.translateFromVersToVers)    
        IArabFromVersToVersAction = qt1.QAction("الإعراب من آية إلى آية", self)
        IArabFromVersToVersAction.setShortcut("ctrl+alt+i")
        surahOption.addAction(IArabFromVersToVersAction)
        IArabFromVersToVersAction.triggered.connect(self.IArabFromVersToVers)    
        playFromVersToVersAction = qt1.QAction("التشغيل من آية إلى آية", self)
        playFromVersToVersAction.setShortcut("ctrl+alt+p")
        surahOption.addAction(playFromVersToVersAction)
        playFromVersToVersAction.triggered.connect(self.playFromVersToVers)    
        playSurahToEnd = qt1.QAction("التشغيل إلى نهاية الفئة", self)
        playSurahToEnd.setShortcut("ctrl+shift+p")
        surahOption.addAction(playSurahToEnd)
        playSurahToEnd.triggered.connect(lambda: QuranPlayer(self, self.quranText, self.saved_ayah_index, self.type, self.category).exec())   
        if self.enableNextPreviouseButtons:
            goToCategoryAction = qt1.QAction("الذهاب إلى محتوى فئة", self)
            goToCategoryAction.setShortcut("ctrl+shift+g")
            goToCategoryAction.triggered.connect(self.goToCategory)
            surahOption.addAction(goToCategoryAction)    
        menu.addMenu(surahOption)        
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(font)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)    
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        menu.addMenu(fontMenu)        
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(self.mapToGlobal(self.cursor().pos()))                        
    def onAddNote(self, position_data):
        self.pause_for_action()
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
        self.resume_after_action()    
    def onEditNote(self, position_data, note_name):
        self.pause_for_action()
        note = notesManager.getNoteByName("quran", note_name)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="edit",
                old_name=note["name"]
            )
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
        self.resume_after_action()    
    def saveNote(self, position_data, name, content):
        notesManager.addNewNote("quran", {
            "name": name,
            "content": content,
            "position_data": position_data
        })
        guiTools.speak("تمت إضافة الملاحظة")        
    def updateNote(self, position_data, old_name, new_name, new_content):
        update_data = {
            "name": new_name,
            "content": new_content,
            "position_data": position_data
        }
        success = notesManager.updateNote("quran", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")        
    def onAddOrRemoveNote(self):
        self.pause_for_action()
        if not self.enableBookmarks:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا يمكن إدارة الملاحظات عند تصفح القرآن بشكل مخصص")
            self.resume_after_action()
            return        
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": self.getCurrentAyah(),
            "surah": self.category
        }
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onEditNote(ayah_position, note_exists["name"])
        else:
            self.onAddNote(ayah_position)
        self.resume_after_action()        
    def onViewNote(self):
        self.pause_for_action()
        if not self.enableBookmarks:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا يمكن عرض الملاحظات عند تصفح القرآن بشكل مخصص")
            self.resume_after_action()
            return    
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": self.getCurrentAyah(),
            "surah": self.category
        }
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onNoteAction(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الآية")
        self.resume_after_action()        
    def onNoteAction(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="view",
                old_name=note["name"]
            )
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
        self.resume_after_action()    
    def onDeleteNote(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف", 
                f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", 
                "نعم", "لا"
            )
            if confirm == 0:
                notesManager.removeNote("quran", note["name"])                
                guiTools.speak("تم حذف الملاحظة")
        self.resume_after_action()
    def copyAya(self):
        a = self.quranText.split("\n")[self.saved_ayah_index]
        pyperclip.copy(a)
        winsound.Beep(1000,100)    
        guiTools.speak("تم نسخ الآية المحددة بنجاح")
    def goToAyah(self):
        self.pause_for_action()
        ayah,OK=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية ",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if OK:
            cerser=self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)
            for i in range(ayah-1):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
        self.resume_after_action()    
    def getCurrentAyah(self):        
        cerser=self.text.textCursor()
        return cerser.blockNumber()    
    def on_set(self, ayah_index=None):
        if ayah_index is None:
            ayah_index = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[ayah_index]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
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
        self.time_label.setVisible(True)        
        if not self.media.isPlaying():
            current_ayah = self.getCurrentAyah()
            file_name = self.on_set(current_ayah)
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],file_name)):
                path=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],file_name))
            else:
                path=qt2.QUrl(reciters[self.getCurrentReciter()] + file_name)
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
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))        
    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))    
    def getCurentAyahTafseer(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()    
    def getTafaseerForSurah(self):
        self.pause_for_action()
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def onSurahInfo(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        with open("data/json/files/all_surahs.json","r",encoding="utf-8") as file:
            data=json.load(file)
        surahInfo=data[int(surah)-1]
        numberOfAyah=surahInfo["n"]
        if surahInfo["r"]==0:
            type="مكية"
        else:
            type="مدنية"
        guiTools.qMessageBox.MessageBox.view(self,"معلومات {}".format(juz[1]),"رقم السورة {} \n عدد آياتها {} \n نوع السورة {}".format(str(surah),str(numberOfAyah),type))
        self.resume_after_action()    
    def closeEvent(self,event):
        self.media.stop()
        self.close()        
    def getCurentAyahIArab(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def getIArabForSurah(self):
        self.pause_for_action()
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def getCurrentAyahTanzel(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            self.text.setUpdatesEnabled(False)
            guiTools.TextViewer(self,"أسباب النزول",result).exec()
            self.text.setUpdatesEnabled(True)
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()        
    def getAyahInfo(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nالجزء {} \nالربع {} \nالصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
        self.resume_after_action()        
    def getCurentAyahTranslation(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        current_line = self.quranText.split("\n")[current_ayah]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line)
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def getTranslationForSurah(self):
        self.pause_for_action()
        ayahList=self.quranText.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0])
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1])
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def onAddBookMark(self):
        self.pause_for_action()
        if self.enableBookmarks==False:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا يمكن وضع علامة مرجعية عند تصفح القرآن بشكلا مخصص")
            self.resume_after_action()
            return
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            current_ayah = self.getCurrentAyah()
            functions.bookMarksManager.addNewQuranBookMark(self.type,self.category,current_ayah,False,name)
        self.resume_after_action()        
    def playFromVersToVers(self):
        self.pause_for_action()
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
                self.text.setUpdatesEnabled(False)
                QuranPlayer(self,"\n".join(verses),0,self.type,self.category).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def TafseerFromVersToVers(self):
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                self.text.setUpdatesEnabled(False)
                TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()    
    def translateFromVersToVers(self):
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                self.text.setUpdatesEnabled(False)
                translationViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def IArabFromVersToVers(self):
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","أكتب الرقم",self.getCurrentAyah()+1,1,len(self.quranText.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","أكتب الرقم",len(self.quranText.split("\n")),1,len(self.quranText.split("\n")))
            if ok:
                ayahList=self.quranText.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1])
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1])
                self.text.setUpdatesEnabled(False)
                result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
                guiTools.TextViewer(self,"إعراب",result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()        
    def onNext(self):
        self.pause_for_action()
        if self.CurrentIndex==len(self.typeResult)-1:
            self.CurrentIndex=0
        else:
            self.CurrentIndex+=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        self.category = indexs 
        self.quranText=self.typeResult[indexs][1]
        self._set_text_with_delay(self.quranText)
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(indexs))
        self.info.setText(indexs)
        self.resume_after_action()        
    def onPreviouse(self):
        self.pause_for_action()
        if self.CurrentIndex==0:
            self.CurrentIndex=len(self.typeResult)-1
        else:
            self.CurrentIndex-=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        self.category = indexs 
        self.quranText=self.typeResult[indexs][1]
        self._set_text_with_delay(self.quranText)
        winsound.PlaySound("data/sounds/previous_page.wav",1)
        guiTools.speak(str(indexs))
        self.info.setText(indexs)
        self.resume_after_action()        
    def goToCategory(self):
        self.pause_for_action()
        category,OK=qt.QInputDialog.getItem(self,"الذهاب إلى محتوى فئة","اختر عنصر",self.typeResult,self.CurrentIndex,True)
        if OK:
            self.CurrentIndex=list(self.typeResult.keys()).index(category)
            indexs=list(self.typeResult.keys())[self.CurrentIndex]
            self.category = indexs
            self.info.setText(indexs)
            self.quranText=self.typeResult[indexs][1]
            self._set_text_with_delay(self.quranText)
        self.resume_after_action()        
    def onChangeCategory(self):
        self.pause_for_action()
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
        self.resume_after_action()        
    def ONChangeCategoryRequested(self):
        self.pause_for_action()
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
        self._set_text_with_delay(self.quranText)
        self.resume_after_action()        
    def onRemoveBookmark(self):
        self.pause_for_action()
        try:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف", 
                f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", 
                "نعم", "لا"
            )
            if confirm == 0:
                functions.bookMarksManager.removeQuranBookMark(self.nameOfBookmark)                
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.speak("تم حذف العلامة المرجعية")
        self.resume_after_action()
    def onAddOrRemoveBookmark(self):
        self.pause_for_action()
        current_ayah = self.getCurrentAyah()
        state,self.nameOfBookmark=functions.bookMarksManager.getQuranBookmarkName(self.type,self.category,current_ayah,isPlayer=False)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
        self.resume_after_action()    
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
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")    
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)    
    def onChangeRecitersContextMenuRequested(self):
        self.pause_for_action()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.resume_after_action()
    def _set_initial_ayah_position(self):
        cerser = self.text.textCursor()
        cerser.movePosition(cerser.MoveOperation.Start)
        for i in range(self.initial_ayah_index):
            cerser.movePosition(cerser.MoveOperation.Down)
        self.text.setTextCursor(cerser)
    def onDeleteNoteShortcut(self):        
        self.pause_for_action()
        if not self.enableBookmarks:
            guiTools.speak("لا يمكن حذف الملاحظات في هذا الوضع")
            self.resume_after_action()
            return                    
        current_ayah = self.getCurrentAyah()
        ayah_position = {
            "ayah_text": self.getcurrentAyahText(),
            "ayah_number": current_ayah,
            "surah": self.category
        }                
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onDeleteNote(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
        self.resume_after_action()