import os, requests, subprocess, shutil
import PyQt6.QtCore as qt2


class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    cancelled = qt2.pyqtSignal()
    network_error = qt2.pyqtSignal(str)

    def __init__(self, url, filepath):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.is_cancelled = False
        self.is_paused = False

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        while not self.is_cancelled:
            if self.is_paused:
                self.msleep(200)
                continue
            downloaded_size = os.path.getsize(self.filepath) if os.path.exists(self.filepath) else 0
            headers = {}
            if downloaded_size > 0:
                headers['Range'] = f'bytes={downloaded_size}-'
            try:
                response = requests.get(self.url, stream=True, timeout=15, headers=headers)
                if response.status_code in (200, 206):
                    header_len = response.headers.get('content-length')
                    content_range = response.headers.get('content-range')
                    if content_range:
                        total_size = int(content_range.split('/')[-1])
                    elif header_len:
                        total_size = downloaded_size + int(header_len)
                    else:
                        total_size = 0
                    mode = 'ab' if (downloaded_size > 0 and response.status_code == 206) else 'wb'
                    if mode == 'wb':
                        downloaded_size = 0
                    with open(self.filepath, mode) as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            while self.is_paused and not self.is_cancelled:
                                self.msleep(200)
                            if self.is_cancelled:
                                self.cancelled.emit()
                                return
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                if total_size > 0:
                                    progress_percent = min(100, int((downloaded_size / total_size) * 100))
                                else:
                                    progress_percent = min(99, int(downloaded_size / 3000))
                                self.progress.emit(progress_percent)
                    self.progress.emit(100)
                    self.finished.emit()
                    return
                else:
                    self.cancelled.emit()
                    return
            except (requests.exceptions.RequestException, Exception) as e:
                print(f"Error during download or file writing: {e}")
                self.is_paused = True
                self.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")


class MergeThread(qt2.QThread):
    finished = qt2.pyqtSignal(bool, str)

    def __init__(self, ffmpeg_path, input_files, output_file):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.input_files = input_files
        self.output_file = output_file
        self.process = None

    def run(self):
        list_filepath = os.path.join(os.path.dirname(self.output_file), "mergelist.txt")
        try:
            with open(list_filepath, 'w', encoding='utf-8') as f:
                for file_path in self.input_files:
                    safe_path = file_path.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")
            command = [self.ffmpeg_path,"-y","-f", "concat","-safe", "0","-i", list_filepath,"-ar", "44100","-ac", "2","-b:a", "192k",self.output_file]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = self.process.communicate()
            if self.process.returncode == 0:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"فشل الدمج أو تم إلغاؤه.\n{stderr}")
        except Exception as e:
            self.finished.emit(False, f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if os.path.exists(list_filepath):
                os.remove(list_filepath)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()


class SaveThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal(bool, str)
    cancelled = qt2.pyqtSignal()

    def __init__(self, merge_list, output_dir, parent=None):
        super().__init__(parent)
        self.merge_list = merge_list
        self.output_dir = output_dir
        self.is_cancelled = False
        self.total = len(merge_list)
        self.current = 0

    def run(self):
        try:
            for idx, item in enumerate(self.merge_list, start=1):
                if self.is_cancelled:
                    self.cancelled.emit()
                    return
                src = item["local_path"]
                if not os.path.exists(src):
                    self.finished.emit(False, f"الملف {item['filename']} غير موجود.")
                    return
                if self.total == 1:
                    dest = os.path.join(self.output_dir, item['filename'])
                else:
                    prefix = f"{idx:04d}_"
                    dest = os.path.join(self.output_dir, prefix + item['filename'])
                if src != dest:
                    if os.path.basename(src).startswith("temp_") and os.path.normpath(os.path.dirname(src)) == os.path.normpath(self.output_dir):
                        shutil.move(src, dest)
                    else:
                        shutil.copy2(src, dest)
                self.current = idx
                progress = int((idx / self.total) * 100)
                self.progress.emit(progress)
            msg = "تم حفظ الآية بنجاح." if self.total == 1 else "تم حفظ الآيات بنجاح."
            self.finished.emit(True, msg)
        except Exception as e:
            self.finished.emit(False, f"خطأ أثناء الحفظ: {str(e)}")

    def cancel(self):
        self.is_cancelled = True
