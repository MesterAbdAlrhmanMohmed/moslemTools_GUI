import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
global_player = None
global_audio_output = None
global_current_url = None
class other_brotcasts(qt.QWidget):
    def __init__(self, audio_output_instance):
        super().__init__()
        self.audio_output = audio_output_instance
        style_sheet = "QListWidget::item { font-weight: bold; }"
        self.list_of_other = qt.QListWidget()
        self.list_of_other.setSpacing(1)
        self.list_of_other.setStyleSheet(style_sheet)
        self.list_of_other.itemActivated.connect(self.play)        
        self.list_of_other.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
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
        self.list_of_other.addItem("الفكر والدعوة والثقافة الإسلامية")
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
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_other.currentItem()
        if not selected_item:
            return
        station_name = selected_item.text()
        url_to_play = None        
        if station_name == "تَكْبِيرَات العيد":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9728")
        elif station_name == "الرقية الشرعية":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9936")
        elif station_name == "إذاعة الصحابة":
            url_to_play = qt2.QUrl("http://s5.voscast.com:10130/;stream1603343063302/1")
        elif station_name == "فتاوى إبن باز":
            url_to_play = qt2.QUrl("https://qurango.net/radio/alaikhtiarat_alfiqhayh_bin_baz")
        elif station_name == "صور من حياة الصحابة":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:8028")
        elif station_name == "إذاعة عمر عبد الكافي":
            url_to_play = qt2.QUrl("http://node-28.zeno.fm/66geh5zntp8uv?zs=u1rolhJRRS-k08Aw1jvY8Q&rj-tok=AAABgNAugTEAylkfGQGe4UQM-w&rj-ttl=5")
        elif station_name == "السُنَّة السلفية":
            url_to_play = qt2.QUrl("http://andromeda.shoutca.st:8189/live")
        elif station_name == "في ظِلال السيرة النبوية":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/fi_zilal_alsiyra")
        elif station_name == "فتاوى ابن العُثيمين":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:8014")
        elif station_name == "العاصمة أونلاين":
            url_to_play = qt2.QUrl("https://asima.out.airtime.pro/asima_a")
        elif station_name == "الإحسان":
            url_to_play = qt2.QUrl("https://cdn.bmstudiopk.com/alehsaan/live/playlist.m3u8")
        elif station_name == "الإستقامى":
            url_to_play = qt2.QUrl("https://jmc-live.ercdn.net/alistiqama/alistiqama.m3u8")
        elif station_name == "الفتح":
            url_to_play = qt2.QUrl("https://alfat7-q.com:5443/LiveApp/streams/986613792230697141226562.m3u8")
        elif station_name == "المرأة المسلمة":
            url_to_play = qt2.QUrl("https://radio.alukah.net/almarah")
        elif station_name == "اللغة العربية وعلومها":
            url_to_play = qt2.QUrl("https://radio.alukah.net/arabiyyah")
        elif station_name == "المهارات الحياتية والعلوم التربوية":
            url_to_play = qt2.QUrl("https://radio.alukah.net/maharat")
        elif station_name == "السلوك والآداب والأخلاق ومحاسن الأعمال":
            url_to_play = qt2.QUrl("https://radio.alukah.net/assuluk")
        elif station_name == "التوعية الاجتماعية":
            url_to_play = qt2.QUrl("https://radio.alukah.net/attawiyy")
        elif station_name == "الإذاعة الفقهية":
            url_to_play = qt2.QUrl("https://radio.alukah.net/fiqhiyyah")
        elif station_name == "الحج":
            url_to_play = qt2.QUrl("https://radio.alukah.net/hajj")
        elif station_name == "رمضان المبارك":
            url_to_play = qt2.QUrl("https://radio.alukah.net/ramdan")
        elif station_name == "التراجم والتاريخ والسير":
            url_to_play = qt2.QUrl("https://radio.alukah.net/tarajim")
        elif station_name == "الفكر والدعوة والثقافة الإسلامية":
            url_to_play = qt2.QUrl("https://radio.alukah.net/alfikr")
        elif station_name == "السيرة النبوية وقصص القرآن والأنبياء والصحابة":
            url_to_play = qt2.QUrl("https://radio.alukah.net/sirah")
        elif station_name == "الحديث وعلومه":
            url_to_play = qt2.QUrl("https://radio.alukah.net/hadith")
        elif station_name == "العقيدة والتوحيد":
            url_to_play = qt2.QUrl("https://radio.alukah.net/aqidah")
        elif station_name == "علوم القرآن الكريم":
            url_to_play = qt2.QUrl("https://radio.alukah.net/ulumalquran")
        elif station_name == "راديو كبار العلماء":
            url_to_play = qt2.QUrl("https://radio.alukah.net/ulama")
        elif station_name == "الدكتور سعد الحميد":
            url_to_play = qt2.QUrl("https://radio.alukah.net/humayid")
        elif station_name == "الدكتور خالد الجريسي":
            url_to_play = qt2.QUrl("https://radio.alukah.net/aljeraisy")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)            
    def decrease_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)            
