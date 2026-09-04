from datetime import datetime
from hijridate import Gregorian, Hijri


def get_dates_info():
    gregorian_months = ["يَنَايِر", "فِبْرَايِر", "مَارِس", "أَبْرِيل", "مَايُو", "يُونْيُو", "يُولْيُو", "أَغُسْطُس", "سِبْتَمْبَر", "أُكْتُوبَر", "نُوفَمْبَر", "دِيسَمْبَر"]
    hijri_months = ["مُحَرَّم", "صَفَر", "رَبِيع ٱلْأَوَّل", "رَبِيع ٱلثَّانِي", "جُمَادَىٰ ٱلْأُولَىٰ", "جُمَادَىٰ ٱلثَّانِيَة", "رَجَب", "شَعْبَان", "رَمَضَان", "شَوَّال", "ذُو ٱلْقَعْدَة", "ذُو ٱلْحِجَّة"]
    days_of_week = ["الإثنين", "الثلثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    now = datetime.now()
    day_name = days_of_week[now.weekday()]
    day = now.weekday()
    current_greg_month_name = gregorian_months[now.month - 1]
    gregorian_date = f"{day_name} - {now.day} {current_greg_month_name} {now.year}"
    today_hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    current_hijri_month_name = hijri_months[today_hijri.month - 1]
    hijri_date = f"{today_hijri.day} {current_hijri_month_name} {today_hijri.year}"
    ramadan_year = today_hijri.year
    if today_hijri.month >= 9:
        ramadan_year += 1
    ramadan_start_hijri = Hijri(ramadan_year, 9, 1)
    ramadan_start_greg = ramadan_start_hijri.to_gregorian()
    next_month_year = now.year
    next_month = now.month + 1
    if next_month > 12:
        next_month = 1
        next_month_year += 1
    greg_end_dt = datetime(next_month_year, next_month, 1)
    next_hijri_month = today_hijri.month + 1
    next_hijri_year = today_hijri.year
    if next_hijri_month > 12:
        next_hijri_month = 1
        next_hijri_year += 1
    first_day_next_hijri_obj = Hijri(next_hijri_year, next_hijri_month, 1)
    first_day_next_hijri_greg = first_day_next_hijri_obj.to_gregorian()
    hijri_end_dt = datetime(first_day_next_hijri_greg.year, first_day_next_hijri_greg.month, first_day_next_hijri_greg.day)
    return gregorian_date, hijri_date, day, ramadan_start_greg, greg_end_dt, hijri_end_dt, current_greg_month_name, current_hijri_month_name
