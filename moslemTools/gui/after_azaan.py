import PyQt6.QtGui as qt1
from PyQt6 import QtWidgets as qt
from PyQt6 import QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
import guiTools, pyperclip, winsound, settings
class AfterAdaan(qt.QDialog):
    def __init__(self,p):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)        
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.setWindowTitle("دعاء بعد الأذان")        
        self.media_player=QMediaPlayer()
        self.audio_output=QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(qt2.QUrl.fromLocalFile("data/sounds/prayAfterAdaan.m4a"))
        self.media_player.play()        
        self.suplication = guiTools.QReadOnlyTextEdit()
        self.suplication.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.suplication.customContextMenuRequested.connect(self.onContextMenu)        
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"        
        self.suplication.setText("اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ القَائِمَةِ، آتِ مُحَمَّدًا الوَسِيلَةَ وَالفَضِيلَةَ، وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ\nيُستحب إضافة: إِنَّكَ لَا تُخْلِفُ المِيعَادَ.\n\nثواب الدعاء بعد الأذان\nقال رسول الله صل الله عليه وسلم: مَنْ قَالَ حِينَ يَسْمَعُ النِّدَاءَ: اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ القَائِمَةِ، آتِ مُحَمَّدًا الوَسِيلَةَ وَالفَضِيلَةَ، وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ؛ حَلَّتْ لَهُ شَفَاعَتِي يَوْمُ القِيَامَةِ\nرواه البخاري في صحيحه.")                        
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel(str(self.font_size))
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.suplication)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)        
        qt1.QShortcut("escape",self).activated.connect(self.closewindow)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        self.update_font_size()
    def onContextMenu(self, pos):
        menu = qt.QMenu("الخيارات", self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setFont(font)        
        text_options = qt.QMenu("خيارات النص", self)
        text_options.setFont(font)
        copy_all = text_options.addAction("نسخ النص كاملا (Ctrl+A)")
        copy_all.triggered.connect(self.copy_text)        
        copy_selected_text = text_options.addAction("نسخ النص المحدد (Ctrl+C)")
        copy_selected_text.triggered.connect(self.copy_line)
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(font)        
        incressFontAction = qt1.QAction("تكبير الخط (Ctrl+=)", self)
        fontMenu.addAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)        
        decreaseFontSizeAction = qt1.QAction("تصغير الخط (Ctrl+-)", self)
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)        
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        fontMenu.addAction(set_font_size)
        menu.addMenu(text_options)
        menu.addMenu(fontMenu)
        menu.exec(self.suplication.mapToGlobal(pos))
    def increase_font_size(self):
        if self.font_size < 100:
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
        cursor = self.suplication.textCursor()
        self.suplication.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.suplication.setCurrentFont(font)
        self.suplication.setTextCursor(cursor)
    def copy_line(self):
        try:
            cursor = self.suplication.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", str(e))
    def copy_text(self):
        try:
            pyperclip.copy(self.suplication.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", str(e))
    def closewindow(self):
        self.media_player.stop()
        self.accept()
    def set_font_size_dialog(self):
        try:
            size, ok = guiTools.QInputDialog.getInt(
                self,
                "تغيير حجم الخط",
                "أدخل حجم الخط (من 1 الى 100):",
                value=self.font_size,
                min=1,
                max=100
            )
            if ok:
                self.font_size = size
                self.show_font.setText(str(self.font_size))
                self.update_font_size()
                guiTools.speak(f"تم تغيير حجم الخط إلى {size}")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "حدث خطأ", str(error))