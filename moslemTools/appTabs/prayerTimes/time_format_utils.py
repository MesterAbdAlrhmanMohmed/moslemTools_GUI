def format_arabic_time_unit(number, units):
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


def format_timedelta_arabic(td):
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    days = total_seconds // (24 * 3600)
    total_seconds = total_seconds % (24 * 3600)
    hours = total_seconds // 3600
    total_seconds = total_seconds % 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    day_units = {'singular': 'يوم', 'dual': 'يومين', 'plural': 'أيام', 'singular_acc': 'يوماً'}
    hour_units = {'singular': 'ساعة', 'dual': 'ساعتين', 'plural': 'ساعات', 'singular_acc': 'ساعة'}
    minute_units = {'singular': 'دقيقة', 'dual': 'دقيقتين', 'plural': 'دقائق', 'singular_acc': 'دقيقة'}
    second_units = {'singular': 'ثانية', 'dual': 'ثانيتين', 'plural': 'ثواني', 'singular_acc': 'ثانية'}
    d_str = format_arabic_time_unit(days, day_units)
    h_str = format_arabic_time_unit(hours, hour_units)
    m_str = format_arabic_time_unit(minutes, minute_units)
    s_str = format_arabic_time_unit(seconds, second_units)
    parts = [p for p in [d_str, h_str, m_str, s_str] if p]
    return " و ".join(parts) if parts else "لحظات"
