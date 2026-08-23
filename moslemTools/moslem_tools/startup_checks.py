import os, sys, datetime, random
import ujson as json
import update, guiTools
from settings import settings_handler, app
from .display_name import get_smart_display_name


def check_missed_khatmah_alert(parent_window=None):
    try:
        if settings_handler.get("khatmah_reminder", "enabled") != "True":
            return False
        if settings_handler.get("khatmah_reminder", "missed_alert") == "False":
            return False

        khatmah_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "khatmah.json")
        if not os.path.exists(khatmah_path):
            data = {
                "has_khatmah": True,
                "target_days": 30,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": 20,
                "completed_pages": 0,
                "is_completed": False
            }
        else:
            with open(khatmah_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        if data.get("is_completed", False):
            return False

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

        missed_key = f"{today_str}_{h24}:{minute}"
        if (data.get("last_missed_alert_key") == missed_key or 
            settings_handler.get("khatmah_reminder", "last_reminded_time") == missed_key):
            return False

        start_date_str = data.get("start_date", today_str)
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except Exception:
            start_date = today

        days_passed = max(0, (today - start_date).days)
        daily_pages = data.get("daily_pages", 20)
        completed_pages = data.get("completed_pages", 0)

        now = datetime.datetime.now()
        rem_dt = datetime.datetime(today.year, today.month, today.day, h24, minute)

        if days_passed > 0 or now >= rem_dt:
            expected_pages = min(604, (days_passed + 1) * daily_pages)
        else:
            expected_pages = min(604, days_passed * daily_pages)

        if completed_pages < expected_pages:
            use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
            username1 = get_smart_display_name() if use_name_enabled else ""
            gender = settings_handler.get("g", "user_gender") or "ذكر"
            is_female = (gender == "أنثى")
            if not use_name_enabled:
                msg = "تنبيه: لقد فاتك موعد الورد اليومي للختمة القرآنية."
            elif is_female:
                msg = f"تنبيه: لقد فاتكِ موعد وردكِ اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد فاتكِ موعد وردكِ اليومي للختمة القرآنية."
            else:
                msg = f"تنبيه: لقد فاتك موعد وردك اليومي للختمة القرآنية يا {username1}." if username1 else "تنبيه: لقد فاتك موعد وردك اليومي للختمة القرآنية."

            guiTools.MessageBox.view(parent_window, "تنبيه فوات الورد القرآني", msg)
            data["last_missed_alert_key"] = missed_key
            data["last_missed_alert_date"] = today_str
            settings_handler.set("khatmah_reminder", "last_reminded_time", missed_key)
            settings_handler.set("khatmah_reminder", "last_reminded_date", today_str)
            try:
                with open(khatmah_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error updating khatmah json: {e}")
            return True
        return False
    except Exception as e:
        print(f"Error checking missed khatmah alert: {e}")
        return False


def show_random_quote_message(parent=None):
    try:
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", "json", "QuotesMessages.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_message = random.choice(data)
        guiTools.TextViewer(parent, "رسالة لك", random_message).exec()
        return True
    except Exception as e:
        print(f"Error showing random quote message: {e}")
        return False


def run_startup_checks():
    try:
        check_missed_khatmah_alert(None)
    except Exception as e:
        print(f"Error in khatmah startup alert: {e}")

    shown = False
    if settings_handler.get("update", "autoCheck") == "True":
        try:
            shown = update.check(None, message=False)
        except Exception as e:
            print(f"Error checking update at startup: {e}")
    if shown: return True
    try:
        shown = guiTools.messageHandler.check(None)
    except Exception as e:
        print(f"Error checking messages at startup: {e}")
    if shown: return True

    if settings_handler.get("g", "randomMessageAtStartup") == "True":
        try:
            show_random_quote_message(None)
            return True
        except Exception as e:
            print(f"Error showing quote message at startup: {e}")

    return False
