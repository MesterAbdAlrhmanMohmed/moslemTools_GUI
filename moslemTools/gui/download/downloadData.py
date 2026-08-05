import os, requests, re, guiTools, functions, settings
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from guiTools.QCustomListDialog import QCustomListDialog


def log_error(func_name, error):
	error_message = f"!!! خطأ فادح في {func_name}: {str(error)}"
	print(error_message)


def format_item_count(count):
	if count == 1:
		return "عنصر واحد"
	elif count == 2:
		return "عنصرين"
	elif 3 <= count <= 10:
		return f"{count} عناصر"
	else:
		return f"{count} عنصراً"


def format_file_count(count):
	if count == 1:
		return "ملف واحد"
	elif count == 2:
		return "ملفين"
	elif 3 <= count <= 10:
		return f"{count} ملفات"
	else:
		return f"{count} ملفاً"


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
		self.setMinimumSize(1050, 500)
		self.resize(1100, 560)
		self.center()
		self.data = {}
		self.dirName = dirName
		self.start_selection_index = None
		self.custom_download_list = []
		self.fileName = fileName

		layout = qt.QVBoxLayout(self)

		search_label = qt.QLineEdit("بحث")
		search_label.setReadOnly(True)
		search_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(search_label)

		self.search_bar = qt.QLineEdit()
		self.search_bar.setPlaceholderText("بحث ...")
		self.search_bar.textChanged.connect(self.onsearch)
		self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.search_bar)

		self.item = guiTools.QListWidget()
		self.item.setSpacing(3)
		self.item.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
		self.item.customContextMenuRequested.connect(self.show_context_menu)
		font = qt1.QFont()
		font.setBold(True)
		self.item.setFont(font)
		layout.addWidget(self.item)

		self.info_label = qt.QLineEdit("لمزيد من خيارات التحميل، قم بالضغط على عنصر من القائمة باستخدام زر التطبيقات أو click الأيمن")
		self.info_label.setReadOnly(True)
		self.info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.info_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px; margin: 5px;")
		self.info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.info_label.setVisible(False)
		layout.addWidget(self.info_label)

		self.selection_status_label = qt.QLineEdit("")
		self.selection_status_label.setReadOnly(True)
		self.selection_status_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.selection_status_label.setStyleSheet("color: #008000; font-weight: bold; font-size: 12px;")
		self.selection_status_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.selection_status_label.setVisible(False)
		layout.addWidget(self.selection_status_label)

		self.item.itemActivated.connect(self.on_item_clicked)

		self.shortcut_start = qt1.QShortcut(qt1.QKeySequence("Ctrl+B"), self)
		self.shortcut_start.activated.connect(self.set_as_start)

		self.shortcut_range = qt1.QShortcut(qt1.QKeySequence("Ctrl+D"), self)
		self.shortcut_range.activated.connect(self.download_from_start_to_here)

		self.loading_label = qt.QLineEdit("جاري تحميل البيانات، يرجى الانتظار...")
		self.loading_label.setReadOnly(True)
		self.loading_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.loading_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.loading_label)

		self.item.setVisible(False)
		self.onLoad()

	def center(self):
		frame_geometry = self.frameGeometry()
		screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
		frame_geometry.moveCenter(screen_center)
		self.move(frame_geometry.topLeft())

	def show_context_menu(self, position):
		if self.item.count() == 0:
			return
		menu = qt.QMenu(self)

		if self.start_selection_index is None:
			if not self.custom_download_list:
				act_add = menu.addAction("بدء التحميل من هذا العنصر")
				act_add.triggered.connect(self.add_to_custom_list)
			else:
				act_add = menu.addAction(f"إضافة العنصر رقم {len(self.custom_download_list) + 1} للتحميل")
				act_add.triggered.connect(self.add_to_custom_list)

				act_rem = menu.addAction("إزالة عنصر من قائمة التحميل")
				act_rem.triggered.connect(self.remove_from_custom_list)

				act_run = menu.addAction("بدء تحميل العناصر المحددة")
				act_run.triggered.connect(self.download_custom_list)

				act_can = qt.QWidgetAction(self)
				btn_can = guiTools.QPushButton("إلغاء التحميل")
				btn_can.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
				btn_can.clicked.connect(self.cancel_custom_list)
				btn_can.clicked.connect(menu.close)
				act_can.setDefaultWidget(btn_can)
				menu.addAction(act_can)

		menu.addSeparator()

		if not self.custom_download_list:
			if self.start_selection_index is None:
				act_start = menu.addAction("تحديد كبداية للتحميل")
				act_start.triggered.connect(self.set_as_start)
			else:
				curr_row = self.item.currentRow()
				if 0 <= self.start_selection_index < self.item.count():
					start_name = self.item.item(self.start_selection_index).text()
					hdr = menu.addAction(f"البداية المحددة: {start_name}")
					hdr.setEnabled(False)

				if curr_row != self.start_selection_index:
					act_rng = menu.addAction("التحميل من البداية المحددة إلى هنا")
					act_rng.triggered.connect(self.download_from_start_to_here)

				act_can_start = qt.QWidgetAction(self)
				btn_can_start = guiTools.QPushButton("إلغاء تحديد بداية التحميل")
				btn_can_start.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
				btn_can_start.clicked.connect(self.cancel_start_selection)
				btn_can_start.clicked.connect(menu.close)
				act_can_start.setDefaultWidget(btn_can_start)
				menu.addAction(act_can_start)

		menu.exec(self.item.mapToGlobal(position))

	def add_to_custom_list(self):
		self.cancel_start_selection()
		curr_item = self.item.currentItem()
		if curr_item:
			text = curr_item.text()
			if text not in self.custom_download_list:
				self.custom_download_list.append(text)
				guiTools.speak(f"تمت إضافة {text} كعنصر رقم {len(self.custom_download_list)} للتحميل")
				self.update_selection_ui()

	def remove_from_custom_list(self):
		if not self.custom_download_list:
			return
		num_items = len(self.custom_download_list)
		item_names = [f"{i+1}: {text}" for i, text in enumerate(self.custom_download_list)]
		selected_item_str, ok = QCustomListDialog.getItem(self, "إزالة عنصر", "اختر العنصر لإزالته من القائمة:", item_names)
		if ok and selected_item_str:
			idx = int(selected_item_str.split(':')[0]) - 1
			if 0 <= idx < num_items:
				del self.custom_download_list[idx]
				self.update_selection_ui()

	def download_custom_list(self):
		if not self.custom_download_list:
			return
		file_keys = [self.data[text] for text in self.custom_download_list if text in self.data]
		self.custom_download_list.clear()
		self.update_selection_ui()
		if file_keys:
			StartDownloading(self, file_keys, self.dirName).exec()

	def cancel_custom_list(self):
		self.custom_download_list.clear()
		guiTools.speak("تم إلغاء التحميل")
		self.update_selection_ui()

	def set_as_start(self):
		self.cancel_custom_list()
		row = self.item.currentRow()
		if row >= 0:
			self.start_selection_index = row
			text = self.item.currentItem().text()
			guiTools.speak(f"تم تحديد {text} كبداية للتحميل")
			self.update_selection_ui()

	def cancel_start_selection(self):
		self.start_selection_index = None
		guiTools.speak("تم إلغاء تحديد بداية التحميل")
		self.update_selection_ui()

	def download_from_start_to_here(self):
		if self.start_selection_index is None:
			guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء تحديد بداية التحميل أولاً.")
			return
		end_index = self.item.currentRow()
		if end_index < 0:
			return
		start_index = self.start_selection_index
		if start_index > end_index:
			start_index, end_index = end_index, start_index
		file_keys = []
		for i in range(start_index, end_index + 1):
			it = self.item.item(i)
			if it and it.text() in self.data:
				file_keys.append(self.data[it.text()])
		self.start_selection_index = None
		self.update_selection_ui()
		if file_keys:
			StartDownloading(self, file_keys, self.dirName).exec()

	def update_selection_ui(self):
		if self.custom_download_list:
			self.selection_status_label.setText(f"تم تحديد {format_item_count(len(self.custom_download_list))} للتحميل.")
			self.selection_status_label.setVisible(True)
		elif self.start_selection_index is not None and 0 <= self.start_selection_index < self.item.count():
			start_text = self.item.item(self.start_selection_index).text()
			self.selection_status_label.setText(f"تم تحديد بداية التحميل: {start_text}")
			self.selection_status_label.setVisible(True)
		else:
			self.selection_status_label.setText("")
			self.selection_status_label.setVisible(False)

	def on_item_clicked(self):
		try:
			if self.custom_download_list:
				self.download_custom_list()
			else:
				curr = self.item.currentItem()
				if curr and curr.text() in self.data:
					StartDownloading(self, self.data[curr.text()], self.dirName).exec()
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
		self.info_label.setVisible(True)

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
			self.start_selection_index = None
			self.custom_download_list.clear()
			self.update_selection_ui()
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
	def __init__(self, p, FileName, DIRName: str):
		super().__init__(p)
		if isinstance(FileName, list):
			self.files = FileName
		else:
			self.files = [FileName]
		self.DIRName = DIRName
		self.total_count = len(self.files)
		self.current_index = 0
		self.successful_count = 0
		self.thread = None

		self.setMinimumSize(1050, 500)
		self.resize(1100, 560)
		self.center()
		self.setWindowTitle("جاري التحميل")
		layout = qt.QVBoxLayout(self)

		self.status_label = qt.QLineEdit("")
		self.status_label.setReadOnly(True)
		self.status_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.status_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		font = qt1.QFont()
		font.setBold(True)
		self.status_label.setFont(font)
		layout.addWidget(self.status_label)

		self.progressBar = qt.QProgressBar()
		self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		layout.addWidget(self.progressBar)

		btns_layout = qt.QHBoxLayout()
		self.pause_button = guiTools.QPushButton("إيقاف مؤقت")
		self.pause_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #0000CC;}")
		self.pause_button.clicked.connect(self.toggle_pause)
		btns_layout.addWidget(self.pause_button)

		self.cancel = guiTools.QPushButton("إلغاء الملف الحالي")
		self.cancel.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #A52A2A;}")
		self.cancel.clicked.connect(self.cancel_current_file)
		btns_layout.addWidget(self.cancel)

		self.cancel_all_button = guiTools.QPushButton("إلغاء المتبقي")
		self.cancel_all_button.setStyleSheet("QPushButton {background-color: #550000; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #770000;}")
		self.cancel_all_button.clicked.connect(self.cancel_all)
		btns_layout.addWidget(self.cancel_all_button)

		layout.addLayout(btns_layout)

		self.start_next_file()
		qt1.QShortcut("escape", self).activated.connect(self.close)

	def center(self):
		frame_geometry = self.frameGeometry()
		screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
		frame_geometry.moveCenter(screen_center)
		self.move(frame_geometry.topLeft())

	def start_next_file(self):
		if self.current_index < self.total_count:
			current_file = self.files[self.current_index]
			sc_str = format_file_count(self.successful_count) if self.successful_count > 0 else "0 ملف"
			tot_str = format_file_count(self.total_count)
			self.status_label.setText(f"تم تحميل {sc_str} من إجمالي {tot_str} (جاري تحميل الملف {self.current_index + 1})")
			self.progressBar.setValue(0)
			self.pause_button.setText("إيقاف مؤقت")
			self.thread = DownloadThread(current_file, self.DIRName)
			self.thread.finished.connect(self.onFinished)
			self.thread.progress.connect(self.onProgreesBarChanged)
			self.thread.network_error.connect(self.on_network_error)
			self.thread.start()
		else:
			guiTools.qMessageBox.MessageBox.view(self, "تم", f"اكتملت عملية التحميل بنجاح ({format_file_count(self.successful_count)} من إجمالي {format_file_count(self.total_count)})")
			self.accept()

	def toggle_pause(self):
		if self.thread and self.thread.isRunning():
			if self.thread.is_paused:
				self.pause_button.setText("إيقاف مؤقت")
				self.thread.resume()
			else:
				self.pause_button.setText("استئناف")
				self.thread.pause()

	def on_network_error(self, msg):
		self.pause_button.setText("استئناف")
		guiTools.MessageBox.error(self, "انقطاع الاتصال", msg)

	def cancel_current_file(self):
		if self.current_index < self.total_count:
			result = guiTools.QQuestionMessageBox.view(self, "تأكيد", "هل تريد إلغاء تحميل الملف الحالي؟", "نعم", "لا")
			if result == 0:
				if self.thread and self.thread.isRunning():
					self.thread.cancel()
					self.thread.terminate()
				current_file = self.files[self.current_index]
				try:
					functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
				except Exception as e:
					log_error("cancel_current_file", e)
				self.current_index += 1
				self.start_next_file()

	def cancel_all(self):
		result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل تريد إلغاء تحميل المتبقي بالكامل؟ (سيتم الاحتفاظ بالملفات التي تم تحميلها بالفعل)", "نعم", "لا")
		if result == 0:
			if self.thread and self.thread.isRunning():
				self.thread.cancel()
				self.thread.terminate()
			if self.current_index < self.total_count:
				current_file = self.files[self.current_index]
				try:
					functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
				except Exception as e:
					log_error("cancel_all", e)
			guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", f"تم إلغاء عملية التحميل. تم حفظ {format_file_count(self.successful_count)} بنجاح.")
			self.accept()

	def closeEvent(self, a0):
		try:
			result = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد إلغاء عملية التحميل بالكامل؟ (سيتم الاحتفاظ بالملفات المكتملة)", "نعم", "لا")
			if result == 0:
				if self.thread and self.thread.isRunning():
					self.thread.cancel()
					self.thread.terminate()
				if self.current_index < self.total_count:
					current_file = self.files[self.current_index]
					try:
						functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
					except Exception:
						pass
				a0.accept()
			else:
				a0.ignore()
		except Exception as e:
			log_error("closeEvent", e)
			a0.accept()

	def onFinished(self, state):
		if state:
			self.successful_count += 1
		self.current_index += 1
		self.start_next_file()

	def onProgreesBarChanged(self, value):
		self.progressBar.setValue(value)
