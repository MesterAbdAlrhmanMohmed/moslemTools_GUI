import pyperclip, requests, geocoder, winsound, gui, os
from guiTools import speak
from settings import settings_handler
from hijridate import Gregorian, Hijri
from datetime import datetime,timedelta
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class PrayerTimesWorker(qt2.QObject):
    finished = qt2.pyqtSignal(object, object, object, object, object, object, object, object)
    error = qt2.pyqtSignal(str)    
    def get_dates_info(self):        
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
            "الإثنين", "الثلثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"
        ]        
        now = datetime.now()
        day_name = days_of_week[now.weekday()]
        day = now.weekday()
        gregorian_date = f"{day_name} - {now.day} {gregorian_months[now.month - 1]} {now.year}"
        hijri_date_obj = Gregorian.today().to_hijri()
        hijri_date = f"{hijri_date_obj.day} {hijri_months[hijri_date_obj.month - 1]} {hijri_date_obj.year}"                
        today_greg = datetime.now().date()
        today_hijri = Gregorian.today().to_hijri()
        ramadan_year = today_hijri.year
        if today_hijri.month >= 9:
            ramadan_year += 1
        ramadan_start_hijri = Hijri(ramadan_year, 9, 1)
        ramadan_start_greg = ramadan_start_hijri.to_gregorian()
        time_left = ramadan_start_greg - today_greg
        total_days_left = time_left.days
        ramadan_countdown_message = ""        
        if total_days_left == 0:
            ramadan_countdown_message = "اليوم هو أول أيام شهر رمضان!"
        elif total_days_left > 0:
            months = total_days_left // 30
            days = total_days_left % 30
            if months > 0 and days > 0:
                ramadan_countdown_message = f"باقي على شهر رمضان حوالي: {months} شهر و {days} يوم"
            elif months > 0 and days == 0:
                ramadan_countdown_message = f"باقي على شهر رمضان: {months} شهر بالضبط"
            elif months == 0 and days > 0:
                ramadan_countdown_message = f"باقي على شهر رمضان: {days} يوم"        
        return gregorian_date, hijri_date, ramadan_countdown_message, day        
    def run(self):
        try:            
            gregorian_date, hijri_date, ramadan_countdown_message, day = self.get_dates_info()            
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
                    prayers = list(prayers_ar.values())
                    times = []
                    for prayer_en, prayer_ar in prayers_ar.items():
                        time_24h = data[prayer_en]
                        time_12h = datetime.strptime(time_24h, "%H:%M").strftime("%I:%M %p")
                        times.append(time_12h)                    
                    self.finished.emit(prayers, times, gregorian_date, hijri_date, ramadan_countdown_message, day, None, None)
                else:
                    self.finished.emit([], [], gregorian_date, hijri_date, ramadan_countdown_message, day, "حدث خطأ في جلب مواقيت الصلاة.", None)
            else:
                self.finished.emit([], [], gregorian_date, hijri_date, ramadan_countdown_message, day, "لم يتم تحديد الموقع الجغرافي. تأكد من اتصال الإنترنت، ولن تعمل خدمة مواقيت الصلاة مع استخدام بيانات الهاتف المحمول", None)
        except Exception as e:            
            try:
                gregorian_date, hijri_date, ramadan_countdown_message, day = self.get_dates_info()
                self.finished.emit([], [], gregorian_date, hijri_date, ramadan_countdown_message, day, f"حدث خطأ غير متوقع: {str(e)}", None)
            except:
                self.error.emit(f"حدث خطأ غير متوقع: {str(e)}")
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
        self.next_prayer_item = None
        self.countdown_timer = qt2.QTimer(self)
        self.countdown_timer.timeout.connect(self.update_next_prayer_countdown)
        self.information = qt.QListWidget()
        self.information.setSpacing(1)
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
        self.worning0 = qt.QLabel()
        self.worning0.setText("قال رسولُ اللهِ صلَّى الله عليه وسلَّم:\n«إنَّ العهدَ الذي بيننا وبينهم الصلاةُ، فمَن تركها فقد كفر».\nفلا تتركوا أيَّ صلاةٍ مفروضةٍ لأيِّ سبب.")
        self.worning0.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning0.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning3 = qt.QLabel()
        self.worning3.setText("معلومة هامة: لا يمكن تحديد مواقيت الصلاة باستخدام بيانات الهاتف المحمول")
        self.worning3.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning3.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
        layout = qt.QVBoxLayout()
        layout.addWidget(self.information)
        layout.addWidget(self.worning0)        
        layout.addItem(qt.QSpacerItem(0, 15, qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed))
        layout.addWidget(self.worning3)
        layout.addWidget(self.worning1)
        layout.addWidget(self.worning2)
        layout.addWidget(self.worning)
        self.setLayout(layout)
        self.display_prayer_times()        
    def format_arabic_time_unit(self, number, units):
        if number == 0:
            return ""
        if number == 1:
            return units['singular']
        elif number == 2:
            return units['dual']
        elif 3 <= number <= 10:
            return f"{number} {units['plural']}"
        else:
            return f"{number} {units['singular_acc']}"
    def update_next_prayer_countdown(self):
        if not self.times or not self.prayers:
            return
        now = datetime.now()
        next_prayer_name = None
        next_prayer_time_obj = None
        for i, time_str in enumerate(self.times):
            try:
                prayer_time_obj = datetime.strptime(time_str, "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
                if prayer_time_obj > now:
                    next_prayer_time_obj = prayer_time_obj
                    next_prayer_name = self.prayers[i]
                    break
            except ValueError:
                continue
        if next_prayer_name is None:
            fajr_time_str = self.times[0]
            tomorrow = now + timedelta(days=1)
            next_prayer_time_obj = datetime.strptime(fajr_time_str, "%I:%M %p").replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
            next_prayer_name = self.prayers[0]
        time_left = next_prayer_time_obj - now
        total_seconds = int(time_left.total_seconds())
        if total_seconds < 0:
             total_seconds = 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        hour_units = {'singular': 'ساعة', 'dual': 'ساعتين', 'plural': 'ساعات', 'singular_acc': 'ساعة'}
        minute_units = {'singular': 'دقيقة', 'dual': 'دقيقتين', 'plural': 'دقائق', 'singular_acc': 'دقيقة'}
        second_units = {'singular': 'ثانية', 'dual': 'ثانيتين', 'plural': 'ثواني', 'singular_acc': 'ثانية'}
        h_str = self.format_arabic_time_unit(hours, hour_units)
        m_str = self.format_arabic_time_unit(minutes, minute_units)
        s_str = self.format_arabic_time_unit(seconds, second_units)    
        parts = [p for p in [h_str, m_str, s_str] if p]        
        time_str = ""
        if len(parts) > 0:
            time_str = " و ".join(parts)
        else:             
            self.update_next_prayer_countdown()
            return
        countdown_message = f"متبقي على صلاة {next_prayer_name} {time_str}"
        if self.next_prayer_item:
            self.next_prayer_item.setText(countdown_message)
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
            index = self.times.index(time_str)
            prayer_name = self.prayers[index]            
            if currentTime == time_str:
                self.reminded=False
                if settings_handler.get("prayerTimes", "adaanReminder") == "True":                    
                    prayer_key = self.get_prayer_key(prayer_name)                    
                    if prayer_key:                        
                        sound_file = settings_handler.get("adhanSounds", prayer_key)
                        sound_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", sound_file)                                                
                        gui.AdaanDialog(self, index, prayer_name, sound_path).exec()                    
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
                        if index in medias:
                            self.p.media_player.setSource(qt2.QUrl.fromLocalFile("data\\sounds\\before_azan\\" + medias[index]))
                            self.p.media_player.play()
                            print(f"Playing pre-Adhan reminder for {prayer_name}")
                        else:
                            print(f"No specific pre-Adhan sound for prayer {prayer_name}")
                else:
                    print(f"Warning: 'remindBeforeAdaan' value '{beforeOptions}' not found in beforeChoises. No before-Adhan reminder will be set.")        
    def get_prayer_key(self, prayer_name_ar):        
        prayer_map = {
            "الفجر": "fajr",
            "الظهر": "dhuhr",
            "العصر": "asr",
            "المغرب": "maghrib",
            "العشاء": "isha"
        }
        return prayer_map.get(prayer_name_ar, None)        
    def copy_all_items(self):
        all_text = "\n".join([self.information.item(i).text() for i in range(self.information.count())])
        pyperclip.copy(all_text)
        speak("تم نسخ كل المحتوى بنجاح")        
        winsound.Beep(1000, 100)        
    def copy_selected_item(self):
        selected_item = self.information.currentItem()
        if selected_item:
            pyperclip.copy(selected_item.text())
            winsound.Beep(1000, 100)    
            speak("تم نسخ المحتوى المحدد بنجاح")    
    def display_prayer_times(self):
        self.countdown_timer.stop()
        self.information.clear()
        self.information.addItem("جاري تحميل مواقيت الصلاة...")                
        self.worker = PrayerTimesWorker()
        self.thread = qt2.QThread()
        self.worker.moveToThread(self.thread)                
        self.worker.finished.connect(self.on_prayer_times_ready)
        self.worker.error.connect(self.on_prayer_times_error)                
        self.thread.started.connect(self.worker.run)
        self.thread.start()    
    def on_prayer_times_ready(self, prayers, times, gregorian_date, hijri_date, ramadan_countdown_message, day, error_message, _):        
        self.thread.quit()
        self.thread.wait()                
        self.information.clear()
        self.prayers = prayers
        self.times = times
        self.day = day                    
        if prayers and times:
            for i in range(len(prayers)):
                self.information.addItem(f"{prayers[i]}: {times[i]}")        
            self.next_prayer_item = qt.QListWidgetItem("جاري حساب الوقت المتبقي...")
            self.information.addItem(self.next_prayer_item)
        self.information.addItem("التاريخ الميلادي: " + gregorian_date)
        self.information.addItem("التاريخ الهجري: " + hijri_date)                
        if ramadan_countdown_message:
            self.information.addItem(ramadan_countdown_message)                
        if error_message:
            self.information.addItem(error_message)                        
        if not self.timer.isActive() and prayers and times:
            self.timer.start(10000)    
        if prayers and times:
            self.update_next_prayer_countdown()
            self.countdown_timer.start(1000)
    def on_prayer_times_error(self, error_message):        
        self.thread.quit()
        self.thread.wait()                
        self.information.clear()
        self.information.addItem(error_message)                
        self.countdown_timer.stop()
        try:
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
                "الإثنين", "الثلثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"
            ]            
            now = datetime.now()
            day_name = days_of_week[now.weekday()]
            gregorian_date = f"{day_name} - {now.day} {gregorian_months[now.month - 1]} {now.year}"
            hijri_date_obj = Gregorian.today().to_hijri()
            hijri_date = f"{hijri_date_obj.day} {hijri_months[hijri_date_obj.month - 1]} {hijri_date_obj.year}"            
            self.information.addItem("التاريخ الميلادي: " + gregorian_date)
            self.information.addItem("التاريخ الهجري: " + hijri_date)
        except:
            pass