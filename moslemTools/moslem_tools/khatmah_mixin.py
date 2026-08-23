import os
import datetime
import ujson as json
from settings import settings_handler
from .display_name import get_smart_display_name
import guiTools


class KhatmahMixin:
    def check_scheduled_khatmah_reminder(self):
        try:
            if settings_handler.get("khatmah_reminder", "enabled") != "True":
                return

            today = datetime.date.today()
            today_str = today.strftime("%Y-%m-%d")

            try:
                hour = int(settings_handler.get("khatmah_reminder", "hour") or 8)
            except Exception:
                hour = 8
            try:
                minute = int(settings_handler.get("khatmah_reminder", "minute") or 0)
            except Exception:
                minute = 0
            period = settings_handler.get("khatmah_reminder", "period") or "صباحاً"

            if period == "مساءً" and hour < 12:
                h24 = hour + 12
            elif period == "صباحاً" and hour == 12:
                h24 = 0
            else:
                h24 = hour

            time_key = f"{today_str}_{h24}:{minute}"
            last_reminded_time = settings_handler.get("khatmah_reminder", "last_reminded_time")
            if last_reminded_time == time_key:
                return

            now = datetime.datetime.now()
            rem_dt = datetime.datetime(today.year, today.month, today.day, h24, minute)

            if now >= rem_dt:
                khatmah_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "khatmah.json")
                if os.path.exists(khatmah_path):
                    with open(khatmah_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("is_completed", False):
                        return

                use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
                username1 = get_smart_display_name() if use_name_enabled else ""
                gender = settings_handler.get("g", "user_gender") or "ذكر"
                is_female = (gender == "أنثى")
                if not use_name_enabled:
                    msg = "تنبيه: لقد حان موعد الورد اليومي للختمة القرآنية."
                elif is_female:
                    msg = f"تنبيه: لقد حان موعد وردكِ اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد حان موعد وردكِ اليومي للختمة القرآنية."
                else:
                    msg = f"تنبيه: لقد حان موعد وردك اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد حان موعد وردك اليومي للختمة القرآنية."

                settings_handler.set("khatmah_reminder", "last_reminded_time", time_key)
                settings_handler.set("khatmah_reminder", "last_reminded_date", today_str)
                guiTools.SendNotification("تنبيه الورد القرآني", msg)
                guiTools.MessageBox.view(self, "تنبيه الورد القرآني", msg)
        except Exception as e:
            print(f"Error in scheduled khatmah reminder: {e}")
