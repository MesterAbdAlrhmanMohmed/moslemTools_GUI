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


class SearchHandlerMixin:
    def _is_invalid_search_line(self):
        if self.is_search_view and self.text.toPlainText().startswith("عدد نتائج البحث"):
            if self.text.textCursor().blockNumber() < 2:
                return True
        current_line_text = self.text.textCursor().block().text().strip()
        if not current_line_text or re.match(r'^صفحة \d+$', current_line_text):
            return True
        return False

    def _handle_invalid_search_line_action(self):
        winsound.Beep(440, 200)
        guiTools.speak("لا يمكن تنفيذ هذا الإجراء على هذا السطر")

    def _handle_search_view_restriction(self):
        winsound.Beep(440, 200)
        guiTools.speak("هذا الخيار غير متاح في وضع البحث")

    def toggle_search_bar(self):
        if self.search_widget.isVisible():
            self.search_widget.hide()
            self.toggle_search_button.setText("البحث في المحتوى المعروض")
            guiTools.speak("تم إخفاء شريط البحث")
            self.text.setFocus()
        else:
            self.search_widget.show()
            self.toggle_search_button.setText("إخفاء شريط البحث")
            self.search_input.setFocus()

    def show_search_mode_dialog(self):
        self.pause_for_action()
        dialog = SearchModeDialog(self, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            settings_values = dialog.get_settings()
            self.ignore_tashkeel = settings_values["ignore_tashkeel"]
            self.ignore_hamza = settings_values["ignore_hamza"]
            self.ignore_symbols = settings_values["ignore_symbols"]
            guiTools.speak("تم تطبيق إعدادات البحث بنجاح")
        else:
            guiTools.speak("تم إلغاء التغييرات")
        self.resume_after_action()

    def search(self, pattern, text_list):
        def remove_tashkeel(text):
            return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        def normalize_hamza(text):
            return re.sub(r'[أإآ]', 'ا', text)
        def normalize(text):
            normalized_text = text
            if self.ignore_tashkeel:
                normalized_text = remove_tashkeel(normalized_text)
            if self.ignore_hamza:
                normalized_text = normalize_hamza(normalized_text)
            return normalized_text
        normalized_pattern = normalize(pattern)
        return [text for text in text_list if normalized_pattern in normalize(text)]

    def perform_search(self):
        search_term = self.search_input.text()
        if not search_term:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        source_text_list = self.original_quran_text.split('\n')
        try:
            results = self.search(search_term, source_text_list)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في البحث", f"حدث خطأ غير متوقع أثناء البحث: {e}")
            return
        if results:
            self.is_search_view = True
            self.numbering_button.setVisible(False)
            self.enableBookmarks = False
            header = f"عدد نتائج البحث: {len(results)}"
            guiTools.speak(header)
            display_text = [header, ""] + results
            self.quranText = "\n".join(results)
            self.text.setText("\n".join(display_text))
            self.update_font_size()
            self.clear_results_button.show()
            if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media.stop()
        else:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على نتائج")

    def clear_search_results(self):
        self.is_search_view = False
        self.numbering_button.setVisible(True)
        self.enableBookmarks = self.initial_enableBookmarks
        self.quranText = self.original_quran_text
        self.text.setText(self.original_quran_text)
        self.update_font_size()
        self.clear_results_button.hide()
        self.search_input.clear()
        guiTools.speak("تمت العودة إلى العرض الأصلي")
