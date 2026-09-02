import os
import subprocess
import shutil
import PyQt6.QtCore as qt2
import custom_errors

class MergeThread(qt2.QThread):
    finished = qt2.pyqtSignal(bool, str)

    def __init__(self, ffmpeg_path, input_files, output_file):
        super().__init__()
        self.ffmpeg_path = os.path.abspath(ffmpeg_path)
        self.input_files = input_files
        self.output_file = os.path.abspath(output_file)
        self.process = None

    def run(self):
        list_filepath = os.path.join(os.path.dirname(self.output_file), "mergelist.txt")
        try:
            with open(list_filepath, "w", encoding="utf-8") as f:
                for file_path in self.input_files:
                    safe_path = os.path.abspath(file_path).replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
            command = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_filepath, "-ar", "44100", "-ac", "2", "-b:a", "192k", self.output_file]
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
            stdout, stderr = self.process.communicate()
            if self.process.returncode == 0:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"فشل الدمج:\n{stderr}")
        except Exception as e:
            custom_errors.handle_exception(e)
            self.finished.emit(False, f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if os.path.exists(list_filepath):
                try:
                    os.remove(list_filepath)
                except:
                    pass

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()

class SaveThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal(bool, str)
    cancelled = qt2.pyqtSignal()

    def __init__(self, file_list, output_dir, parent=None):
        super().__init__(parent)
        self.file_list = file_list
        self.output_dir = os.path.abspath(output_dir)
        self.is_cancelled = False
        self.total = len(file_list)

    def run(self):
        try:
            for idx, item in enumerate(self.file_list, start=1):
                if self.is_cancelled:
                    self.cancelled.emit()
                    return
                src = os.path.abspath(item["src"])
                dest = os.path.join(self.output_dir, item["dest_name"])
                if os.path.exists(src):
                    shutil.copy2(src, dest)
                progress = int((idx / self.total) * 100) if self.total > 0 else 100
                self.progress.emit(progress)
            self.finished.emit(True, "تم حفظ الملفات بنجاح.")
        except Exception as e:
            custom_errors.handle_exception(e)
            self.finished.emit(False, f"خطأ أثناء الحفظ: {str(e)}")

    def cancel(self):
        self.is_cancelled = True