class brotcasts_of_suplications(qt.QWidget):
    def __init__(self, audio_output_instance):
        super().__init__()
        self.audio_output = audio_output_instance
        style_sheet = "QListWidget::item { font-weight: bold; }"
        self.list_of_adhkar = qt.QListWidget()
        self.list_of_adhkar.setSpacing(1)
        self.list_of_adhkar.setStyleSheet(style_sheet)
        self.list_of_adhkar.itemActivated.connect(self.play)
        self.list_of_adhkar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_adhkar.addItem("أذكار الصباح")
        self.list_of_adhkar.addItem("أذكار المساء")
        self.list_of_adhkar.addItem("أدعية وأذكار يومية")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_adhkar)        
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_adhkar)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_adhkar)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_adhkar.currentItem()
        if not selected_item:
            return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "اذكار الصباح":
            url_to_play = qt2.QUrl("https://qurango.net/radio/athkar_sabah")
        elif station_name == "أذكار المساء":
            url_to_play = qt2.QUrl("https://qurango.net/radio/athkar_masa")
        elif station_name == "أدعية وأذكار يومية":
            url_to_play = qt2.QUrl("https://radio.alukah.net/adiyyaha")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)            
    def decrease_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)            
class brotcasts_of_tafseer(qt.QWidget):
    def __init__(self, audio_output_instance):
        super().__init__()
        self.audio_output = audio_output_instance
        style_sheet = "QListWidget::item { font-weight: bold; }"
        self.list_of_tafseer = qt.QListWidget()
        self.list_of_tafseer.setSpacing(1)
        self.list_of_tafseer.setStyleSheet(style_sheet)
        self.list_of_tafseer.itemActivated.connect(self.play)
        self.list_of_tafseer.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
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
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_tafseer.currentItem()
        if not selected_item:
            return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "تفسير النابلسي":
            url_to_play = qt2.QUrl("http://206.72.199.179:9992/;stream.mp3")
        elif station_name == "تفسير الشعراوي":
            url_to_play = qt2.QUrl("http://206.72.199.180:9990/;")
        elif station_name == "الله أكبر لتفسير الشعراوي":
            url_to_play = qt2.QUrl("http://66.45.232.132:9996/;stream.mp3")
        elif station_name == "المختصر في التفسير":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9698")
        elif station_name == "إذاعة التفسير":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9718")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)            
    def decrease_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)            
