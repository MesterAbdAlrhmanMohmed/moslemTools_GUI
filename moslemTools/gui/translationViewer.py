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
        self.permanent_stabilizer_bar = qt.QWidget()
        self.permanent_stabilizer_bar.setFixedHeight(0)
        self.permanent_stabilizer_bar.setAccessibleName(" ")
        self.permanent_stabilizer_bar.setAccessibleDescription(" ")
        layout.addWidget(self.permanent_stabilizer_bar)
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
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        fontLayout.addWidget(self.show_font)
        bottomLayout.addLayout(fontLayout)
        self.warning_label = qt.QLabel("تنبيه: إذا غيرت الترجمة ولم يظهر النص، اختر نفس الترجمة مرة أخرى.")
        self.warning_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        bottomLayout.addWidget(self.warning_label, 0, qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(bottomLayout)
        self.getResult()
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        menu.setAccessibleName("الخيارات")
        save = menu.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_astxt)
        printerAction = menu.addAction("طباعة")
        printerAction.setShortcut("ctrl+p")
        printerAction.triggered.connect(self.print_text)
        copy_all = menu.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text = menu.addAction("نسخ النص المحدد")
        copy_selected_text .setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_current_selection)
        fontMenu = qt.QMenu("حجم الخط", self)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        menu.addMenu(fontMenu)
        menu.exec(qt1.QCursor.pos())

    def on_change_translation(self):
        menu = qt.QMenu("اختر ترجمة", self)
        menu.setAccessibleName("اختر ترجمة")
        action_group = qt1.QActionGroup(self)
        action_group.setExclusive(True)

        current_translation_name = functions.translater.gettranslationByIndex(self.index)                
        all_translations = list(functions.translater.translations.keys())
        if current_translation_name in all_translations:
            all_translations.remove(current_translation_name)
            all_translations.insert(0, current_translation_name)

        for name in all_translations:
            action = qt1.QAction(name, self)
            action.setCheckable(True)
            if name == current_translation_name:
                action.setChecked(True)            
            action.triggered.connect(lambda checked, n=name: self.on_translation_changed(n) if checked else None)
            menu.addAction(action)
            action_group.addAction(action)

        menu.exec(qt1.QCursor.pos())

    def on_translation_changed(self, name: str):
        new_index = functions.translater.translations.get(name)
        if new_index is not None and self.index != new_index:
            self.index = new_index
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
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))
    def increase_font_size(self):
        if self.show_font.value() < 100:
            self.show_font.setValue(self.show_font.value() + 1)
    def decrease_font_size(self):
        if self.show_font.value() > 1:
            self.show_font.setValue(self.show_font.value() - 1)
    def update_font_size(self):
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
        if self.show_font.value() != self.font_size:
            self.show_font.blockSignals(True)
            self.show_font.setValue(self.font_size)
            self.show_font.blockSignals(False)
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
        self.full_content = functions.translater.gettranslation(functions.translater.gettranslationByIndex(self.index),self.From, self.to)
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