from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
class book_viewer(qt.QDialog):
    def __init__(self, p, book_name, partName: str, content: list, index: int = 0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.data = content
        self.index = index
        self.bookName = book_name
        self.part = partName        
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("alt+right", self).activated.connect(self.next_book)
        qt1.QShortcut("alt+left", self).activated.connect(self.previous_book)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.go_to_book)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copy_page_range)
        qt1.QShortcut("ctrl+alt+s", self).activated.connect(self.save_page_range_as_txt)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.save_page_range_as_docx)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit()
        self.text.setText(self.data[self.index])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size = 12
        font = self.font()
        font.setPointSize(self.font_size)
        self.text.setFont(font)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.N_book = guiTools.QPushButton("الصفحة التالية")
        self.N_book.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_book.clicked.connect(self.next_book)
        self.N_book.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_book.setAutoDefault(False)
        self.P_book = guiTools.QPushButton("الصفحة السابقة")
        self.P_book.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_book.clicked.connect(self.previous_book)
        self.P_book.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_book.setAutoDefault(False)
        self.book_number_laybol = qt.QLabel("رقم الصفحة")
        self.book_number_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_book_number = qt.QLabel()
        self.show_book_number.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_book_number.setAccessibleDescription("رقم الصفحة")
        self.show_book_number.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.book_number_laybol)
        layout.addWidget(self.show_book_number)
        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.P_book)
        layout1.addWidget(self.N_book)        
        layout.addLayout(layout1)        
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")        
        book_menu = qt.QMenu("خيارات الصفحة", self)
        book_menu.setFont(boldFont)
        next_action = book_menu.addAction("الصفحة التالية")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.next_book)    
        previous_action = book_menu.addAction("الصفحة السابقة")
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.previous_book)    
        go_action = book_menu.addAction("الذهاب إلى صفحة")
        go_action.setShortcut("ctrl+g")
        go_action.triggered.connect(self.go_to_book)    
        menu.addMenu(book_menu)        
        book_options_menu = qt.QMenu("خيارات الكتاب", self)
        book_options_menu.setFont(boldFont)        
        copy_range_action = book_options_menu.addAction("نسخ محتوى الكتاب")
        copy_range_action.setShortcut("ctrl+alt+c")
        copy_range_action.triggered.connect(self.copy_page_range)        
        save_txt_range_action = book_options_menu.addAction("حفظ محتوى الكتاب كملف نصي")
        save_txt_range_action.setShortcut("ctrl+alt+s")
        save_txt_range_action.triggered.connect(self.save_page_range_as_txt)        
        save_docx_range_action = book_options_menu.addAction("حفظ محتوة الكتاب كملف Word")
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
        font_menu.addAction(increase_font_action)    
        decrease_font_action = qt1.QAction("تصغير الخط", self)
        decrease_font_action.setShortcut("ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        font_menu.addAction(set_font_size)
        font_menu.addAction(decrease_font_action)
        menu.addMenu(font_menu)        
        book_position = {
            "bookName": self.bookName,
            "partName": self.part,
            "pageNumber": self.index
        }    
        note_exists = notesManager.getNotesForPosition("islamicBooks", book_position)    
        if note_exists:
            note_action = qt1.QAction("عرض ملاحظة الصفحة الحالية", self)
            note_action.setShortcut("ctrl+o")
            note_action.triggered.connect(lambda: self.onNoteAction(book_position))
            book_menu.addAction(note_action)            
            delete_note_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف ملاحظة الصفحة الحالية:  ctrl+shift+n")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+shift+n")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")            
            delete_button.clicked.connect(lambda: self.onDeleteNote(book_position))
            delete_note_action.setDefaultWidget(delete_button)
            book_menu.addAction(delete_note_action)
        else:
            note_action = qt1.QAction("إضافة ملاحظة للصفحة الحالية", self)
            note_action.setShortcut("ctrl+n")
            note_action.triggered.connect(lambda: self.onAddNote(book_position))    
            book_menu.addAction(note_action)                
        state, self.nameOfBookmark = functions.bookMarksManager.getIslamicBookBookmarkName(self.bookName, self.index)
        if state:
            delete_bookmark_action = qt.QWidgetAction(self)
            delete_bookmark_button = qt.QPushButton("حذف العلامة المرجعية للصفحة الحالية: ctrl+b")
            delete_bookmark_button.setDefault(True)
            delete_bookmark_button.setShortcut("ctrl+b")
            delete_bookmark_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_bookmark_button.clicked.connect(self.onRemoveBookmark)
            delete_bookmark_action.setDefaultWidget(delete_bookmark_button)
            book_menu.addAction(delete_bookmark_action)
        else:
            add_bookmark_action = qt1.QAction("إضافة علامة مرجعية للصفحة الحالية", self)
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)
            book_menu.addAction(add_bookmark_action)        
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def get_page_range(self):        
        start_page, ok1 = guiTools.QInputDialog.getInt(
            self, "بداية النطاق", "أدخل رقم صفحة البداية:", 
            value=self.index + 1, min=1, max=len(self.data)
        )
        if not ok1:
            return None, None            
        end_page, ok2 = guiTools.QInputDialog.getInt(
            self, "نهاية النطاق", f"أدخل رقم صفحة النهاية (1-{len(self.data)}):", 
            value=len(self.data), 
            min=1, max=len(self.data)
        )
        if not ok2:
            return None, None        
        if start_page > end_page:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "صفحة البداية لا يمكن أن تكون أكبر من صفحة النهاية")
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
            guiTools.qMessageBox.MessageBox.view(self, "تم النسخ", f"تم نسخ المحتوى من الصفحة {start} إلى الصفحة {end}")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في النسخ", str(e))
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
                guiTools.speak(f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))
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
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف Word")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))
    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()    
    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("islamicBooks", note_name)
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
        notesManager.addNewNote("islamicBooks", {
            "name": name,
            "content": content,
            "position_data": position_data
        })    
        guiTools.speak("تمت إضافة الملاحظة")    
    def updateNote(self, position_data, old_name, new_name, new_content):
        update_data = {
            "name": new_name,
            "content": new_content,
            "position_data": position_data
        }
        success = notesManager.updateNote("islamicBooks", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")    
    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
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
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف", 
                f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", 
                "نعم", "لا"
            )
            if confirm == 0:
                notesManager.removeNote("islamicBooks", note["name"])
                guiTools.speak("تم حذف الملاحظة")    
    def onAddOrRemoveNote(self):
        position_data = {
            "bookName": self.bookName,
            "partName": self.part,
            "pageNumber": self.index
        }
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)    
    def onViewNote(self):
        position_data = {
            "bookName": self.bookName,
            "partName": self.part,
            "pageNumber": self.index
        }
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الصفحة")
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
            cursor = self.text.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text = self.text.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            functions.bookMarksManager.addNewislamicBookBookMark(self.bookName, self.part, self.index, name)
            guiTools.speak("تمت إضافة العلامة المرجعية")
    def onRemoveBookmark(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(
                self, "تأكيد الحذف", 
                f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", 
                "نعم", "لا"
            )
            if confirm == 0:
                functions.bookMarksManager.removeislamicBookBookMark(self.nameOfBookmark)                
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف العلامة المرجعية")    
    def onAddOrRemoveBookmark(self):
        state, self.nameOfBookmark = functions.bookMarksManager.getIslamicBookBookmarkName(self.bookName, self.index)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
    def next_book(self):
        self.index = 0 if self.index == len(self.data) - 1 else self.index + 1
        self.text.setText(self.data[self.index])
        guiTools.speak(str(self.index + 1))
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/next_page.wav", 1)
    def previous_book(self):
        self.index = len(self.data) - 1 if self.index == 0 else self.index - 1
        self.text.setText(self.data[self.index])
        guiTools.speak(str(self.index + 1))
        self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
        winsound.PlaySound("data/sounds/previous_page.wav", 1)
    def go_to_book(self):
        book, OK = guiTools.QInputDialog.getInt(self, "الذهاب إلى صفحة", "أكتب رقم الصفحة", self.index + 1, 1, len(self.data))
        if OK:
            self.index = book - 1
            self.text.setText(self.data[self.index])
            self.show_book_number.setText(f"{self.index + 1} من {len(self.data)}")
    def onDeleteNoteShortcut(self):
        position_data = {
            "bookName": self.bookName,
            "partName": self.part,
            "pageNumber": self.index
        }
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
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