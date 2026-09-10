import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name


class brotcasts_of_translations(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_translations = qt.QListWidget()
        self.list_of_translations.setSpacing(3)
        self.list_of_translations.setStyleSheet(style_sheet)
        self.list_of_translations.itemActivated.connect(self.play)
        self.list_of_translations.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_translations.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_translations.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الأسبانية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الألبانية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الألمانية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الأمازيغية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الأوردية - السديس والشريم")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الأوردية - المنشاوي")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الأوردية - عبدالباسط عبدالصمد")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الإنجليزية - عبدالباسط عبدالصمد")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الإنجليزية - عبدالله بصفر")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الإنجليزية -ترجمة والك")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة البرتغالية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة البوسنية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة التركية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الروسية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الصينية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الفارسية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الفرنسية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الكردية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الكورية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة المجرية")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة الهوسا")
        self.list_of_translations.addItem("ترجمة معاني القرآن باللغة اليونانية")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_translations)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_translations)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_translations)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_translations.itemAt(pos)
        if not item:
            item = self.list_of_translations.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_translations.currentItem()
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
