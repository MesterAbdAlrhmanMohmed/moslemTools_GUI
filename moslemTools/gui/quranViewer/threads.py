import time, winsound, pyperclip, os, re, requests, subprocess, shutil
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools, settings, functions


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
                    content_range = response.headers.get('content-range')
                    if content_range:
                        total_size = int(content_range.split('/')[-1])
                    elif 'content-length' in response.headers:
                        total_size = downloaded_size + int(response.headers['content-length'])
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
                                    progress_percent = int((downloaded_size / total_size) * 100)
                                    self.progress.emit(progress_percent)
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
            command = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_filepath, "-ar", "44100", "-ac", "2", "-b:a", "192k", self.output_file]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = self.process.communicate()
            if self.process.returncode == 0:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"فشل العملية أو تم إلغاؤه.\n{stderr}")
        except Exception as e:
            self.finished.emit(False, f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if os.path.exists(list_filepath):
                os.remove(list_filepath)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()


class PreMergeCheckThread(qt2.QThread):
    finished = qt2.pyqtSignal(list, list)
    error = qt2.pyqtSignal(str)

    def __init__(self, start_ayah_index, end_ayah_index, quran_text, category, type_index, current_reciter_index, reciters_data):
        super().__init__()
        self.start_ayah_index = start_ayah_index
        self.end_ayah_index = end_ayah_index
        self.quran_text = quran_text
        self.category = category
        self.type_index = type_index
        self.current_reciter_index = current_reciter_index
        self.reciters_data = reciters_data

    def _get_current_reciter_name(self):
        return list(self.reciters_data.keys())[self.current_reciter_index]

    def _create_ayah_filename(self, ayah_text):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text, self.category, self.type_index)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            return f"{surah_str}{ayah_str}.mp3"
        except:
            return None

    def run(self):
        try:
            lines = self.quran_text.split("\n")
            reciter_name = self._get_current_reciter_name()
            reciter_url_base = self.reciters_data[reciter_name]
            reciter_folder_name = reciter_url_base.split("/")[-3]
            reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
            merge_list = []
            ayahs_to_download = []
            for i in range(self.start_ayah_index, self.end_ayah_index):
                if i >= len(lines): continue
                ayah_text = lines[i]
                ayah_filename = self._create_ayah_filename(ayah_text)
                if not ayah_filename: continue
                local_path = os.path.join(reciter_local_path_base, ayah_filename)
                ayah_info = {"index": i, "filename": ayah_filename, "url": reciter_url_base + ayah_filename, "local_path": local_path}
                merge_list.append(ayah_info)
                if not os.path.exists(local_path):
                    ayahs_to_download.append(ayah_info)
            self.finished.emit(merge_list, ayahs_to_download)
        except Exception as e:
            self.error.emit(f"حدث خطأ أثناء التحضير للعملية: {str(e)}")


class SaveThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal(bool, str)

    def __init__(self, merge_list, output_dir, numbering=True):
        super().__init__()
        self.merge_list = merge_list
        self.output_dir = output_dir
        self.numbering = numbering
        self.cancelled = False

    def run(self):
        total = len(self.merge_list)
        for idx, item in enumerate(self.merge_list):
            if self.cancelled:
                self.finished.emit(False, "تم إلغاء العملية من قبل المستخدم.")
                return
            if self.numbering and total > 1:
                new_name = f"{idx+1:04d}_{item['filename']}"
            else:
                new_name = item['filename']
            dest_path = os.path.join(self.output_dir, new_name)
            source_path = item["local_path"]
            if not os.path.exists(source_path):
                try:
                    response = requests.get(item["url"], stream=True)
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    with open(dest_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            if self.cancelled:
                                f.close()
                                os.remove(dest_path)
                                self.finished.emit(False, "تم إلغاء العملية.")
                                return
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = int((downloaded / total_size) * 100)
                                    self.progress.emit(int((idx + downloaded/total_size) * 100 / total))
                except Exception as e:
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    self.finished.emit(False, f"فشل تحميل الآية {item['filename']}: {str(e)}")
                    return
            else:
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception as e:
                    self.finished.emit(False, f"فشل نسخ الآية {item['filename']}: {str(e)}")
                    return
            self.progress.emit(int((idx+1) * 100 / total))
        msg = "تم حفظ الآية بنجاح." if total == 1 else "تم حفظ الآيات بنجاح."
        self.finished.emit(True, msg)

    def cancel(self):
        self.cancelled = True


class SajdaGoToDialog(qt.QDialog):
    def __init__(self, parent, title, label, items, selected_index):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(250, 120)
        self.selected_index = -1
        layout = qt.QVBoxLayout(self)
        self.label = qt.QLabel(label)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.combo = qt.QComboBox()
        self.combo.setAccessibleName(label)
        self.combo.addItems(items)
        if selected_index != -1:
            self.combo.setCurrentIndex(selected_index)
        self.combo.setFixedHeight(40)
        layout.addWidget(self.combo)
        buttons = qt.QHBoxLayout()
        self.go_button = guiTools.QPushButton("ذهاب")
        self.go_button.setStyleSheet("background-color:#006400;color:white;padding:5px;")
        self.go_button.clicked.connect(self.on_go)
        self.go_button.setFixedHeight(40)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(40)
        buttons.addWidget(self.go_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

    def on_go(self):
        self.selected_index = self.combo.currentIndex()
        self.accept()


class AsbabAlnozoleGoToDialog(qt.QDialog):
    def __init__(self, parent, title, label, items, selected_index):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(250, 120)
        self.selected_index = -1
        layout = qt.QVBoxLayout(self)
        self.label = qt.QLabel(label)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.combo = qt.QComboBox()
        self.combo.setAccessibleName(label)
        self.combo.addItems(items)
        if selected_index != -1:
            self.combo.setCurrentIndex(selected_index)
        self.combo.setFixedHeight(40)
        layout.addWidget(self.combo)
        buttons = qt.QHBoxLayout()
        self.go_button = guiTools.QPushButton("ذهاب")
        self.go_button.setStyleSheet("background-color:#006400;color:white;padding:5px;")
        self.go_button.clicked.connect(self.on_go)
        self.go_button.setFixedHeight(40)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(40)
        buttons.addWidget(self.go_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

    def on_go(self):
        self.selected_index = self.combo.currentIndex()
        self.accept()


class SajdaFinderThread(qt2.QThread):
    finished = qt2.pyqtSignal(list)

    def __init__(self, ayah_list, category, category_type):
        super().__init__()
        self.ayah_list = ayah_list
        self.category = category
        self.category_type = category_type

    def run(self):
        sajda_verses = []
        for index, ayah_text in enumerate(self.ayah_list):
            try:
                if not ayah_text.strip(): continue
                num, _, juz_info, _, _ = functions.quranJsonControl.getAyah(ayah_text, self.category, self.category_type)
                if juz_info[3]:
                    sajda_verses.append({"index": index, "surah": juz_info[1], "numberInSurah": num})
            except:
                continue
        self.finished.emit(sajda_verses)


class AsbabAlnozoleFinderThread(qt2.QThread):
    finished = qt2.pyqtSignal(list)

    def __init__(self, ayah_list, category, category_type):
        super().__init__()
        self.ayah_list = ayah_list
        self.category = category
        self.category_type = category_type

    def run(self):
        asbab_verses = []
        for index, ayah_text in enumerate(self.ayah_list):
            try:
                if not ayah_text.strip(): continue
                num, _, juz_info, _, _ = functions.quranJsonControl.getAyah(ayah_text, self.category, self.category_type)
                if juz_info[4]:
                    asbab_verses.append({"index": index, "surah": juz_info[1], "numberInSurah": num})
            except:
                continue
        self.finished.emit(asbab_verses)


class SearchModeDialog(qt.QDialog):
    def __init__(self, parent=None, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True):
        super().__init__(parent)
        self.setWindowTitle("إعدادات نمط البحث")
        self.setFixedSize(350, 200)
        self.initial_ignore_tashkeel = ignore_tashkeel
        self.initial_ignore_hamza = ignore_hamza
        self.initial_ignore_symbols = ignore_symbols
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols
        self.init_ui()

    def init_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        self.tashkeel_checkbox = qt.QCheckBox("تجاهل التشكيل")
        self.tashkeel_checkbox.setChecked(self.initial_ignore_tashkeel)
        self.tashkeel_checkbox.setFont(bold_font)
        self.tashkeel_checkbox.stateChanged.connect(self._set_ignore_tashkeel)
        layout.addWidget(self.tashkeel_checkbox)
        self.hamza_checkbox = qt.QCheckBox("تجاهل الهمزات")
        self.hamza_checkbox.setChecked(self.initial_ignore_hamza)
        self.hamza_checkbox.setFont(bold_font)
        self.hamza_checkbox.stateChanged.connect(self._set_ignore_hamza)
        layout.addWidget(self.hamza_checkbox)
        self.symbols_checkbox = qt.QCheckBox("تجاهل الرموز والعلامات")
        self.symbols_checkbox.setChecked(self.initial_ignore_symbols)
        self.symbols_checkbox.setFont(bold_font)
        self.symbols_checkbox.stateChanged.connect(self._set_ignore_symbols)
        layout.addWidget(self.symbols_checkbox)
        layout.addStretch(1)
        buttons_layout = qt.QHBoxLayout()
        self.apply_button = guiTools.QPushButton("تطبيق التغييرات")
        self.apply_button.setDefault(True)
        self.apply_button.setObjectName("applySearchModeChangesButton")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setAutoDefault(False)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)

    def _set_ignore_tashkeel(self, state):
        self.ignore_tashkeel = bool(state)

    def _set_ignore_hamza(self, state):
        self.ignore_hamza = bool(state)

    def _set_ignore_symbols(self, state):
        self.ignore_symbols = bool(state)

    def get_settings(self):
        return {"ignore_tashkeel": self.ignore_tashkeel, "ignore_hamza": self.ignore_hamza, "ignore_symbols": self.ignore_symbols}


class GoToCategoryDialog(qt.QDialog):
    def __init__(self,parent,title:str,label:str,items:list,selected_index:int):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(250,120)
        self.selected_item=None
        layout=qt.QVBoxLayout(self)
        self.label=qt.QLabel(label)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.list_widget=qt.QComboBox()
        self.list_widget.addItems(items)
        self.list_widget.setCurrentIndex(selected_index)
        self.list_widget.setAccessibleName(label)
        self.list_widget.setFixedHeight(40)
        layout.addWidget(self.list_widget)
        self.ok_button=guiTools.QPushButton("موافق")
        self.ok_button.setStyleSheet("background-color:#006400;color:white;padding:5px;")
        self.ok_button.clicked.connect(self.on_ok)
        self.ok_button.setFixedHeight(40)
        self.cancel_button=guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(40)
        buttons_layout=qt.QHBoxLayout()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def on_ok(self):
        if self.list_widget.currentText():
            self.selected_item=self.list_widget.currentText()
            self.accept()
    @staticmethod

    def getItem(parent,title:str,label:str,items:list,selected_index:int):
        dialog=GoToCategoryDialog(parent,title,label,items,selected_index)
        result=dialog.exec()
        if result==qt.QDialog.DialogCode.Accepted:
            return dialog.selected_item,True
        return "",False
