import os
import subprocess
import shutil
import requests
import PyQt6.QtCore as qt2
import custom_errors

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
                os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
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
                src_path = item.get("src", item.get("local_path", ""))
                src = os.path.abspath(src_path)
                dest_name = item.get("dest_name", item.get("filename", os.path.basename(src)))
                dest = os.path.join(self.output_dir, dest_name)
                if os.path.exists(src):
                    shutil.copy2(src, dest)
                progress = int((idx / self.total) * 100) if self.total > 0 else 100
                self.progress.emit(progress)
            msg = "تم حفظ صوت البيت بنجاح." if self.total == 1 else "تم حفظ الأبيات بنجاح."
            self.finished.emit(True, msg)
        except Exception as e:
            custom_errors.handle_exception(e)
            self.finished.emit(False, f"خطأ أثناء الحفظ: {str(e)}")

    def cancel(self):
        self.is_cancelled = True


class PreMergeCheckThread(qt2.QThread):
    finished = qt2.pyqtSignal(list, list)
    error = qt2.pyqtSignal(str)

    def __init__(self, verses_slice, reciter_slug, matn_slug, matn_name, reciter_type="N"):
        super().__init__()
        self.verses_slice = verses_slice
        self.reciter_slug = reciter_slug
        self.matn_slug = matn_slug
        self.matn_name = matn_name
        self.reciter_type = reciter_type

    def run(self):
        try:
            merge_list = []
            verses_to_download = []
            from functions.moton_data import get_moton_bayt_audio_path, get_moton_appdata_dir, get_moton_continuous_audio_path

            if self.reciter_type != "N":
                local_path = get_moton_continuous_audio_path(self.reciter_slug, self.matn_slug)
                if not local_path:
                    local_path = os.path.join(get_moton_appdata_dir(self.reciter_slug), f"{self.matn_slug}.mp3")
                url = f"https://huggingface.co/datasets/alcoder01/DataMoton/resolve/main/Qasaed/{self.reciter_slug}/{self.matn_slug}.mp3"
                item_info = {
                    "index": 0,
                    "filename": f"{self.matn_name}.mp3",
                    "url": url,
                    "local_path": local_path
                }
                merge_list.append(item_info)
                if not os.path.exists(local_path):
                    verses_to_download.append(item_info)
            else:
                total = len(self.verses_slice)
                for idx, v in enumerate(self.verses_slice):
                    b_num = v.get("global_num")
                    if b_num is None:
                        continue
                    filename = f"{b_num:04d}_{self.matn_name}_بيت_{b_num}.mp3" if total > 1 else f"{self.matn_name}_بيت_{b_num}.mp3"
                    local_path = get_moton_bayt_audio_path(self.reciter_slug, self.matn_slug, b_num)
                    if not local_path:
                        local_path = os.path.join(get_moton_appdata_dir(self.reciter_slug, self.matn_slug), f"{b_num}.mp3")
                    url = f"https://huggingface.co/datasets/alcoder01/DataMoton/resolve/main/Qasaed/{self.reciter_slug}/{self.matn_slug}/{b_num}.mp3"
                    item_info = {
                        "index": idx,
                        "global_num": b_num,
                        "filename": filename,
                        "url": url,
                        "local_path": local_path
                    }
                    merge_list.append(item_info)
                    if not os.path.exists(local_path):
                        verses_to_download.append(item_info)

            self.finished.emit(merge_list, verses_to_download)
        except Exception as e:
            self.error.emit(f"حدث خطأ أثناء التحضير للعملية: {str(e)}")

