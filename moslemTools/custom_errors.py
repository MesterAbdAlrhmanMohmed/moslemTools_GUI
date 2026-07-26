import traceback, os, ctypes, datetime

def log_error_to_file(error_msg):
    try:
        app_dir = os.path.join(os.getenv('appdata'), "moslemTools_GUI")
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        log_file = os.path.join(app_dir, "error.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}]\n{error_msg}\n{'-'*50}\n")
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