class brotcasts_of_reciters(qt.QWidget):
    def __init__(self, audio_output_instance):
        super().__init__()
        self.audio_output = audio_output_instance
        style_sheet = "QListWidget::item { font-weight: bold; }"
        self.list_of_reciters = qt.QListWidget()
        self.list_of_reciters.setSpacing(1)
        self.list_of_reciters.setStyleSheet(style_sheet)
        self.list_of_reciters.itemActivated.connect(self.play)
        self.list_of_reciters.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
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
        self.list_of_reciters.addItem("القارئ  محمد عبد الحكيم قِراءة ابن كثير")
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
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_reciters.currentItem()
        if not selected_item:
            return
        reciter_name = selected_item.text()
        url_to_play = None        
        if reciter_name == "إذاعة القُراء":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:8006")
        elif reciter_name == "القارء أبو بكر الشاطري":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9966")
        elif reciter_name == "القارئ إدريس أبكر":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9968")
        elif reciter_name == "القارئ سعود الشريم":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9986")
        elif reciter_name == "القارئ صلاح البدير":
            url_to_play = qt2.QUrl("https://qurango.net/radio/salah_albudair")
        elif reciter_name == "القارئ عبد الباسط عبد الصمد":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9980")
        elif reciter_name == "القارئ عبد الرحمن السديس":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9988")
        elif reciter_name == "القارئ ماهر المعيقلي":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9996")
        elif reciter_name == "القارئ محمود خليل الحُصَري":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9958/;")
        elif reciter_name == "القارئ محمود خليل الحُصَري القرآن بالتحقيق":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/mahmoud_khalil_alhussary_mojawwad")
        elif reciter_name == "القارئ محمود علي البنا القرآن بالتحقيق":
            url_to_play = qt2.QUrl("https://qurango.net/radio/mahmoud_ali__albanna_mojawwad")
        elif reciter_name == "مشاري راشد":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9982")
        elif reciter_name == "القارئ مصطفى رعد العزاوي":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/mustafa_raad_alazawy")
        elif reciter_name == "القارئ مصطفى اللاهونِي":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9798")
        elif reciter_name == "القارئ يحيى حوا":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/yahya_hawwa")
        elif reciter_name == "القارئ يوسف بن نوح":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/yousef_bin_noah_ahmad")
        elif reciter_name == "القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/ahmad_khader_altarabulsi")
        elif reciter_name == "القارئ طارق دعوب- رواية قالون عن نافع":
            url_to_play = qt2.QUrl("https://qurango.net/radio/tareq_abdulgani_daawob")
        elif reciter_name == "القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9956")
        elif reciter_name == "القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني":
            url_to_play = qt2.QUrl("https://qurango.net/radio/mohammad_abdullkarem_alasbahani")
        elif reciter_name == "القارئ  محمد عبد الحكيم قِراءة ابن كثير":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/mohammad_alabdullah_albizi")
        elif reciter_name == "القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/alfateh_alzubair")
        elif reciter_name == "القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/muftah_alsaltany_aldori_an_abi_amr")
        elif reciter_name == "القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر":
            url_to_play = qt2.QUrl("https://qurango.net/radio/muftah_alsaltany_ibn_thakwan_an_ibn_amr")
        elif reciter_name == "القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/mohammad_alabdullah_aldorai")
        elif reciter_name == "القارئ عبد الرشيد صوفي- رواية خلف عن حمزة":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/abdulrasheed_soufi_khalaf")
        elif reciter_name == "القارئ محمود الشيمي- رواية الدُوري عن الكِسائي":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/mahmood_alsheimy")
        elif reciter_name == "القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/muftah_alsaltany_aldorai")
        elif reciter_name == "القارئ ياسر المزروعي قِراءة يعقوب":
            url_to_play = qt2.QUrl("https://Qurango.net/radio/yasser_almazroyee")
        elif reciter_name == "القارئ الشيخ العيون الكوشي - ورش عن نافع":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9912/;")
        elif reciter_name == "القارِء الشيخ سعد الغامدي":
            url_to_play = qt2.QUrl("https://qurango.net/radio/saad_alghamdi")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)            
    def decrease_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)            
