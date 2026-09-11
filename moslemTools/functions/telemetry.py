import os, sys, threading,requests
from settings import settings_handler, app

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwduy_YfbzAfpoTY0A_xXRogIOXbCiuILtCo4YT3kLVJH9p_9YQ9Spw5V8FI9VJKOxC/exec"


def get_unique_device_id():
    """الحصول على معرّف فريد وثابت للجهاز من ريجستري الويندوز لمنع التكرار"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        if guid and str(guid).strip():
            return str(guid).strip()
    except Exception:
        pass

    try:
        import uuid
        return f"UUID_{uuid.getnode()}"
    except Exception:
        return "UNKNOWN_DEVICE"


def get_device_username():
    """الحصول على اسم مستخدم الويندوز للجهاز واسم المستخدم المخصص"""
    os_user = ""
    try:
        import getpass
        os_user = os.environ.get("USERNAME") or getpass.getuser() or os.getlogin()
        if os_user:
            os_user = os_user.strip()
    except Exception:
        pass

    custom_name = ""
    try:
        val = settings_handler.get("g", "user_name")
        if val and val.strip() and "\ufffd" not in val and "?" not in val:
            custom_name = val.strip()
    except Exception:
        pass

    if os_user and custom_name and custom_name != os_user:
        return f"{os_user} ({custom_name})"
    elif os_user:
        return os_user
    elif custom_name:
        return custom_name
    return "Unknown"


def _send_telemetry_request():
    """إرسال بيانات الجهاز إلى Google Sheets في الخلفية"""
    try:
        version_str = str(getattr(app, "version", "unknown"))
        payload = {
            "device_id": get_unique_device_id(),
            "username": get_device_username(),
            "version": version_str
        }

        requests.post(
            WEB_APP_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
    except Exception:
        # صامت تماماً لضمان عدم تأثر البرنامج نهائياً في حال انقطاع النت
        pass


def record_device_async():
    """تشغيل عملية التسجيل في ثريد منفصل في الخلفية عند بدء تشغيل البرنامج"""
    try:
        thread = threading.Thread(target=_send_telemetry_request, name="TelemetryThread", daemon=True)
        thread.start()
    except Exception:
        pass

# https://docs.google.com/spreadsheets/d/1EZlpMOY-EcLK7Wutu7-vNY1OnZ3wq5GMnM9ikK6ZknQ/edit?gid=0#gid=0