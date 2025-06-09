import guiTools,pyperclip,winsound,json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
class NamesOfAllah(qt.QWidget):
    def __init__(self):
        super().__init__()        
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        with open("data/json/namesOfAllah.json","r",encoding="utf-8") as file:
            self.data=json.load(file)
        layout=qt.QVBoxLayout(self)
        self.information=guiTools.QReadOnlyTextEdit()
        font1=qt1.QFont()
        font1.setBold(True)
        self.information.setFont(font1)
        result=""
        for item in self.data[settings_handler.get("g","lang")]:
            result+=item["name"] + " : \n" + item["meaning"]+"\n"
        self.information.setText(result)
        self.information.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.information.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        self.information.setFont(font)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLineEdit()
        self.show_font.setReadOnly(True)
        self.show_font.setAccessibleName("حجم النص")                
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        layout.addWidget(self.information)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)        
    def OnContextMenu(self):
        menu=qt.QMenu("الخيارات",self)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        text_options=qt.QMenu("خيارات النص",self)
        save=text_options.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)        
        print=text_options.addAction("طباعة")
        print.setShortcut("ctrl+p")
        print.triggered.connect(self.print_text)
        copy_all=text_options.addAction("نسخ النص كاملا")        
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text=text_options.addAction("نسخ النص المحدد")
        copy_selected_text .setShortcut("ctrl+c")
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
        menu.addMenu(text_options)
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
        cursor=self.information.textCursor()
        self.information.selectAll()
        font=self.information.font()
        font.setPointSize(self.font_size)
        self.information.setCurrentFont(font)        
        self.information.setTextCursor(cursor)
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.information.print(printer)
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
                    text = self.information.toPlainText()
                    file.write(text)                
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_line(self):
        try:
            cursor=self.information.textCursor()
            if cursor.hasSelection():
                selected_text=cursor.selectedText()
                pyperclip.copy(selected_text)                
                winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text=self.information.toPlainText()
            pyperclip.copy(text)            
            winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))