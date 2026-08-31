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


class PlayerAudioControlsMixin:
    def play(self):
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.paused_position = self.mp.position()
            self.mp.pause()
        else:
            if getattr(self, 'paused_position', None) is not None:
                self.mp.setPosition(self.paused_position)
                self.paused_position = None
            self.mp.play()

    def stop_audio_completely(self):
        self.paused_position = None
        self.mp.stop()
        self.mp.setSource(qt2.QUrl())
        self.startingPosition = None
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        self._is_seeking_loop = False
        self.Slider.blockSignals(True)
        self.Slider.setValue(0)
        self.Slider.blockSignals(False)
        if not self.volume_timer.isActive():
            self.duration.setText("0 ثانية")
        speak("تم إيقاف المقطع")

    def restore_duration_text(self):
        self.time_VA()

    def skip_forward_5s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = min(self.mp.duration(), current_pos + 5000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("تقديم 5 ثواني")

    def skip_backward_5s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = max(0, current_pos - 5000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("ترجيع 5 ثواني")

    def skip_forward_10s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = min(self.mp.duration(), current_pos + 10000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("تقديم 10 ثواني")

    def skip_backward_10s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = max(0, current_pos - 10000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("ترجيع 10 ثواني")

    def skip_forward_30s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = min(self.mp.duration(), current_pos + 30000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("تقديم 30 ثانية")

    def skip_backward_30s(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = max(0, current_pos - 30000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("ترجيع 30 ثانية")

    def skip_forward_1m(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = min(self.mp.duration(), current_pos + 60000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("تقديم دقيقة واحدة")

    def skip_backward_1m(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        current_pos = self.paused_position if (self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        new_position = max(0, current_pos - 60000)
        self.mp.setPosition(new_position)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_position
        speak("ترجيع دقيقة واحدة")

    def t10(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.1)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t20(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.2)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t30(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.3)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t40(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.4)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t50(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.5)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t60(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.6)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t70(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.7)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t80(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.8)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def t90(self):
        if self.mp.duration() == 0:
            speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.mp.duration()
        new_pos = int(total_duration * 0.9)
        self.mp.setPosition(new_pos)
        if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.paused_position = new_pos

    def increase_volume(self):
        current_volume = self.au.volume()
        new_volume = min(current_volume + 0.10, 1.0)
        self.au.setVolume(new_volume)
        volume_percent = int(new_volume * 100)
        speak(f"نسبة الصوت {volume_percent}")
        self.duration.setText(f"نسبة الصوت: {volume_percent}%")
        self.volume_timer.start(1000)

    def decrease_volume(self):
        current_volume = self.au.volume()
        new_volume = max(current_volume - 0.10, 0.0)
        self.au.setVolume(new_volume)
        volume_percent = int(new_volume * 100)
        speak(f"نسبة الصوت {volume_percent}")
        self.duration.setText(f"نسبة الصوت: {volume_percent}%")
        self.volume_timer.start(1000)

    def increase_speed(self):
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        current_speed = self.load_speed()
        idx = min(range(len(speeds)), key=lambda i: abs(speeds[i] - current_speed))
        new_idx = min(idx + 1, len(speeds) - 1)
        new_speed = speeds[new_idx]
        self.change_speed(new_speed)
        speak(f"السرعة {new_speed}")
        self.duration.setText(f"السرعة: {new_speed}")
        self.volume_timer.start(1000)

    def decrease_speed(self):
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        current_speed = self.load_speed()
        idx = min(range(len(speeds)), key=lambda i: abs(speeds[i] - current_speed))
        new_idx = max(idx - 1, 0)
        new_speed = speeds[new_idx]
        self.change_speed(new_speed)
        speak(f"السرعة {new_speed}")
        self.duration.setText(f"السرعة: {new_speed}")
        self.volume_timer.start(1000)

    def set_position_from_slider(self, value):
        duration = self.mp.duration()
        if duration > 0:
            new_position = int((value / 100) * duration)
            self.mp.setPosition(new_position)
            if self.mp.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.paused_position = new_position

    def update_slider(self):
        if self.isAMustToGoToBookmark and self.mp.position() >= 3000:
            self.isAMustToGoToBookmark = False
            self.mp.setPosition(self.bookmarksPosition)
        if self.repeatFromPositionToPosition and self.startingPosition is not None and self.endingPosition is not None:
            if self.mp.position() >= self.endingPosition:
                if not getattr(self, '_is_seeking_loop', False):
                    self._is_seeking_loop = True
                    self.mp.setPosition(self.startingPosition)
                    if self.mp.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                        self.mp.play()
            elif self.mp.position() < self.endingPosition:
                self._is_seeking_loop = False
        if self.mp.duration() > 0:
            try:
                self.Slider.blockSignals(True)
                position_ratio = self.mp.position() / self.mp.duration()
                self.Slider.setValue(int(position_ratio * 100))
                self.Slider.blockSignals(False)
                self.time_VA()
            except ZeroDivisionError:
                self.Slider.setValue(0)
                if not self.volume_timer.isActive():
                    self.duration.setText("0 ثانية")
        else:
            self.Slider.setValue(0)
            if not self.volume_timer.isActive():
                self.duration.setText("0 ثانية")

    def time_VA(self):
        if self.volume_timer.isActive():
            return
        position = self.mp.position()
        duration = self.mp.duration()
        remaining = max(0, duration - position)
        position_str = functions.text_actions.format_arabic_time(position)
        remaining_str = functions.text_actions.format_arabic_time(remaining)
        if self.startingPosition is not None and self.endingPosition is not None:
            start_sec = self.startingPosition // 1000
            start_m = start_sec // 60
            start_s = start_sec % 60
            end_sec = self.endingPosition // 1000
            end_m = end_sec // 60
            end_s = end_sec % 60
            info_text = f"يتم التشغيل من الدقيقة {start_m} والثانية {start_s} إلى الدقيقة {end_m} والثانية {end_s}"
        else:
            duration_str = functions.text_actions.format_arabic_time(duration)
            info_text = f"الوقت المنقضي: {position_str}، الوقت المتبقي: {remaining_str}، مدة المقطع: {duration_str}"
        self.duration.setText(info_text)

    def load_speed(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("quranPlayerTab", 1.0)
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
            data["quranPlayerTab"] = speed
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Handled exception: {e}")

    def change_speed(self, speed):
        is_playing = self.mp.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        pos = self.paused_position if (not is_playing and getattr(self, 'paused_position', None) is not None) else self.mp.position()
        if is_playing:
            self.mp.pause()
        self.save_speed(speed)
        self.mp.setPlaybackRate(speed)
        if hasattr(self.mp, 'setPitchCompensation'):
            self.mp.setPitchCompensation(True)
        if self.mp.duration() > 0 and pos > 0:
            self.mp.setPosition(pos)
        if is_playing:
            self.mp.play()
            self.paused_position = None
        else:
            if pos > 0:
                self.paused_position = pos

    def apply_speed(self):
        speed = self.load_speed()
        self.mp.setPlaybackRate(speed)
        if hasattr(self.mp, 'setPitchCompensation'):
            self.mp.setPitchCompensation(True)
