from guiTools import note_dialog
import functions.notesManager as notesManager
from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
from ..quranPlayer import QuranPlayer
import time, winsound, pyperclip, os, re, requests, subprocess, shutil, traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, SajdaGoToDialog, AsbabAlnozoleGoToDialog, SajdaFinderThread, AsbabAlnozoleFinderThread, SearchModeDialog, GoToCategoryDialog

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class NotesBookmarksMixin:
    def onAddNote(self, position_data):
        self.pause_for_action()
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()
        self.resume_after_action()

    def onEditNote(self, position_data, note_name):
        self.pause_for_action()
        note = notesManager.getNoteByName("quran", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()
        self.resume_after_action()

    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("quran", name)
        if existing_note is not None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("quran", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")

    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("quran", new_name)
            if existing_note is not None:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("quran", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")

    def onAddOrRemoveNote(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن إدارة الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        ayah_position = {"ayah_text": self.getcurrentAyahText(), "ayah_number": self.getCurrentAyah(), "surah": self.category}
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onEditNote(ayah_position, note_exists["name"])
        else:
            self.onAddNote(ayah_position)
        self.resume_after_action()

    def onViewNote(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن عرض الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        ayah_position = {"ayah_text": self.getcurrentAyahText(), "ayah_number": self.getCurrentAyah(), "surah": self.category}
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onNoteAction(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لهذه الآية")
        self.resume_after_action()

    def onNoteAction(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()
        self.resume_after_action()

    def onDeleteNote(self, position_data):
        self.pause_for_action()
        note = notesManager.getNotesForPosition("quran", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("quran", note["name"])
                guiTools.speak("تم حذف الملاحظة")
        self.resume_after_action()

    def onAddBookMark(self):
        self.pause_for_action()
        if self.enableBookmarks==False:
            guiTools.qMessageBox.MessageBox.error(self,"تنبيه","لا يمكن وضع علامة مرجعية عند تصفح القرآن بشكلا مخصص")
            self.resume_after_action()
            return
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getQuranBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                self.resume_after_action()
                return
            current_ayah = self.getCurrentAyah()
            functions.bookMarksManager.addNewQuranBookMark(self.type, self.category, current_ayah, False, name)
        self.resume_after_action()

    def onRemoveBookmark(self):
        self.pause_for_action()
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", "نعم", "لا")
            if confirm == 0:
                functions.bookMarksManager.removeQuranBookMark(self.nameOfBookmark)
                guiTools.speak("تم حذف العلامة المرجعية")
        except:
            guiTools.speak("تم حذف العلامة المرجعية")
        self.resume_after_action()

    def onAddOrRemoveBookmark(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن إدارة العلامات المرجعية في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        current_ayah = self.getCurrentAyah()
        state, self.nameOfBookmark = functions.bookMarksManager.getQuranBookmarkName(self.type, self.category, current_ayah, isPlayer=False)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()
        self.resume_after_action()

    def onDeleteNoteShortcut(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        if not self.enableBookmarks:
            winsound.Beep(440, 200)
            guiTools.speak("لا يمكن حذف الملاحظات في وضع البحث أو التصفح المخصص")
            self.resume_after_action()
            return
        current_ayah = self.getCurrentAyah()
        ayah_position = {"ayah_text": self.getcurrentAyahText(), "ayah_number": current_ayah, "surah": self.category}
        note_exists = notesManager.getNotesForPosition("quran", ayah_position)
        if note_exists:
            self.onDeleteNote(ayah_position)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
        self.resume_after_action()
