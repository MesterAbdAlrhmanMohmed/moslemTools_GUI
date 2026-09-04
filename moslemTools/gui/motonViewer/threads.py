import os
import subprocess
import shutil
import requests
import ujson as json
import PyQt6.QtCore as qt2
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import custom_errors
import guiTools
import settings

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


class GoToBaytDialog(qt.QDialog):
    def __init__(self, parent, title, label, value, min_val, max_val, show_play_checkbox=True):
        super().__init__(parent)
        self.show_play_checkbox = show_play_checkbox
        self.setWindowTitle(title)
        if self.show_play_checkbox:
            self.setMinimumSize(310, 200)
            self.resize(330, 210)
        else:
            self.setMinimumSize(310, 150)
            self.resize(330, 160)
        self.config_path = os.path.join(os.getenv('appdata'), settings.app.appName if hasattr(settings, 'app') and hasattr(settings.app, 'appName') else "moslemTools", "goto_bayt.json")
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 12, 15, 12)
        self.label = qt.QLabel(label)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.spin_box = qt.QSpinBox()
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setValue(value)
        self.spin_box.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.spin_box.setAccessibleName(label)
        self.spin_box.setMinimumHeight(32)
        layout.addWidget(self.spin_box)
        layout.addSpacing(4)
        if self.show_play_checkbox:
            self.play_checkbox = qt.QCheckBox("تشغيل البيت عند الذهاب إليه")
            self.play_checkbox.setAccessibleName("تشغيل البيت عند الذهاب إليه")
            self.play_checkbox.setChecked(self.load_setting())
            layout.addWidget(self.play_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(6)
        else:
            self.play_checkbox = None
        buttons_layout = qt.QHBoxLayout()
        self.go_button = guiTools.QPushButton("موافق")
        self.go_button.setStyleSheet("background-color:#006400;color:white;padding:5px;")
        self.go_button.clicked.connect(self.on_go)
        self.go_button.setMinimumHeight(32)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(32)
        buttons_layout.addWidget(self.go_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
        qt1.QShortcut("Return", self).activated.connect(self.on_go)
        qt1.QShortcut("Enter", self).activated.connect(self.on_go)

    def load_setting(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("play_on_goto", False)
        except Exception:
            pass
        return False

    def save_setting(self, play_state):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"play_on_goto": play_state}, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def on_go(self):
        if self.play_checkbox is not None:
            self.save_setting(self.play_checkbox.isChecked())
        self.accept()

    def get_values(self):
        play_state = self.play_checkbox.isChecked() if self.play_checkbox is not None else True
        return self.spin_box.value(), play_state

class SearchModeDialog(qt.QDialog):
    def __init__(self, parent=None, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True):
        super().__init__(parent)
        self.setWindowTitle("إعدادات نمط البحث")
        self.setMinimumSize(300, 180)
        self.resize(350, 200)
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
        return {
            "ignore_tashkeel": self.tashkeel_checkbox.isChecked(),
            "ignore_hamza": self.hamza_checkbox.isChecked(),
            "ignore_symbols": self.symbols_checkbox.isChecked()
        }

class ChangeMotonReciterDialog(qt.QDialog):
    def __init__(self, parent=None, reciters=None, current_slug=""):
        super().__init__(parent)
        self.setWindowTitle("اختيار القارئ")
        self.resize(360, 420)
        self.reciters = reciters or []
        self.current_slug = current_slug
        self.selected_reciter = None
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        label = qt.QLabel("اختر القارئ المطلوب:")
        label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)
        self.list_widget = guiTools.QListWidget()
        self.list_widget.setSpacing(5)
        self.list_widget.setStyleSheet("QListWidget::item { padding: 6px; }")
        layout.addWidget(self.list_widget)
        selected_row = 0
        for idx, (r_ar, r_slug, r_type) in enumerate(self.reciters):
            self.list_widget.addItem(r_ar)
            if r_slug == self.current_slug:
                selected_row = idx
        if self.reciters:
            self.list_widget.setCurrentRow(selected_row)
        self.list_widget.itemClicked.connect(self.on_select)
        self.list_widget.itemActivated.connect(self.on_select)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)

    def on_select(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.reciters):
            self.selected_reciter = self.reciters[row]
            self.accept()

    def get_reciter(self):
        return self.selected_reciter

class GoToCategoryDialog(qt.QDialog):
    def __init__(self, parent, title: str, label: str, items: list, selected_index: int):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(250, 140)
        self.resize(300, 150)
        self.selected_item = None
        layout = qt.QVBoxLayout(self)
        self.label = qt.QLabel(label)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.list_widget = qt.QComboBox()
        self.list_widget.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.list_widget.addItems(items)
        if 0 <= selected_index < len(items):
            self.list_widget.setCurrentIndex(selected_index)
        self.list_widget.setAccessibleName(label)
        self.list_widget.setMinimumHeight(35)
        layout.addWidget(self.list_widget)
        self.ok_button = guiTools.QPushButton("موافق")
        self.ok_button.setStyleSheet("background-color:#006400;color:white;padding:5px;")
        self.ok_button.clicked.connect(self.on_ok)
        self.ok_button.setMinimumHeight(35)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(35)
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def on_ok(self):
        if self.list_widget.currentText():
            self.selected_item = self.list_widget.currentText()
            self.accept()

    @staticmethod
    def getItem(parent, title: str, label: str, items: list, selected_index: int):
        dialog = GoToCategoryDialog(parent, title, label, items, selected_index)
        result = dialog.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dialog.selected_item, True
        return "", False

