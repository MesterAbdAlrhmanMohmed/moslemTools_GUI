import os
import ujson as json
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import PyQt6.QtWidgets as qt
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
import custom_errors
import guiTools
from settings import settings_handler
from functions import audio_manager, text_actions
from functions.moton_data import get_moton_bayt_audio_url, get_moton_continuous_audio_url

class MotonPlayerAudioMixin:
    def init_audio(self):
        self.media = QMediaPlayer(self)
        self.audioOutput = QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("moton_player"))
        self.media.setAudioOutput(self.audioOutput)
        self.audioOutput.setVolume(1.0)
        self.speed_file_path = os.path.join(os.getenv("appdata"), "moslemTools_GUI", "playback_speed.json")
        self.playback_speed = self.load_speed()
        self.media.setPlaybackRate(self.playback_speed)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.media.positionChanged.connect(self.update_slider)
        self.media.durationChanged.connect(self.duration_changed)
        self.times = int(settings_handler.get("motonPlayer", "times") or 1)
        self.currentTime = 1
        self.is_closing = False
        self.is_custom_seeking = False
        self.current_continuous_end_ms = 0
        self.pending_continuous_seek_ms = None
        self.was_playing_before_action = False
        self.register_audio_shortcuts()

    def pause_for_action(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
            self.PPS.setText("تشغيل")
        else:
            self.was_playing_before_action = False

    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
            self.was_playing_before_action = False

    def register_audio_shortcuts(self):
        qt1.QShortcut(qt1.QKeySequence("Ctrl+S"), self).activated.connect(self.stop_audio)
        for i in range(1, 10):
            qt1.QShortcut(qt1.QKeySequence(f"ctrl+{i}"), self).activated.connect(lambda pct=i*10: self.seek_percent(pct))
        qt1.QShortcut(qt1.QKeySequence("ctrl+0"), self).activated.connect(lambda: self.seek_percent(10))

    def load_speed(self):
        if os.path.exists(self.speed_file_path):
            try:
                with open(self.speed_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return float(data.get("motonPlayerGui", 1.0))
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
        data["motonPlayerGui"] = speed
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
                guiTools.speak(f"سرعة التشغيل {self.playback_speed}x")
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
        self.is_closing = True
        self.is_user_paused = False
        self.saved_pause_position = 0
        self._last_playback_pos = 0
        self.media.stop()
        self.media.setSource(qt2.QUrl())
        self.audioOutput.setVolume(0.0)
        self.currentTime = 1
        self.PPS.setText("تشغيل")

    def on_play(self):
        if getattr(self, "is_closing", False):
            return
        if not (0 <= self.current_index < self.total_verses):
            return

        now = qt2.QDateTime.currentMSecsSinceEpoch()
        if hasattr(self, '_last_toggle_time') and now - self._last_toggle_time < 200:
            return
        self._last_toggle_time = now

        if getattr(self, "is_user_paused", False):
            self.is_user_paused = False
            resume_pos = getattr(self, "saved_pause_position", 0)
            if resume_pos > 0:
                self.media.setPosition(resume_pos)
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
            return

        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.is_user_paused = True
            pos = self.media.position()
            self.saved_pause_position = pos if pos > 0 else getattr(self, '_last_playback_pos', 0)
            self.media.pause()
            self.PPS.setText("تشغيل")
            return

        self.is_user_paused = False
        self.saved_pause_position = 0
        self._last_playback_pos = 0
        self.audioOutput.setVolume(1.0)
        bayt = self.all_verses_list[self.current_index]
        self.current_bayt_num = bayt.get("global_num", self.current_index + 1)
        global_bayt_num = self.current_bayt_num

        is_continuous = (self.current_reciter_type == "Y")
        if is_continuous:
            url = get_moton_continuous_audio_url(self.current_reciter_slug, self.matn_slug)
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
            self.current_continuous_end_ms = end_ms
            if self.media.source() != url:
                self.pending_continuous_seek_ms = start_ms
                self.media.setSource(url)
            else:
                self.pending_continuous_seek_ms = None
                self.media.setPosition(start_ms)
                self.PPS.setText("إيقاف مؤقت")
                qt2.QTimer.singleShot(80, lambda: (self.apply_speed(self.playback_speed), self.media.play()))
        else:
            url = get_moton_bayt_audio_url(self.current_reciter_slug, self.matn_slug, global_bayt_num)
            if self.media.source() != url:
                self.media.setSource(url)
            self.PPS.setText("إيقاف مؤقت")
            qt2.QTimer.singleShot(80, lambda: (self.apply_speed(self.playback_speed), self.media.play()))

    def on_state(self, state):
        if getattr(self, "is_closing", False):
            return
        if state in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if getattr(self, "pending_continuous_seek_ms", None) is not None:
                seek_ms = self.pending_continuous_seek_ms
                self.pending_continuous_seek_ms = None
                self.media.setPosition(seek_ms)
                self.PPS.setText("إيقاف مؤقت")
                qt2.QTimer.singleShot(80, lambda: (self.apply_speed(self.playback_speed), self.media.play()))
        elif state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.is_user_paused = False
            self.saved_pause_position = 0
            self._last_playback_pos = 0
            dur_val = settings_handler.get("motonPlayer", "duration")
            duration_ms = int(dur_val if (dur_val and str(dur_val).isdigit()) else 0) * 1000
            max_times = int(settings_handler.get("motonPlayer", "times") or 1)
            if self.currentTime == max_times:
                if settings_handler.get("motonPlayer", "replay") == "False":
                    if not self.current_index + 1 == self.total_verses:
                        qt2.QTimer.singleShot(duration_ms, qt2.Qt.TimerType.PreciseTimer, self.onNextBayt)
                    else:
                        self.PPS.setText("تشغيل")
                        self.current_index = 0
                        self.update_display_text()
                else:
                    qt2.QTimer.singleShot(duration_ms, qt2.Qt.TimerType.PreciseTimer, self.onNextBayt)
            else:
                self.currentTime += 1
                qt2.QTimer.singleShot(duration_ms, qt2.Qt.TimerType.PreciseTimer, self.media.play)

    def update_slider(self, position):
        if position > 0:
            self._last_playback_pos = position
        if not self.is_custom_seeking and self.media.duration() > 0:
            self.media_progress.blockSignals(True)
            pct = int((position / self.media.duration()) * 100)
            self.media_progress.setValue(pct)
            self.media_progress.blockSignals(False)
        self.update_time_label(position, self.media.duration())
        if self.current_reciter_type == "Y" and self.current_continuous_end_ms > 0:
            if position >= self.current_continuous_end_ms:
                self.media.stop()
                self.on_state(QMediaPlayer.MediaStatus.EndOfMedia)

    def duration_changed(self, duration):
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
