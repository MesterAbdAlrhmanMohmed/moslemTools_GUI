import guiTools, pyperclip, winsound, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from PyQt6.QtCore import QTimer
class TextViewer(qt.QDialog):
    def __init__(self, p, title, text):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.set_font_size_dialog)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        self.context_menu_active = False
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.setWindowTitle(title)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self._set_text_with_delay(text)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
    def _set_full_text_and_update_font(self, full_text):
        self.text.setText(full_text)
        self.update_font_size()
    def OnContextMenu(self):
        cursor = self.text.textCursor()
        self.saved_selection_start = cursor.selectionStart()
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_selection_end = cursor.selectionEnd()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        font = qt1.QFont()
        font.setBold(True)
        menu = qt.QMenu("الخيارات", self)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        text_options = qt.QMenu("خيارات النص", self)
        text_options.setFont(font)
        save = text_options.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(lambda: QTimer.singleShot(250, self.save_text_as_txt))
        print_action = text_options.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(lambda: QTimer.singleShot(250, self.print_text))
        copy_all = text_options.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(lambda: QTimer.singleShot(250, self.copy_text))
        copy_selected_text = text_options.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(lambda: QTimer.singleShot(250, self.copy_line))
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(font)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(lambda: QTimer.singleShot(250, self.increase_font_size))
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(lambda: QTimer.singleShot(250, self.decrease_font_size))
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(lambda: QTimer.singleShot(250, self.set_font_size_dialog))
        fontMenu.addAction(set_font_size)
        menu.addMenu(text_options)
        menu.addMenu(fontMenu)
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
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
            QTimer.singleShot(200, self.restore_full_content)
    def restore_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
            self.update_font_size()
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
    def print_text(self):
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
        cursor = self.text.textCursor()
        selected_text_start = cursor.selectionStart()
        selected_text_end = cursor.selectionEnd()
        fmt = qt1.QTextCharFormat()
        fmt.setFontPointSize(self.font_size)
        if self.font_is_bold:
            fmt.setFontWeight(qt1.QFont.Weight.Bold)
        else:
            fmt.setFontWeight(qt1.QFont.Weight.Normal)
        cursor.select(qt1.QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(fmt)
        cursor.setPosition(selected_text_start)
        if selected_text_start != selected_text_end:
            cursor.setPosition(selected_text_end, qt1.QTextCursor.MoveMode.KeepAnchor)
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            if self.saved_selection_start != -1 and self.saved_selection_end != -1 and self.saved_selection_start < self.saved_selection_end:
                selected_text = self.saved_text[self.saved_selection_start:self.saved_selection_end]
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            pyperclip.copy(self.saved_text)
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def _set_text_with_delay(self, full_text):
        self.saved_text = full_text
        lines = full_text.split('\n')
        self.text.setText('\n'.join(lines[:40]))
        self.update_font_size()
        if len(lines) > 40:
            QTimer.singleShot(200, self._display_full_content)
    def _display_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.saved_text)
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
            guiTools.MessageBox.error(self, "حدث خطأ", str(error))
    def copy_current_selection(self):
        try:
            cursor = self.text.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))