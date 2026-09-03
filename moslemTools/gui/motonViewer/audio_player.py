import os
import winsound
import ujson as json
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import PyQt6.QtWidgets as qt
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
import custom_errors
import guiTools
from functions import audio_manager, text_actions

class MotonAudioPlayerMixin:
    def init_audio_player(self):
        self.media = QMediaPlayer(self)
        self.audioOutput = QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("moton_viewer"))
        self.media.setAudioOutput(self.audioOutput)
        self.audioOutput.setVolume(1.0)
        self.current_playing_bayt = None
        self.is_playing_continuous = False
        self.continuous_end_bayt = None
        self.current_continuous_end_ms = 0
        self.pending_continuous_seek_ms = None
        self.speed_file_path = os.path.join(os.getenv("appdata"), "moslemTools_GUI", "playback_speed.json")
        self.playback_speed = self.load_speed()
        self.media.setPlaybackRate(self.playback_speed)
        self.media.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media.positionChanged.connect(self.update_slider)
        self.media.durationChanged.connect(self.on_duration_changed)
        self.register_audio_shortcuts()

    def register_audio_shortcuts(self):
        for i in range(1, 10):
            qt1.QShortcut(qt1.QKeySequence(f"ctrl+{i}"), self).activated.connect(lambda pct=i*10: self.seek_percent(pct))
        qt1.QShortcut(qt1.QKeySequence("ctrl+0"), self).activated.connect(lambda: self.seek_percent(10))

    def load_speed(self):
        if os.path.exists(self.speed_file_path):
            try:
                with open(self.speed_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return float(data.get("motonViewerGui", 1.0))
            except:
                return 1.0
        return 1.0

    def save_speed(self, speed):
        os.makedirs(os.path.dirname(self.speed_file_path), exist_ok=True)
        data = {}
        if os.path.exists(self.speed_file_path):
            try:
                with open(self.speed_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}
        data["motonViewerGui"] = speed
        try:
            with open(self.speed_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except:
            pass

    def apply_speed(self, speed=None):
        if speed is not None:
            self.playback_speed = float(speed)
            self.save_speed(self.playback_speed)
        else:
            self.playback_speed = self.load_speed()
        self.media.setPlaybackRate(self.playback_speed)

    def increase_speed(self):
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            if s > self.playback_speed + 0.01:
                self.apply_speed(s)
                guiTools.speak(f"سرعة التشغيل {self.playback_speed}x")
                return

    def decrease_speed(self):
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in reversed(speeds):
            if s < self.playback_speed - 0.01:
                self.apply_speed(s)
                return

    def volume_up(self):
        vol = min(1.0, self.audioOutput.volume() + 0.05)
        self.audioOutput.setVolume(vol)
        guiTools.speak(f"مستوى الصوت {int(vol * 100)}%")

    def volume_down(self):
        vol = max(0.0, self.audioOutput.volume() - 0.05)
        self.audioOutput.setVolume(vol)
        guiTools.speak(f"مستوى الصوت {int(vol * 100)}%")

    def seek_percent(self, percent):
        if self.media.playbackState() != QMediaPlayer.PlaybackState.StoppedState and self.media.duration() > 0:
            pos = int(self.media.duration() * (percent / 100.0))
            self.media.setPosition(pos)
            guiTools.speak(f"{percent}%")

    def stop_audio(self):
        self.media.stop()
        self.is_playing_continuous = False
        self.continuous_end_bayt = None
        self.current_playing_bayt = None
        self.is_user_paused = False
        self.saved_pause_position = 0
        self._last_playback_pos = 0
        self.media_progress.setVisible(False)
        self.time_label.setVisible(False)

    def on_play(self):
        now = qt2.QDateTime.currentMSecsSinceEpoch()
        if hasattr(self, '_last_toggle_time') and now - self._last_toggle_time < 200:
            return
        self._last_toggle_time = now

        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return

        target_global_num = bayt["global_num"]

        if getattr(self, "is_user_paused", False) and (self.current_playing_bayt == target_global_num):
            self.is_user_paused = False
            resume_pos = getattr(self, "saved_pause_position", 0)
            if resume_pos > 0:
                self.media.setPosition(resume_pos)
            self.media.play()
            return

        if (self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState) and (self.current_playing_bayt == target_global_num):
            self.is_user_paused = True
            pos = self.media.position()
            self.saved_pause_position = pos if pos > 0 else getattr(self, '_last_playback_pos', 0)
            self.media.pause()
            return

        self.is_user_paused = False
        self.saved_pause_position = 0
        self._last_playback_pos = 0
        self.media.stop()
        self.play_bayt(target_global_num)

    def play_bayt(self, global_bayt_num):
        if self.current_reciter_type == "Y":
            self.play_bayt_continuous_mode(global_bayt_num)
        else:
            self.play_bayt_split_mode(global_bayt_num)

    def play_bayt_split_mode(self, global_bayt_num):
        audio_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, self.matn_slug, f"{global_bayt_num}.mp3"))
        if not os.path.exists(audio_path):
            winsound.Beep(440, 200)
            guiTools.speak("ملف الصوت غير متوفر محليا")
            return
        self.current_playing_bayt = global_bayt_num
        self.media_progress.setVisible(True)
        self.time_label.setVisible(True)
        url = qt2.QUrl.fromLocalFile(audio_path)
        if self.media.source() != url:
            self.media.setSource(url)
        qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.media.play()))
        self.highlight_playing_bayt(global_bayt_num)

    def play_bayt_continuous_mode(self, global_bayt_num):
        audio_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, f"{self.matn_slug}.mp3"))
        if not os.path.exists(audio_path):
            winsound.Beep(440, 200)
            guiTools.speak("ملف الصوت غير متوفر محليا")
            return
        dur_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, "Durations", f"{self.matn_slug}.txt"))
        timestamps = []
        if os.path.exists(dur_path):
            with open(dur_path, "r", encoding="utf-8") as f:
                timestamps = [int(line.strip()) for line in f if line.strip().isdigit()]

        start_ms = 0
        end_ms = 0
        has_intro_offset = (len(timestamps) == self.total_verses + 1)
        if has_intro_offset:
            if 1 <= global_bayt_num <= len(timestamps):
                start_ms = timestamps[global_bayt_num - 1]
                end_ms = timestamps[global_bayt_num] if global_bayt_num < len(timestamps) else 0
        else:
            if global_bayt_num == 1:
                start_ms = 0
                end_ms = timestamps[0] if len(timestamps) > 0 else 0
            elif 1 < global_bayt_num <= len(timestamps) + 1:
                start_ms = timestamps[global_bayt_num - 2] if len(timestamps) >= global_bayt_num - 1 else 0
                end_ms = timestamps[global_bayt_num - 1] if len(timestamps) >= global_bayt_num else 0

        self.current_playing_bayt = global_bayt_num
        self.current_continuous_end_ms = end_ms
        self.media_progress.setVisible(True)
        self.time_label.setVisible(True)
        curr_src = self.media.source().toLocalFile()
        target_url = qt2.QUrl.fromLocalFile(audio_path)
        if os.path.normpath(curr_src) != os.path.normpath(audio_path):
            self.pending_continuous_seek_ms = start_ms
            self.media.setSource(target_url)
        else:
            self.pending_continuous_seek_ms = None
            self.media.setPosition(start_ms)
            self.apply_speed()
            self.media.play()
        self.highlight_playing_bayt(global_bayt_num)

    def playFromBaytToEnd(self):
        if hasattr(self, '_is_invalid_search_line') and self._is_invalid_search_line():
            self.handle_invalid_line_action()
            return
        b = self.get_bayt_at_cursor()
        if not b:
            self.handle_invalid_line_action()
            return
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.stop()
        start_idx = self.getCurrentBaytIndex()
        verses_to_play = self.displayed_verses[start_idx:]
        if not verses_to_play:
            return
        from ..motonPlayer import MotonPlayer
        player = MotonPlayer(
            self,
            matn_name=self.matn_name,
            matn_slug=self.matn_slug,
            parsed_sections=None,
            start_bayt=1,
            current_reciter_slug=self.current_reciter_slug,
            current_reciter_type=self.current_reciter_type,
            verses=verses_to_play
        )
        player.exec()

    def playFromVersToVers(self):
        if hasattr(self, 'is_search_view') and self.is_search_view:
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        b = self.get_bayt_at_cursor()
        if not b or not self.displayed_verses:
            self.handle_invalid_line_action()
            return
        use_matn_num = (self.verse_numbering_mode == "by_matn")
        if use_matn_num:
            min_val = self.displayed_verses[0]["global_num"]
            max_val = self.displayed_verses[-1]["global_num"]
            current_val = b["global_num"]
        else:
            min_val = 1
            max_val = len(self.displayed_verses)
            current_val = b.get("chapter_bayt_num", self.getCurrentBaytIndex() + 1) if not self.is_full_matn else (self.getCurrentBaytIndex() + 1)

        self.pause_for_action()
        from_bayt, ok = guiTools.QInputDialog.getInt(self, "التشغيل من البيت", "التشغيل من:", current_val, min_val, max_val)
        if ok:
            to_bayt, ok2 = guiTools.QInputDialog.getInt(self, "التشغيل إلى البيت", "التشغيل إلى:", max_val, from_bayt, max_val)
            if ok2:
                if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.media.stop()
                if use_matn_num:
                    verses_to_play = [v for v in self.displayed_verses if from_bayt <= v.get("global_num", 0) <= to_bayt]
                else:
                    if not self.is_full_matn:
                        verses_to_play = [v for v in self.displayed_verses if from_bayt <= v.get("chapter_bayt_num", 0) <= to_bayt]
                    else:
                        verses_to_play = self.displayed_verses[from_bayt - 1: to_bayt]
                if verses_to_play:
                    from ..motonPlayer import MotonPlayer
                    player = MotonPlayer(
                        self,
                        matn_name=self.matn_name,
                        matn_slug=self.matn_slug,
                        parsed_sections=None,
                        start_bayt=1,
                        current_reciter_slug=self.current_reciter_slug,
                        current_reciter_type=self.current_reciter_type,
                        verses=verses_to_play
                    )
                    player.exec()
        self.resume_after_action()

    def on_media_status_changed(self, status):
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if getattr(self, "pending_continuous_seek_ms", None) is not None:
                seek_ms = self.pending_continuous_seek_ms
                self.pending_continuous_seek_ms = None
                self.media.setPosition(seek_ms)
                self.apply_speed()
                self.media.play()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_progress.setVisible(False)
            self.time_label.setVisible(False)
            self.current_playing_bayt = None
            self.is_user_paused = False
            self.saved_pause_position = 0
            self._last_playback_pos = 0

    def update_slider(self, position):
        if position > 0:
            self._last_playback_pos = position
        if self.media.duration() > 0:
            self.media_progress.blockSignals(True)
            pct = int((position / self.media.duration()) * 100)
            self.media_progress.setValue(pct)
            self.media_progress.blockSignals(False)
        self.update_time_label(position, self.media.duration())
        if not self.is_playing_continuous and self.current_reciter_type == "Y" and self.current_continuous_end_ms > 0:
            if position >= self.current_continuous_end_ms:
                self.media.stop()

    def on_duration_changed(self, duration):
        self.update_time_label(self.media.position(), duration)

    def set_position_from_slider(self, value):
        if self.media.duration() > 0:
            target_pos = int((value / 100.0) * self.media.duration())
            self.media.setPosition(target_pos)

    def update_time_label(self, current_ms, total_ms):
        position_str = text_actions.format_arabic_time(current_ms)
        duration_str = text_actions.format_arabic_time(total_ms)
        remaining_str = text_actions.format_arabic_time(max(0, total_ms - current_ms))
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة البيت: {duration_str}")
