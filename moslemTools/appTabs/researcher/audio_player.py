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


class ResearcherAudioMixin:
    def start_playback(self, metadata):
        with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
            reciters = json.load(file)
        reciter_url = list(reciters.values())[self.currentReciter]
        reciter_folder = reciter_url.split('/')[-3]
        surah_num_str = str(metadata["surah_number"]).zfill(3)
        ayah_num_str = str(metadata["ayah_number_in_surah"]).zfill(3)
        filename = f"{surah_num_str}{ayah_num_str}.mp3"
        local_path = os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciter_folder,filename)
        if os.path.exists(local_path):
            path = qt2.QUrl.fromLocalFile(local_path)
        else:
            path = qt2.QUrl(reciter_url + filename)
        self.media_player.setSource(path)
        self.player_widget.setVisible(True)
        qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.media_player.play()))

    def handle_play_toggle(self, selected_metadata):
        current_media_src = self.media_player.source().fileName().split('/')[-1]
        expected_filename = f'{str(selected_metadata["surah_number"]).zfill(3)}{str(selected_metadata["ayah_number_in_surah"]).zfill(3)}.mp3'
        is_playing_this_verse = self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState and current_media_src == expected_filename
        if is_playing_this_verse:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            elif self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.media_player.play()
        else:
            self.start_playback(selected_metadata)

    def on_media_state_changed(self, state):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player_widget.setVisible(False)

    def update_slider_and_time(self):
        self.media_progress.blockSignals(True)
        position = self.media_player.position()
        duration = self.media_player.duration()
        if duration > 0:
            progress_value = int((position * 100) / duration)
            self.media_progress.setValue(progress_value)
            position_str = functions.text_actions.format_arabic_time(position)
            duration_str = functions.text_actions.format_arabic_time(duration)
            remaining_str = functions.text_actions.format_arabic_time(max(0, duration - position))
            self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")
        self.media_progress.blockSignals(False)

    def set_media_position(self, value):
        duration = self.media_player.duration()
        if duration > 0:
            new_position = int((value / 100) * duration)
            self.media_player.setPosition(new_position)
            guiTools.speak(f"{value}%")

    def pause_for_action(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media_player.pause()
        else:
            self.was_playing_before_action = False

    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media_player.play()

    def t10(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.1))

    def t20(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.2))

    def t30(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.3))

    def t40(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.4))

    def t50(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.5))

    def t60(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.6))

    def t70(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.7))

    def t80(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.8))

    def t90(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.9))

    def on_spacebar_pressed(self):
        if self.results.hasFocus():
            cursor = self.results.textCursor()
            line_number = cursor.blockNumber() + 1
            selected_metadata = self.search_metadata.get(line_number)
            if selected_metadata and selected_metadata.get("type") != "hadith":
                self.handle_play_toggle(selected_metadata)

    def load_speed(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("researcherTab", 1.0)
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
            data["researcherTab"] = speed
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Handled exception: {e}")

    def change_speed(self, speed):
        self.save_speed(speed)
        self.media_player.setPlaybackRate(speed)
        if hasattr(self.media_player, 'setPitchCompensation'):
            self.media_player.setPitchCompensation(True)

    def apply_speed(self):
        speed = self.load_speed()
        self.media_player.setPlaybackRate(speed)
        if hasattr(self.media_player, 'setPitchCompensation'):
            self.media_player.setPitchCompensation(True)

    def on_change_reciter_requested(self):
        self.pause_for_action()
        with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
            reciters = json.load(file)
        reciter_list = list(reciters.keys())
        dlg = ChangeReciter(self, reciter_list, self.currentReciter)
        if dlg.exec() == qt.QDialog.DialogCode.Accepted:
            self.currentReciter = dlg.recitersListWidget.currentRow()
        self.resume_after_action()
