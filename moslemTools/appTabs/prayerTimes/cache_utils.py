import os
import calendar
from datetime import datetime, date
import ujson as json
from settings import settings_handler


def get_cache_file_path():
    return os.path.join(os.getenv('appdata'), settings_handler.appName, "prayer_times_cache.json")


def get_remaining_months_and_days(current_date, end_date):
    if current_date > end_date:
        return 0, 0
    temp_date = current_date
    months = 0
    while True:
        year = temp_date.year
        month = temp_date.month + 1
        if month > 12:
            month = 1
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(temp_date.day, max_day)
        next_month_date = date(year, month, day)
        if next_month_date <= end_date:
            months += 1
            temp_date = next_month_date
        else:
            break
    days = (end_date - temp_date).days
    return months, days


def format_arabic_remaining_time(months, days):
    def format_months(m):
        if m == 0:
            return ""
        elif m == 1:
            return "شهر واحد"
        elif m == 2:
            return "شهران"
        elif 3 <= m <= 10:
            return f"{m} أشهر"
        else:
            return f"{m} شهراً"

    def format_days(d):
        if d == 0:
            return ""
        elif d == 1:
            return "يوم واحد"
        elif d == 2:
            return "يومان"
        elif 3 <= d <= 10:
            return f"{d} أيام"
        else:
            return f"{d} يوماً"

    m_str = format_months(months)
    d_str = format_days(days)

    if m_str and d_str:
        combined = f"{m_str} و {d_str}"
    elif m_str:
        combined = m_str
    elif d_str:
        combined = d_str
    else:
        return "متبقي أقل من يوم لإعادة تحميل مواقيت الصلاة باستخدام الإنترنت"

    return f"متبقي {combined} لإعادة تحميل مواقيت الصلاة باستخدام الإنترنت"


def get_cache_status_message():
    cache_file = get_cache_file_path()
    if not os.path.exists(cache_file):
        return "لم يتم حفظ مواقيت الصلاة بعد، اضغط F5 لتحميل مواقيت العام بالإنترنت"
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        cache_year = cache_data.get("year", datetime.now().year)
        end_date = date(cache_year, 12, 31)
        today = datetime.now().date()
        if today > end_date:
            return "انتهت صلاحية مواقيت الصلاة المخزنة، يرجى الاتصال بالإنترنت والضغط على F5 للتحديث"
        else:
            months, days = get_remaining_months_and_days(today, end_date)
            return format_arabic_remaining_time(months, days)
    except Exception:
        return ""
