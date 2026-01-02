from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, json, functions, settings, os
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
class hadeeth_viewer(qt.QDialog):
    def __init__(self, p, book_name, index: int = 0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        try:
            with open(os.path.join(os.getenv('appdata'), settings.app.appName, "ahadeeth", book_name), "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.index = index
            self.bookName = book_name
        except:
            guiTools.MessageBox.error(self, "خطأ", "تعذر فتح الملف ")
            self.close()
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("alt+right", self).activated.connect(self.next_hadeeth)
        qt1.QShortcut("alt+left", self).activated.connect(self.previous_hadeeth)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.go_to_hadeeth)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copy_page_range)
        qt1.QShortcut("ctrl+alt+s", self).activated.connect(self.save_page_range_as_txt)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.save_page_range_as_docx)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setText(self.data[self.index])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.N_hadeeth = guiTools.QPushButton("الحديث التالي")
        self.N_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_hadeeth.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_hadeeth.clicked.connect(self.next_hadeeth)
        self.N_hadeeth.setAutoDefault(False)
        self.P_hadeeth = guiTools.QPushButton("الحديث السابق")
        self.P_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_hadeeth.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_hadeeth.clicked.connect(self.previous_hadeeth)
        self.P_hadeeth.setAutoDefault(False)
        self.hadeeth_number_laybol = qt.QLabel("رقم الحديث")
        self.hadeeth_number_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_hadeeth_number = qt.QLabel(f"{self.index + 1} من {len(self.data)}")
        self.show_hadeeth_number.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_hadeeth_number.setAccessibleDescription("رقم الحديث")
        self.show_hadeeth_number.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.hadeeth_number_laybol)
        layout.addWidget(self.show_hadeeth_number)
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.P_hadeeth)
        layout1.addWidget(self.N_hadeeth)
        layout.addLayout(layout1)
        self.update_font_size()
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        hadeeth_menu = qt.QMenu("خيارات الحديث", self)
        hadeeth_menu.setFont(boldFont)
        next_action = hadeeth_menu.addAction("الحديث التالي")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.next_hadeeth)
        previous_action = hadeeth_menu.addAction("الحديث السابق")
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.previous_hadeeth)
        go_action = hadeeth_menu.addAction("الذهاب إلى حديث")
        go_action.setShortcut("ctrl+g")
        go_action.triggered.connect(self.go_to_hadeeth)
        menu.addMenu(hadeeth_menu)
        book_options_menu = qt.QMenu("خيارات الكتاب", self)
        book_options_menu.setFont(boldFont)
        copy_range_action = book_options_menu.addAction("نسخ الأحاديث")
        copy_range_action.setShortcut("ctrl+alt+c")
        copy_range_action.triggered.connect(self.copy_page_range)
        save_txt_range_action = book_options_menu.addAction("حفظ الأحاديث كملف نصي")
        save_txt_range_action.setShortcut("ctrl+alt+s")
        save_txt_range_action.triggered.connect(self.save_page_range_as_txt)
        save_docx_range_action = book_options_menu.addAction("حفظ الأحاديث كملف Word")
        save_docx_range_action.setShortcut("ctrl+alt+d")
        save_docx_range_action.triggered.connect(self.save_page_range_as_docx)
        menu.addMenu(book_options_menu)
        text_options_menu = qt.QMenu("خيارات النص", self)
        text_options_menu.setFont(boldFont)
        save_action = text_options_menu.addAction("حفظ كملف نصي")
        save_action.setShortcut("ctrl+s")
        save_action.triggered.connect(self.save_text_as_txt)
        print_action = text_options_menu.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all_action = text_options_menu.addAction("نسخ النص كاملاً")
        copy_all_action.setShortcut("ctrl+a")
        copy_all_action.triggered.connect(self.copy_text)
        copy_selected_action = text_options_menu.addAction("نسخ النص المحدد")
        copy_selected_action.setShortcut("ctrl+c")
        copy_selected_action.triggered.connect(self.copy_line)
        menu.addMenu(text_options_menu)
        font_menu = qt.QMenu("حجم الخط", self)
        font_menu.setFont(boldFont)
        increase_font_action = qt1.QAction("تكبير الخط", self)
        increase_font_action.setShortcut("ctrl+=")
        increase_font_action.triggered.connect(self.increase_font_size)
        decrease_font_action = qt1.QAction("تصغير الخط", self)
        decrease_font_action.setShortcut("ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)
        font_menu.addAction(increase_font_action)
        font_menu.addAction(decrease_font_action)
        menu.addMenu(font_menu)
        hadeeth_position = {"bookName": self.bookName,"hadeethNumber": self.index}
        note_exists = notesManager.getNotesForPosition("ahadeeth", hadeeth_position)
        if note_exists:
            note_action = qt1.QAction("عرض ملاحظة الحديث الحالي", self)
            note_action.setShortcut("ctrl+o")
            note_action.triggered.connect(lambda: self.onNoteAction(hadeeth_position))
            hadeeth_menu.addAction(note_action)
            delete_note_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف ملاحظة الحديث الحالي:   ctrl+shift+n")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+shift+n")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_button.clicked.connect(lambda: self.onDeleteNote(hadeeth_position))
            delete_note_action.setDefaultWidget(delete_button)
            hadeeth_menu.addAction(delete_note_action)
        else:
            note_action = qt1.QAction("إضافة ملاحظة للحديث الحالي", self)
            note_action.setShortcut("ctrl+n")
            note_action.triggered.connect(lambda: self.onAddNote(hadeeth_position))
            hadeeth_menu.addAction(note_action)
        state, self.nameOfBookmark = functions.bookMarksManager.getAhdeethBookmarkName(self.bookName, self.index)
        if state:
            delete_bookmark_action = qt.QWidgetAction(self)
            delete_bookmark_button = qt.QPushButton("حذف العلامة المرجعية للحديث الحالي: ctrl+b")
            delete_bookmark_button.setDefault(True)
            delete_bookmark_button.setShortcut("ctrl+b")
            delete_bookmark_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_bookmark_button.clicked.connect(self.onRemoveBookmark)
            delete_bookmark_action.setDefaultWidget(delete_bookmark_button)
            hadeeth_menu.addAction(delete_bookmark_action)
        else:
            add_bookmark_action = qt1.QAction("إضافة علامة مرجعية للحديث الحالي", self)
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)
            hadeeth_menu.addAction(add_bookmark_action)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def get_page_range(self):
        start_page, ok1 = guiTools.QInputDialog.getInt(self, "بداية النطاق", "أدخل رقم حديث البداية:", value=self.index + 1, min=1, max=len(self.data))
        if not ok1:
            return None, None
        end_page, ok2 = guiTools.QInputDialog.getInt(self, "نهاية النطاق", f"أدخل رقم حديث النهاية (1-{len(self.data)}):", value=len(self.data), min=1, max=len(self.data))
        if not ok2:
            return None, None
        if start_page > end_page:
            guiTools.MessageBox.error(self, "خطأ", "حديث البداية لا يمكن أن يكون أكبر من حديث النهاية")
            return None, None
        return start_page, end_page
    def copy_page_range(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        content = ""
        for i in range(start-1, end):
            content += self.data[i] + "\n\n"
        try:
            pyperclip.copy(content)
            winsound.Beep(1000, 100)
            guiTools.MessageBox.view(self, "تم النسخ", f"تم نسخ المحتوى من الحديث {start} إلى الحديث {end}")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في النسخ", str(e))
    def save_page_range_as_txt(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    for i in range(start-1, end):
                        file.write(self.data[i] + "\n\n")
                guiTools.speak(f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف نصي")
                guiTools.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف نصي")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في الحفظ", str(e))
    def save_page_range_as_docx(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Word Documents (*.docx);;All Files (*)")
            file_dialog.setDefaultSuffix("docx")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                doc = Document()
                for i in range(start-1, end):
                    p = doc.add_paragraph(self.data[i])
                    if i < end-1:
                        doc.add_page_break()
                doc.save(file_name)
                guiTools.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف Word")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في الحفظ", str(e))
    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("ahadeeth", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("ahadeeth", name)
        if existing_note is not None:
            guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("ahadeeth", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")
    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("ahadeeth", new_name)
            if existing_note is not None:
                guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("ahadeeth", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")
    def onAddOrRemoveNote(self):
        position_data = {"bookName": self.bookName,"hadeethNumber": self.index}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)
    def onViewNote(self):
        position_data = {"bookName": self.bookName,"hadeethNumber": self.index}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذا الحديث")
    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("ahadeeth", note["name"])
                guiTools.speak("تم حذف الملاحظة")
    def next_hadeeth(self):
        if self.index == len(self.data) - 1:
            self.index = 0
        else:
            self.index += 1
        self.text.setText(self.data[self.index])
        self.update_font_size()
        guiTools.speak(str(self.index + 1))
        self.show_hadeeth_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/next_page.wav", 1)
    def previous_hadeeth(self):
        if self.index == 0:
            self.index = len(self.data) - 1
        else:
            self.index -= 1
        self.text.setText(self.data[self.index])
        self.update_font_size()
        guiTools.speak(str(self.index + 1))
        self.show_hadeeth_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/previous_page.wav", 1)
    def go_to_hadeeth(self):
        hadeeth, OK = guiTools.QInputDialog.getInt(self, "الذهاب إلى حديث", "أكتب رقم الحديث", self.index + 1, 1, len(self.data))
        if OK:
            self.index = hadeeth - 1
            self.text.setText(self.data[self.index])
            self.update_font_size()
            self.show_hadeeth_number.setText(f"{self.index + 1} من {len(self.data)}")
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
                    file.write(self.text.toPlainText())
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            cursor = self.text.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            pyperclip.copy(self.text.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ المحتوى بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getAhadeethBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
            functions.bookMarksManager.addNewHadeethBookMark(self.bookName, self.index, name)
            guiTools.speak("تمت إضافة العلامة المرجعية")
    def onRemoveBookmark(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", "نعم", "لا")
            if confirm == 0:
                functions.bookMarksManager.removeAhadeethBookMark(self.nameOfBookmark)
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.MessageBox.error(self, "خطأ", "تعذر حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state, self.nameOfBookmark = functions.bookMarksManager.getAhdeethBookmarkName(self.bookName, self.index)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
    def onDeleteNoteShortcut(self):
        position_data = {"bookName": self.bookName,"hadeethNumber": self.index}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")