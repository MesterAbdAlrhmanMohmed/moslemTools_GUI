import guiTools, pyperclip, winsound, json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
class NamesOfAllah(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.font_is_bold = settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings_handler.get("font", "size"))
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.is_loaded = False
        layout = qt.QVBoxLayout(self)
        self.information = guiTools.QReadOnlyTextEdit()
        self.information.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.information.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        layout.addWidget(self.information)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        self.update_font_size()
    def showEvent(self, event):
        super().showEvent(event)
        if not self.is_loaded:
            self.load_data()
    def load_data(self):
        with open("data/json/namesOfAllah.json", "r", encoding="utf-8") as file:
            all_data = json.load(file)
        self.data = all_data.get("ar", [])
        formatted_text = ""
        for item in self.data:
            name = item.get("name", "اسم غير موجود")
            meaning = item.get("meaning", "معنى غير موجود")
            formatted_text += f"{name}\n{meaning}\n"
        self.information.setText(formatted_text.strip())
        self.is_loaded = True
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        menu.setFont(bold_font)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        text_options = qt.QMenu("خيارات النص", self)
        text_options.setFont(bold_font)
        save = text_options.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)
        print_action = text_options.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all = text_options.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text = text_options.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_line)
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(bold_font)
        increase_font_action = qt1.QAction("تكبير الخط", self)
        increase_font_action.setShortcut("ctrl+=")
        fontMenu.addAction(increase_font_action)
        fontMenu.setDefaultAction(increase_font_action)
        increase_font_action.triggered.connect(self.increase_font_size)
        decrease_font_size_action = qt1.QAction("تصغير الخط", self)
        decrease_font_size_action.setShortcut("ctrl+-")
        fontMenu.addAction(decrease_font_size_action)
        decrease_font_size_action.triggered.connect(self.decrease_font_size)
        menu.addMenu(text_options)
        menu.addMenu(fontMenu)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))
    def increase_font_size(self):
        if self.show_font.value() < 100:
            self.show_font.setValue(self.show_font.value() + 1)
    def decrease_font_size(self):
        if self.show_font.value() > 1:
            self.show_font.setValue(self.show_font.value() - 1)
    def update_font_size(self):
        cursor = self.information.textCursor()
        self.information.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.information.setCurrentFont(font)
        self.information.setTextCursor(cursor)
    def print_text(self):
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.information.print(printer)
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
                    text = self.information.toPlainText()
                    file.write(text)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_line(self):
        try:
            cursor = self.information.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text = self.information.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))