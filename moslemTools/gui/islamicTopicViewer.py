from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
class IslamicTopicViewer(qt.QDialog):
    def __init__(self, p, file_path: str, title: str, content: str, all_topics: dict, index: int = 0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)                
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
        qt1.QShortcut("ctrl+1", self).activated.connect(self.set_font_size_dialog)                
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.file_path = file_path
        self.all_topics = all_topics
        self.current_title = title                
        self.topic_titles = list(self.all_topics.keys())
        self.currentIndex = self.topic_titles.index(self.current_title)
        self.resize(1200, 600)                
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setText(content)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)                        
        self.font_laybol = qt.QLabel("حجم الخط")        
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel(str(self.font_size))
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        self.info = qt.QLabel(self.current_title)
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)                
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.info)                
        buttonsLayout = qt.QHBoxLayout()
        self.previous = guiTools.QPushButton("الموضوع السابق")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.clicked.connect(self.onPrevious)
        self.previous.setShortcut("alt+left")
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")
        self.previous.setAutoDefault(False)        
        self.next = guiTools.QPushButton("الموضوع التالي")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.clicked.connect(self.onNext)
        self.next.setShortcut("alt+right")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")
        self.next.setAutoDefault(False)        
        buttonsLayout.addWidget(self.previous)
        buttonsLayout.addWidget(self.next)
        layout.addLayout(buttonsLayout)        
        self.update_font_size()    
        if index > 0:
            cursor = self.text.textCursor()
            cursor.movePosition(qt1.QTextCursor.MoveOperation.Start)
            for _ in range(index):
                cursor.movePosition(qt1.QTextCursor.MoveOperation.Down)
            self.text.setTextCursor(cursor)
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)        
        text_options = menu.addMenu("خيارات النص")
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
        copy_selected_action.triggered.connect(self.copy_current_selection)        
        topic_options = menu.addMenu("خيارات الموضوع")
        topic_options.setFont(boldFont)
        next_action = topic_options.addAction("الموضوع التالي")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.onNext)
        prev_action = topic_options.addAction("الموضوع السابق")
        prev_action.setShortcut("alt+left")
        prev_action.triggered.connect(self.onPrevious)        
        position_data = self.get_position_data()                
        note_exists = notesManager.getNotesForPosition("islamicTopics", position_data)
        if note_exists:
            view_note_action = topic_options.addAction("عرض ملاحظة السطر الحالي")
            view_note_action.setShortcut("ctrl+o")
            view_note_action.triggered.connect(self.onViewNote)            
            delete_note_widget_action = qt.QWidgetAction(self)                        
            delete_note_button = guiTools.QPushButton("حذف ملاحظة السطر الحالي (ctrl+shift+n)")
            delete_note_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_note_button.setShortcut("ctrl+shift+n")
            delete_note_button.setAutoDefault(False)
            delete_note_button.clicked.connect(self.onDeleteNoteShortcut)
            delete_note_widget_action.setDefaultWidget(delete_note_button)
            topic_options.addAction(delete_note_widget_action)
        else:
            add_note_action = topic_options.addAction("إضافة ملاحظة للسطر الحالي")
            add_note_action.setShortcut("ctrl+n")
            add_note_action.triggered.connect(lambda: self.onAddNote(position_data))                    
        state, bookmark_name = functions.bookMarksManager.getIslamicTopicBookmarkName(self.file_path, self.current_title, self.getCurrentLine())
        if state:            
            remove_bookmark_widget_action = qt.QWidgetAction(self)
            remove_bookmark_button = guiTools.QPushButton("حذف العلامة المرجعية الحالية (ctrl+b)")
            remove_bookmark_button.setStyleSheet("background-color: #8B0000; color: white;")
            remove_bookmark_button.setShortcut("ctrl+b")
            remove_bookmark_button.setAutoDefault(False)
            remove_bookmark_button.clicked.connect(lambda: self.onRemoveBookmark(bookmark_name))
            remove_bookmark_widget_action.setDefaultWidget(remove_bookmark_button)
            topic_options.addAction(remove_bookmark_widget_action)
        else:
            add_bookmark_action = topic_options.addAction("إضافة علامة مرجعية للسطر الحالي")
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)        
        fontMenu = menu.addMenu("حجم الخط")
        fontMenu.setFont(boldFont)
        increase_font_action = fontMenu.addAction("تكبير الخط")
        increase_font_action.setShortcut("ctrl+=")
        increase_font_action.triggered.connect(self.increase_font_size)
        decrease_font_action = fontMenu.addAction("تصغير الخط")
        decrease_font_action.setShortcut("ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)        
        set_font_action = fontMenu.addAction("تعيين حجم مخصص للنص")
        set_font_action.setShortcut("ctrl+1")
        set_font_action.triggered.connect(self.set_font_size_dialog)
        menu.exec(qt1.QCursor.pos())
    def getCurrentLine(self):
        return self.text.textCursor().blockNumber()
    def get_position_data(self):
        return {"file": self.file_path, "title": self.current_title, "line": self.getCurrentLine()}    
    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("islamicTopics", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
    def saveNote(self, position_data, name, content):
        if notesManager.getNoteByName("islamicTopics", name) is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل.")
            return
        notesManager.addNewNote("islamicTopics", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")
    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name and notesManager.getNoteByName("islamicTopics", new_name) is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة الجديد موجود بالفعل.")
            return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        if notesManager.updateNote("islamicTopics", old_name, update_data):
            guiTools.speak("تم تحديث الملاحظة")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل تحديث الملاحظة.")    
    def onAddOrRemoveNote(self):
        position_data = self.get_position_data()
        note = notesManager.getNotesForPosition("islamicTopics", position_data)
        if note:
            self.onEditNote(position_data, note["name"])
        else:
            self.onAddNote(position_data)            
    def onViewNote(self):
        position_data = self.get_position_data()
        note = notesManager.getNotesForPosition("islamicTopics", position_data)
        if note:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذا الموضوع")            
    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("islamicTopics", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("islamicTopics", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("islamicTopics", note["name"])
                guiTools.speak("تم حذف الملاحظة")    
    def onDeleteNoteShortcut(self):
        position_data = self.get_position_data()
        if notesManager.getNotesForPosition("islamicTopics", position_data):
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب اسماً للعلامة المرجعية:")
        if OK and name:
            if any(bookmark['name'] == name for bookmark in functions.bookMarksManager.getIslamicTopicsBookmarks()):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل.")
                return
            functions.bookMarksManager.addNewIslamicTopicBookMark(self.file_path, self.current_title, self.getCurrentLine(), name)
            guiTools.speak("تمت إضافة العلامة المرجعية")
    def onRemoveBookmark(self, bookmark_name):
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف العلامة المرجعية '{bookmark_name}'؟", "نعم", "لا")
        if confirm == 0:
            functions.bookMarksManager.removeIslamicTopicBookMark(bookmark_name)
            guiTools.speak("تم حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state, bookmark_name = functions.bookMarksManager.getIslamicTopicBookmarkName(self.file_path, self.current_title, self.getCurrentLine())
        if state:
            self.onRemoveBookmark(bookmark_name)
        else:
            self.onAddBookMark()
    def onNext(self):
        self.currentIndex = (self.currentIndex + 1) % len(self.topic_titles)
        self.update_topic()
    def onPrevious(self):
        self.currentIndex = (self.currentIndex - 1 + len(self.topic_titles)) % len(self.topic_titles)
        self.update_topic()
    def update_topic(self):
        self.current_title = self.topic_titles[self.currentIndex]
        content = self.all_topics[self.current_title]
        self.text.setText(content)
        self.update_font_size()
        self.info.setText(self.current_title)
        winsound.PlaySound("data/sounds/next_page.wav", winsound.SND_ASYNC)
        guiTools.speak(self.current_title)
    def update_font_size(self):
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
        self.show_font.setText(str(self.font_size))
    def increase_font_size(self):
        if self.font_size < 100:
            self.font_size += 1
            guiTools.speak(str(self.font_size))
            self.update_font_size()
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
            guiTools.speak(str(self.font_size))
            self.update_font_size()
    def set_font_size_dialog(self):
        size, ok = guiTools.QInputDialog.getInt(self, "تغيير حجم الخط", "أدخل حجم الخط (1-100):", self.font_size, 1, 100)
        if ok:
            self.font_size = size
            self.update_font_size()
            guiTools.speak(f"تم تغيير حجم الخط إلى {size}")
    def copy_text(self):
        pyperclip.copy(self.text.toPlainText())
        winsound.Beep(1000, 100)
        guiTools.speak("تم نسخ كل المحتوى")
    def copy_current_selection(self):
        cursor = self.text.textCursor()
        if cursor.hasSelection():
            pyperclip.copy(cursor.selectedText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النص المحدد")
    def save_text_as_txt(self):
        file_name, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(self.text.toPlainText())
                guiTools.speak("تم حفظ الملف")
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم حفظ الملف: {e}")
    def print_text(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.text.print(printer)