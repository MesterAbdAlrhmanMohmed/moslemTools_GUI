from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
import time,os,requests,subprocess,shutil,re,traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, SaveThread

with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)


class PlayerAudioMixin:
    def seek_position(self, new_position):
        is_playing = self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if is_playing:
            self.media.pause()
            self.pending_seek_resume = True
        self.media.setPosition(new_position)
        if is_playing:
            qt2.QTimer.singleShot(150, self._check_seek_resume)

    def _check_seek_resume(self):
        if getattr(self, 'pending_seek_resume', False):
            if hasattr(self, 'media_progress') and self.media_progress.isSliderDown():
                qt2.QTimer.singleShot(150, self._check_seek_resume)
                return
            if self.media.mediaStatus() in (QMediaPlayer.MediaStatus.BufferedMedia, QMediaPlayer.MediaStatus.LoadedMedia):
                self.pending_seek_resume = False
                self.media.play()
            elif self.media.mediaStatus() in (QMediaPlayer.MediaStatus.BufferingMedia, QMediaPlayer.MediaStatus.LoadingMedia, QMediaPlayer.MediaStatus.StalledMedia):
                qt2.QTimer.singleShot(200, self._check_seek_resume)

    def t10(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.1))

    def t20(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.2))

    def t30(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.3))

    def t40(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.4))

    def t50(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.5))

    def t60(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.6))

    def t70(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.7))

    def t80(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.8))

    def t90(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.seek_position(int(total_duration * 0.9))

    def show_volume_feedback(self, volume):
        vol_percent = int(round(volume * 100))
        guiTools.speak(f"{vol_percent}%")

    def volume_up(self):
        volume = round(self.audioOutput.volume(), 2)
        new_volume = min(1.0, round(volume + 0.10, 2))
        self.audioOutput.setVolume(new_volume)
        self.save_volume(new_volume)
        self.show_volume_feedback(new_volume)

    def volume_down(self):
        volume = round(self.audioOutput.volume(), 2)
        new_volume = max(0.0, round(volume - 0.10, 2))
        self.audioOutput.setVolume(new_volume)
        self.save_volume(new_volume)
        self.show_volume_feedback(new_volume)

    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.seek_position(new_position)
        guiTools.speak(f"{value}%")

    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            position, duration = self.media.position(), self.media.duration()
            if duration > 0:
                self.media_progress.setValue(int((position / duration) * 100))
                self.update_time_label(position, duration)
            self.media_progress.blockSignals(False)
        except: pass

    def update_time_label(self, position, duration):
        position_str = functions.text_actions.format_arabic_time(position)
        duration_str = functions.text_actions.format_arabic_time(duration)
        remaining_str = functions.text_actions.format_arabic_time(max(0, duration - position))
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")

    def on_state(self, state):
        if getattr(self, 'pending_seek_resume', False):
            if hasattr(self, 'media_progress') and self.media_progress.isSliderDown():
                return
            if state in (QMediaPlayer.MediaStatus.BufferedMedia, QMediaPlayer.MediaStatus.LoadedMedia):
                self.pending_seek_resume = False
                self.media.play()
        elif state == QMediaPlayer.MediaStatus.InvalidMedia:
            if not self.media.source().isLocalFile():
                self.media.stop()
                self.PPS.setText("تشغيل")
                if not getattr(self, '_showing_network_error', False):
                    self._showing_network_error = True
                    guiTools.MessageBox.error(self, "خطأ", "لا يوجد اتصال بالإنترنت")
                    self._showing_network_error = False
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            dur_val = settings.settings_handler.get("quranPlayer","duration")
            duration_ms = int(dur_val if (dur_val and str(dur_val).isdigit()) else 0) * 1000
            if self.times==self.currentTime:
                if settings.settings_handler.get("quranPlayer","replay")=="False":
                    if not self.index+1==len(self.quranText): qt2.QTimer.singleShot(duration_ms,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
                    else:
                        self.PPS.setText("تشغيل")
                        self.index=0
                        self.original_ayah_text = self.quranText[self.index]
                        self.update_display_text()
                else: qt2.QTimer.singleShot(duration_ms,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
            else:
                self.currentTime+=1
                qt2.QTimer.singleShot(duration_ms,qt2.Qt.TimerType.PreciseTimer,self.media.play)

    def on_media_error(self, error=None, error_string=""):
        if not self.media.source().isLocalFile():
            self.media.stop()
            self.PPS.setText("تشغيل")
            if not getattr(self, '_showing_network_error', False):
                self._showing_network_error = True
                guiTools.MessageBox.error(self, "خطأ", "لا يوجد اتصال بالإنترنت")
                self._showing_network_error = False

    def on_play(self):
        if not self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            reciter_folder = reciters[self.getCurrentReciter()].split("/")[-3]
            filename = self.on_set()
            local_path = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder, filename)
            if os.path.exists(local_path):
                path = qt2.QUrl.fromLocalFile(local_path)
            else:
                if not guiTools.check_internet():
                    self.media.stop()
                    self.PPS.setText("تشغيل")
                    guiTools.MessageBox.error(self, "خطأ", "لا يوجد اتصال بالإنترنت")
                    return
                path = qt2.QUrl(reciters[self.getCurrentReciter()] + filename)
            if not self.media.source() == path:
                self.media.setSource(path)
            self.PPS.setText("إيقاف مؤقت")
            qt2.QTimer.singleShot(80, lambda: (self.apply_speed(), self.media.play()))
        else:
            self.pending_seek_resume = False
            self.media.pause()
            self.PPS.setText("تشغيل")

    def resume_playback(self):
        if hasattr(self, 'was_playing') and self.was_playing and not self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState and not self.is_merging:
            if not self.media.source().isLocalFile() and not guiTools.check_internet():
                self.media.stop()
                self.PPS.setText("تشغيل")
                guiTools.MessageBox.error(self, "خطأ", "لا يوجد اتصال بالإنترنت")
                return
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")

    def load_speed(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "playback_speed.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("quranPlayerGui", 1.0)
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
            data["quranPlayerGui"] = speed
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Handled exception: {e}")

    def change_speed(self, speed):
        is_playing = self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        pos = self.media.position()
        if is_playing:
            self.media.pause()
        self.save_speed(speed)
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)
        if self.media.duration() > 0 and pos > 0:
            self.media.setPosition(pos)
        if is_playing:
            self.media.play()

    def apply_speed(self):
        speed = self.load_speed()
        self.media.setPlaybackRate(speed)
        if hasattr(self.media, 'setPitchCompensation'):
            self.media.setPitchCompensation(True)

    def load_volume(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "volume.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("quranPlayerGui", 1.0)
        except Exception as e:
            print(f"Handled exception: {e}")
        return 1.0

    def save_volume(self, volume):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "volume.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Handled exception: {e}")
            data["quranPlayerGui"] = round(volume, 2)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Handled exception: {e}")

    def set_volume_dialog(self):
        current_volume_percent = int(round(self.audioOutput.volume() * 100))
        vol, ok = guiTools.QInputDialog.getInt(self, "تحديد مستوى الصوت", "أدخل مستوى الصوت من 0 إلى 100:", current_volume_percent, 0, 100)
        if ok:
            new_volume = vol / 100.0
            self.audioOutput.setVolume(new_volume)
            self.save_volume(new_volume)
