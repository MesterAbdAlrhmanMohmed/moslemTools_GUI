import re
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QMediaPlayer
from guiTools import speak, check_internet, MessageBox

showing_network_error = False


def search_stations(pattern, text_list):
    tashkeel_pattern = re.compile(r'[\u0610-\u061A\u0640\u064B-\u065F\u0670\u06D6-\u06ED\u08C9-\u08FF]')
    p = tashkeel_pattern.sub('', pattern).replace('\u0671', '\u0627').lower()
    if not p:
        return list(text_list)
    matches = [text for text in text_list if p in tashkeel_pattern.sub('', text).replace('\u0671', '\u0627').lower()]
    if matches:
        return matches
    def norm_alef(s):
        return re.sub(r'[إأآٱ]', 'ا', s)
    p_alef = norm_alef(p)
    return [text for text in text_list if p_alef in norm_alef(tashkeel_pattern.sub('', text).lower())]


global_player = None
global_audio_output = None
global_current_url = None


def get_global_player():
    return global_player


def get_global_audio_output():
    return global_audio_output


def get_global_current_url():
    return global_current_url


def on_media_error(error, error_string=""):
    global global_player, global_current_url, showing_network_error
    if global_player:
        global_player.stop()
    global_current_url = None
    if not showing_network_error:
        showing_network_error = True
        MessageBox.error(None, "خطأ", "لا يوجد اتصال بالإنترنت")
        showing_network_error = False


def on_media_status_changed(status):
    global global_player, global_current_url, showing_network_error
    if status == QMediaPlayer.MediaStatus.InvalidMedia:
        if global_player:
            global_player.stop()
        global_current_url = None
        if not showing_network_error:
            showing_network_error = True
            MessageBox.error(None, "خطأ", "لا يوجد اتصال بالإنترنت")
            showing_network_error = False


def set_globals(player, output, url):
    global global_player, global_audio_output, global_current_url
    global_player = player
    global_audio_output = output
    global_current_url = url
    if global_player:
        try:
            global_player.errorOccurred.connect(on_media_error)
            global_player.mediaStatusChanged.connect(on_media_status_changed)
        except Exception:
            pass


