import os
import shutil
import subprocess
import requests
import PyQt6.QtCore as qt2
import functions
from settings.app import appName


class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    cancelled = qt2.pyqtSignal()

    def __init__(self, url, filepath):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.is_cancelled = False

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            with open(self.filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if self.is_cancelled:
                        self.cancelled.emit()
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percent)
            self.finished.emit()
        except Exception as e:
            print(f"Error during download or file writing: {e}")
            self.cancelled.emit()

    def cancel(self):
        self.is_cancelled = True


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
            command = [
                self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_filepath,
                "-ar", "44100", "-ac", "2", "-b:a", "192k", self.output_file
            ]
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


class PreMergeCheckThread(qt2.QThread):
    finished = qt2.pyqtSignal(list, list, str, str)
    error = qt2.pyqtSignal(str)

    def __init__(self, all_ayahs_text, current_reciter, reciters_data):
        super().__init__()
        self.all_ayahs_text = all_ayahs_text
        self.current_reciter = current_reciter
        self.reciters_data = reciters_data

    def _create_ayah_filename(self, ayah_text):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            return f"{surah_str}{ayah_str}.mp3"
        except:
            return None

    def run(self):
        try:
            reciter_name = list(self.reciters_data.keys())[self.current_reciter]
            reciter_url_base = self.reciters_data[reciter_name]
            reciter_folder_name = reciter_url_base.split("/")[-3]
            reciter_local_path_base = os.path.join(os.getenv('appdata'), appName, "reciters", reciter_folder_name)
            merge_list = []
            ayahs_to_download = []
            for ayah_text in self.all_ayahs_text:
                ayah_filename = self._create_ayah_filename(ayah_text)
                if not ayah_filename: continue
                local_path = os.path.join(reciter_local_path_base, ayah_filename)
                ayah_info = {"filename": ayah_filename, "url": reciter_url_base + ayah_filename, "local_path": local_path}
                merge_list.append(ayah_info)
                if not os.path.exists(local_path):
                    ayahs_to_download.append(ayah_info)
            self.finished.emit(merge_list, ayahs_to_download, reciter_name, reciter_local_path_base)
        except Exception as e:
            self.error.emit(f"حدث خطأ أثناء التحضير للدمج: {str(e)}")


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
                prefix = f"{idx:04d}_" if self.total > 1 else ""
                dest = os.path.join(self.output_dir, prefix + item["filename"])
                src = item["local_path"]
                if os.path.exists(src):
                    shutil.copy2(src, dest)
                elif not os.path.exists(dest):
                    self.finished.emit(False, f"الملف {item['filename']} غير موجود.")
                    return
                self.current = idx
                progress = int((idx / self.total) * 100)
                self.progress.emit(progress)
            msg = "تم حفظ الآية بنجاح." if self.total == 1 else "تم حفظ الآيات بنجاح."
            self.finished.emit(True, msg)
        except Exception as e:
            self.finished.emit(False, f"خطأ أثناء الحفظ: {str(e)}")

    def cancel(self):
        self.is_cancelled = True
