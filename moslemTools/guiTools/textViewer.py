import guiTools, pyperclip, winsound, settings, functions
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
        self.font_wrap = settings.settings_handler.get("font", "wrap") == "True"
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        self.context_menu_active = False
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.setWindowTitle(title)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit(viewer_name="textViewer")
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.more_options_label = guiTools.QNavigableLabel("لمزيد من الخيارات، نستخدم زر التطبيقات أو click الأيمن")
        self.more_options_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.more_options_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        layout = qt.QVBoxLayout(self)
        self.permanent_stabilizer_bar = qt.QWidget()
        self.permanent_stabilizer_bar.setFixedHeight(0)
        self.permanent_stabilizer_bar.setAccessibleName(" ")
        self.permanent_stabilizer_bar.setAccessibleDescription(" ")
        layout.addWidget(self.permanent_stabilizer_bar)
        layout.addWidget(self.text)
        layout.addWidget(self.more_options_label)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self._set_text_with_delay(text)

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
        menu = guiTools.QCustomContextMenu("الخيارات", self)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        save = menu.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(lambda: QTimer.singleShot(250, self.save_text_as_txt))
        print_action = menu.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(lambda: QTimer.singleShot(250, self.print_text))
        copy_all = menu.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(lambda: QTimer.singleShot(250, self.copy_text))
        copy_selected_text = menu.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(lambda: QTimer.singleShot(250, self.copy_line))
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
        functions.text_actions.print_text_content(self, self.text)

    def save_text_as_txt(self):
        functions.text_actions.save_text_file(self, self.text)

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

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

    def copy_line(self):
        try:
            if self.saved_selection_start != -1 and self.saved_selection_end != -1 and self.saved_selection_start < self.saved_selection_end:
                selected_text = self.saved_text[self.saved_selection_start:self.saved_selection_end]
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
            elif self.saved_text:
                pyperclip.copy(self.saved_text)
                winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))

    def copy_text(self):
        functions.text_actions.copy_all_text(self, self.text)

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

    def copy_current_selection(self):
        functions.text_actions.copy_current_selection(self, self.text)
