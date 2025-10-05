import functions, settings, guiTools, winsound, pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
class translationViewer(qt.QDialog):
    def __init__(self, p, From, to):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)        
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_astxt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)        
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.index = settings.settings_handler.get("translation", "translation")
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
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        bottomLayout = qt.QHBoxLayout()
        self.changeTranslation = qt.QPushButton("تغيير الترجمة")
        self.changeTranslation.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeTranslation.clicked.connect(self.on_change_translation)
        self.changeTranslation.setFixedSize(150, 40)
        bottomLayout.addWidget(self.changeTranslation)
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
        self.warning_label = qt.QLabel("تنبيه: إذا غيرت الترجمة ولم يظهر النص، اختر نفس الترجمة مرة أخرى.")
        self.warning_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        bottomLayout.addWidget(self.warning_label, 0, qt2.Qt.AlignmentFlag.AlignCenter)
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
        save.triggered.connect(lambda: QTimer.singleShot(501, self.save_text_astxt))
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
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(qt1.QCursor.pos())    
    def restore_after_menu(self):
        self.context_menu_active = False
        lines = self.saved_text.split('\n')
        self.text.setText('\n'.join(lines[:40]))
        self.update_font_size()
        self.text.setUpdatesEnabled(True)
        if self.saved_cursor_position is not None:
            cursor = self.text.textCursor()
            cursor.setPosition(self.saved_cursor_position)
            self.text.setTextCursor(cursor)
        if len(lines) > 40:
            QTimer.singleShot(500, self.restore_full_content)    
    def restore_full_content(self):    
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
            self.update_font_size()
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)    
    def on_change_translation(self):
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        menu = qt.QMenu("اختر ترجمة", self)
        menu.setAccessibleName("اختر ترجمة")
        translations = list(functions.translater.translations.keys())
        current_translation = functions.translater.gettranslationByIndex(self.index)
        translations.remove(current_translation)
        currentAction = qt1.QAction(current_translation, self)
        menu.addAction(currentAction)
        currentAction.setCheckable(True)
        currentAction.setChecked(True)
        currentAction.triggered.connect(lambda: self.on_translation_changed(current_translation))
        menu.setDefaultAction(currentAction)
        for t in translations:
            tAction = qt1.QAction(t, self)
            tAction.triggered.connect(lambda checked, name=t: self.on_translation_changed(name))
            menu.addAction(tAction)
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(qt1.QCursor.pos())
    def on_translation_changed(self, name: str):
        self.index = functions.translater.translations[name]        
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.context_menu_active = False
        self.getResult()
    def print_text(self):
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def save_text_astxt(self):
        try:
            file_dialog = qt.QFileDialog(self)
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(self.text.toPlainText())
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            if self.saved_selection_start != -1 and self.saved_selection_end != -1 and self.saved_selection_start < self.saved_selection_end:
                selected_text = self.saved_text[self.saved_selection_start:self.saved_selection_end]
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:            
            pyperclip.copy(self.text.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
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
        self.full_content = functions.translater.gettranslation(
            functions.translater.gettranslationByIndex(self.index),
            self.From, self.to
        )
        lines = self.full_content.split('\n')
        self.text.setText('\n'.join(lines[:40]))
        self.update_font_size()
        if len(lines) > 40:
            QTimer.singleShot(500, self.display_full_content)
    def display_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.full_content)
            self.update_font_size()
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
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