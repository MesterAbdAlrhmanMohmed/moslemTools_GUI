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
        self._is_closing = False
        self._closed = False
        self._open_after_azaan = False

        self.setWindowFlags(qt2.Qt.WindowType.Window | qt2.Qt.WindowType.WindowMinimizeButtonHint | qt2.Qt.WindowType.WindowCloseButtonHint)
        self.setWindowModality(qt2.Qt.WindowModality.NonModal)
        self.resize(500, 600)
        self.setWindowTitle(title)
        self.lay = qt.QLabel(title)
        self.lay.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.lay.setStyleSheet("font-size:100px;")
        self.media_player = QMediaPlayer(self)
        self.media_player.mediaStatusChanged.connect(self.onStateChanged)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setDevice(audio_manager.get_audio_device("adhan"))
        self.audio_output.setVolume(int(settings.settings_handler.get("prayerTimes", "volume")) / 100)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(qt2.QUrl.fromLocalFile(sound_path))
        self.media_player.play()
        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(lambda: self.safe_close(open_after_azaan=False))
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.lay)

    def exec(self):
        self.show()
        self.raise_()
        self.activateWindow()
        return 1

    def keyPressEvent(self, event):
        if event.key() == qt2.Qt.Key.Key_Escape:
            self.safe_close(open_after_azaan=False)
            event.accept()
            return
        super().keyPressEvent(event)

    def reject(self):
        self.safe_close(open_after_azaan=False)

    def safe_close(self, open_after_azaan=False):
        if getattr(self, '_is_closing', False):
            return
        self._is_closing = True
        self._open_after_azaan = open_after_azaan

        try:
            self.media_player.mediaStatusChanged.disconnect()
        except Exception:
            pass

        try:
            if hasattr(self, 'audio_output') and self.audio_output:
                self.audio_output.setVolume(0.0)
        except Exception:
            pass

        try:
            if hasattr(self, 'media_player') and self.media_player:
                if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                    self.media_player.stop()
                self.media_player.setSource(qt2.QUrl())
        except Exception:
            pass

        self.hide()
        qt2.QTimer.singleShot(100, self._finalize_close)

    def _finalize_close(self):
        self._closed = True
        AdaanDialog._instance = None
        self.close()

        if getattr(self, '_open_after_azaan', False):
            if settings.settings_handler.get("prayerTimes", "playPrayerAfterAdhaan") == "True":
                window = AfterAdaan(None)
                window.setWindowModality(qt2.Qt.WindowModality.NonModal)
                AdaanDialog._after_azaan_instance = window
                window.destroyed.connect(lambda: setattr(AdaanDialog, '_after_azaan_instance', None))
                window.show()
                window.raise_()
                window.activateWindow()

    def closeEvent(self, event):
        if getattr(self, '_closed', False):
            AdaanDialog._instance = None
            if event:
                event.accept()
            return

        if event:
            event.ignore()
        self.safe_close(open_after_azaan=False)

    def onStateChanged(self, state):
        if state == self.media_player.MediaStatus.EndOfMedia:
            self.safe_close(open_after_azaan=True)
