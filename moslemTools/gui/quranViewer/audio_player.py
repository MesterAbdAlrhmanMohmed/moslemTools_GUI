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


class AudioPlayerMixin:
    def t10(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.1))

    def t20(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.2))

    def t30(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.3))

    def t40(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.4))

    def t50(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.5))

    def t60(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.6))

    def t70(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.7))

    def t80(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.8))

    def t90(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.9))

    def on_play(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.media_progress.setVisible(True)
        self.time_label.setVisible(True)
        current_ayah_index = self.getCurrentAyah()
        if current_ayah_index < 0:
            return
        file_name = self.on_set(current_ayah_index)
        if not file_name:
            return
        reciter_key = self.getCurrentReciter()
        reciter_folder = reciters[reciter_key].split("/")[-3]
        local_file_path = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder, file_name)
        if os.path.exists(local_file_path):
            path = qt2.QUrl.fromLocalFile(local_file_path)
        else:
            path = qt2.QUrl(reciters[reciter_key] + file_name)
        is_playing_this_verse = (self.media.playbackState() != QMediaPlayer.PlaybackState.StoppedState) and (self.media.source() == path)
        if is_playing_this_verse:
            if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media.pause()
            elif self.media.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.media.play()
        else:
            self.media.stop()
            self.media.setSource(path)
            qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.media.play()))

    def onPlayToEnd(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        text_for_player = self.original_quran_text if not self.is_search_view else self.quranText
        QuranPlayer(self, text_for_player, self.getCurrentAyah(), self.type, self.category).exec()

    def playFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","التشغيل من",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","التشغيل إلى",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                verses=[]
                allVerses=self.original_quran_text.split("\n")
                for vers in allVerses:
                    index=allVerses.index(vers)+1
                    if index>=FromVers and index<=toVers:
                        verses.append(vers)
                self.text.setUpdatesEnabled(False)
                QuranPlayer(self,"\n".join(verses),0,self.type,self.category).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)
        guiTools.speak(f"{value}%")

    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            position = self.media.position()
            duration = self.media.duration()
            if duration > 0:
                progress_value = int((position / duration) * 100)
                self.media_progress.setValue(progress_value)
                self.update_time_label(position, duration)
            self.media_progress.blockSignals(False)
        except Exception as e:
            print(f"Handled exception: {e}")

    def update_time_label(self, position, duration):
        position_str = functions.text_actions.format_arabic_time(position)
        duration_str = functions.text_actions.format_arabic_time(duration)
        remaining_str = functions.text_actions.format_arabic_time(max(0, duration - position))
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")

    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)

    def load_speed(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("quranViewer", 1.0)
        except Exception as e:
            print(f"Handled exception: {e}")
        return 1.0

    def save_speed(self, speed):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Handled exception: {e}")
            data["quranViewer"] = speed
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Handled exception: {e}")

    def change_speed(self, speed):
        self.save_speed(speed)
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)

    def apply_speed(self):
        speed = self.load_speed()
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)
