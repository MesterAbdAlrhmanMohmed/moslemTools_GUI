import guiTools, pyperclip, winsound, functions, re, os, settings, requests, shutil
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from gui.quranViewer import QuranViewer
from gui.tafaseerViewer import TafaseerViewer
from gui.translationViewer import translationViewer
from gui.changeReciter import ChangeReciter
from .search_worker import DownloadThread, SearchModeDialog, SearchThread, RemainingThread


class ResearcherSearchEngineMixin:
    def on_scope_changed(self, index):
        self.specific_scope_combo.clear()
        if index == 0:
            self.specific_scope_label.setVisible(False)
            self.specific_scope_combo.setVisible(False)
            self.current_scope = None
        else:
            self.specific_scope_label.setVisible(True)
            self.specific_scope_combo.setVisible(True)
            items = []
            label = ""
            if index == 1:
                items = list(self.surahsList.keys())
                label = "اختر السورة"
            elif index == 2:
                items = [str(i) for i in range(1, 605)]
                label = "اختر الصفحة"
            elif index == 3:
                items = [str(i) for i in range(1, 31)]
                label = "اختر الجزء"
            elif index == 4:
                items = [str(i) for i in range(1, 241)]
                label = "اختر الربع"
            elif index == 5:
                items = [str(i) for i in range(1, 61)]
                label = "اختر الحزب"
            self.specific_scope_label.setText(label)
            self.specific_scope_combo.setAccessibleName(label)
            self.specific_scope_combo.addItems(items)
            self.adjust_combo_width(self.specific_scope_combo)

    def onSearchClicked(self):
        if not self.serch_input.text():
            guiTools.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        if self.current_search_thread and self.current_search_thread.isRunning():
            guiTools.speak("جاري تنفيذ عملية بحث أخرى. يرجى الانتظار")
            return
        if hasattr(self, 'remaining_thread') and self.remaining_thread and self.remaining_thread.isRunning():
            self.remaining_thread.cancel()
            self.remaining_thread.wait()
        self.loading_label.hide()
        self.results.clear()
        self.search_metadata.clear()
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        self.start.setEnabled(False)
        self.start.setText("جاري البحث...")
        search_type = self.serch.currentIndex()
        search_text = self.serch_input.text()
        ahadeeth_text = self.ahadeeth.currentText()
        scope_index = self.surahs.currentIndex()
        if scope_index == 0:
            self.current_scope = None
        else:
            item = self.specific_scope_combo.currentText()
            if scope_index == 1:
                self.current_scope = ('surah', item)
            else:
                stype = ['page', 'juz', 'quarter', 'hizb'][scope_index-2]
                self.current_scope = (stype, int(item))
        self.current_search_thread = SearchThread(self, search_type, search_text, self.current_scope, ahadeeth_text, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        self.current_search_thread.searchFinished.connect(self.onSearchFinished)
        self.current_search_thread.start()

    def onSearchFinished(self, display_text, search_metadata, total_results_count, remaining_chunks):
        self.start.setEnabled(True)
        self.start.setText("البحث")
        self.search_metadata = search_metadata
        if total_results_count > 0:
            self.results.setText("\n".join(display_text))
            self.update_font_size()
            self.clear_results_button.setDisabled(False)
            self.results.setFocus()
            if remaining_chunks:
                self.loading_label.show()
                self.remaining_thread = RemainingThread(remaining_chunks, self)
                self.remaining_thread.chunkFinished.connect(self.onRemainingChunkFinished)
                self.remaining_thread.finished.connect(self.onRemainingFinished)
                self.remaining_thread.start()
            else:
                self.loading_label.hide()
                guiTools.speak("تم تحميل جميع نتائج البحث")
        else:
            self.loading_label.hide()
            guiTools.MessageBox.view(self,"تنبيه","لم يتم العثور على نتائج")
            self.clear_results_button.setDisabled(True)
            self.serch_input.setFocus()

    def onRemainingChunkFinished(self, chunk_display, chunk_metadata):
        if hasattr(self, 'remaining_thread') and self.remaining_thread and self.remaining_thread.is_cancelled:
            return
        if chunk_display:
            self.results.append("\n".join(chunk_display))
            self.search_metadata.update(chunk_metadata)
            qt2.QCoreApplication.processEvents()

    def onRemainingFinished(self):
        self.loading_label.hide()
        if hasattr(self, 'remaining_thread') and self.remaining_thread and self.remaining_thread.is_cancelled:
            return
        guiTools.speak("تم تحميل جميع نتائج البحث")

    def get_metadata_from_result(self, result_text):
        match = re.search(r'^(\d+).+?\((\d+)\)$', result_text)
        if match:
            surah_number = int(match.group(1))
            ayah_number_in_surah = int(match.group(2))
            try:
                surah_name = self.quran_data[str(surah_number)]["name"]
                ayah_data = self.quran_data[str(surah_number)]['ayahs'][ayah_number_in_surah - 1]
                overall_ayah_number = ayah_data['number']
                clean_ayah_text = f"{ayah_data['text']} ({ayah_number_in_surah})"
                return {"surah_number": surah_number,"surah_name": surah_name,"ayah_number_in_surah": ayah_number_in_surah,"overall_ayah_number": overall_ayah_number, "clean_ayah_text": clean_ayah_text}
            except (KeyError, IndexError):
                return None
        return None

    def clear_results(self):
        if hasattr(self, 'remaining_thread') and self.remaining_thread and self.remaining_thread.isRunning():
            self.remaining_thread.cancel()
            self.remaining_thread.wait()
        self.loading_label.hide()
        if self.results.toPlainText():
            self.results.clear()
            self.search_metadata.clear()
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
            self.player_widget.setVisible(False)
            self.clear_results_button.setDisabled(True)
            guiTools.speak("تم حذف نتائج البحث")
        else:
            self.clear_results_button.setDisabled(True)

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

    def handle_error(self, error_msg):
        if "خطأ في البيانات" in error_msg:
            guiTools.MessageBox.error(self, "خطأ في البيانات", error_msg.split(': ', 1)[1])
        elif "خطأ غير متوقع" in error_msg:
            guiTools.MessageBox.error(self, "خطأ غير متوقع", error_msg.split(': ', 1)[1])

    def toggle_ahadeeth_visibility(self):
        if self.serch.currentText() == "الأحاديث":
            self.ahadeeth_laibol.show()
            self.ahadeeth.show()
            self.surahs_laybol.hide()
            self.surahs.hide()
            self.specific_scope_label.hide()
            self.specific_scope_combo.hide()
        else:
            self.ahadeeth_laibol.hide()
            self.ahadeeth.hide()
            self.surahs_laybol.show()
            self.surahs.show()
            if self.surahs.currentIndex() != 0:
                self.specific_scope_label.show()
                self.specific_scope_combo.show()
        self.adjust_all_combos_width()

    def adjust_combo_width(self, combo, extra_padding=65):
        if not combo or combo.count() == 0:
            return
        fm = qt1.QFontMetrics(combo.font())
        current_text = combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        combo.setFixedWidth(text_width + extra_padding)

    def adjust_all_combos_width(self):
        for combo in (self.serch, self.ahadeeth, self.surahs, self.specific_scope_combo):
            if combo.count() > 0:
                self.adjust_combo_width(combo)
