import traceback, os, ctypes, datetime

def log_error_to_file(error_msg):
    try:
        app_dir = os.path.join(os.getenv('appdata'), "moslemTools_GUI")
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        log_file = os.path.join(app_dir, "error.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_count = 0
        file_exists = os.path.exists(log_file) and os.path.getsize(log_file) > 0
        if file_exists:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    import re
                    matches = re.findall(r'^الخطأ\s+(\d+):', content, re.MULTILINE)
                    if matches:
                        error_count = max(int(m) for m in matches)
                    else:
                        error_count = len(re.findall(r'^\d{4}-\d{2}-\d{2}', content, re.MULTILINE))
            except Exception:
                error_count = 0

        current_error_num = error_count + 1

        with open(log_file, "a", encoding="utf-8") as f:
            if file_exists:
                f.write(f"\n\n\nالخطأ {current_error_num}:\n[{timestamp}]\n{error_msg}\n")
            else:
                f.write(f"الخطأ {current_error_num}:\n[{timestamp}]\n{error_msg}\n")
    except Exception:
        pass

def my_excepthook(exctype, value, tb):
    tb_list = traceback.extract_tb(tb)
    error_message = ""
    for tb in tb_list:
        file_name = os.path.basename(tb.filename)
        line_number = tb.lineno
        code = tb.line
        error_message += f"\nFile: {file_name}\nLine: {line_number}\nCode: {code}\n"
    error_message += f"\n{exctype.__name__}: {value}"
    log_error_to_file(error_message)
    ctypes.windll.user32.MessageBoxW(None, error_message, "Error", 0x10)
