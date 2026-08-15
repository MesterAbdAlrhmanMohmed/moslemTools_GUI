from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
import re
from gui.quranViewer.threads import SearchModeDialog


class BookNotesBookmarksMixin:
    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()

    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("islamicBooks", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()

    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("islamicBooks", name)
        if existing_note is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("islamicBooks", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")

    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("islamicBooks", new_name)
            if existing_note is not None:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("islamicBooks", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")

    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()

    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("islamicBooks", note["name"])
                guiTools.speak("تم حذف الملاحظة")

    def onAddOrRemoveNote(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)

    def onViewNote(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الصفحة")

    def onDeleteNoteShortcut(self):
        position_data = {"bookName": self.bookName, "partName": self.part, "pageNumber": self.index}
        note_exists = notesManager.getNotesForPosition("islamicBooks", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")

    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getIslamicBookBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
            functions.bookMarksManager.addNewislamicBookBookMark(self.bookName, self.part, self.index, name)
            guiTools.speak("تمت إضافة العلامة المرجعية")

    def onRemoveBookmark(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", "نعم", "لا")
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
