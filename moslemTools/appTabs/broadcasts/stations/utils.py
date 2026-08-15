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
