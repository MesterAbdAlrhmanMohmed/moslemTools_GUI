import os
import requests
import geocoder
from datetime import datetime
import ujson as json
import PyQt6.QtCore as qt2
from settings import settings_handler
from .cache_utils import get_cache_file_path
from .dates_utils import get_dates_info


class PrayerTimesWorker(qt2.QObject):
    finished = qt2.pyqtSignal(object, object, object, object, object, object, object, object, object, object, object)
    error = qt2.pyqtSignal(str)

    def __init__(self, force_refresh=False):
        super().__init__()
        self.force_refresh = force_refresh

    def run(self):
        try:
            gregorian_date, hijri_date, day, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month = get_dates_info()
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            current_year = now.year
            cache_file = get_cache_file_path()

            is_auto_detect = (settings_handler.get("location", "autoDetect") == "True")
            method = settings_handler.get("location", "calculationMethod")
            if not method:
                method = "5"
            else:
                method = str(method)

            cache_data = None
            cache_hit = False
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                except Exception:
                    cache_data = None

            if not self.force_refresh and cache_data and isinstance(cache_data, dict):
                cached_year = cache_data.get("year")
                cached_method = str(cache_data.get("method", ""))
                timings_dict = cache_data.get("timings", {})

                if cached_year == current_year and today_str in timings_dict and cached_method == method:
                    if is_auto_detect:
                        if cache_data.get("auto_detect") is True:
                            cache_hit = True
                    else:
                        try:
                            lat = float(settings_handler.get("location", "LT2"))
                            lon = float(settings_handler.get("location", "LT1"))
                            if (round(cache_data.get("latitude", 0), 3) == round(lat, 3) and
                                round(cache_data.get("longitude", 0), 3) == round(lon, 3)):
                                cache_hit = True
                        except Exception:
                            pass

            if cache_hit:
                day_timings = cache_data["timings"][today_str]
                dhuhr_name = 'صلاة الجمعة' if day == 4 else 'الظهر'
                prayers_ar = {'Fajr': 'الفجر', 'Sunrise': 'الشروق', 'Dhuhr': dhuhr_name, 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
                prayers = list(prayers_ar.values())
                times = []
                for prayer_en in prayers_ar.keys():
                    time_24h = day_timings.get(prayer_en, "00:00")
                    time_12h = datetime.strptime(time_24h, "%H:%M").strftime("%I:%M %p")
                    times.append(time_12h)
                self.finished.emit(prayers, times, gregorian_date, hijri_date, day, None, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
                return

            latitude = None
            longitude = None
            if is_auto_detect:
                try:
                    g = geocoder.ip('me')
                    if g.ok:
                        latitude = g.latlng[0]
                        longitude = g.latlng[1]
                except Exception:
                    pass
                if latitude is None:
                    if cache_data and "latitude" in cache_data and "longitude" in cache_data:
                        latitude = cache_data["latitude"]
                        longitude = cache_data["longitude"]
                    else:
                        try:
                            latitude = float(settings_handler.get("location", "LT2"))
                            longitude = float(settings_handler.get("location", "LT1"))
                        except Exception:
                            latitude, longitude = 30.0444, 31.2357
            else:
                latitude = float(settings_handler.get("location", "LT2"))
                longitude = float(settings_handler.get("location", "LT1"))

            url = f"http://api.aladhan.com/v1/calendar/{current_year}"
            response = requests.get(url, params={'latitude': latitude, 'longitude': longitude, 'method': int(method)}, timeout=15)
            if response.status_code == 200:
                raw_months = response.json().get('data', {})
                new_timings = {}
                for m_key, days_list in raw_months.items():
                    for day_info in days_list:
                        greg_date_str = day_info.get('date', {}).get('gregorian', {}).get('date', '')
                        if greg_date_str:
                            parts = greg_date_str.split('-')
                            if len(parts) == 3:
                                d_part, m_part, y_part = parts
                                iso_key = f"{y_part}-{m_part.zfill(2)}-{d_part.zfill(2)}"
                                day_t = day_info.get('timings', {})
                                clean_t = {}
                                for p_k in ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                                    val = day_t.get(p_k, '00:00').split(' ')[0]
                                    clean_t[p_k] = val
                                new_timings[iso_key] = clean_t

                new_cache = {
                    "year": current_year,
                    "latitude": latitude,
                    "longitude": longitude,
                    "method": method,
                    "auto_detect": is_auto_detect,
                    "last_updated": datetime.now().isoformat(),
                    "timings": new_timings
                }
                try:
                    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(new_cache, f, ensure_ascii=False)
                except Exception as e_write:
                    print(f"Failed to write cache: {e_write}")

                if today_str in new_timings:
                    day_timings = new_timings[today_str]
                    dhuhr_name = 'صلاة الجمعة' if day == 4 else 'الظهر'
                    prayers_ar = {'Fajr': 'الفجر', 'Sunrise': 'الشروق', 'Dhuhr': dhuhr_name, 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
                    prayers = list(prayers_ar.values())
                    times = [datetime.strptime(day_timings[p_en], "%H:%M").strftime("%I:%M %p") for p_en in prayers_ar.keys()]
                    self.finished.emit(prayers, times, gregorian_date, hijri_date, day, None, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
                else:
                    self.finished.emit([], [], gregorian_date, hijri_date, day, "حدث خطأ: لم يتم العثور على مواقيت اليوم في البيانات المستلمة.", ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
            else:
                if cache_data and today_str in cache_data.get("timings", {}):
                    day_timings = cache_data["timings"][today_str]
                    dhuhr_name = 'صلاة الجمعة' if day == 4 else 'الظهر'
                    prayers_ar = {'Fajr': 'الفجر', 'Sunrise': 'الشروق', 'Dhuhr': dhuhr_name, 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
                    prayers = list(prayers_ar.values())
                    times = [datetime.strptime(day_timings[p_en], "%H:%M").strftime("%I:%M %p") for p_en in prayers_ar.keys()]
                    self.finished.emit(prayers, times, gregorian_date, hijri_date, day, "تعذر تحديث المواقيت من الإنترنت، يتم عرض المواقيت المحفوظة مسبقاً.", ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
                else:
                    self.finished.emit([], [], gregorian_date, hijri_date, day, "حدث خطأ في جلب مواقيت الصلاة من الإنترنت.", ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
        except Exception as e:
            try:
                gregorian_date, hijri_date, day, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month = get_dates_info()
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                cache_file = get_cache_file_path()
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                        if today_str in cache_data.get("timings", {}):
                            day_timings = cache_data["timings"][today_str]
                            dhuhr_name = 'صلاة الجمعة' if day == 4 else 'الظهر'
                            prayers_ar = {'Fajr': 'الفجر', 'Sunrise': 'الشروق', 'Dhuhr': dhuhr_name, 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
                            prayers = list(prayers_ar.values())
                            times = [datetime.strptime(day_timings[p_en], "%H:%M").strftime("%I:%M %p") for p_en in prayers_ar.keys()]
                            self.finished.emit(prayers, times, gregorian_date, hijri_date, day, "لا يوجد اتصال بالإنترنت، يتم عرض مواقيت الصلاة المحفوظة مسبقاً.", ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
                            return
                    except Exception:
                        pass
                self.finished.emit([], [], gregorian_date, hijri_date, day, f"حدث خطأ في الاتصال بالإنترنت: {str(e)}", ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month)
            except Exception as e_inner:
                self.error.emit(f"حدث خطأ غير متوقع: {str(e_inner)}")
