import os, requests, re, guiTools, functions, settings, shutil, time, urllib.parse
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from guiTools.QCustomListDialog import QCustomListDialog


def log_error(func_name, error):
	error_message = f"!!! خطأ في {func_name}: {str(error)}"
	print(error_message)


def format_item_count(count):
	if count == 1:
		return "عنصر واحد"
	elif count == 2:
		return "عنصرين"
	elif 3 <= count <= 10:
		return f"{count} عناصر"
	else:
		return f"{count} عنصر"


def format_file_count(count):
	if count == 1:
		return "ملف واحد"
	elif count == 2:
		return "ملفين"
	elif 3 <= count <= 10:
		return f"{count} ملفات"
	else:
		return f"{count} ملف"


class IslamicBookDataLoaderThread(qt2.QThread):
	data_loaded = qt2.pyqtSignal(object)
	loading_error = qt2.pyqtSignal(str)

	def __init__(self, fileName: str, parent=None):
		super().__init__(parent)
		self.fileName = fileName

	def run(self):
		try:
			jsonContent = None
			# 1. Try local file first (ensures offline reliability)
			local_map_path = os.path.join("data", "json", "files", self.fileName)
			if os.path.exists(local_map_path):
				try:
					with open(local_map_path, "r", encoding="utf-8") as file:
						jsonContent = json.load(file)
				except Exception as e:
					log_error("IslamicBookDataLoaderThread.local_read", e)

			# 2. Try remote if local not found
			if not jsonContent:
				url = "https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/refs/heads/main/moslemTools/data/json/files/" + self.fileName
				headers = {
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
				}
				r = requests.get(url, timeout=15, headers=headers)
				if r.status_code == 200:
					jsonContent = r.json()
					os.makedirs(os.path.dirname(local_map_path), exist_ok=True)
					with open(local_map_path, "w", encoding="utf-8") as file:
						json.dump(jsonContent, file, ensure_ascii=False, indent=4)

			if jsonContent:
				# Remove already downloaded books from available list
				downloadedData = list(functions.islamicBooks.books.keys())
				for data in downloadedData:
					if data in jsonContent:
						del jsonContent[data]
				self.data_loaded.emit(jsonContent)
			else:
				self.loading_error.emit("تعذر تحميل قائمة الكتب المتاحة")
		except Exception as e:
			log_error("IslamicBookDataLoaderThread.run", e)
			self.loading_error.emit(str(e))


