import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name


class brotcasts_of_reciters(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_reciters = qt.QListWidget()
        self.list_of_reciters.setSpacing(3)
        self.list_of_reciters.setStyleSheet(style_sheet)
        self.list_of_reciters.itemActivated.connect(self.play)
        self.list_of_reciters.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_reciters.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_reciters.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_reciters.addItem("إذاعة القُراء")
        self.list_of_reciters.addItem("القارء أبو بكر الشاطري")
        self.list_of_reciters.addItem("القارئ إدريس أبكر")
        self.list_of_reciters.addItem("القارئ سعود الشريم")
        self.list_of_reciters.addItem("القارئ صلاح البدير")
        self.list_of_reciters.addItem("القارئ عبد الباسط عبد الصمد")
        self.list_of_reciters.addItem("القارئ عبد الرحمن السديس")
        self.list_of_reciters.addItem("القارئ ماهر المعيقلي")
        self.list_of_reciters.addItem("القارئ محمود خليل الحُصَري")
        self.list_of_reciters.addItem("القارئ محمود خليل الحُصَري القرآن بالتحقيق")
        self.list_of_reciters.addItem("القارئ محمود علي البنا القرآن بالتحقيق")
        self.list_of_reciters.addItem("مشاري راشد")
        self.list_of_reciters.addItem("القارئ مصطفى رعد العزاوي")
        self.list_of_reciters.addItem("القارئ مصطفى اللاهونِي")
        self.list_of_reciters.addItem("القارئ يحيى حوا")
        self.list_of_reciters.addItem("القارئ يوسف بن نوح")
        self.list_of_reciters.addItem("القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع")
        self.list_of_reciters.addItem("القارئ طارق دعوب- رواية قالون عن نافع")
        self.list_of_reciters.addItem("القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع")
        self.list_of_reciters.addItem("القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني")
        self.list_of_reciters.addItem("القارئ\xa0 محمد عبد الحكيم قِراءة ابن كثير")
        self.list_of_reciters.addItem("القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر")
        self.list_of_reciters.addItem("القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ عبد الرشيد صوفي- رواية خلف عن حمزة")
        self.list_of_reciters.addItem("القارئ محمود الشيمي- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ ياسر المزروعي قِراءة يعقوب")
        self.list_of_reciters.addItem("القارئ الشيخ العيون الكوشي - ورش عن نافع")
        self.list_of_reciters.addItem("القارِء الشيخ سعد الغامدي")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_reciters)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_reciters)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_reciters)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_reciters.itemAt(pos)
        if not item:
            item = self.list_of_reciters.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_reciters.currentItem()
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
