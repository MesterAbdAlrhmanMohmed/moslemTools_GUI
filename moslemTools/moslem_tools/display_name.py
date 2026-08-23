import os, ctypes
from ctypes import wintypes
from settings import settings_handler


def get_smart_display_name():
    try:
        if settings_handler.get("g", "use_name_in_occasions") != "True":
            return ""
        name_type = settings_handler.get("g", "name_type") or "custom_name"
        if name_type == "custom_name":
            custom_val = settings_handler.get("g", "user_name").strip()
            if custom_val:
                return custom_val
        elif name_type == "os_username":
            try:
                username = os.getlogin()
                if username and username.strip():
                    return username.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
        elif name_type == "personal_name":
            try:
                GetUserNameExW = ctypes.windll.secur32.GetUserNameExW
                NameDisplay = 3
                size = wintypes.DWORD(256)
                buffer = ctypes.create_unicode_buffer(size.value)
                if GetUserNameExW(NameDisplay, buffer, ctypes.byref(size)) and buffer.value.strip():
                    return buffer.value.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
            try:
                username = os.getlogin()
                generic_names = ['dell', 'hp', 'lenovo', 'user', 'admin', 'administrator', 'pc', 'com']
                if username and username.lower().strip() not in generic_names:
                    return username.strip()
            except Exception as e:
                print(f"Handled exception: {e}")
    except Exception as e:
        print(f"Handled exception: {e}")
    return ""
