import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from .after_azaan import AfterAdaan
from functions import audio_manager
import settings


class AdaanDialog(qt.QDialog):
    _instance = None
    _after_azaan_instance = None

    def __init__(self, p, index: int, title: str, sound_path: str):
        super().__init__(None)
        AdaanDialog._instance = self
        self.setWindowFlags(qt2.Qt.WindowType.Window | qt2.Qt.WindowType.WindowMinimizeButtonHint | qt2.Qt.WindowType.WindowCloseButtonHint)
        self.setWindowModality(qt2.Qt.WindowModality.NonModal)
        self.resize(500, 600)
        self.setWindowTitle(title)
        self.lay = qt.QLabel(title)
        self.lay.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.lay.setStyleSheet("font-size:100px;")
        self.media_player = QMediaPlayer()
        self.media_player.mediaStatusChanged.connect(self.onStateChanged)
        self.audio_output = QAudioOutput()
        self.audio_output.setDevice(audio_manager.get_audio_device("adhan"))
        self.audio_output.setVolume(int(settings.settings_handler.get("prayerTimes", "volume")) / 100)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(qt2.QUrl.fromLocalFile(sound_path))
        self.media_player.play()
        qt1.QShortcut("escape", self).activated.connect(self.close)
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.lay)

    def exec(self):
        self.show()
        self.raise_()
        self.activateWindow()
        return 1

    def closeEvent(self, event):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        self.accept()
        AdaanDialog._instance = None
        if event:
            event.accept()

    def onStateChanged(self, state):
        if state == self.media_player.MediaStatus.EndOfMedia:
            self.close()
            AdaanDialog._instance = None
            if settings.settings_handler.get("prayerTimes", "playPrayerAfterAdhaan") == "True":
                window = AfterAdaan(None)
                window.setWindowModality(qt2.Qt.WindowModality.NonModal)
                AdaanDialog._after_azaan_instance = window
                window.destroyed.connect(lambda: setattr(AdaanDialog, '_after_azaan_instance', None))
                window.show()
                window.raise_()
                window.activateWindow()
