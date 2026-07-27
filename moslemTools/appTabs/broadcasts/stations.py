import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QMediaPlayer
from guiTools import speak

global_player = None
global_audio_output = None
global_current_url = None


def get_global_player():
    return global_player


def get_global_audio_output():
    return global_audio_output


def get_global_current_url():
    return global_current_url


def set_globals(player, output, url):
    global global_player, global_audio_output, global_current_url
    global_player = player
    global_audio_output = output
    global_current_url = url


ALL_STATIONS = {
    # Quran broadcasts
    "إذاعة القرآن الكريم من نابلِس": "http://www.quran-radio.org:8002/;stream.mp3",
    "إذاعة القرآن الكريم من القاهرة": "http://n0e.radiojar.com/8s5u5tpdtwzuv?rj-ttl=5&rj-tok=AAABeel-l8gApvlPoJcG2WWz8A",
    "إذاعة القرآن الكريم من السعودية": "https://stream.radiojar.com/4wqre23fytzuv",
    "إذاعة دُبَيْ للقرآن الكريم": "http://uk5.internet-radio.com:8079/stream",
    "تلاوات خاشعة": "http://live.mp3quran.net:9992",
    "إذاعة القرآن الكريم من أستراليا": "http://listen.qkradio.com.au:8382/listen.mp3",
    "إذاعة طيبة للقرآن الكريم من السودان": "http://live.mp3quran.net:9960",
    "إذاعة القرآن الكريم من مصر": "http://66.45.232.131:9994/;stream",
    "إذاعة القرآن الكريم من فَلَسطين": "http://streamer.mada.ps:8029/quranfm",
    "إذاعة تراتيل": "http://live.mp3quran.net:8030",

    # Reciters
    "إذاعة القُراء": "http://live.mp3quran.net:8006",
    "القارء أبو بكر الشاطري": "http://live.mp3quran.net:9966",
    "القارئ إدريس أبكر": "http://live.mp3quran.net:9968",
    "القارئ سعود الشريم": "http://live.mp3quran.net:9986",
    "القارئ صلاح البدير": "https://qurango.net/radio/salah_albudair",
    "القارئ عبد الباسط عبد الصمد": "http://live.mp3quran.net:9980",
    "القارئ عبد الرحمن السديس": "http://live.mp3quran.net:9988",
    "القارئ ماهر المعيقلي": "http://live.mp3quran.net:9996",
    "القارئ محمود خليل الحُصَري": "http://live.mp3quran.net:9958/;",
    "القارئ محمود خليل الحُصَري القرآن بالتحقيق": "https://Qurango.net/radio/mahmoud_khalil_alhussary_mojawwad",
    "القارئ محمود علي البنا القرآن بالتحقيق": "https://qurango.net/radio/mahmoud_ali__albanna_mojawwad",
    "مشاري راشد": "http://live.mp3quran.net:9982",
    "القارئ مصطفى رعد العزاوي": "https://Qurango.net/radio/mustafa_raad_alazawy",
    "القارئ مصطفى اللاهونِي": "http://live.mp3quran.net:9798",
    "القارئ يحيى حوا": "https://Qurango.net/radio/yahya_hawwa",
    "القارئ يوسف بن نوح": "https://Qurango.net/radio/yousef_bin_noah_ahmad",
    "القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع": "https://Qurango.net/radio/ahmad_khader_altarabulsi",
    "القارئ طارق دعوب- رواية قالون عن نافع": "https://qurango.net/radio/tareq_abdulgani_daawob",
    "القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع": "http://live.mp3quran.net:9956",
    "القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني": "https://qurango.net/radio/mohammad_abdullkarem_alasbahani",
    "القارئ\xa0 محمد عبد الحكيم قِراءة ابن كثير": "https://Qurango.net/radio/mohammad_alabdullah_albizi",
    "القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو": "https://Qurango.net/radio/alfateh_alzubair",
    "القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو": "https://Qurango.net/radio/muftah_alsaltany_aldori_an_abi_amr",
    "القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر": "https://qurango.net/radio/muftah_alsaltany_ibn_thakwan_an_ibn_amr",
    "القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي": "https://Qurango.net/radio/mohammad_alabdullah_aldorai",
    "القارئ عبد الرشيد صوفي- رواية خلف عن حمزة": "https://Qurango.net/radio/abdulrasheed_soufi_khalaf",
    "القارئ محمود الشيمي- رواية الدُوري عن الكِسائي": "https://Qurango.net/radio/mahmood_alsheimy",
    "القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي": "https://Qurango.net/radio/muftah_alsaltany_aldorai",
    "القارئ ياسر المزروعي قِراءة يعقوب": "https://Qurango.net/radio/yasser_almazroyee",
    "القارئ الشيخ العيون الكوشي - ورش عن نافع": "http://live.mp3quran.net:9912/;",
    "القارِء الشيخ سعد الغامدي": "https://qurango.net/radio/saad_alghamdi",

    # Tafseer
    "تفسير النابلسي": "http://206.72.199.179:9992/;stream.mp3",
    "تفسير الشعراوي": "http://206.72.199.180:9990/;",
    "الله أكبر لتفسير الشعراوي": "http://66.45.232.132:9996/;stream.mp3",
    "المختصر في التفسير": "http://live.mp3quran.net:9698",
    "إذاعة التفسير": "http://live.mp3quran.net:9718",

    # Suplications / Athkar
    "أذكار الصباح": "https://qurango.net/radio/athkar_sabah",
    "أذكار المساء": "https://qurango.net/radio/athkar_masa",
    "أدعية وأذكار يومية": "https://radio.alukah.net/adiyyaha",

    # Other broadcasts
    "تَكْبِيرَات العيد": "http://live.mp3quran.net:9728",
    "الرقية الشرعية": "http://live.mp3quran.net:9936",
    "إذاعة الصحابة": "http://s5.voscast.com:10130/;stream1603343063302/1",
    "فتاوى إبن باز": "https://qurango.net/radio/alaikhtiarat_alfiqhayh_bin_baz",
    "صور من حياة الصحابة": "http://live.mp3quran.net:8028",
    "إذاعة عمر عبد الكافي": "http://node-28.zeno.fm/66geh5zntp8uv?zs=u1rolhJRRS-k08Aw1jvY8Q&rj-tok=AAABgNAugTEAylkfGQGe4UQM-w&rj-ttl=5",
    "السُنَّة السلفية": "http://andromeda.shoutca.st:8189/live",
    "في ظِلال السيرة النبوية": "https://Qurango.net/radio/fi_zilal_alsiyra",
    "فتاوى ابن العُثيمين": "http://live.mp3quran.net:8014",
    "العاصمة أونلاين": "https://asima.out.airtime.pro/asima_a",
    "الإحسان": "https://cdn.bmstudiopk.com/alehsaan/live/playlist.m3u8",
    "الإستقامى": "https://jmc-live.ercdn.net/alistiqama/alistiqama.m3u8",
    "الفتح": "https://alfat7-q.com:5443/LiveApp/streams/986613792230697141226562.m3u8",
    "المرأة المسلمة": "https://radio.alukah.net/almarah",
    "اللغة العربية وعلومها": "https://radio.alukah.net/arabiyyah",
    "المهارات الحياتية والعلوم التربوية": "https://radio.alukah.net/maharat",
    "السلوك والآداب والأخلاق ومحاسن الأعمال": "https://radio.alukah.net/assuluk",
    "التوعية الاجتماعية": "https://radio.alukah.net/attawiyy",
    "الإذاعة الفقهية": "https://radio.alukah.net/fiqhiyyah",
    "الحج": "https://radio.alukah.net/hajj",
    "رمضان المبارك": "https://radio.alukah.net/ramdan",
    "التراجم والتاريخ والسير": "https://radio.alukah.net/tarajim",
    "الفكر والدعوة وثقافة الإسلامية": "https://radio.alukah.net/alfikr",
    "السيرة النبوية وقصص القرآن والأنبياء والصحابة": "https://radio.alukah.net/sirah",
    "الحديث وعلومه": "https://radio.alukah.net/hadith",
    "العقيدة والتوحيد": "https://radio.alukah.net/aqidah",
    "علوم القرآن الكريم": "https://radio.alukah.net/ulumalquran",
    "راديو كبار العلماء": "https://radio.alukah.net/ulama",
    "الدكتور سعد الحميد": "https://radio.alukah.net/humayid",
    "الدكتور خالد الجريسي": "https://radio.alukah.net/aljeraisy",
}


