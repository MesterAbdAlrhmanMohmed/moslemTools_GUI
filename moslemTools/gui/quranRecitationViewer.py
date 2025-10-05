import guiTools, pyperclip, winsound, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2

class QuranRecitationViewer(qt.QDialog):
    def __init__(self,p,text):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.quranText=text
        qt1.QShortcut("ctrl+g",self).activated.connect(self.goToAyah)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        self.resize(1200,600)
        self.text=guiTools.QReadOnlyTextEdit()
        self.text.setText(text)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self.update_font_size()
    def OnContextMenu(self):
        menu=qt.QMenu("الخيارات",self)
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        text_options=qt.QMenu("خيارات النص",self)
        goToAyah=qt1.QAction("الذهاب إلى آية")
        goToAyah.setShortcut("ctrl+g")
        text_options.addAction(goToAyah)
        goToAyah.triggered.connect(self.goToAyah)
        text_options.setDefaultAction(goToAyah)
        save=text_options.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)
        print_action=text_options.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all=text_options.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text=text_options.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_line)
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
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        fontMenu.addAction(set_font_size)
        menu.addMenu(text_options)
        menu.addMenu(fontMenu)
        text_options.setFont(boldFont)
        fontMenu.setFont(boldFont)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
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
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
            guiTools.MessageBox.error(self, "حدث خطأ", str(error))