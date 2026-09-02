import winsound
import guiTools
from guiTools import note_dialog
import functions.notesManager as notesManager
import functions.bookMarksManager as bookMarksManager

class MotonNotesBookmarksMixin:
    def onAddOrRemoveBookmark(self):
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        bayt_num = bayt["global_num"]
        bayt_text = f"{bayt['sadr']} - {bayt['ajuz']}"
        state, bm_name = bookMarksManager.getMotonBookmarkName(self.matn_name, bayt_num)
        if state:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{bm_name}'؟", "نعم", "لا")
            if confirm == 0:
                bookMarksManager.removeMotonBookmark(bm_name)
                guiTools.speak("تم حذف العلامة المرجعية")
        else:
            name, ok = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أدخل اسم العلامة المرجعية:", "")
            if ok and name.strip():
                bookmarks = bookMarksManager.getMotonBookmarks()
                if any(b.get('name') == name.strip() for b in bookmarks):
                    guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                    return
                bookMarksManager.addMotonBookmark(name.strip(), self.matn_name, bayt.get("chapter_title", ""), bayt_num, bayt_text)
                guiTools.speak("تمت إضافة العلامة المرجعية")

    def onAddOrRemoveNote(self):
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        bayt_num = bayt["global_num"]
        bayt_text = f"{bayt['sadr']} - {bayt['ajuz']}"
        position_data = {
            "matn_name": self.matn_name,
            "chapter_title": bayt.get("chapter_title", ""),
            "bayt_number": bayt_num,
            "bayt_text": bayt_text
        }
        note_exists = notesManager.getNotesForPosition("moton", position_data)
        if note_exists:
            dialog = note_dialog.NoteDialog(self, title=note_exists["name"], content=note_exists["content"], mode="edit", old_name=note_exists["name"])
            dialog.saved.connect(lambda old, new, content: self.update_note(position_data, old, new, content))
            dialog.exec()
        else:
            dialog = note_dialog.NoteDialog(self, mode="add")
            dialog.saved.connect(lambda old, new, content: self.save_note(position_data, new, content))
            dialog.exec()

    def save_note(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("moton", name)
        if existing_note is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("moton", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")

    def update_note(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("moton", new_name)
            if existing_note is not None:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("moton", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")

    def onViewNote(self):
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        bayt_num = bayt["global_num"]
        bayt_text = f"{bayt['sadr']} - {bayt['ajuz']}"
        position_data = {
            "matn_name": self.matn_name,
            "chapter_title": bayt.get("chapter_title", ""),
            "bayt_number": bayt_num,
            "bayt_text": bayt_text
        }
        note = notesManager.getNotesForPosition("moton", position_data)
        if note:
            guiTools.TextViewer(self, f"ملاحظة: {note['name']}", note["content"]).exec()
        else:
            guiTools.speak("لا توجد ملاحظة لهذا البيت")

    def onDeleteNoteShortcut(self):
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        bayt_num = bayt["global_num"]
        bayt_text = f"{bayt['sadr']} - {bayt['ajuz']}"
        position_data = {
            "matn_name": self.matn_name,
            "chapter_title": bayt.get("chapter_title", ""),
            "bayt_number": bayt_num,
            "bayt_text": bayt_text
        }
        note = notesManager.getNotesForPosition("moton", position_data)
        if note:
            notesManager.removeNote("moton", note["name"])
            guiTools.speak("تم حذف الملاحظة")
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
