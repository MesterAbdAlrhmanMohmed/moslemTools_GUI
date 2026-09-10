import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name, search_stations


class brotcasts_of_tafseer(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        category_name = "إذاعات التفاسير"

        font = qt1.QFont()
        font.setBold(True)
        self.search_label = qt.QLabel(f"البحث عن إذاعة في {category_name}")
        self.search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_label.setFont(font)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setFont(font)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setPlaceholderText(f"البحث عن إذاعة في {category_name}")
        self.search_bar.setAccessibleName(f"البحث عن إذاعة في {category_name}")
        self.search_bar.textChanged.connect(self.on_search)

        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_tafseer = qt.QListWidget()
        self.list_of_tafseer.setSpacing(3)
        self.list_of_tafseer.setStyleSheet(style_sheet)
        self.list_of_tafseer.itemActivated.connect(self.play)
        self.list_of_tafseer.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_tafseer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_tafseer.customContextMenuRequested.connect(self.on_context_menu)

        self.all_stations = [
            "تفسير النابلسي",
            "تفسير الشعراوي",
            "الله أكبر لتفسير الشعراوي",
            "المختصر في التفسير",
            "إذاعة التفسير",
            "علوم القرآن الكريم",
            "إذاعة تفسير القرآن الكريم",
            "المختصر في تفسير القرآن الكريم",
            "تفسير القران الكريم-الخلاصة من تفسير الطبري",
            "تفسير غريب القرآن",
        ]
        self.list_of_tafseer.addItems(self.all_stations)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_of_tafseer)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_tafseer)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_tafseer)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_search(self):
        search_text = self.search_bar.text().lower()
        self.list_of_tafseer.clear()
        results = search_stations(search_text, self.all_stations)
        self.list_of_tafseer.addItems(results)
        if hasattr(self.parent_widget, 'view_mode_combo') and self.parent_widget.view_mode_combo.currentIndex() == 1:
            self.parent_widget.update_grid_size_for_widget(self.list_of_tafseer)

    def on_context_menu(self, pos):
        if hasattr(self.parent_widget, 'open_station_context_menu'):
            self.parent_widget.open_station_context_menu(self.list_of_tafseer, pos)

    def play(self):
        selected_item = self.list_of_tafseer.currentItem()
        if not selected_item: return
        play_station_by_name(selected_item.text())

    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            if hasattr(self.parent_widget, 'save_volume'):
                self.parent_widget.save_volume(new_volume)
            volume_percent = int(round(new_volume * 100))
            if hasattr(self.parent_widget, 'update_aud_status_text'):
                self.parent_widget.update_aud_status_text(volume_percent)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(3000)

    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            if hasattr(self.parent_widget, 'save_volume'):
                self.parent_widget.save_volume(new_volume)
            volume_percent = int(round(new_volume * 100))
            if hasattr(self.parent_widget, 'update_aud_status_text'):
                self.parent_widget.update_aud_status_text(volume_percent)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(3000)
