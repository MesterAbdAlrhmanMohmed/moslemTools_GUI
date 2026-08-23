import sys
import os
import random
import ujson as json
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QMediaPlayer
from settings import settings_handler, formatDuration
from functions import audio_manager
import guiTools


class AthkarMixin:
    def play_random_basmala(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        self.audio_output.setDevice(audio_manager.get_audio_device("random_athkar"))
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.abspath(os.path.join(base_dir, "data", "sounds", "basmala"))
        if not os.path.exists(folder_path): return
        sound_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if sound_files:
            chosen_file = random.choice(sound_files)
            file_path = os.path.abspath(os.path.join(folder_path, chosen_file))
            self.media_player.setSource(qt2.QUrl.fromLocalFile(file_path))
            self.media_player.play()

    def play_startup_athkar(self):
        if settings_handler.get("athkar", "playAtStartup") == "True":
            self.random_audio_theker()
        elif settings_handler.get("athkar", "playBasmalaAtStartup") == "True":
            self.play_random_basmala()

    def show_random_theker(self):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", "json", "text_athkar.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_theckr = random.choice(data)
        if settings_handler.get("athkar", "text_type") == "1":
            guiTools.MessageBox.view(self, "ذكر عشوائي", random_theckr)
        else:
            guiTools.SendNotification("ذكر عشوائي", random_theckr)

    def notification_random_thecker(self):
        self.TIMER1.stop()
        duration = formatDuration("athkar", "text")
        if duration != 0:
            self.TIMER1.start(duration)

    def runAudioThkarTimer(self):
        self.timer.stop()
        if formatDuration("athkar", "voice") != 0:
            self.timer.start(formatDuration("athkar", "voice"))

    def random_audio_theker(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
            return
        self.audio_output.setDevice(audio_manager.get_audio_device("random_athkar"))
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.abspath(os.path.join(base_dir, "data", "sounds", "athkar"))
        if not os.path.exists(folder_path): return
        sound_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if sound_files:
            chosen_file = random.choice(sound_files)
            file_path = os.path.abspath(os.path.join(folder_path, chosen_file))
            self.media_player.setSource(qt2.QUrl.fromLocalFile(file_path))
            self.media_player.play()
