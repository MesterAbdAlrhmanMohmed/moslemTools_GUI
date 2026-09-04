import os
import pyperclip
import winsound
from datetime import datetime, timedelta
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

import gui
from guiTools import speak, QReadOnlyTextEdit, QNavigableLabel
from guiTools.qMessageBox import MessageBox
from settings import settings_handler
from functions import audio_manager

from .worker import PrayerTimesWorker
from .cache_utils import get_cache_status_message
from .time_format_utils import format_arabic_time_unit, format_timedelta_arabic
from .dates_utils import get_dates_info


class prayer_times(qt.QWidget):
    TEST_MODE = False

    def __init__(self, p):
        super().__init__()
        self.p = p
        self.day = 0
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_selected_item)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_all_items)
        qt1.QShortcut("f5", self).activated.connect(lambda: self.display_prayer_times(force_refresh=True))
        self.prayers = []
        self.times = []
        self.timer = qt2.QTimer(self)
        self.timer.timeout.connect(self.onTimer)
        self.next_prayer_item = None
        self.ramadan_countdown_item = None
        self.greg_month_countdown_item = None
        self.hijri_month_countdown_item = None
        self.cache_countdown_item = None
        self.current_greg_month = ""
        self.current_hijri_month = ""
        self.ramadan_start_greg = None
        self.greg_end_dt = None
        self.hijri_end_dt = None
        self.current_day_check = datetime.now().day
        self.countdown_timer = qt2.QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdowns)
        self.information = qt.QListWidget()
        self.information.setSpacing(3)
        self.worning = QNavigableLabel("F5: لإعادة تحميل مواقيت الصلاة")
        self.worning.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning1 = QNavigableLabel("CTRL+A: لنسخ كل القائمة")
        self.worning1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning2 = QNavigableLabel("CTRL+C: لنسخ عنصر محدد من القائمة")
        self.worning2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.reminded = False
        self.information.setFont(font)
        self.worning.setFont(font)
        self.worning1.setFont(font)
        self.worning2.setFont(font)
        self.worning0 = QReadOnlyTextEdit()
        self.worning0.setText("قال رسولُ اللهِ صلَّى الله عليه وسلَّم:\n«إنَّ العهدَ الذي بيننا وبينهم الصلاةُ، فمَن تركها فقد كفر».\nفلا تتركوا أيَّ صلاةٍ مفروضةٍ لأيِّ سبب.")
        self.worning0.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning0.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning0.setFont(font)
        self.worning3 = QNavigableLabel("معلومة هامة: لا يمكن تحديد مواقيت الصلاة باستخدام بيانات الهاتف المحمول")
        self.worning3.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.worning3.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.worning3.setFont(font)
        layout = qt.QVBoxLayout()
        layout.addWidget(self.information, 1)
        layout.addSpacing(20)
        bottom_widget = qt.QWidget()
        bottom_widget.setLayoutDirection(qt2.Qt.LayoutDirection.RightToLeft)
        bottom_layout = qt.QHBoxLayout(bottom_widget)
        left_layout = qt.QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.addWidget(self.worning3)
        left_layout.addWidget(self.worning1)
        left_layout.addWidget(self.worning2)
        left_layout.addWidget(self.worning)
        left_layout.addStretch()
        right_layout = qt.QVBoxLayout()
        right_layout.addSpacing(15)
        right_layout.addWidget(self.worning0)
        right_layout.addStretch()
        bottom_layout.addLayout(right_layout)
        bottom_layout.addLayout(left_layout)
        layout.addWidget(bottom_widget, 0)
        self.setLayout(layout)
        if self.TEST_MODE:
            self.information.addItem("وضع الاختبار يعمل...")
            self.information.addItem("سيتم رفع أذان الظهر بعد 10 ثوانٍ.")
            qt2.QTimer.singleShot(10000, self.trigger_test_adhan)
        else:
            self.display_prayer_times()

    def trigger_test_adhan(self):
        test_index = 2
        test_prayer_name = "صلاة الجمعة" if self.day == 4 else "الظهر"
        prayer_key = self.get_prayer_key(test_prayer_name)
        if prayer_key:
            sound_file = settings_handler.get("adhanSounds", prayer_key)
            sound_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", sound_file)
            self.information.addItem(f"تم تشغيل أذان {test_prayer_name}")
            gui.AdaanDialog(self, test_index, test_prayer_name, sound_path).exec()
            self.schedule_iqama_timer(prayer_key)
            self.information.addItem("انتهى الاختبار بنجاح (وجاري انتظار الإقامة إذا تم ضبطها).")
        else:
            self.information.addItem("خطأ في تشغيل الاختبار.")

    def update_countdowns(self):
        now = datetime.now()
        if now.day != self.current_day_check:
            self.current_day_check = now.day
            self.display_prayer_times()
            return
        if self.times and self.prayers:
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
            h_str = format_arabic_time_unit(hours, hour_units)
            m_str = format_arabic_time_unit(minutes, minute_units)
            s_str = format_arabic_time_unit(seconds, second_units)
            parts = [p for p in [h_str, m_str, s_str] if p]
            time_str = " و ".join(parts) if parts else ""
            if self.next_prayer_item:
                if time_str:
                    if next_prayer_name == 'الشروق':
                        display_text = f"متبقي على شروق الشمس {time_str}"
                    elif next_prayer_name == 'صلاة الجمعة':
                        display_text = f"متبقي على {next_prayer_name} {time_str}"
                    else:
                        display_text = f"متبقي على صلاة {next_prayer_name} {time_str}"
                    self.next_prayer_item.setText(display_text)
                else:
                    if next_prayer_name == 'الشروق':
                        self.next_prayer_item.setText("حان الآن موعد شروق الشمس")
                    elif next_prayer_name == 'صلاة الجمعة':
                        self.next_prayer_item.setText(f"حان الآن موعد {next_prayer_name}")
                    else:
                        self.next_prayer_item.setText(f"حان الآن موعد صلاة {next_prayer_name}")
        if self.greg_end_dt and self.greg_month_countdown_item:
            td = self.greg_end_dt - now
            self.greg_month_countdown_item.setText(f"متبقي على نهاية شهر {self.current_greg_month}: {format_timedelta_arabic(td)}")
        if self.hijri_end_dt and self.hijri_month_countdown_item:
            td = self.hijri_end_dt - now
            self.hijri_month_countdown_item.setText(f"متبقي على نهاية شهر {self.current_hijri_month}: {format_timedelta_arabic(td)}")
        if self.ramadan_start_greg:
            ramadan_start_dt = datetime.combine(self.ramadan_start_greg, datetime.min.time())
            if now >= ramadan_start_dt and now.date() <= (ramadan_start_dt + timedelta(days=29)).date():
                ramadan_message = "رمضان كريم وكل عام وأنتم بخير!"
            elif now > ramadan_start_dt:
                ramadan_message = ""
            else:
                time_left = ramadan_start_dt - now
                days_total = time_left.days
                if days_total < 0:
                    days_total = 0
                months = days_total // 30
                days = days_total % 30
                month_units = {'singular': 'شهر', 'dual': 'شهرين', 'plural': 'أشهر', 'singular_acc': 'شهراً'}
                day_units = {'singular': 'يوم', 'dual': 'يومين', 'plural': 'أيام', 'singular_acc': 'يوماً'}
                mo_str = format_arabic_time_unit(months, month_units)
                d_str = format_arabic_time_unit(days, day_units)
                parts = [p for p in [mo_str, d_str] if p]
                if parts:
                    time_str = " و ".join(parts)
                    ramadan_message = f"باقي على شهر رمضان حوالي: {time_str}"
                else:
                    ramadan_message = "رمضان على الأبواب!"
            if self.ramadan_countdown_item:
                self.ramadan_countdown_item.setText(ramadan_message)
                self.ramadan_countdown_item.setHidden(not ramadan_message)
        if self.cache_countdown_item:
            self.cache_countdown_item.setText(get_cache_status_message())

    def onTimer(self):
        currentTimeOBJ = datetime.now()
        currentTime = currentTimeOBJ.strftime("%I:%M %p")
        beforeOptions = settings_handler.get("prayerTimes", "remindBeforeAdaan")
        beforeChoises = {"0": 15, "1": 30, "2": 60}
        if self.day == 4:
            ZoharDay = "gomaasoon.mp3"
        else:
            ZoharDay = "zohrsoon.mp3"
        for index, time_str in enumerate(self.times):
            prayer_name = self.prayers[index]
            if currentTime == time_str:
                self.reminded = False
                if settings_handler.get("prayerTimes", "adaanReminder") == "True":
                    prayer_key = self.get_prayer_key(prayer_name)
                    if prayer_key:
                        sound_file = settings_handler.get("adhanSounds", prayer_key)
                        sound_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", sound_file)
                        gui.AdaanDialog(self, index, prayer_name, sound_path).exec()
                        self.schedule_iqama_timer(prayer_key)
                        self.timer.stop()
                        self.timer.singleShot(60000, qt2.Qt.TimerType.PreciseTimer, lambda: self.timer.start(1000))
                        return
            if beforeOptions != "3":
                if beforeOptions in beforeChoises:
                    minutes_to_subtract = beforeChoises[beforeOptions]
                    prayer_time_obj = datetime.strptime(time_str, "%I:%M %p")
                    beforeTimeOBJ = prayer_time_obj - timedelta(minutes=minutes_to_subtract)
                    beforeTime = beforeTimeOBJ.strftime("%I:%M %p")
                    if self.reminded:
                        continue
                    medias = {0: "fagrsoon.mp3", 2: ZoharDay, 3: "asrsoon.mp3", 4: "maghribsoon.mp3", 5: "eshaasoon.mp3"}
                    if beforeTime == currentTime:
                        self.reminded = True
                        if self.p.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                            self.p.media_player.stop()
                        self.p.audio_output.setDevice(audio_manager.get_audio_device("adhan"))
                        if index in medias:
                            before_azan_sound = os.path.join("data", "sounds", "before_azan", medias[index])
                            self.p.media_player.setSource(qt2.QUrl.fromLocalFile(before_azan_sound))
                            self.p.media_player.play()

    def get_prayer_key(self, prayer_name_ar):
        if "الظهر" in prayer_name_ar or "الجمعة" in prayer_name_ar:
            return "dhuhr"
        prayer_map = {"الفجر": "fajr", "العصر": "asr", "المغرب": "maghrib", "العشاء": "isha"}
        return prayer_map.get(prayer_name_ar, None)

    def play_iqama_sound(self):
        if self.p.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.p.media_player.stop()
        sound_file = settings_handler.get("adhanSounds", "iqama")
        sound_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "addan", sound_file)
        if not os.path.exists(sound_path):
            return
        try:
            self.iqama_media_player = QMediaPlayer()
            self.iqama_audio_output = QAudioOutput()
            self.iqama_audio_output.setDevice(audio_manager.get_audio_device("adhan"))
            self.iqama_audio_output.setVolume(int(settings_handler.get("prayerTimes", "iqamaVolume")) / 100)
            self.iqama_media_player.setAudioOutput(self.iqama_audio_output)
            self.iqama_media_player.setSource(qt2.QUrl.fromLocalFile(sound_path))
            self.iqama_media_player.mediaStatusChanged.connect(self.on_iqama_finished)
            self.iqama_media_player.play()
        except Exception:
            pass

    def on_iqama_finished(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if hasattr(self, 'iqama_media_player'):
                self.iqama_media_player.deleteLater()
                self.iqama_audio_output.deleteLater()

    def schedule_iqama_timer(self, prayer_key):
        if prayer_key is None:
            return
        iqama_setting = settings_handler.get("prayerTimes", "remindAfterAdaan")
        if iqama_setting == "3":
            return
        minutes_map = {"0": 5, "1": 10, "2": 15}
        minutes_to_wait = minutes_map.get(iqama_setting)
        if minutes_to_wait:
            milliseconds_to_wait = minutes_to_wait * 60 * 1000
            qt2.QTimer.singleShot(milliseconds_to_wait, self.play_iqama_sound)

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

    def display_prayer_times(self, force_refresh=False):
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            MessageBox.error(self, "خطأ", "يتم تحميل مواقيت الصلاة بالفعل، يرجى الانتظار.")
            return
        self.countdown_timer.stop()
        self.information.clear()
        self.information.addItem("جاري تحميل مواقيت الصلاة...")
        self.worker = PrayerTimesWorker(force_refresh=force_refresh)
        self.worker_thread = qt2.QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.finished.connect(self.on_prayer_times_ready)
        self.worker.error.connect(self.on_prayer_times_error)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def on_prayer_times_ready(self, prayers, times, gregorian_date, hijri_date, day, error_message, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month):
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.information.clear()
        self.prayers = prayers
        self.times = times
        self.day = day
        self.ramadan_start_greg = ramadan_start_greg
        self.greg_end_dt = greg_end_dt
        self.hijri_end_dt = hijri_end_dt
        self.current_greg_month = greg_month
        self.current_hijri_month = hijri_month
        if prayers and times:
            for i in range(len(prayers)):
                self.information.addItem(f"{prayers[i]}: {times[i]}")
            self.next_prayer_item = qt.QListWidgetItem("...")
            self.information.addItem(self.next_prayer_item)
        self.information.addItem("التاريخ الميلادي: " + gregorian_date)
        self.information.addItem("التاريخ الهجري: " + hijri_date)
        self.greg_month_countdown_item = qt.QListWidgetItem("...")
        self.information.addItem(self.greg_month_countdown_item)
        self.hijri_month_countdown_item = qt.QListWidgetItem("...")
        self.information.addItem(self.hijri_month_countdown_item)
        if self.ramadan_start_greg:
            self.ramadan_countdown_item = qt.QListWidgetItem("...")
            self.information.addItem(self.ramadan_countdown_item)
        if error_message:
            self.information.addItem(error_message)
        self.cache_countdown_item = qt.QListWidgetItem(get_cache_status_message())
        self.information.addItem(self.cache_countdown_item)
        if not self.timer.isActive() and prayers and times:
            self.timer.start(1000)
        self.update_countdowns()
        self.countdown_timer.start(1000)

    def on_prayer_times_error(self, error_message):
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.information.clear()
        self.information.addItem(error_message)
        self.countdown_timer.stop()
        try:
            gregorian_date, hijri_date, day, ramadan_start_greg, greg_end_dt, hijri_end_dt, greg_month, hijri_month = get_dates_info()
            self.information.addItem("التاريخ الميلادي: " + gregorian_date)
            self.information.addItem("التاريخ الهجري: " + hijri_date)
        except Exception as e:
            print(f"Handled exception: {e}")
        self.cache_countdown_item = qt.QListWidgetItem(get_cache_status_message())
        self.information.addItem(self.cache_countdown_item)
