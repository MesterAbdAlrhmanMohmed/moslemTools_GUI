import json, os, requests, re, guiTools, functions
import guiTools, gui, settings, settings, functions
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
def log_error(func_name, error):    
    error_message = f"!!! خطأ فادح في {func_name}: {str(error)}"
    print(error_message)
    # كتابة الخطأ في ملف لوج
    # with open("error_log.txt", "a", encoding="utf-8") as f:
    #     f.write(error_message + "\n")
class SelectItem(qt.QDialog):
    def __init__(self, p, fileName: str, dirName):
        super().__init__(p)
        self.resize(900, 500)
        self.data = {}
        self.dirName = dirName
        layout = qt.QVBoxLayout(self)
        serch = qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.item = guiTools.QListWidget()
        self.item.setSpacing(3)
        font = qt1.QFont()
        font.setBold(True)
        self.item.setFont(font)
        layout.addWidget(self.item)
        self.item.clicked.connect(self.on_item_clicked)
        self.fileName = fileName
        self.onLoad()
    def on_item_clicked(self):
        try:
            selected_item_text = self.item.currentItem().text()
            if selected_item_text in self.data:
                StartDownloading(self, self.data[selected_item_text], self.dirName).exec()
        except Exception as e:
            log_error("SelectItem.on_item_clicked", e)
    def onLoad(self):
        try:
            url = "https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/refs/heads/main/moslemTools/data/json/files/" + self.fileName
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            r = requests.get(url, timeout=30, headers=headers)
            if r.status_code == 200:
                jsonContent = r.json()
                full_data_copy = jsonContent.copy()
                local_map_path = os.path.join("data", "json", "files", self.fileName)
                os.makedirs(os.path.dirname(local_map_path), exist_ok=True)
                with open(local_map_path, "w", encoding="utf-8") as file:
                    json.dump(jsonContent, file, ensure_ascii=False, indent=4)
                downloadedData = []
                if self.fileName == "all_tafaseers.json":
                    downloadedData = list(functions.tafseer.tafaseers.keys())
                elif self.fileName == "all_translater.json":
                    downloadedData = list(functions.translater.translations.keys())
                elif self.fileName == "all_ahadeeth.json":
                    downloadedData = list(functions.ahadeeth.ahadeeths.keys())
                elif self.fileName == "all_islamic_books.json":
                    downloadedData = list(functions.islamicBooks.books.keys())
                for data in downloadedData:
                    if data in jsonContent:
                        del jsonContent[data]
                self.data = jsonContent
                self.item.addItems(self.data.keys())
            else:
                log_error("onLoad", f"Status code {r.status_code} - فشل تحميل الخريطة من جيت هاب")
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ أثناء تحميل البيانات (Code 1)")
                self.close()
        except Exception as e:
            log_error("onLoad", e)
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ أثناء تحميل البيانات (Code 2)")
            self.accept()
    def search(self, pattern, text_list):
        try:
            tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
            normalized_pattern = tashkeel_pattern.sub('', pattern)
            matches = [
                text for text in text_list
                if normalized_pattern in tashkeel_pattern.sub('', text)
            ]
            return matches
        except Exception as e:
            log_error("search", e)
            return text_list
    def onsearch(self):
        try:
            search_text = self.search_bar.text().lower()
            self.item.clear()
            result = self.search(search_text, list(self.data.keys()))
            self.item.addItems(result)
        except Exception as e:
            log_error("onsearch", e)
class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal(bool)
    def __init__(self, fileName: str, DIRName: str):
        super().__init__()
        self.fileName = fileName
        self.DIRName = DIRName
    def run(self):
        try:
            github_base_url = "https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/refs/heads/main/moslemTools/data/json/"
            translater_archive_url = "https://archive.org/download/dv.divehi/"
            ahadeeth_archive_url = "https://ia803201.us.archive.org/17/items/bukhari_202511/"
            tafaseer_archive_url = "https://ia803201.us.archive.org/17/items/tabary_202511/"
            books_archive_url = "https://archive.org/download/0072_20251110/"
            dir_lower = self.DIRName.strip().lower().replace(" ", "")
            if "translat" in dir_lower:
                url = translater_archive_url + self.fileName
            elif "ahadeeth" in dir_lower or "hadith" in dir_lower:
                url = ahadeeth_archive_url + self.fileName
            elif "tafseer" in dir_lower or "tafaseer" in dir_lower:
                url = tafaseer_archive_url + self.fileName
            elif "book" in dir_lower:
                url = books_archive_url + self.fileName
            else:
                url = github_base_url + self.DIRName + "/" + self.fileName
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            with requests.get(url, stream=True, timeout=30, headers=headers) as r:
                if r.status_code == 200:
                    save_path = os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, self.fileName)
                    directory = os.path.dirname(save_path)
                    os.makedirs(directory, exist_ok=True)
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded_size = 0
                    with open(save_path, "wb") as file:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                file.write(chunk)
                                downloaded_size += len(chunk)
                                if total_size > 0:
                                    progress_percent = int((downloaded_size / total_size) * 100)
                                    self.progress.emit(progress_percent)
                                else:
                                    self.progress.emit(int(downloaded_size / 1024) % 100)
                    functions.tafseer.setTafaseer()
                    functions.translater.settranslation()
                    functions.ahadeeth.setahadeeth()
                    functions.islamicBooks.setBooks()
                    self.finished.emit(True)
                else:
                    log_error("DownloadThread.run", f"Status code {r.status_code} - فشل تحميل الملف من اللينك: {url}")
                    self.finished.emit(False)
        except Exception as e:
            log_error("DownloadThread.run", e)
            self.finished.emit(False)
class StartDownloading(qt.QDialog):
    def __init__(self, p, FileName: str, DIRName: str):
        super().__init__(p)
        self.fileName = FileName
        self.DIRName = DIRName
        layout = qt.QVBoxLayout(self)
        self.progressBar = qt.QProgressBar()
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.progressBar)
        self.cancel = guiTools.QPushButton("إلغاء")
        self.cancel.setStyleSheet("background-color: #0000AA; color: #e0e0e0;")
        self.cancel.clicked.connect(self.close)
        layout.addWidget(self.cancel)
        self.thread = DownloadThread(FileName, DIRName)
        self.thread.finished.connect(self.onFinished)
        self.thread.progress.connect(self.onProgreesBarChanged)
        self.thread.start()
        qt1.QShortcut("escape", self).activated.connect(self.close)
    def closeEvent(self, a0):
        try:
            result = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد إلغاء العملية؟", "نعم", "لا")
            if result == 0:
                self.thread.terminate()
                functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, self.fileName))
                a0.accept()
            else:
                a0.ignore()
        except Exception as e:
            log_error("closeEvent", e)
            a0.accept()
    def onFinished(self, state):
        if state:
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل بنجاح")
            self.accept()
        else:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "حدث خطأ أثناء التحميل")
            self.close()
    def onProgreesBarChanged(self, value):
        self.progressBar.setValue(value)