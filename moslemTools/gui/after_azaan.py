import PyQt6.QtGui as qt1
from PyQt6 import QtWidgets as qt
from PyQt6 import QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
class AfterAdaan(qt.QDialog):
    def __init__(self,p):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.resize(1200,600)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.setWindowTitle("دعاء بعد الأذان")
        self.media_player=QMediaPlayer()        
        self.audio_output=QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(qt2.QUrl.fromLocalFile("data/sounds/prayAfterAdaan.m4a"))
        self.media_player.play()
        self.suplication=qt.QTextEdit()
        self.suplication.setReadOnly(True)                        
        self.suplication.setTextInteractionFlags(qt2.Qt.TextInteractionFlag.TextSelectableByMouse|qt2.Qt.TextInteractionFlag.TextSelectableByKeyboard)        
        self.suplication.setLineWrapMode(qt.QTextEdit.LineWrapMode.NoWrap)
        self.suplication.setAcceptRichText(True)
        self.suplication.setAccessibleName("دعاء بعد الأذان")
        self.suplication.setText("اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ القَائِمَةِ، آتِ مُحَمَّدًا الوَسِيلَةَ وَالفَضِيلَةَ، وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ\nيُستحب إضافة: إِنَّكَ لَا تُخْلِفُ المِيعَادَ.\n\nثواب الدعاء بعد الأذان\nقال رسول الله صل الله عليه وسلم: مَنْ قَالَ حِينَ يَسْمَعُ النِّدَاءَ: اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ القَائِمَةِ، آتِ مُحَمَّدًا الوَسِيلَةَ وَالفَضِيلَةَ، وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ؛ حَلَّتْ لَهُ شَفَاعَتِي يَوْمَ القِيَامَةِ\nرواه البخاري في صحيحه.")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.suplication)        
        qt1.QShortcut("escape",self).activated.connect(self.closewindow)
    def closewindow(self):
        self.media_player.stop()
        self.accept()