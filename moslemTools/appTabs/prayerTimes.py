import pyperclip, requests, geocoder, winsound, gui
from settings import settings_handler
from hijri_converter import Gregorian
from datetime import datetime,timedelta
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class prayer_times(qt.QWidget):
    def __init__(self,p):
        super().__init__()
        self.p=p
        self.day=0
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_selected_item)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_all_items)
        qt1.QShortcut("f5", self).activated.connect(self.display_prayer_times)
        self.prayers = []
        self.times = []
        self.timer = qt2.QTimer(self)
        self.timer.timeout.connect(self.onTimer)
        self.information = qt.QListWidget()
        self.worning = qt.QLabel()
        self.worning.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning.setText("F5: لإعادة تحميل مواقيت الصلاة")
        self.worning.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning1 = qt.QLabel()
        self.worning1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning1.setText("CTRL+A: لنسخ كل القائمة")
        self.worning1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning2 = qt.QLabel()
        self.worning2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning2.setText("CTRL+C: لنسخ عنصر محدد من القائمة")
        self.worning2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.reminded=False
        self.information.setFont(font)
        self.worning.setFont(font)
        layout = qt.QVBoxLayout()
        layout.addWidget(self.information)
        layout.addWidget(self.worning1)
        layout.addWidget(self.worning2)
        layout.addWidget(self.worning)
        self.setLayout(layout)
        self.display_prayer_times()
    def onTimer(self):
        currentTimeOBJ = datetime.now()
        currentTime=currentTimeOBJ.strftime("%I:%M %p")
        beforeOptions=settings_handler.get("prayerTimes","remindBeforeAdaan")        
        beforeChoises={"0":15,"1":30,"2":60} 
        if self.day==4:
            ZoharDay="gomaasoon.mp3"
        else:
            ZoharDay="zohrsoon.mp3"
        for time_str in self.times:
            if self.times.index(time_str) == 1: 
                continue            
            if currentTime == time_str:
                self.reminded=False
                if settings_handler.get("prayerTimes", "adaanReminder") == "True":
                    print("addaan")
                    gui.AdaanDialog(self, self.times.index(time_str), self.prayers[self.times.index(time_str)]).exec()                    
                    self.timer.stop()
                    self.timer.singleShot(60000, qt2.Qt.TimerType.PreciseTimer, lambda: self.timer.start(10000))
                    return
            if beforeOptions != "3":                
                if beforeOptions in beforeChoises:
                    minutes_to_subtract = beforeChoises[beforeOptions]                                        
                    prayer_time_obj = datetime.strptime(time_str, "%I:%M %p")
                    beforeTimeOBJ = prayer_time_obj - timedelta(minutes=minutes_to_subtract)
                    beforeTime = beforeTimeOBJ.strftime("%I:%M %p")
                    if self.reminded:
                        continue                                        
                    medias={0:"fagrsoon.mp3",2:ZoharDay,3:"asrsoon.mp3",4:"maghribsoon.mp3",5:"eshaasoon.mp3"}
                    if beforeTime==currentTime:
                        self.reminded=True
                        if self.p.media_player.isPlaying():
                            self.p.media_player.stop()                        
                        if self.times.index(time_str) in medias:
                            self.p.media_player.setSource(qt2.QUrl.fromLocalFile("data\\sounds\\before_azan\\" + medias[self.times.index(time_str)]))
                            self.p.media_player.play()
                            print(f"Playing pre-Adhan reminder for {self.prayers[self.times.index(time_str)]}")
                        else:
                            print(f"No specific pre-Adhan sound for prayer index {self.times.index(time_str)}")
                else:
                    print(f"Warning: 'remindBeforeAdaan' value '{beforeOptions}' not found in beforeChoises. No before-Adhan reminder will be set.")
    def copy_all_items(self):
        all_text = "\n".join([self.information.item(i).text() for i in range(self.information.count())])
        pyperclip.copy(all_text)
        winsound.Beep(1000, 100)
    def copy_selected_item(self):
        selected_item = self.information.currentItem()
        if selected_item:
            pyperclip.copy(selected_item.text())
            winsound.Beep(1000, 100)
    def display_prayer_times(self):
        self.information.clear()
        gregorian_months = [
            "يَنَايِر", "فِبْرَايِر", "مَارِس", "أَبْرِيل", "مَايُو", "يُونْيُو",
            "يُولْيُو", "أَغُسْطُس", "سِبْتَمْبَر", "أُكْتُوبَر", "نُوفَمْبَر", "دِيسَمْبَر",
        ]
        hijri_months = [
            "مُحَرَّم", "صَفَر", "رَبِيع ٱلْأَوَّل", "رَبِيع ٱلثَّانِي", "جُمَادَىٰ ٱلْأُولَىٰ",
            "جُمَادَىٰ ٱلثَّانِيَة", "رَجَب", "شَعْبَان", "رَمَضَان", "شَوَّال",
            "ذُو ٱلْقَعْدَة", "ذُو ٱلْحِجَّة",
        ]
        days_of_week = [
            "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"
        ]
        g = geocoder.ip('me')
        if g.ok:
            if settings_handler.get("location","autoDetect")=="True":
                latitude = g.latlng[0]
                longitude = g.latlng[1]
            else:
                latitude=float(settings_handler.get("location","LT2"))
                longitude=float(settings_handler.get("location","LT1"))
            method = 5
            response = requests.get('http://api.aladhan.com/v1/timings', params={
                'latitude': latitude,
                'longitude': longitude,
                'method': method
            })
            if response.status_code == 200:
                data = response.json()['data']['timings']
                prayers_ar = {
                    'Fajr': 'الفجر',
                    'Sunrise': 'الشروق',
                    'Dhuhr': 'الظهر',
                    'Asr': 'العصر',
                    'Maghrib': 'المغرب',
                    'Isha': 'العشاء'
                }
                self.prayers = list(prayers_ar.values())
                self.times = []
                self.timer.start(10000)
                for prayer_en, prayer_ar in prayers_ar.items():
                    time_24h = data[prayer_en]
                    time_12h = datetime.strptime(time_24h, "%H:%M").strftime("%I:%M %p")
                    self.times.append(time_12h)
                    self.information.addItem(f"{prayer_ar}: {time_12h}")
            else:
                self.information.addItem("حدث خطأ في جلب مواقيت الصلاة.")
        else:
            self.information.addItem("لم يتم تحديد الموقع الجغرافي. تأكد من اتصال الإنترنت.")        
        now = datetime.now()
        day_name = days_of_week[now.weekday()]
        self.day=now.weekday()
        gregorian_date = f"{day_name} - {now.day} {gregorian_months[now.month - 1]} {now.year}"
        hijri_date_obj = Gregorian.today().to_hijri()
        hijri_date = f"{hijri_date_obj.day} {hijri_months[hijri_date_obj.month - 1]} {hijri_date_obj.year}"
        self.information.addItem("التاريخ الميلادي: " + gregorian_date)
        self.information.addItem("التاريخ الهجري: " + hijri_date)