import os, requests, re, guiTools, functions, settings, shutil, time, urllib.parse, custom_errors
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl
from guiTools.QCustomListDialog import QCustomListDialog


def log_error(func_name, error):
	custom_errors.handle_exception(error, f"خطأ في {func_name}")


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
					try:
						os.makedirs(os.path.dirname(local_map_path), exist_ok=True)
						with open(local_map_path, "w", encoding="utf-8") as file:
							json.dump(jsonContent, file, ensure_ascii=False, indent=4)
					except Exception:
						pass

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

		self.cat_search_bar = qt.QLineEdit()
		self.cat_search_bar.setPlaceholderText("بحث في فئات الكتب")
		self.cat_search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		self.cat_search_bar.setMinimumHeight(32)
		self.cat_search_bar.textChanged.connect(self.on_search_category)
		layout.addWidget(self.cat_search_bar)

		cat_header_layout = qt.QHBoxLayout()
		cat_header_layout.setSpacing(10)
		cat_header_layout.addStretch(1)

		self.category_combo = guiTools.QComboBox()
		self.category_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
		self.category_combo.setSizePolicy(qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed)
		self.category_combo.setAccessibleName("اختيار الفئة")
		self.category_combo.setMinimumHeight(35)
		self.category_combo.setStyleSheet("QComboBox { padding: 4px 15px; font-weight: bold; font-size: 13px; }")
		self.category_combo.currentIndexChanged.connect(self.on_category_changed)
		cat_header_layout.addWidget(self.category_combo)

		self.cat_label = qt.QLabel("اختيار الفئة:")
		self.cat_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
		self.cat_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter)
		self.cat_label.setFont(font_bold)
		cat_header_layout.addWidget(self.cat_label)

		cat_header_layout.addStretch(1)
		layout.addLayout(cat_header_layout)

		self.search_bar = qt.QLineEdit()
		self.search_bar.setPlaceholderText("بحث في الكتب")
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

	def closeEvent(self, a0):
		if hasattr(self, 'loader_thread') and self.loader_thread and self.loader_thread.isRunning():
			self.loader_thread.quit()
			self.loader_thread.wait(1000)
		a0.accept()

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
				btn_can.setAutoDefault(False)
				btn_can.setDefault(False)
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
				btn_can_start.setAutoDefault(False)
				btn_can_start.setDefault(False)
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

	def __init__(self, fileName: str = "", DIRName: str = ""):
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

		self.manager = QNetworkAccessManager(self)
		self.reply = None
		self.current_file_handle = None
		self.is_paused = False
		self.is_cancelled = False
		self.downloaded_size = 0
		self.current_save_path = None

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
		self.pause_button.setAutoDefault(False)
		self.pause_button.setDefault(False)
		self.pause_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #0000CC;}")
		self.pause_button.clicked.connect(self.toggle_pause)
		btns_layout.addWidget(self.pause_button)

		self.cancel = guiTools.QPushButton("إلغاء تحميل الملف" if self.total_count == 1 else "إلغاء الملف الحالي")
		self.cancel.setAutoDefault(False)
		self.cancel.setDefault(False)
		self.cancel.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #A52A2A;}")
		self.cancel.clicked.connect(self.cancel_current_file)
		btns_layout.addWidget(self.cancel)

		self.cancel_all_button = guiTools.QPushButton("إلغاء المتبقي")
		self.cancel_all_button.setAutoDefault(False)
		self.cancel_all_button.setDefault(False)
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

	def save_book_category(self, current_file, current_display):
		try:
			if current_file:
				norm_path = current_file.replace("\\", "/")
				parts = norm_path.split("/")
				if len(parts) > 1 and parts[0]:
					cat_folder = parts[0]
				elif "shabah" in current_file.lower() or current_display == "حياة الصحابة":
					cat_folder = "السيرة والشمائل"
				else:
					cat_folder = "أخرى"
				cat_file_path = os.path.join(os.getenv('appdata'), settings.app.appName, "book_categories.json")
				cat_data = {"categories": [], "book_map": {}}
				if os.path.exists(cat_file_path):
					with open(cat_file_path, "r", encoding="utf-8") as f:
						cat_data = json.load(f)
				cats = cat_data.get("categories", [])
				book_map = cat_data.get("book_map", {})
				if cat_folder not in cats:
					cats.append(cat_folder)
				if current_display not in book_map:
					book_map[current_display] = []
				if cat_folder not in book_map[current_display]:
					book_map[current_display].append(cat_folder)
				cat_data["categories"] = cats
				cat_data["book_map"] = book_map
				os.makedirs(os.path.dirname(cat_file_path), exist_ok=True)
				with open(cat_file_path, "w", encoding="utf-8") as f:
					json.dump(cat_data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log_error("save_book_category", e)

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
			self.is_paused = False
			self.is_cancelled = False

			save_path = os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file)
			directory = os.path.dirname(save_path)
			os.makedirs(directory, exist_ok=True)
			self.current_save_path = save_path

			local_src = os.path.join("data", "json", "islamicBooks", current_file)
			if not os.path.exists(local_src):
				fname = os.path.basename(current_file)
				for root, dirs, files in os.walk(os.path.join("data", "json", "islamicBooks")):
					if fname in files:
						local_src = os.path.join(root, fname)
						break

			if os.path.exists(local_src):
				try:
					shutil.copy2(local_src, save_path)
					self.progressBar.setValue(100)
					self.save_book_category(current_file, current_display)
					functions.islamicBooks.reload_books()
					self.successful_count += 1
					self.current_index += 1
					qt2.QTimer.singleShot(0, self.start_next_file)
					return
				except Exception as e:
					log_error("StartDownloadingIslamicBooks.local_copy", e)

			self.downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
			encoded_filename = urllib.parse.quote(current_file.replace("\\", "/"), safe="/")
			url_str = f"https://huggingface.co/datasets/alcoder01/Islamic_Books/resolve/main/{encoded_filename}"
			request = QNetworkRequest(QUrl(url_str))
			request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
			request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
			if self.downloaded_size > 0:
				request.setRawHeader(b"Range", f"bytes={self.downloaded_size}-".encode("utf-8"))

			mode = "ab" if self.downloaded_size > 0 else "wb"
			try:
				self.current_file_handle = open(save_path, mode)
			except Exception as e:
				custom_errors.handle_exception(e)
				self.on_network_error(str(e))
				return

			self.reply = self.manager.get(request)
			self.reply.downloadProgress.connect(self.on_download_progress)
			self.reply.readyRead.connect(self.on_ready_read)
			self.reply.finished.connect(self.on_reply_finished)
		else:
			functions.islamicBooks.reload_books()
			if self.total_count == 1 and self.successful_count == 1:
				current_display = self.display_names[0] if self.display_names else self.files[0]
				guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم تحميل {current_display}")
			else:
				guiTools.qMessageBox.MessageBox.view(self, "تم", f"اكتملت عملية التحميل بنجاح ({format_file_count(self.successful_count)} من إجمالي {format_file_count(self.total_count)})")
			self.accept()

	def on_ready_read(self):
		if self.reply and self.current_file_handle:
			data = self.reply.readAll()
			if data:
				self.current_file_handle.write(data.data())

	def on_download_progress(self, bytes_received, bytes_total):
		if bytes_total > 0:
			total = self.downloaded_size + bytes_total
			current = self.downloaded_size + bytes_received
			self.progressBar.setValue(min(100, int((current / total) * 100)))

	def on_reply_finished(self):
		if not self.reply:
			return
		reply = self.reply
		self.reply = None
		if self.current_file_handle:
			try:
				data = reply.readAll()
				if data:
					self.current_file_handle.write(data.data())
			except Exception:
				pass
			try:
				self.current_file_handle.close()
			except Exception:
				pass
			self.current_file_handle = None

		if self.is_cancelled or self.is_paused:
			reply.deleteLater()
			return

		error = reply.error()
		status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
		reply.deleteLater()

		if error == QNetworkReply.NetworkError.NoError and status_code in (200, 206):
			current_file = self.files[self.current_index]
			current_display = self.display_names[self.current_index] if self.current_index < len(self.display_names) else current_file
			self.save_book_category(current_file, current_display)
			functions.islamicBooks.reload_books()
			self.successful_count += 1
			self.current_index += 1
			qt2.QTimer.singleShot(0, self.start_next_file)
		elif status_code == 416:
			current_file = self.files[self.current_index]
			current_display = self.display_names[self.current_index] if self.current_index < len(self.display_names) else current_file
			self.save_book_category(current_file, current_display)
			functions.islamicBooks.reload_books()
			self.successful_count += 1
			self.current_index += 1
			qt2.QTimer.singleShot(0, self.start_next_file)
		else:
			self.is_paused = True
			qt2.QTimer.singleShot(0, lambda: self.on_network_error("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف."))

	def toggle_pause(self):
		if self.is_paused:
			self.pause_button.setText("إيقاف مؤقت")
			guiTools.speak("تم استئناف التحميل")
			self.is_paused = False
			if self.current_file_handle:
				try:
					self.current_file_handle.close()
				except Exception:
					pass
				self.current_file_handle = None
			current_file = self.files[self.current_index]
			save_path = self.current_save_path
			self.downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
			encoded_filename = urllib.parse.quote(current_file.replace("\\", "/"), safe="/")
			url_str = f"https://huggingface.co/datasets/alcoder01/Islamic_Books/resolve/main/{encoded_filename}"
			request = QNetworkRequest(QUrl(url_str))
			request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
			request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
			if self.downloaded_size > 0:
				request.setRawHeader(b"Range", f"bytes={self.downloaded_size}-".encode("utf-8"))
			mode = "ab" if self.downloaded_size > 0 else "wb"
			try:
				self.current_file_handle = open(save_path, mode)
			except Exception as e:
				custom_errors.handle_exception(e)
				self.on_network_error(str(e))
				return
			self.reply = self.manager.get(request)
			self.reply.downloadProgress.connect(self.on_download_progress)
			self.reply.readyRead.connect(self.on_ready_read)
			self.reply.finished.connect(self.on_reply_finished)
		else:
			self.pause_button.setText("استئناف")
			guiTools.speak("تم إيقاف التحميل مؤقتاً")
			self.is_paused = True
			if self.reply and self.reply.isRunning():
				self.reply.abort()
			if self.current_file_handle:
				try:
					self.current_file_handle.close()
				except Exception:
					pass
				self.current_file_handle = None

	def on_network_error(self, msg):
		self.pause_button.setText("استئناف")
		guiTools.speak("تم إيقاف التحميل مؤقتاً بسبب انقطاع الاتصال بالإنترنت")
		guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

	def cancel_current_file(self):
		if self.current_index < self.total_count:
			result = guiTools.QQuestionMessageBox.view(self, "تأكيد", "هل تريد إلغاء تحميل الملف الحالي؟", "نعم", "لا")
			if result == 0:
				self.is_cancelled = True
				if self.reply and self.reply.isRunning():
					self.reply.abort()
				if self.current_file_handle:
					try:
						self.current_file_handle.close()
					except Exception:
						pass
					self.current_file_handle = None
				current_file = self.files[self.current_index]
				try:
					functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
				except Exception as e:
					log_error("cancel_current_file", e)
				self.current_index += 1
				qt2.QTimer.singleShot(0, self.start_next_file)

	def cancel_all(self):
		result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل تريد إلغاء تحميل المتبقي بالكامل؟ (سيتم الاحتفاظ بالملفات التي تم تحميلها بالفعل)", "نعم", "لا")
		if result == 0:
			self.is_cancelled = True
			if self.reply and self.reply.isRunning():
				self.reply.abort()
			if self.current_file_handle:
				try:
					self.current_file_handle.close()
				except Exception:
					pass
				self.current_file_handle = None
			if self.current_index < self.total_count:
				current_file = self.files[self.current_index]
				try:
					functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
				except Exception as e:
					log_error("cancel_all", e)
			functions.islamicBooks.reload_books()
			guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", f"تم إلغاء عملية التحميل. تم حفظ {format_file_count(self.successful_count)} بنجاح.")
			self.accept()

	def closeEvent(self, a0):
		try:
			result = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد إلغاء عملية التحميل بالكامل؟ (سيتم الاحتفاظ بالملفات المكتملة)", "نعم", "لا")
			if result == 0:
				self.is_cancelled = True
				if self.reply and self.reply.isRunning():
					self.reply.abort()
				if self.current_file_handle:
					try:
						self.current_file_handle.close()
					except Exception:
						pass
					self.current_file_handle = None
				if self.current_index < self.total_count:
					current_file = self.files[self.current_index]
					try:
						functions.removeManager.addNewFile(os.path.join(os.getenv('appdata'), settings.app.appName, self.DIRName, current_file))
					except Exception:
						pass
				functions.islamicBooks.reload_books()
				a0.accept()
			else:
				a0.ignore()
		except Exception as e:
			log_error("closeEvent", e)
			a0.accept()