class SelectIslamicBookItem(qt.QDialog):
	def __init__(self, p, fileName: str, dirName: str):
		super().__init__(p)
		self.setMinimumSize(650, 450)
		self.resize(980, 580)
		self.center()
		self.all_data = {}  # { display_name: rel_path }
		self.cat_groups = {}  # { cat_folder: { display_name: rel_path } }
		self.current_filtered_data = {}
		self.dirName = dirName
		self.start_selection_index = None
		self.custom_download_list = []
		self.fileName = fileName

		layout = qt.QVBoxLayout(self)
		layout.setSpacing(8)

		font_bold = qt1.QFont()
		font_bold.setBold(True)

		# 0. Category Search Bar before Category Combo Box
		cat_search_label = qt.QLabel("بحث في فئات الكتب:")
		cat_search_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
		cat_search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		cat_search_label.setFont(font_bold)
		layout.addWidget(cat_search_label)

		self.cat_search_bar = qt.QLineEdit()
		self.cat_search_bar.setPlaceholderText("ابحث عن فئة...")
		self.cat_search_bar.setAccessibleName("بحث في فئات الكتب")
		self.cat_search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.cat_search_bar.setMinimumHeight(32)
		self.cat_search_bar.textChanged.connect(self.on_search_category)
		layout.addWidget(self.cat_search_bar)

		# 1. Category Combo Box (centered with label beside it)
		cat_header_layout = qt.QHBoxLayout()
		cat_header_layout.setSpacing(10)
		cat_header_layout.addStretch(1)

		self.cat_label = qt.QLabel("اختيار الفئة:")
		self.cat_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
		self.cat_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter)
		self.cat_label.setFont(font_bold)
		cat_header_layout.addWidget(self.cat_label)

		self.category_combo = qt.QComboBox()
		self.category_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
		self.category_combo.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed)
		self.category_combo.setAccessibleName("اختيار الفئة")
		self.category_combo.setMinimumHeight(35)
		self.category_combo.setStyleSheet("QComboBox { padding: 4px 15px; font-weight: bold; font-size: 13px; }")
		self.category_combo.currentIndexChanged.connect(self.on_category_changed)
		cat_header_layout.addWidget(self.category_combo)

		cat_header_layout.addStretch(1)
		layout.addLayout(cat_header_layout)

		# 2. Search bar
		search_label = qt.QLabel("بحث في الكتب:")
		search_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
		search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		search_label.setFont(font_bold)
		layout.addWidget(search_label)

		self.search_bar = qt.QLineEdit()
		self.search_bar.setPlaceholderText("اكتب للبحث...")
		self.search_bar.setAccessibleName("بحث في الكتب")
		self.search_bar.textChanged.connect(self.onsearch)
		self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.search_bar.setMinimumHeight(32)
		layout.addWidget(self.search_bar)

		# 3. Book Items List
		self.item = guiTools.QListWidget()
		self.item.setSpacing(3)
		self.item.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
		self.item.customContextMenuRequested.connect(self.show_context_menu)
		self.item.setFont(font_bold)
		layout.addWidget(self.item)

		# 4. Info and Selection Status Labels
		self.info_label = guiTools.QNavigableLabel("لمزيد من خيارات التحميل، قم بالضغط على عنصر من القائمة باستخدام زر التطبيقات أو click الأيمن")
		self.info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.info_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px; margin: 5px;")
		self.info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.info_label.setVisible(False)
		layout.addWidget(self.info_label)

		self.selection_status_label = guiTools.QNavigableLabel("")
		self.selection_status_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.selection_status_label.setStyleSheet("color: #008000; font-weight: bold; font-size: 12px;")
		self.selection_status_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
		self.selection_status_label.setVisible(False)
		layout.addWidget(self.selection_status_label)

		self.item.itemActivated.connect(self.on_item_clicked)

		self.loading_label = guiTools.QNavigableLabel("جاري تحميل الكتب المتاحة، يرجى الانتظار...")
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

	def onLoad(self):
		self.loader_thread = IslamicBookDataLoaderThread(self.fileName)
		self.loader_thread.data_loaded.connect(self.onDataLoaded)
		self.loader_thread.loading_error.connect(self.onLoadingError)
		self.loader_thread.start()

	def normalize_cat(self, text):
		t = re.sub(r'[ؗ-ًؚ-ْٰ]', '', text)
		t = re.sub(r'[إأآ]', 'ا', t)
		return t.replace('ى', 'ي').strip().lower()

	def populate_categories(self, search_text=""):
		prev_selected = self.category_combo.currentData()
		self.category_combo.blockSignals(True)
		self.category_combo.clear()

		q = self.normalize_cat(search_text) if search_text else ""

		# Add matching categories
		for cat_folder in sorted(self.cat_groups.keys()):
			if not q or q in self.normalize_cat(cat_folder):
				count = len(self.cat_groups[cat_folder])
				self.category_combo.addItem(f"{cat_folder} ({count})", cat_folder)

		# Add the final item: "كل الكتب" with total count
		total_count = len(self.all_data)
		if not q or q in self.normalize_cat("كل الكتب") or "كل" in q or "جميع" in q:
			self.category_combo.addItem(f"كل الكتب ({total_count})", "ALL")

		# Restore previous selection or default to 0
		if prev_selected:
			restore_idx = self.category_combo.findData(prev_selected)
			if restore_idx >= 0:
				self.category_combo.setCurrentIndex(restore_idx)
			elif self.category_combo.count() > 0:
				self.category_combo.setCurrentIndex(0)
		elif self.category_combo.count() > 0:
			self.category_combo.setCurrentIndex(0)

		self.category_combo.blockSignals(False)
		self.update_filtered_books()

	def on_search_category(self):
		self.populate_categories(self.cat_search_bar.text())

	def onDataLoaded(self, jsonContent):
		self.all_data = jsonContent  # { display_name: rel_path }
		self.cat_groups = {}

		# Group by category folder name
		for display_name, rel_path in self.all_data.items():
			norm_path = rel_path.replace("\\", "/")
			parts = norm_path.split("/")
			if len(parts) > 1 and parts[0]:
				cat_folder = parts[0]
			elif "shabah" in rel_path.lower() or display_name == "حياة الصحابة":
				cat_folder = "السيرة والشمائل"
			else:
				cat_folder = "أخرى"
			self.cat_groups.setdefault(cat_folder, {})[display_name] = rel_path

		self.populate_categories(self.cat_search_bar.text())

		self.loading_label.setVisible(False)
		self.item.setVisible(True)
		self.info_label.setVisible(True)

	def onLoadingError(self, error_message):
		log_error("onLoad", error_message)
		guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر تحميل قائمة الكتب")
		self.accept()

	def on_category_changed(self):
		self.start_selection_index = None
		self.custom_download_list.clear()
		self.update_selection_ui()
		self.update_filtered_books()

	def update_filtered_books(self):
		selected_data = self.category_combo.currentData()
		if selected_data == "ALL" or not selected_data:
			self.current_filtered_data = dict(self.all_data)
		else:
			self.current_filtered_data = dict(self.cat_groups.get(selected_data, {}))

		# Apply search filter if active
		search_text = self.search_bar.text().lower()
		self.item.clear()
		if search_text:
			result = self.search(search_text, list(self.current_filtered_data.keys()))
			self.item.addItems(result)
		else:
			self.item.addItems(self.current_filtered_data.keys())

	def search(self, pattern, text_list):
		try:
			tashkeel_pattern = re.compile(r'[ؗ-ًؚ-ْٰ]')
			normalized_pattern = tashkeel_pattern.sub('', pattern)
			matches = [
				text for text in text_list
				if normalized_pattern in tashkeel_pattern.sub('', text).lower()
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
			result = self.search(search_text, list(self.current_filtered_data.keys()))
			self.item.addItems(result)
		except Exception as e:
			log_error("onsearch", e)

	def show_context_menu(self, position):
		if self.item.count() == 0:
			return
		menu = guiTools.QCustomContextMenu(self)

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
		file_keys = [self.all_data[text] for text in self.custom_download_list if text in self.all_data]
		display_names = [text for text in self.custom_download_list if text in self.all_data]
		self.custom_download_list.clear()
		self.update_selection_ui()
		if file_keys:
			StartDownloadingIslamicBooks(self, file_keys, self.dirName, display_names).exec()
			self.refresh_after_download()

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
		display_names = []
		for i in range(start_index, end_index + 1):
			it = self.item.item(i)
			if it and it.text() in self.all_data:
				file_keys.append(self.all_data[it.text()])
				display_names.append(it.text())
		self.start_selection_index = None
		self.update_selection_ui()
		if file_keys:
			StartDownloadingIslamicBooks(self, file_keys, self.dirName, display_names).exec()
			self.refresh_after_download()

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
				if curr and curr.text() in self.all_data:
					StartDownloadingIslamicBooks(self, self.all_data[curr.text()], self.dirName, curr.text()).exec()
					self.refresh_after_download()
		except Exception as e:
			log_error("SelectIslamicBookItem.on_item_clicked", e)

	def refresh_after_download(self):
		functions.islamicBooks.reload_books()
		downloadedData = list(functions.islamicBooks.books.keys())
		for d in downloadedData:
			if d in self.all_data:
				del self.all_data[d]
		self.onDataLoaded(self.all_data)


class IslamicBookDownloadThread(qt2.QThread):
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

		# 1. First priority: if file exists locally in data/json/islamicBooks (offline copy)
		local_src = os.path.join("data", "json", "islamicBooks", self.fileName)
		if not os.path.exists(local_src):
			fname = os.path.basename(self.fileName)
			for root, dirs, files in os.walk(os.path.join("data", "json", "islamicBooks")):
				if fname in files:
					local_src = os.path.join(root, fname)
					break

		if os.path.exists(local_src):
			try:
				total_size = os.path.getsize(local_src)
				copied = 0
				with open(local_src, "rb") as src_f, open(save_path, "wb") as dst_f:
					while not self.is_cancelled:
						while self.is_paused and not self.is_cancelled:
							self.msleep(200)
						if self.is_cancelled:
							return
						chunk = src_f.read(64 * 1024)
						if not chunk:
							break
						dst_f.write(chunk)
						copied += len(chunk)
						if total_size > 0:
							self.progress.emit(min(100, int((copied / total_size) * 100)))
						self.msleep(15)  # smooth visual feedback

				if not self.is_cancelled:
					functions.islamicBooks.reload_books()
					self.finished.emit(True)
					return
			except Exception as e:
				log_error("IslamicBookDownloadThread.local_copy", e)

		# 2. Remote download from Hugging Face dataset
		encoded_filename = urllib.parse.quote(self.fileName.replace("\\", "/"), safe="/")
		url = f"https://huggingface.co/datasets/alcoder01/Islamic_Books/resolve/main/{encoded_filename}"
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
		}
		while not self.is_cancelled:
			if self.is_paused:
				self.msleep(200)
				continue
			downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
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
					functions.islamicBooks.reload_books()
					self.finished.emit(True)
					return
				else:
					self.finished.emit(False)
					return
			except (requests.exceptions.RequestException, Exception) as e:
				log_error("IslamicBookDownloadThread.run", e)
				self.is_paused = True
				self.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")


