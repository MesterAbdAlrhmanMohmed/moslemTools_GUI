from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
class StoryViewer(qt.QDialog):
    def __init__(self, p, text, type: int, category: str, stories: list, index=0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        self.type = type
        self.stories = stories
        self.category = category
        self.CurrentIndex = list(self.stories.keys()).index(self.category)
        self.context_menu_active = False
        self.saved_text = ""
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setText(text)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel(str(self.font_size))
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self.info = qt.QLabel(self.category)
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info)
        buttonsLayout = qt.QHBoxLayout()
        self.previous = guiTools.QPushButton("القصة السابقة")
        self.previous.clicked.connect(self.onPreviouse)
        self.previous.setShortcut("alt+left")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")
        self.previous.setAutoDefault(False)
        self.next = guiTools.QPushButton("القصة التالية")
        self.next.clicked.connect(self.onNext)
        self.next.setShortcut("alt+right")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")
        self.next.setAutoDefault(False)
        buttonsLayout.addWidget(self.previous)
        buttonsLayout.addWidget(self.next)
        layout.addLayout(buttonsLayout)
        if index != 0:
            cerser = self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)            
            for _ in range(index):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
        self.update_font_size()
    def OnContextMenu(self):        
        current_line = self.getCurrentLine()
        cursor = self.text.textCursor()
        self.saved_selection_start = cursor.selectionStart()
        self.saved_selection_end = cursor.selectionEnd()
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_text = self.text.toPlainText()
        self.text.setUpdatesEnabled(False)
        self.text.clear()
        self.context_menu_active = True
        menu = qt.QMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        text_options = qt.QMenu("خيارات النص", self)
        text_options.setFont(boldFont)
        save_action = text_options.addAction("حفظ كملف نصي")
        save_action.setShortcut("ctrl+s")
        save_action.triggered.connect(self.save_text_as_txt)
        print_action = text_options.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all_action = text_options.addAction("نسخ النص كاملا")
        copy_all_action.setShortcut("ctrl+a")
        copy_all_action.triggered.connect(self.copy_text)
        copy_selected_action = text_options.addAction("نسخ النص المحدد")
        copy_selected_action.setShortcut("ctrl+c")
        copy_selected_action.triggered.connect(self.copy_line)
        menu.addMenu(text_options)
        story_options = qt.QMenu("خيارات القصة", self)
        story_options.setFont(boldFont)
        story_options.addAction("القصة التالية", self.onNext).setShortcut("alt+right")
        story_options.addAction("القصة السابقة", self.onPreviouse).setShortcut("alt+left")                
        story_position = {
            "type": self.type,
            "category": self.category,
            "line": current_line
        }
        note_exists = notesManager.getNotesForPosition("stories", story_position)
        if note_exists:
            note_action = qt1.QAction("عرض ملاحظة السطر الحالي", self)
            note_action.setShortcut("ctrl+o")
            note_action.triggered.connect(lambda: self.onNoteAction(story_position))
            story_options.addAction(note_action)
            delete_note_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف ملاحظة السطر الحالي: CTRL+shift+N")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+shift+n")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_button.setAutoDefault(False)
            delete_button.clicked.connect(lambda: self.onDeleteNote(story_position))
            delete_note_action.setDefaultWidget(delete_button)
            story_options.addAction(delete_note_action)
        else:
            note_action = qt1.QAction("إضافة ملاحظة للسطر الحالي", self)
            note_action.setShortcut("ctrl+n")
            note_action.triggered.connect(lambda: self.onAddNote(story_position))
            story_options.addAction(note_action)                
        state, bookmark_name = functions.bookMarksManager.getStoriesBookmarkName(
            self.category, current_line
        )
        if state:
            delete_bookmark_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف العلامة المرجعية: Ctrl+B")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+b")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_button.setAutoDefault(False)
            delete_button.clicked.connect(lambda: self.onRemoveBookmark(bookmark_name))
            delete_bookmark_action.setDefaultWidget(delete_button)
            story_options.addAction(delete_bookmark_action)
        else:
            add_bookmark_action = qt1.QAction("إضافة علامة مرجعية للسطر الحالي", self)
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)
            story_options.addAction(add_bookmark_action)
        menu.addMenu(story_options)
        fontMenu = qt.QMenu("حجم الخط", self)
        fontMenu.setFont(boldFont)
        fontMenu.addAction("تكبير الخط", self.increase_font_size).setShortcut("ctrl+=")
        fontMenu.addAction("تصغير الخط", self.decrease_font_size).setShortcut("ctrl+-")
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        fontMenu.addAction(set_font_size)
        menu.addMenu(fontMenu)
        menu.aboutToHide.connect(self.restore_after_menu)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def restore_after_menu(self):
        self.context_menu_active = False
        self.text.setText(self.saved_text)
        self.update_font_size()
        self.text.setUpdatesEnabled(True)
        if self.saved_cursor_position is not None:
            cursor = self.text.textCursor()
            cursor.setPosition(self.saved_cursor_position)
            self.text.setTextCursor(cursor)
    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("stories", note_name)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="edit",
                old_name=note["name"]
            )
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("stories", name)
        if existing_note is not None:
            guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("stories", {
            "name": name,
            "content": content,
            "position_data": position_data
        })
        guiTools.speak("تمت إضافة الملاحظة")
    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("stories", new_name)
            if existing_note is not None:
                guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {
            "name": new_name,
            "content": new_content,
            "position_data": position_data
        }
        success = notesManager.updateNote("stories", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")
    def onAddOrRemoveNote(self):
        position_data = {
            "type": self.type,
            "category": self.category,
            "line": self.getCurrentLine()
        }
        note_exists = notesManager.getNotesForPosition("stories", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)
    def onViewNote(self):
        position_data = {
            "type": self.type,
            "category": self.category,
            "line": self.getCurrentLine()
        }
        note_exists = notesManager.getNotesForPosition("stories", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذا السطر")
    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("stories", position_data)
        if note:
            dialog = note_dialog.NoteDialog(
                self,
                title=note["name"],
                content=note["content"],
                mode="view",
                old_name=note["name"]
            )
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("stories", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف",
                f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟",
                "نعم", "لا"
            )
            if confirm == 0:
                notesManager.removeNote("stories", note["name"])
                guiTools.speak("تم حذف الملاحظة")
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
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            pyperclip.copy(self.saved_text)
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def getCurrentLine(self):
        return self.text.textCursor().blockNumber()
    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getStoriesBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
            functions.bookMarksManager.addNewStoriesBookMark(self.type, self.category, self.getCurrentLine(), name)
            guiTools.speak("تمت إضافة العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state, bookmark_name = functions.bookMarksManager.getStoriesBookmarkName(self.category, self.getCurrentLine())
        if state:
            self.onRemoveBookmark(bookmark_name)
        else:
            self.onAddBookMark()
    def onRemoveBookmark(self, bookmark_name):
        try:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف",
                f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{bookmark_name}'؟",
                "نعم", "لا"
            )
            if confirm == 0:
                functions.bookMarksManager.removeStoriesBookMark(bookmark_name)
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.MessageBox.error(self, "خطأ", "تعذر حذف العلامة المرجعية")
    def onNext(self):
        self.CurrentIndex = (self.CurrentIndex + 1) % len(self.stories)
        self.category = list(self.stories.keys())[self.CurrentIndex]
        self.text.setText(self.stories[self.category])
        self.update_font_size()
        self.info.setText(self.category)
        winsound.PlaySound("data/sounds/next_page.wav", 1)
        guiTools.speak(self.category)
    def onPreviouse(self):
        self.CurrentIndex = (self.CurrentIndex - 1) % len(self.stories)
        self.category = list(self.stories.keys())[self.CurrentIndex]
        self.text.setText(self.stories[self.category])
        self.update_font_size()
        self.info.setText(self.category)
        winsound.PlaySound("data/sounds/next_page.wav", 1)
        guiTools.speak(self.category)
    def onDeleteNoteShortcut(self):
        position_data = {
            "type": self.type,
            "category": self.category,
            "line": self.getCurrentLine()
        }
        note_exists = notesManager.getNotesForPosition("stories", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
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