import os, requests, re, guiTools, functions, guiTools, gui, settings, settings, functions
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


def log_error(func_name, error):
	error_message = f"!!! خطأ فادح في {func_name}: {str(error)}"
	print(error_message)


class DataLoaderThread(qt2.QThread):
	data_loaded = qt2.pyqtSignal(object)
	loading_error = qt2.pyqtSignal(str)
	def __init__(self, fileName: str, parent=None):
		super().__init__(parent)
		self.fileName = fileName
	def run(self):
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
				self.data_loaded.emit(jsonContent)
			else:
				self.loading_error.emit(f"Status code {r.status_code} - فشل تحميل الخريطة من جيت هاب")
		except Exception as e:
			log_error("DataLoaderThread.run", e)
			self.loading_error.emit(str(e))


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
		self.loading_label = qt.QLabel("جاري تحميل البيانات، يرجى الانتظار...")
		self.loading_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.loading_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.loading_label)
		self.item.setVisible(False)
		self.onLoad()
	def on_item_clicked(self):
		try:
			selected_item_text = self.item.currentItem().text()
			if selected_item_text in self.data:
				StartDownloading(self, self.data[selected_item_text], self.dirName).exec()
		except Exception as e:
			log_error("SelectItem.on_item_clicked", e)
	def onLoad(self):
		self.loader_thread = DataLoaderThread(self.fileName)
		self.loader_thread.data_loaded.connect(self.onDataLoaded)
		self.loader_thread.loading_error.connect(self.onLoadingError)
		self.loader_thread.start()
	def onDataLoaded(self, jsonContent):
		self.data = jsonContent
		self.item.addItems(self.data.keys())
		self.loading_label.setVisible(False)
		self.item.setVisible(True)
	def onLoadingError(self, error_message):
		log_error("onLoad", error_message)
		guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ أثناء تحميل البيانات")
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
	network_error = qt2.pyqtSignal(str)
	def __init__(self, fileName: str, DIRName: str):
		super().__init__()
		self.fileName = fileName
		self.DIRName = DIRName
		self.is_paused = False
		self.is_cancelled = False
	def pause(self):
		self.is_paused = True
	def resume(self):
		self.is_paused = False
	def cancel(self):
		self.is_cancelled = True
	def run(self):
		save_path = os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, self.fileName)
		directory = os.path.dirname(save_path)
		os.makedirs(directory, exist_ok=True)
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
		while not self.is_cancelled:
			if self.is_paused:
				self.msleep(200)
				continue
			downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
			headers = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
			}
			if downloaded_size > 0:
				headers['Range'] = f'bytes={downloaded_size}-'
			try:
				r = requests.get(url, stream=True, timeout=15, headers=headers)
				if r.status_code in (200, 206):
					content_range = r.headers.get('content-range')
					if content_range:
						total_size = int(content_range.split('/')[-1])
					elif 'content-length' in r.headers:
						total_size = downloaded_size + int(r.headers['content-length'])
					else:
						total_size = 0
					mode = "ab" if (downloaded_size > 0 and r.status_code == 206) else "wb"
					if mode == "wb":
						downloaded_size = 0
					with open(save_path, mode) as file:
						for chunk in r.iter_content(chunk_size=1024):
							while self.is_paused and not self.is_cancelled:
								self.msleep(200)
							if self.is_cancelled:
								return
							if chunk:
								file.write(chunk)
								downloaded_size += len(chunk)
								if total_size > 0:
									self.progress.emit(int((downloaded_size / total_size) * 100))
								else:
									self.progress.emit(int(downloaded_size / 1024) % 100)
					try:
						functions.tafseer.reload_tafaseers()
						functions.translater.reload_translations()
						functions.ahadeeth.reload_ahadeeths()
						functions.islamicBooks.reload_books()
					except Exception as e:
						log_error("DownloadThread.run (post-processing)", e)
					self.finished.emit(True)
					return
				else:
					log_error("DownloadThread.run", f"Status code {r.status_code} - فشل تحميل الملف من اللينك: {url}")
					self.finished.emit(False)
					return
			except (requests.exceptions.RequestException, Exception) as e:
				log_error("DownloadThread.run", e)
				self.is_paused = True
				self.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")


class StartDownloading(qt.QDialog):
	def __init__(self, p, FileName: str, DIRName: str):
		super().__init__(p)
		self.fileName = FileName
		self.DIRName = DIRName
		self.resize(400, 150)
		self.setWindowTitle("جاري التحميل")
		layout = qt.QVBoxLayout(self)
		self.progressBar = qt.QProgressBar()
		self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		layout.addWidget(self.progressBar)
		btns_layout = qt.QHBoxLayout()
		self.pause_button = guiTools.QPushButton("إيقاف مؤقت")
		self.pause_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #0000CC;}")
		self.pause_button.clicked.connect(self.toggle_pause)
		btns_layout.addWidget(self.pause_button)
		self.cancel = guiTools.QPushButton("إلغاء")
		self.cancel.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #A52A2A;}")
		self.cancel.clicked.connect(self.close)
		btns_layout.addWidget(self.cancel)
		layout.addLayout(btns_layout)
		self.thread = DownloadThread(FileName, DIRName)
		self.thread.finished.connect(self.onFinished)
		self.thread.progress.connect(self.onProgreesBarChanged)
		self.thread.network_error.connect(self.on_network_error)
		self.thread.start()
		qt1.QShortcut("escape", self).activated.connect(self.close)
	def toggle_pause(self):
		if self.thread.is_paused:
			self.pause_button.setText("إيقاف مؤقت")
			self.thread.resume()
		else:
			self.pause_button.setText("استئناف")
			self.thread.pause()
	def on_network_error(self, msg):
		self.pause_button.setText("استئناف")
		guiTools.MessageBox.error(self, "انقطاع الاتصال", msg)
	def closeEvent(self, a0):
		try:
			result = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد إلغاء العملية؟", "نعم", "لا")
			if result == 0:
				self.thread.cancel()
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
