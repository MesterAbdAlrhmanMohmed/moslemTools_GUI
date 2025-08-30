import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from .after_azaan import AfterAdaan
import settings
class AdaanDialog(qt.QDialog):
    def __init__(self, p, index: int, title: str, sound_path: str):  # أضفنا sound_path كمعلمة
        super().__init__(p)
        self.resize(500, 600)
        self.setWindowTitle(title)
        self.lay = qt.QLabel(title)
        self.lay.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.lay.setStyleSheet("font-size:100px;")        
        self.media_player = QMediaPlayer()
        self.media_player.mediaStatusChanged.connect(self.onStateChanged)
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(int(settings.settings_handler.get("prayerTimes", "volume")) / 100)
        self.media_player.setAudioOutput(self.audio_output)                
        self.media_player.setSource(qt2.QUrl.fromLocalFile(sound_path))
        self.media_player.play()        
        qt1.QShortcut("escape", self).activated.connect(lambda: self.closeEvent(None))
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.lay)    
    def closeEvent(self, event):
        self.media_player.stop()
        self.accept()    
    def onStateChanged(self, state):
        if state == self.media_player.MediaStatus.EndOfMedia:            
            self.accept()            
            if settings.settings_handler.get("prayerTimes", "playPrayerAfterAdhaan") == "True":
                window = AfterAdaan(self)
                window.exec()