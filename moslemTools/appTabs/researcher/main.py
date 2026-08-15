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
from .context_menu import ResearcherContextMenuMixin
from .actions_and_dialogs import ResearcherActionsMixin
from .search_engine import ResearcherSearchEngineMixin
from .audio_player import ResearcherAudioMixin
from .shortcuts_ui import ResearcherShortcutsUIMixin


class Albaheth(ResearcherContextMenuMixin, ResearcherActionsMixin, ResearcherSearchEngineMixin, ResearcherAudioMixin, ResearcherShortcutsUIMixin, qt.QWidget):
    def __init__(self):
        super().__init__()
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.quran_data = functions.quranJsonControl.data
        self.search_metadata = {}
        self.currentReciter = int(settings.settings_handler.get("g", "reciter"))
        self.media_player = QMediaPlayer(self)
        self.apply_speed()
        self.audio_output = QAudioOutput(self)
        self.audio_output.setDevice(functions.audio_manager.get_audio_device("researcher"))
        self.media_player.setAudioOutput(self.audio_output)
        self.was_playing_before_action = False
        self.current_search_thread = None
        self.remaining_thread = None
        self.is_saving = False
        self.cancellation_requested = False
        self.setStyleSheet("""QPushButton {background-color: #007bff; color: white; border: none; border-radius: 6px; padding: 10px 15px; min-height: 40px; font-weight: bold; outline: none; } QPushButton:hover { background-color: #0056b3; } QPushButton:pressed { background-color: #003d80; } QPushButton#searchModeButton { background-color: #0056b3; } QPushButton#searchModeButton:hover { background-color: #003d80; } QPushButton#searchModeButton:pressed { background-color: #003d80; } QPushButton#startButton { background-color: #28a745; } QPushButton#startButton:hover { background-color: #218838; } QPushButton#startButton:pressed { background-color: #218838; } QPushButton#applySearchModeChangesButton { background-color: #28a745; } QPushButton#applySearchModeChangesButton:hover { background-color: #218838; } QPushButton#applySearchModeChangesButton:pressed { background-color: #218838; } QPushButton#cancelButton { background-color: #dc3545; } QPushButton#cancelButton:hover { background-color: #c82333; } QPushButton#cancelButton:pressed { background-color: #bd2130; } QPushButton#clearResultsButton { background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 10px 15px; min-height: 40px; font-weight: bold; outline: none; } QPushButton#clearResultsButton:hover { background-color: #c82333; } QPushButton#clearResultsButton:pressed { background-color: #bd2130; } QPushButton#clearResultsButton:disabled { background-color: #6c757d; color: #d3d3d3; } """)
        self.init_ui()
        self.create_shortcuts()
        self.media_player.mediaStatusChanged.connect(self.on_media_state_changed)
        self.media_player.durationChanged.connect(self.update_slider_and_time)
        self.media_player.positionChanged.connect(self.update_slider_and_time)