class StartDownloadingIslamicBooks(qt.QDialog):
	def __init__(self, p, FileName, DIRName: str, display_name=None):
		super().__init__(p)
		if isinstance(FileName, list):
			self.files = FileName
		else:
			self.files = [FileName]
		if display_name is not None:
			if isinstance(display_name, list):
				self.display_names = display_name
			else:
				self.display_names = [display_name]
		else:
			self.display_names = list(self.files)
		self.DIRName = DIRName
		self.total_count = len(self.files)
		self.current_index = 0
		self.successful_count = 0
		self.thread = None

		self.setMinimumSize(550, 250)
		self.resize(750, 320)
		self.center()
		self.setWindowTitle("جاري التحميل")
		layout = qt.QVBoxLayout(self)

		self.status_label = guiTools.QNavigableLabel("")
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
		self.pause_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #0000CC;}")
		self.pause_button.clicked.connect(self.toggle_pause)
		btns_layout.addWidget(self.pause_button)

		self.cancel = guiTools.QPushButton("إلغاء تحميل الملف" if self.total_count == 1 else "إلغاء الملف الحالي")
		self.cancel.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #A52A2A;}")
		self.cancel.clicked.connect(self.cancel_current_file)
		btns_layout.addWidget(self.cancel)

		self.cancel_all_button = guiTools.QPushButton("إلغاء المتبقي")
		self.cancel_all_button.setStyleSheet("QPushButton {background-color: #550000; color: white; border: none; padding: 5px 10px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #770000;}")
		self.cancel_all_button.clicked.connect(self.cancel_all)
		btns_layout.addWidget(self.cancel_all_button)
		if self.total_count == 1:
			self.cancel_all_button.hide()

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
			current_display = self.display_names[self.current_index] if self.current_index < len(self.display_names) else current_file
			if self.total_count == 1:
				self.status_label.setText(f"جاري تحميل {current_display}")
			else:
				sc_str = format_file_count(self.successful_count) if self.successful_count > 0 else "0 ملف"
				tot_str = format_file_count(self.total_count)
				self.status_label.setText(f"تم تحميل {sc_str} من إجمالي {tot_str} (جاري تحميل الملف {self.current_index + 1})")
			self.progressBar.setValue(0)
			self.pause_button.setText("إيقاف مؤقت")
			self.thread = IslamicBookDownloadThread(current_file, self.DIRName)
			self.thread.finished.connect(self.onFinished)
			self.thread.progress.connect(self.onProgreesBarChanged)
			self.thread.network_error.connect(self.on_network_error)
			self.thread.start()
		else:
			if self.total_count == 1 and self.successful_count == 1:
				current_display = self.display_names[0] if self.display_names else self.files[0]
				guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم تحميل {current_display}")
			else:
				guiTools.qMessageBox.MessageBox.view(self, "تم", f"اكتملت عملية التحميل بنجاح ({format_file_count(self.successful_count)} من إجمالي {format_file_count(self.total_count)})")
			self.accept()

	def toggle_pause(self):
		if self.thread and self.thread.isRunning():
			if self.thread.is_paused:
				self.pause_button.setText("إيقاف مؤقت")
				guiTools.speak("تم استئناف التحميل")
				self.thread.resume()
			else:
				self.pause_button.setText("استئناف")
				guiTools.speak("تم إيقاف التحميل مؤقتاً")
				self.thread.pause()

	def on_network_error(self, msg):
		self.pause_button.setText("استئناف")
		guiTools.speak("تم إيقاف التحميل مؤقتاً بسبب انقطاع الاتصال بالإنترنت")
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