ALL_STATIONS = {
    # Quran broadcasts
    "إذاعة القرآن الكريم من نابلِس": "http://www.quran-radio.org:8002/;stream.mp3",
    "إذاعة القرآن الكريم من القاهرة": "http://n0e.radiojar.com/8s5u5tpdtwzuv?rj-ttl=5&rj-tok=AAABeel-l8gApvlPoJcG2WWz8A",
    "إذاعة القرآن الكريم من السعودية": "http://stream.radiojar.com/4wqre23fytzuv",
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
    "إذاعة الصحابة": "http://s5.voscast.com:10130/;stream1603343063302/1",
    "فتاوى إبن باز": "https://qurango.net/radio/alaikhtiarat_alfiqhayh_bin_baz",
    "صور من حياة الصحابة": "http://live.mp3quran.net:8028",
    "إذاعة عمر عبد الكافي": "http://node-28.zeno.fm/66geh5zntp8uv?zs=u1rolhJRRS-k08Aw1jvY8Q&rj-tok=AAABgNAugTEAylkfGQGe4UQM-w&rj-ttl=5",
    "السُنَّة السلفية": "http://andromeda.shoutca.st:8189/live",
    "في ظِلال السيرة النبوية": "https://Qurango.net/radio/fi_zilal_alsiyra",
    "فتاوى ابن العُثيمين": "http://live.mp3quran.net:8014",
    "العاصمة أونلاين": "https://asima.out.airtime.pro/asima_a",
    "الإستقامى": "https://jmc-live.ercdn.net/alistiqama/alistiqama.m3u8",
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
    "إذاعة صور من حياة الصحابة والتابعين رضوان الله عليهم": "https://qurango.net/radio/sahabah",
    "إذاعة الرقية الشرعية": "https://qurango.net/radio/roqiah",
    "إذاعة أحمد الطرابلسي": "https://qurango.net/radio/ahmed_altrabulsi",
    "إذاعة أحمد عامر": "https://qurango.net/radio/ahmed_amer",
    "إذاعة ابراهيم الدوسري": "https://qurango.net/radio/ibrahim_aldosari",
    "إذاعة الدوكالي محمد العالم": "https://qurango.net/radio/addokali_mohammad_alalim",
    "إذاعة جمعان العصيمي": "https://qurango.net/radio/jamaan_alosaimi",
    "إذاعة خالد المهنا": "https://qurango.net/radio/khalid_almohana",
    "إذاعة عادل الكلباني": "https://qurango.net/radio/adel_alkhalbany",
    "إذاعة عبدالرحمن الماجد": "https://qurango.net/radio/abdulrahman_almajed",
    "إذاعة عبدالله الكندري": "https://qurango.net/radio/abdullah_alkandari",
    "إذاعة علي جابر": "https://qurango.net/radio/ali_jaber",
    "إذاعة علي حجاج السويسي": "https://qurango.net/radio/ali_hajjaj_alsouasi",
    "إذاعة عماد زهير حافظ": "https://qurango.net/radio/emad_hafez",
    "إذاعة عمر القزابري": "https://qurango.net/radio/omar_alqazabri",
    "إذاعة فارس عباد": "https://qurango.net/radio/fares_abbad",
    "إذاعة ماهر المعيقلي": "https://qurango.net/radio/maher",
    "إذاعة ماهر شخاشيرو": "https://qurango.net/radio/maher_shakhashero",
    "إذاعة محمد أيوب": "https://qurango.net/radio/mohammed_ayyub",
    "إذاعة محمد الطبلاوي": "https://qurango.net/radio/mohammad_altablaway",
    "إذاعة محمد اللحيدان": "https://qurango.net/radio/mohammed_allohaidan",
    "إذاعة محمد جبريل": "https://qurango.net/radio/mohammed_jibreel",
    "إذاعة محمد رشاد الشريف": "https://qurango.net/radio/mohammad_rashad_alshareef",
    "إذاعة محمد صالح عالم شاه": "https://qurango.net/radio/mohammad_saleh_alim_shah",
    "إذاعة محمد صديق المنشاوي - المرتل": "https://qurango.net/radio/mohammed_siddiq_alminshawi",
    "إذاعة محمد صديق المنشاوي - المجود": "https://qurango.net/radio/mohammed_siddiq_alminshawi_mojawwad",
    "إذاعة محمد عبدالكريم": "https://qurango.net/radio/mohammad_abdullkarem",
    "إذاعة محمود الرفاعي": "https://qurango.net/radio/mahmood_al_rifai",
    "إذاعة محمود خليل الحصري - المرتل": "https://qurango.net/radio/mahmoud_khalil_alhussary",
    "إذاعة محمود خليل الحصري - رواية ورش عن نافع": "https://qurango.net/radio/mahmoud_khalil_alhussary_warsh",
    "إذاعة محمود علي البنا - المرتل": "https://qurango.net/radio/mahmoud_ali__albanna",
    "إذاعة مشاري العفاسي": "https://qurango.net/radio/mishary_alafasi",
    "إذاعة مصطفى إسماعيل": "https://qurango.net/radio/mustafa_ismail",
    "إذاعة مصطفى اللاهوني": "https://qurango.net/radio/mustafa_allahoni",
    "إذاعة معيض الحارثي": "https://qurango.net/radio/moeedh_alharthi",
    "إذاعة موسى بلال": "https://qurango.net/radio/mousa_bilal",
    "إذاعة ناصر القطامي": "https://qurango.net/radio/nasser_alqatami",
    "إذاعة نبيل الرفاعي": "https://qurango.net/radio/nabil_al_rifay",
    "إذاعة نعمة الحسان": "https://qurango.net/radio/neamah_alhassan",
    "إذاعة هاني الرفاعي": "https://qurango.net/radio/hani_arrifai",
    "إذاعة وليد النائحي": "https://qurango.net/radio/waleed_alnaehi",
    "إذاعة ياسر الدوسري": "https://qurango.net/radio/yasser_aldosari",
    "إذاعة ياسر القرشي": "https://qurango.net/radio/yasser_alqurashi",
    "إذاعة يوسف الشويعي": "https://qurango.net/radio/yousef_alshoaey",
    "الإذاعة العامة - إذاعة متنوعة لمختلف القراء": "https://qurango.net/radio/mix",
    "إذاعة سورة البقرة - لعدد من القراء": "https://qurango.net/radio/albaqarah",
    "إذاعة تلاوات خاشعة": "https://qurango.net/radio/salma",
    "إذاعة أحمد الحواشي": "https://qurango.net/radio/ahmad_alhawashi",
    "إذاعة أحمد العجمي": "https://qurango.net/radio/ahmad_alajmy",
    "إذاعة أحمد خليل شاهين": "https://qurango.net/radio/ahmad_shaheen",
    "إذاعة أحمد ديبان": "https://qurango.net/radio/ahmad_deban",
    "إذاعة أحمد صابر": "https://qurango.net/radio/ahmad_saber",
    "إذاعة أحمد نعينع": "https://qurango.net/radio/ahmad_nauina",
    "إذاعة أكرم العلاقمي": "https://qurango.net/radio/akram_alalaqmi",
    "إذاعة إبراهيم الأخضر": "https://qurango.net/radio/ibrahim_alakdar",
    "إذاعة إدريس أبكر": "https://qurango.net/radio/idrees_abkr",
    "إذاعة الزين محمد أحمد": "https://qurango.net/radio/alzain_mohammad_ahmad",
    "إذاعة العيون الكوشي": "https://qurango.net/radio/aloyoon_alkoshi",
    "إذاعة الفتاوى العامة": "https://qurango.net/radio/fatwa",
    "إذاعة القارئ ياسين": "https://qurango.net/radio/alqaria_yassen",
    "إذاعة بندر بليلة": "https://qurango.net/radio/bandar_balilah",
    "إذاعة توفيق الصايغ": "https://qurango.net/radio/tawfeeq_assayegh",
    "إذاعة جمال شاكر عبدالله": "https://qurango.net/radio/jamal_shaker_abdullah",
    "إذاعة خالد الجليل": "https://qurango.net/radio/khalid_aljileel",
    "إذاعة خالد القحطاني": "https://qurango.net/radio/khaled_alqahtani",
    "إذاعة خالد عبدالكافي": "https://qurango.net/radio/khalid_abdulkafi",
    "إذاعة خليفة الطنيجي": "https://qurango.net/radio/khalifa_altunaiji",
    "إذاعة زكي داغستاني": "https://qurango.net/radio/zaki_daghistani",
    "إذاعة سعود الشريم": "https://qurango.net/radio/saud_alshuraim",
    "إذاعة سهل ياسين": "https://qurango.net/radio/sahl_yassin",
    "إذاعة سيد رمضان": "https://qurango.net/radio/sayeed_ramadan",
    "إذاعة شيخ أبو بكر الشاطري": "https://qurango.net/radio/shaik_abu_bakr_al_shatri",
    "إذاعة شيرزاد عبدالرحمن طاهر": "https://qurango.net/radio/shirazad_taher",
    "إذاعة صابر عبدالحكم": "https://qurango.net/radio/saber_abdulhakm",
    "إذاعة صلاح الهاشم": "https://qurango.net/radio/salah_alhashim",
    "إذاعة صلاح بو خاطر": "https://qurango.net/radio/slaah_bukhatir",
    "إذاعة عادل ريان": "https://qurango.net/radio/adel_ryyan",
    "إذاعة عبدالبارئ الثبيتي": "https://qurango.net/radio/abdelbari_altoubayti",
    "إذاعة عبدالبارئ محمد": "https://qurango.net/radio/abdulbari_mohammad",
    "إذاعة عبدالباسط عبدالصمد - المجود": "https://qurango.net/radio/abdulbasit_abdulsamad_mojawwad",
    "إذاعة عبدالباسط عبدالصمد - رواية ورش عن نافع": "https://qurango.net/radio/abdulbasit_abdulsamad_warsh",
    "إذاعة عبدالباسط عبدالصمد - المرتل": "https://qurango.net/radio/abdulbasit_abdulsamad",
    "إذاعة عبدالرحمن السديس": "https://qurango.net/radio/abdulrahman_alsudaes",
    "إذاعة عبدالرحمن الشحات": "https://qurango.net/radio/a_alshahhat",
    "إذاعة عبدالرشيد صوفي - رواية السوسي عن أبي عمرو": "https://qurango.net/radio/abdulrasheed_soufi_assosi",
    "إذاعة عبدالعزيز الأحمد": "https://qurango.net/radio/abdul_aziz_alahmad",
    "إذاعة عبدالله الخلف": "https://qurango.net/radio/abdullah_alkhalaf",
    "إذاعة عبدالله المطرود": "https://qurango.net/radio/abdullah_almattrod",
    "إذاعة عبدالله الموسى": "https://qurango.net/radio/abdullah_almousa",
    "إذاعة عبدالله بصفر": "https://qurango.net/radio/abdullah_basfer",
    "إذاعة عبدالله خياط": "https://qurango.net/radio/abdullah_khayyat",
    "إذاعة عبدالله عواد الجهني": "https://qurango.net/radio/abdullah_aljohany",
    "إذاعة عبدالمحسن الحارثي": "https://qurango.net/radio/abdulmohsin_alharthy",
    "إذاعة عبدالمحسن العبيكان": "https://qurango.net/radio/abdulmohsin_alobaikan",
    "إذاعة عبدالمحسن القاسم": "https://qurango.net/radio/abdulmohsen_alqasim",
    "إذاعة عبدالهادي أحمد كناكري": "https://qurango.net/radio/abdulhadi_kanakeri",
    "إذاعة عبدالودود حنيف": "https://qurango.net/radio/abdulwadood_haneef",
    "إذاعة علي الحذيفي": "https://qurango.net/radio/ali_alhuthaifi_qalon",
    "إذاعة علي بن عبدالرحمن الحذيفي": "https://qurango.net/radio/ali_alhuthaifi",
    "إذاعة ماجد الزامل": "https://qurango.net/radio/majed_alzamel",
    "إذاعة محمد أيوب - قراءة مميزة": "https://qurango.net/radio/ayyoub2",
    "إذاعة محمد الأمين قنيوة": "https://qurango.net/radio/qeniwa",
    "إذاعة محمد عثمان خان": "https://qurango.net/radio/mohammed_osman_khan",
    "إذاعة ناصر العصفور": "https://qurango.net/radio/nasser_alosfor",
    "إذاعة ناصر الماجد": "https://qurango.net/radio/nasser_almajed",
    "إذاعة نداء الإسلام - مكة المكرمة": "https://live.kwikmotion.com/sbrksanedaaradiolive/srpksanedaaradio/playlist.m3u8",
    "إذاعة هيثم الجدعاني": "https://qurango.net/radio/hitham_aljadani",
    "إذاعة القرآن الكريم - السعودية": "https://stream.radiojar.com/0tpy1h0kxtzuv",
    "إذاعة القرآن الكريم من السعودية (رابط 2)": "http://m.live.net.sa:1935/live/quran/playlist.m3u8",
    "إذاعة تفسير القرآن الكريم": "https://qurango.net/radio/tafseer",
    "المختصر في السيرة النبوية": "https://qurango.net/radio/almukhtasar_fi_alsiyra",
    "المختصر في تفسير القرآن الكريم": "https://qurango.net/radio/mukhtasartafsir",
    "تفسير القران الكريم-الخلاصة من تفسير الطبري": "https://qurango.net/radio/tabri",
    "تفسير غريب القرآن": "https://qurango.net/radio/gareeb-quran",
    "قصص الأنبياء": "https://qurango.net/radio/alanbiya",
    "تراتيل قصيرة متميزة": "https://qurango.net/radio/tarateel",
    "آيات السكينة": "https://qurango.net/radio/sakeenah",
    "أحمد طالب بن حميد": "https://qurango.net/radio/a_binhameed",
    "إذاعة محمد أبوسنينة": "https://qurango.net/radio/sneineh",
    "الشمائل المحمدية": "https://qurango.net/radio/shmaeel",
    "بدر التركي": "https://qurango.net/radio/bader",
    "ترجمة معاني القرآن باللغة الأسبانية": "https://qurango.net/radio/translation_quran_spanish_afs",
    "ترجمة معاني القرآن باللغة الألبانية": "https://qurango.net/radio/translation_quran_albanian",
    "ترجمة معاني القرآن باللغة الألمانية": "https://qurango.net/radio/translation_quran_german",
    "ترجمة معاني القرآن باللغة الأمازيغية": "https://qurango.net/radio/translation_quran_tamazight",
    "ترجمة معاني القرآن باللغة الأوردية - السديس والشريم": "https://qurango.net/radio/translation_quran_urdu_sds_shur",
    "ترجمة معاني القرآن باللغة الأوردية - المنشاوي": "https://qurango.net/radio/translation_quran_urdu_minsh",
    "ترجمة معاني القرآن باللغة الأوردية - عبدالباسط عبدالصمد": "https://qurango.net/radio/translation_quran_urdu_basit",
    "ترجمة معاني القرآن باللغة الإنجليزية - عبدالباسط عبدالصمد": "https://qurango.net/radio/translation_quran_english_basit",
    "ترجمة معاني القرآن باللغة الإنجليزية - عبدالله بصفر": "https://qurango.net/radio/translation_quran_english_bsfr",
    "ترجمة معاني القرآن باللغة الإنجليزية -ترجمة والك": "https://qurango.net/radio/translation_quran_english_walk_basit",
    "ترجمة معاني القرآن باللغة البرتغالية": "https://qurango.net/radio/translation_quran_portuguese",
    "ترجمة معاني القرآن باللغة البوسنية": "https://qurango.net/radio/translation_quran_bosnia",
    "ترجمة معاني القرآن باللغة التركية": "https://qurango.net/radio/translation_quran_turkish",
    "ترجمة معاني القرآن باللغة الروسية": "https://qurango.net/radio/translation_quran_Russia",
    "ترجمة معاني القرآن باللغة الصينية": "https://qurango.net/radio/translation_quran_chinese",
    "ترجمة معاني القرآن باللغة الفارسية": "https://qurango.net/radio/translation_quran_farsi",
    "ترجمة معاني القرآن باللغة الفرنسية": "https://qurango.net/radio/translation_quran_french",
    "ترجمة معاني القرآن باللغة الكردية": "https://qurango.net/radio/translation_quran_kurdish",
    "ترجمة معاني القرآن باللغة الكورية": "https://qurango.net/radio/translation_quran_Korean",
    "ترجمة معاني القرآن باللغة المجرية": "https://qurango.net/radio/translation_quran_hungarian",
    "ترجمة معاني القرآن باللغة الهوسا": "https://qurango.net/radio/Translation_Quran_Hausa",
    "ترجمة معاني القرآن باللغة اليونانية": "https://qurango.net/radio/translation_quran_greek",
    "حاتم فريد الواعر": "https://qurango.net/radio/hatem_fareed_alwaer",
    "رياض الصالحين": "https://qurango.net/radio/riyad",
    "سورة الملك": "https://qurango.net/radio/Surah_Al-Mulk",
    "صالح الهبدان": "https://qurango.net/radio/saleh_alhabdan",
    "صحيح البخاري": "https://qurango.net/radio/saheh-bokharee",
    "صحيح مسلم": "https://qurango.net/radio/saheh-muslim",
    "عبدالعزيز سحيم": "https://qurango.net/radio/a_sheim",
    "عبدالله البعيجان": "https://qurango.net/radio/buajan",
    "فضل شهر رمضان": "https://qurango.net/radio/ramadan",
    "هزاع البلوشي": "https://qurango.net/radio/hazza",
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
            if not check_internet():
                global_player.stop()
                global_current_url = None
                MessageBox.error(None, "خطأ", "لا يوجد اتصال بالإنترنت")
                return
            global_player.stop()
            global_player.setSource(url_to_play)
            global_player.play()
            global_current_url = url_to_play
