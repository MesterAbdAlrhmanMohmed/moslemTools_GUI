import guiTools, requests, os, winsound, gui, functions, subprocess, shutil
import ujson as json
from guiTools import TextViewer
from guiTools import speak
from guiTools.QCustomListDialog import QCustomListDialog
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from functions import audio_manager
from .threads import DownloadThread, MergeThread
from .favorites import FavoritesManager


class PlayerPlaybackModesMixin:
    def handle_play_all_toggled(self, checked):
        if checked:
            self.play_all_to_start.blockSignals(True)
            self.play_all_to_start.setChecked(False)
            self.play_all_to_start.blockSignals(False)
            self.update_button_style(self.play_all_to_start, False)
            self.repeat_surah_button.blockSignals(True)
            self.repeat_surah_button.setChecked(False)
            self.repeat_surah_button.blockSignals(False)
            self.update_button_style(self.repeat_surah_button, False)
            self.play_all_to_start.setEnabled(False)
            self.repeat_surah_button.setEnabled(False)
            if self.surahListWidget.currentRow() == -1 and self.surahListWidget.count() > 0:
                self.surahListWidget.setCurrentRow(0)
            if self.mp.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.play_selected_audio()
        else:
            self.play_all_to_start.setEnabled(True)
            self.repeat_surah_button.setEnabled(True)

    def handle_play_all_start_toggled(self, checked):
        if checked:
            self.play_all_to_end.blockSignals(True)
            self.play_all_to_end.setChecked(False)
            self.play_all_to_end.blockSignals(False)
            self.update_button_style(self.play_all_to_end, False)
            self.repeat_surah_button.blockSignals(True)
            self.repeat_surah_button.setChecked(False)
            self.repeat_surah_button.blockSignals(False)
            self.update_button_style(self.repeat_surah_button, False)
            self.play_all_to_end.setEnabled(False)
            self.repeat_surah_button.setEnabled(False)
            if self.surahListWidget.currentRow() == -1 and self.surahListWidget.count() > 0:
                self.surahListWidget.setCurrentRow(self.surahListWidget.count() - 1)
            if self.mp.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.play_selected_audio()
        else:
            self.play_all_to_end.setEnabled(True)
            self.repeat_surah_button.setEnabled(True)

    def handle_repeat_toggled(self, checked):
        if checked:
            if not self.check_media_loaded():
                self.repeat_surah_button.blockSignals(True)
                self.repeat_surah_button.setChecked(False)
                self.repeat_surah_button.blockSignals(False)
                self.update_button_style(self.repeat_surah_button, False)
                return
            self.play_all_to_end.blockSignals(True)
            self.play_all_to_end.setChecked(False)
            self.play_all_to_end.blockSignals(False)
            self.update_button_style(self.play_all_to_end, False)
            self.play_all_to_start.blockSignals(True)
            self.play_all_to_start.setChecked(False)
            self.play_all_to_start.blockSignals(False)
            self.update_button_style(self.play_all_to_start, False)
            self.play_all_to_end.setEnabled(False)
            self.play_all_to_start.setEnabled(False)
        else:
            self.play_all_to_end.setEnabled(True)
            self.play_all_to_start.setEnabled(True)

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_surah_button.isChecked():
                self.mp.setPosition(0)
                self.play_selected_audio()
            elif self.play_all_to_end.isChecked():
                self.play_next_in_list()
            elif self.play_all_to_start.isChecked():
                self.play_previous_in_list()

    def play_next_in_list(self):
        current_row = self.surahListWidget.currentRow()
        if current_row < self.surahListWidget.count() - 1:
            self.surahListWidget.setCurrentRow(current_row + 1)
            self.play_selected_audio()
        else:
            self.play_all_to_end.setChecked(False)

    def play_previous_in_list(self):
        current_row = self.surahListWidget.currentRow()
        if current_row > 0:
            self.surahListWidget.setCurrentRow(current_row - 1)
            self.play_selected_audio()
        else:
            self.play_all_to_start.setChecked(False)

    def play_selected_audio(self):
        self.repeatFromPositionToPosition = False
        self.paused_position = None
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                audio_path = os.path.join(audio_folder, selected_item.text() + ".mp3")
                if os.path.exists(audio_path):
                    self.mp.setSource(qt2.QUrl.fromLocalFile(audio_path))
                    qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.mp.play()))
                else:
                    url = self.reciters_data[reciter][selected_item.text()]
                    self.mp.setSource(qt2.QUrl(url))
                    qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.mp.play()))
                is_manual_playback = not self.play_all_to_end.isChecked() and not self.play_all_to_start.isChecked()
                self.repeat_surah_button.setEnabled(is_manual_playback)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تشغيل المقطع:" + str(e))

    def on_reciter_selected(self):
        self.paused_position = None
        self.mp.stop()
        self.surahListWidget.clear()
        self.cancel_merge()
        self.cancel_download_batch()
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item and selected_reciter_item.text() != "لا يوجد قراء في قائمة المفضلة" and selected_reciter_item.text() in self.reciters_data:
            self.merge_all_from_start_button.setVisible(True)
            self.merge_all_from_end_button.setVisible(True)
            reciter = selected_reciter_item.text()
            for surah, link in self.reciters_data[reciter].items():
                self.surahListWidget.addItem(surah)
            self.check_all_surahs_downloaded()
        else:
            self.merge_all_from_start_button.setVisible(False)
            self.merge_all_from_end_button.setVisible(False)

    def onChangeStartingPosition(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        position = self.mp.position()
        self.startingPosition = position
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        self._is_seeking_loop = False
        winsound.Beep(400, 500)
        self.time_VA()

    def onChangeEndingPosition(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        if self.startingPosition is not None:
            if self.startingPosition == self.mp.position():
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لا يمكن أن يكون موضع البداية هو نفس موضع النهاية")
            elif self.startingPosition > self.mp.position():
                guiTools.qMessageBox.MessageBox.view(self, "خطأ", "لا يمكن أن يكون موضع البداية أكبر من موضع النهاية")
            else:
                position = self.mp.position()
                self.endingPosition = position
                winsound.Beep(500, 500)
                self.repeatFromPositionToPosition = True
                self._is_seeking_loop = False
                self.mp.setPosition(self.startingPosition)
                self.time_VA()
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "يرجى تحديد موضع البداية أولا")

    def removePosition(self):
        if self.startingPosition is None and self.endingPosition is None and not self.repeatFromPositionToPosition:
            speak("لم يتم تحديد موضع بداية ونهاية")
            return
        self.startingPosition = None
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        self._is_seeking_loop = False
        winsound.Beep(300, 500)
        self.time_VA()

    def onBookmarkOpened(self):
        gui.book_marcks(self, "quran").exec()

    def onAddNewBookmark(self):
        name, ok = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب اسم العلامة المرجعية")
        if ok and name:
            type = self.recitersListWidget.currentRow()
            surah = self.surahListWidget.currentRow()
            position = self.mp.position()
            functions.bookMarksManager.addNewaudioBookMark("quran", type, surah, position, name)

    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeaudioBookMark("quran",self.nameOfBookmark)
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم الحذف")
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")