def play_station_by_name(station_name):
    global global_current_url, global_player
    url_str = ALL_STATIONS.get(station_name)
    if url_str:
        url_to_play = qt2.QUrl(url_str)
        if global_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState and global_current_url == url_to_play:
            global_player.stop()
            global_current_url = None
        else:
            global_player.stop()
            global_player.setSource(url_to_play)
            global_player.play()
            global_current_url = url_to_play


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


class brotcasts_of_suplications(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_adhkar = qt.QListWidget()
        self.list_of_adhkar.setSpacing(3)
        self.list_of_adhkar.setStyleSheet(style_sheet)
        self.list_of_adhkar.itemActivated.connect(self.play)
        self.list_of_adhkar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_adhkar.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_adhkar.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_adhkar.addItem("أذكار الصباح")
        self.list_of_adhkar.addItem("أذكار المساء")
        self.list_of_adhkar.addItem("أدعية وأذكار يومية")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_adhkar)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_adhkar)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_adhkar)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_adhkar.itemAt(pos)
        if not item:
            item = self.list_of_adhkar.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_adhkar.currentItem()
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


class brotcasts_of_tafseer(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_tafseer = qt.QListWidget()
        self.list_of_tafseer.setSpacing(3)
        self.list_of_tafseer.setStyleSheet(style_sheet)
        self.list_of_tafseer.itemActivated.connect(self.play)
        self.list_of_tafseer.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_tafseer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_tafseer.customContextMenuRequested.connect(self.on_context_menu)
        self.list_of_tafseer.addItem("تفسير النابلسي")
        self.list_of_tafseer.addItem("تفسير الشعراوي")
        self.list_of_tafseer.addItem("الله أكبر لتفسير الشعراوي")
        self.list_of_tafseer.addItem("المختصر في التفسير")
        self.list_of_tafseer.addItem("إذاعة التفسير")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_tafseer)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_tafseer)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_tafseer)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)

    def on_context_menu(self, pos):
        item = self.list_of_tafseer.itemAt(pos)
        if not item:
            item = self.list_of_tafseer.currentItem()
        if item:
            self.parent_widget.toggle_station_favorite(item.text())

    def play(self):
        selected_item = self.list_of_tafseer.currentItem()
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
