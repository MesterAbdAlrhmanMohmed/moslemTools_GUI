import functions, settings, guiTools, winsound, pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
class TafaseerViewer(qt.QDialog):
    def __init__(self, p, From, to):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)        
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        self.index = settings.settings_handler.get("tafaseer", "tafaseer")
        self.context_menu_active = False
        self.saved_text = ""
        self.From = From
        self.to = to
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size = 12
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.text.setFont(font)
        self.text.setStyleSheet(f"font-size: {self.font_size}pt;")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        bottomLayout = qt.QHBoxLayout()
        self.changeTafaseer = qt.QPushButton("تغيير التفسير")
        self.changeTafaseer.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeTafaseer.clicked.connect(self.on_change_tafaseer)
        self.changeTafaseer.setFixedSize(150,40)
        bottomLayout.addWidget(self.changeTafaseer)
        fontLayout = qt.QVBoxLayout()
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        fontLayout.addWidget(self.font_laybol)
        self.show_font = qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        fontLayout.addWidget(self.show_font)
        bottomLayout.addLayout(fontLayout)
        layout.addLayout(bottomLayout)
        self.getResult()
    def OnContextMenu(self):
        cursor = self.text.textCursor()
        self.saved_selection_start = cursor.selectionStart()
        self.saved_selection_end = cursor.selectionEnd()
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        menu = qt.QMenu("الخيارات", self)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        save = menu.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(lambda: QTimer.singleShot(501, self.save_text_as_txt))
        menu.setDefaultAction(save)
        printerAction = menu.addAction("طباعة")
        printerAction.setShortcut("ctrl+p")
        printerAction.triggered.connect(lambda: QTimer.singleShot(501, self.print_text))
        copy_all = menu.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(lambda: QTimer.singleShot(501, self.copy_text))
        copy_selected_text = menu.addAction("نسخ النص المحدد")
        copy_selected_text .setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(lambda: QTimer.singleShot(501, self.copy_line))
        fontMenu = qt.QMenu("حجم الخط", self)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(lambda: QTimer.singleShot(501, self.increase_font_size))
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(lambda: QTimer.singleShot(501, self.decrease_font_size))
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(lambda: QTimer.singleShot(501, self.set_font_size_dialog))
        fontMenu.addAction(set_font_size)
        menu.addMenu(fontMenu)        
        menu.setFocus()
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(qt1.QCursor.pos())    
    def restore_after_menu(self):
        self.context_menu_active = False
        lines = self.saved_text.split('\n')
        self.text.setText('\n'.join(lines[:7]))
        self.text.setUpdatesEnabled(True)
        if self.saved_cursor_position is not None:
            cursor = self.text.textCursor()
            cursor.setPosition(self.saved_cursor_position)
            self.text.setTextCursor(cursor)
        if len(lines) > 7:
            QTimer.singleShot(500, self.restore_full_content)
    
    def restore_full_content(self):    
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
    
    def on_change_tafaseer(self):
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        menu = qt.QMenu("اختر تفسير", self)
        menu.setAccessibleName("اختر تفسير")
        tafaseer = list(functions.tafseer.tafaseers.keys())
        tafaseer.remove(functions.tafseer.getTafaseerByIndex(self.index))
        selectedTafaseer = qt1.QAction(functions.tafseer.getTafaseerByIndex(self.index), self)
        menu.addAction(selectedTafaseer)
        menu.setDefaultAction(selectedTafaseer)
        selectedTafaseer.setCheckable(True)
        selectedTafaseer.setChecked(True)
        selectedTafaseer.triggered.connect(lambda: self.onTafaseerChanged(functions.tafseer.getTafaseerByIndex(self.index)))
        for t in tafaseer:
            tAction = qt1.QAction(t, self)
            tAction.triggered.connect(lambda _, t=t: self.onTafaseerChanged(t))
            menu.addAction(tAction)
        menu.setAccessibleName("اختر تفسير")
        menu.setFocus()
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(qt1.QCursor.pos())
    def onTafaseerChanged(self, name: str):
        self.index = functions.tafseer.tafaseers[self.sender().text()]
        self.getResult()
    def print_text(self):
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def save_text_as_txt(self):
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
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
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = self.text.font()
        font.setPointSize(self.font_size)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            if self.saved_selection_start != -1 and self.saved_selection_end != -1 and self.saved_selection_start < self.saved_selection_end:
                selected_text = self.saved_text[self.saved_selection_start:self.saved_selection_end]
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            pyperclip.copy(self.saved_text)
            winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_current_selection(self):
        try:
            cursor = self.text.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")        
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def getResult(self):
        self.full_content = functions.tafseer.getTafaseer(
            functions.tafseer.getTafaseerByIndex(self.index),
            self.From, self.to
        )
        lines = self.full_content.split('\n')
        self.text.setText('\n'.join(lines[:7]))
        if len(lines) > 7:
            QTimer.singleShot(500, self.display_full_content)
    def display_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.full_content)
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)    
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