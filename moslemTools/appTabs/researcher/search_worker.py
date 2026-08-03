import re, os, settings, requests, ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools, functions


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
                                    self.progress.emit(int((downloaded_size / total_size) * 100))
                    self.finished.emit()
                    return
                else:
                    self.cancelled.emit()
                    return
            except (requests.exceptions.RequestException, Exception) as e:
                self.is_paused = True
                self.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")


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
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setAutoDefault(False)
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


class SearchThread(qt2.QThread):
    searchFinished = qt2.pyqtSignal(list, dict, int)

    def __init__(self, parent, search_type, search_text, search_scope, ahadeeth_text, ignore_tashkeel, ignore_hamza, ignore_symbols):
        super().__init__(parent)
        self.parent_widget = parent
        self.search_type = search_type
        self.search_text = search_text
        self.search_scope = search_scope
        self.ahadeeth_text = ahadeeth_text
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols

    def _search(self, pattern, text_list):
        def remove_tashkeel(text):
            return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        def normalize_hamza(text):
            return re.sub(r'[أإآ]', 'ا', text)
        def normalize(text):
            normalized_text = text
            if self.ignore_tashkeel:
                normalized_text = remove_tashkeel(normalized_text)
            if self.ignore_hamza:
                normalized_text = normalize_hamza(normalized_text)
            return normalized_text
        normalized_pattern = normalize(pattern)
        results = []
        for display_text, search_text in text_list:
            if normalized_pattern in normalize(search_text):
                results.append(display_text)
        return results

    def run(self):
        display_text = []
        search_metadata = {}
        total_results_count = 0
        try:
            if self.search_type == 0:
                listOfWords = []
                data = functions.quranJsonControl.data
                def get_display(sn, sname, a):
                    return f"{sn}{sname} {a['text']}({a['numberInSurah']})"
                if self.search_scope is None:
                    for sn, sv in data.items():
                        sname = sv["name"]
                        for a in sv["ayahs"]:
                            listOfWords.append((get_display(sn, sname, a), a['text']))
                elif self.search_scope[0] == 'surah':
                    surah_key_part = self.search_scope[1].split(' ')[0]
                    for sn, sv in data.items():
                        sname = sv["name"]
                        if f"{sn}{sname}" == surah_key_part:
                            for a in sv["ayahs"]:
                                listOfWords.append((get_display(sn, sname, a), a['text']))
                            break
                else:
                    stype, sval = self.search_scope
                    for sn, sv in data.items():
                        sname = sv["name"]
                        for a in sv["ayahs"]:
                            match = False
                            if stype == 'page' and a['page'] == sval: match = True
                            elif stype == 'juz' and a['juz'] == sval: match = True
                            elif stype == 'quarter' and a['hizbQuarter'] == sval: match = True
                            elif stype == 'hizb' and (a['hizbQuarter']-1)//4+1 == sval: match = True
                            if match: listOfWords.append((get_display(sn, sname, a), a['text']))
                result = self._search(self.search_text, listOfWords)
                if result:
                    header = "عدد نتائج البحث " + str(len(result))
                    display_text.extend([header, ""])
                    current_line_number = 3
                    for line in result:
                        display_text.append(line)
                        metadata = self.parent_widget.get_metadata_from_result(line)
                        if metadata:
                            search_metadata[current_line_number] = metadata
                        current_line_number += 1
                    total_results_count = len(result)
            else:
                search_books = {}
                if self.ahadeeth_text == "البحث في جميع كتب الأحاديث المتاحة":
                    search_books = functions.ahadeeth.ahadeeths
                else:
                    search_books = {self.ahadeeth_text: functions.ahadeeth.ahadeeths[self.ahadeeth_text]}
                current_line_number = 3
                for book_name_ar, file_name in search_books.items():
                    try:
                        full_path = os.path.join(os.getenv("appdata"), settings.app.appName, "ahadeeth", file_name)
                        with open(full_path, "r", encoding="utf-8") as f:
                            ahadeeth_data = json.load(f)
                        if isinstance(ahadeeth_data, list):
                            listOfWords = [(str(i + 1) + ". " + item, item) for i, item in enumerate(ahadeeth_data)]
                            result = self._search(self.search_text, listOfWords)
                            if result:
                                display_text.append(f"عدد النتائج في كتاب {book_name_ar}, {len(result)} نتيجة")
                                current_line_number += 1
                                display_text.append("")
                                current_line_number += 1
                                for item in result:
                                    display_text.append(item)
                                    match = re.match(r'^(\d+)\.', item)
                                    if match:
                                        hadith_index = int(match.group(1)) - 1
                                        metadata = {
                                            "type": "hadith",
                                            "book_name": book_name_ar,
                                            "file_name": file_name,
                                            "hadith_index": hadith_index
                                        }
                                        num_lines = item.count('\n') + 1
                                        for offset in range(num_lines):
                                            search_metadata[current_line_number + offset] = metadata
                                        current_line_number += num_lines
                                    else:
                                        current_line_number += 1
                                display_text.append("")
                                current_line_number += 1
                                total_results_count += len(result)
                        else:
                            qt.QMetaObject.invokeMethod(self.parent_widget, "handle_error", qt2.Qt.ConnectionType.QueuedConnection, qt2.Q_ARG(str, f"خطأ في البيانات: تنسيق ملف الأحاديث غير صحيح لكتاب: {book_name_ar}."))
                    except Exception as e:
                        qt.QMetaObject.invokeMethod(self.parent_widget, "handle_error", qt2.Qt.ConnectionType.QueuedConnection, qt2.Q_ARG(str, f"خطأ غير متوقع أثناء تحميل الأحاديث لكتاب {book_name_ar}: {e}"))
                if total_results_count > 0:
                    if display_text and display_text[-1] == "":
                        display_text.pop()
                    display_text.insert(0, "")
                    display_text.insert(0, f"إجمالي عدد النتائج: {total_results_count}")
                else:
                    display_text = []
        except Exception:
            display_text = []
            search_metadata = {}
            total_results_count = 0
        finally:
            self.searchFinished.emit(display_text, search_metadata, total_results_count)
