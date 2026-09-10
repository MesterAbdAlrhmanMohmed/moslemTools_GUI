import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from guiTools import speak
from .utils import play_station_by_name, search_stations


class brotcasts_of_reciters(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        category_name = "إذاعات القراء"

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
        self.list_of_reciters = qt.QListWidget()
        self.list_of_reciters.setSpacing(3)
        self.list_of_reciters.setStyleSheet(style_sheet)
        self.list_of_reciters.itemActivated.connect(self.play)
        self.list_of_reciters.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_reciters.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_reciters.customContextMenuRequested.connect(self.on_context_menu)

        self.all_stations = [
            "إذاعة القُراء",
            "القارء أبو بكر الشاطري",
            "القارئ إدريس أبكر",
            "القارئ سعود الشريم",
            "القارئ صلاح البدير",
            "القارئ عبد الباسط عبد الصمد",
            "القارئ عبد الرحمن السديس",
            "القارئ ماهر المعيقلي",
            "القارئ محمود خليل الحُصَري",
            "القارئ محمود خليل الحُصَري القرآن بالتحقيق",
            "القارئ محمود علي البنا القرآن بالتحقيق",
            "مشاري راشد",
            "القارئ مصطفى رعد العزاوي",
            "القارئ مصطفى اللاهونِي",
            "القارئ يحيى حوا",
            "القارئ يوسف بن نوح",
            "القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع",
            "القارئ طارق دعوب- رواية قالون عن نافع",
            "القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع",
            "القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني",
            "القارئ\xa0 محمد عبد الحكيم قِراءة ابن كثير",
            "القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو",
            "القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو",
            "القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر",
            "القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي",
            "القارئ عبد الرشيد صوفي- رواية خلف عن حمزة",
            "القارئ محمود الشيمي- رواية الدُوري عن الكِسائي",
            "القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي",
            "القارئ ياسر المزروعي قِراءة يعقوب",
            "القارئ الشيخ العيون الكوشي - ورش عن نافع",
            "إذاعة أحمد الطرابلسي",
            "إذاعة أحمد عامر",
            "إذاعة ابراهيم الدوسري",
            "إذاعة الدوكالي محمد العالم",
            "إذاعة جمعان العصيمي",
            "إذاعة خالد المهنا",
            "إذاعة عادل الكلباني",
            "إذاعة عبدالرحمن الماجد",
            "إذاعة عبدالله الكندري",
            "إذاعة علي جابر",
            "إذاعة علي حجاج السويسي",
            "إذاعة عماد زهير حافظ",
            "إذاعة عمر القزابري",
            "إذاعة فارس عباد",
            "إذاعة ماهر المعيقلي",
            "إذاعة ماهر شخاشيرو",
            "إذاعة محمد أيوب",
            "إذاعة محمد الطبلاوي",
            "إذاعة محمد اللحيدان",
            "إذاعة محمد جبريل",
            "إذاعة محمد رشاد الشريف",
            "إذاعة محمد صالح عالم شاه",
            "إذاعة محمد صديق المنشاوي - المرتل",
            "إذاعة محمد صديق المنشاوي - المجود",
            "إذاعة محمد عبدالكريم",
            "إذاعة محمود الرفاعي",
            "إذاعة محمود خليل الحصري - المرتل",
            "إذاعة محمود خليل الحصري - رواية ورش عن نافع",
            "إذاعة محمود علي البنا - المرتل",
            "إذاعة مشاري العفاسي",
            "إذاعة مصطفى إسماعيل",
            "إذاعة مصطفى اللاهوني",
            "إذاعة معيض الحارثي",
            "إذاعة موسى بلال",
            "إذاعة ناصر القطامي",
            "إذاعة نبيل الرفاعي",
            "إذاعة نعمة الحسان",
            "إذاعة هاني الرفاعي",
            "إذاعة وليد النائحي",
            "إذاعة ياسر الدوسري",
            "إذاعة ياسر القرشي",
            "إذاعة يوسف الشويعي",
            "إذاعة أحمد الحواشي",
            "إذاعة أحمد العجمي",
            "إذاعة أحمد خليل شاهين",
            "إذاعة أحمد ديبان",
            "إذاعة أحمد صابر",
            "إذاعة أحمد نعينع",
            "إذاعة أكرم العلاقمي",
            "إذاعة إبراهيم الأخضر",
            "إذاعة إدريس أبكر",
            "إذاعة الزين محمد أحمد",
            "إذاعة العيون الكوشي",
            "إذاعة الفتاوى العامة",
            "إذاعة القارئ ياسين",
            "إذاعة بندر بليلة",
            "إذاعة توفيق الصايغ",
            "إذاعة جمال شاكر عبدالله",
            "إذاعة خالد الجليل",
            "إذاعة خالد القحطاني",
            "إذاعة خالد عبدالكافي",
            "إذاعة خليفة الطنيجي",
            "إذاعة زكي داغستاني",
            "إذاعة سعود الشريم",
            "إذاعة سهل ياسين",
            "إذاعة سيد رمضان",
            "إذاعة شيخ أبو بكر الشاطري",
            "إذاعة شيرزاد عبدالرحمن طاهر",
            "إذاعة صابر عبدالحكم",
            "إذاعة صلاح الهاشم",
            "إذاعة صلاح بو خاطر",
            "إذاعة عادل ريان",
            "إذاعة عبدالبارئ الثبيتي",
            "إذاعة عبدالبارئ محمد",
            "إذاعة عبدالباسط عبدالصمد - المجود",
            "إذاعة عبدالباسط عبدالصمد - رواية ورش عن نافع",
            "إذاعة عبدالباسط عبدالصمد - المرتل",
            "إذاعة عبدالرحمن السديس",
            "إذاعة عبدالرحمن الشحات",
            "إذاعة عبدالرشيد صوفي - رواية السوسي عن أبي عمرو",
            "إذاعة عبدالعزيز الأحمد",
            "إذاعة عبدالله الخلف",
            "إذاعة عبدالله المطرود",
            "إذاعة عبدالله الموسى",
            "إذاعة عبدالله بصفر",
            "إذاعة عبدالله خياط",
            "إذاعة عبدالله عواد الجهني",
            "إذاعة عبدالمحسن الحارثي",
            "إذاعة عبدالمحسن العبيكان",
            "إذاعة عبدالمحسن القاسم",
            "إذاعة عبدالهادي أحمد كناكري",
            "إذاعة عبدالودود حنيف",
            "إذاعة علي الحذيفي",
            "إذاعة علي بن عبدالرحمن الحذيفي",
            "إذاعة ماجد الزامل",
            "إذاعة محمد أيوب - قراءة مميزة",
            "إذاعة محمد الأمين قنيوة",
            "إذاعة محمد عثمان خان",
            "إذاعة ناصر العصفور",
            "إذاعة ناصر الماجد",
            "إذاعة نداء الإسلام - مكة المكرمة",
            "إذاعة هيثم الجدعاني",
            "أحمد طالب بن حميد",
            "إذاعة محمد أبوسنينة",
            "بدر التركي",
            "حاتم فريد الواعر",
            "صالح الهبدان",
            "عبدالعزيز سحيم",
            "عبدالله البعيجان",
            "هزاع البلوشي",
        ]
        self.list_of_reciters.addItems(self.all_stations)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_of_reciters)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_reciters)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_reciters)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_search(self):
        search_text = self.search_bar.text().lower()
        self.list_of_reciters.clear()
        results = search_stations(search_text, self.all_stations)
        self.list_of_reciters.addItems(results)
        if hasattr(self.parent_widget, 'view_mode_combo') and self.parent_widget.view_mode_combo.currentIndex() == 1:
            self.parent_widget.update_grid_size_for_widget(self.list_of_reciters)

    def on_context_menu(self, pos):
        if hasattr(self.parent_widget, 'open_station_context_menu'):
            self.parent_widget.open_station_context_menu(self.list_of_reciters, pos)

    def play(self):
        selected_item = self.list_of_reciters.currentItem()
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