class quran_brotcast(qt.QWidget):
    def __init__(self, audio_output_instance):
        super().__init__()
        self.audio_output = audio_output_instance
        style_sheet = "QListWidget::item { font-weight: bold; }"
        self.list_of_quran_brotcasts = qt.QListWidget()
        self.list_of_quran_brotcasts.setSpacing(1)
        self.list_of_quran_brotcasts.setStyleSheet(style_sheet)
        self.list_of_quran_brotcasts.itemActivated.connect(self.play)
        self.list_of_quran_brotcasts.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من نابلِس")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من القاهرة")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من السعودية")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من تونس")
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
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_quran_brotcasts.currentItem()
        if not selected_item:
            return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "إذاعة القرآن الكريم من نابلِس":
            url_to_play = qt2.QUrl("http://www.quran-radio.org:8002/;stream.mp3")
        elif station_name == "إذاعة القرآن الكريم من القاهرة":
            url_to_play = qt2.QUrl("http://n0e.radiojar.com/8s5u5tpdtwzuv?rj-ttl=5&rj-tok=AAABeel-l8gApvlPoJcG2WWz8A")
        elif station_name == "إذاعة القرآن الكريم من السعودية":
            url_to_play = qt2.QUrl("https://stream.radiojar.com/4wqre23fytzuv")
        elif station_name == "إذاعة القرآن الكريم من تونس":
            url_to_play = qt2.QUrl("http://5.135.194.225:8000/live")
        elif station_name == "إذاعة دُبَيْ للقرآن الكريم":
            url_to_play = qt2.QUrl("http://uk5.internet-radio.com:8079/stream")
        elif station_name == "تلاوات خاشعة":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9992")
        elif station_name == "إذاعة القرآن الكريم من أستراليا":
            url_to_play = qt2.QUrl("http://listen.qkradio.com.au:8382/listen.mp3")
        elif station_name == "إذاعة طيبة للقرآن الكريم من السودان":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:9960")
        elif station_name == "إذاعة القرآن الكريم من مصر":
            url_to_play = qt2.QUrl("http://66.45.232.131:9994/;stream")
        elif station_name == "إذاعة القرآن الكريم من فَلَسطين":
            url_to_play = qt2.QUrl("http://streamer.mada.ps:8029/quranfm")
        elif station_name == "إذاعة تراتيل":
            url_to_play = qt2.QUrl("http://live.mp3quran.net:8030")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)            
    def decrease_volume(self):        
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
class protcasts(qt.QWidget):
    def __init__(self):
        super().__init__()
        global global_player, global_audio_output, global_current_url
        global_player = QMediaPlayer()
        global_audio_output = QAudioOutput()
        global_player.setAudioOutput(global_audio_output)
        global_audio_output.setVolume(0.5)
        global_current_url = None
        self.brotcasts_tab = qt.QTabWidget()        
        self.brotcasts_tab.addTab(quran_brotcast(global_audio_output), "إذاعات القرآن الكريم")
        self.brotcasts_tab.addTab(brotcasts_of_reciters(global_audio_output), "إذاعات القراء")
        self.brotcasts_tab.addTab(brotcasts_of_tafseer(global_audio_output), "إذاعات التفاسير")
        self.brotcasts_tab.addTab(brotcasts_of_suplications(global_audio_output), "إذاعات الأذكار والأدعية")
        self.brotcasts_tab.addTab(other_brotcasts(global_audio_output), "إذاعات إسلامية أخرى")
        self.aud = qt.QLabel()
        self.aud.setText("لرفع أو خفض الصوت: اضغط في القائمة ثم استخدم Shift + الأسهم، أعلى وأسفل")
        self.aud.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.aud.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.brotcasts_tab.setStyleSheet("""
QTabWidget::pane {
    border: 1px solid #444;
    border-radius: 6px;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background: #2b2b2b;
    color: white;
    padding: 10px 20px;
    border: 1px solid #444;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin: 2px;
    min-width: 100px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #0078d7; /* الأزرق */
    color: white;
    border: 1px solid #0078d7;
}
QTabBar::tab:hover {
    background: #3a3a3a;
}
""")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.brotcasts_tab)
        layout.addWidget(self.aud)