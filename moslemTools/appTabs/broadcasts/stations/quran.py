import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name


class quran_brotcast(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_quran_brotcasts = qt.QListWidget()
        self.list_of_quran_brotcasts.setSpacing(3)
        self.list_of_quran_brotcasts.setStyleSheet(style_sheet)
        self.list_of_quran_brotcasts.itemActivated.connect(self.play)
        self.list_of_quran_brotcasts.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_quran_brotcasts.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_quran_brotcasts.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من نابلِس")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من القاهرة")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من السعودية")
        self.list_of_quran_brotcasts.addItem("إذاعة دُبَيْ للقرآن الكريم")
        self.list_of_quran_brotcasts.addItem("تلاوات خاشعة")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من أستراليا")
        self.list_of_quran_brotcasts.addItem("إذاعة طيبة للقرآن الكريم من السودان")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من مصر")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من فَلَسطين")
        self.list_of_quran_brotcasts.addItem("إذاعة تراتيل")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_quran_brotcasts)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_quran_brotcasts)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_quran_brotcasts)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_quran_brotcasts.itemAt(pos)
        if not item:
            item = self.list_of_quran_brotcasts.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_quran_brotcasts.currentItem()
        if not selected_item: return
        play_station_by_name(selected_item.text())

    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)

    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
