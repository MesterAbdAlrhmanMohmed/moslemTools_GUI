import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name


class other_brotcasts(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_other = qt.QListWidget()
        self.list_of_other.setSpacing(3)
        self.list_of_other.setStyleSheet(style_sheet)
        self.list_of_other.itemActivated.connect(self.play)
        self.list_of_other.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_other.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_other.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_other.addItem("تَكْبِيرَات العيد")
        self.list_of_other.addItem("الرقية الشرعية")
        self.list_of_other.addItem("إذاعة الصحابة")
        self.list_of_other.addItem("فتاوى إبن باز")
        self.list_of_other.addItem("صور من حياة الصحابة")
        self.list_of_other.addItem("إذاعة عمر عبد الكافي")
        self.list_of_other.addItem("السُنَّة السلفية")
        self.list_of_other.addItem("في ظِلال السيرة النبوية")
        self.list_of_other.addItem("فتاوى ابن العُثيمين")
        self.list_of_other.addItem("العاصمة أونلاين")
        self.list_of_other.addItem("الإحسان")
        self.list_of_other.addItem("الإستقامى")
        self.list_of_other.addItem("الفتح")
        self.list_of_other.addItem("المرأة المسلمة")
        self.list_of_other.addItem("اللغة العربية وعلومها")
        self.list_of_other.addItem("المهارات الحياتية والعلوم التربوية")
        self.list_of_other.addItem("السلوك والآداب والأخلاق ومحاسن الأعمال")
        self.list_of_other.addItem("التوعية الاجتماعية")
        self.list_of_other.addItem("الإذاعة الفقهية")
        self.list_of_other.addItem("الحج")
        self.list_of_other.addItem("رمضان المبارك")
        self.list_of_other.addItem("التراجم والتاريخ والسير")
        self.list_of_other.addItem("الفكر والدعوة وثقافة الإسلامية")
        self.list_of_other.addItem("السيرة النبوية وقصص القرآن والأنبياء والصحابة")
        self.list_of_other.addItem("الحديث وعلومه")
        self.list_of_other.addItem("العقيدة والتوحيد")
        self.list_of_other.addItem("علوم القرآن الكريم")
        self.list_of_other.addItem("راديو كبار العلماء")
        self.list_of_other.addItem("الدكتور سعد الحميد")
        self.list_of_other.addItem("الدكتور خالد الجريسي")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_other)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_other)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_other)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_other.itemAt(pos)
        if not item:
            item = self.list_of_other.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_other.currentItem()
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
