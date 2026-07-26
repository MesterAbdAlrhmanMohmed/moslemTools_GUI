import gui,guiTools,os,re,shutil,threading
import ujson as json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class AthkarLoader(qt2.QThread):
    data_loaded = qt2.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
                athkar_data = json.load(data)
            self.data_loaded.emit(athkar_data)
        except Exception as e:
            print(f"Error loading athkar: {e}")
            self.data_loaded.emit([])


class Athker(qt.QWidget):
    def __init__(self):
        super().__init__()
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)
        self.data = None
        self.all_athkars_data = []
        self.is_loaded = False
        self.loader_thread = None
        self.favorites = []
        self.show_favorites_only = False
        self.fav_file_path = os.path.join(os.getenv('appdata'), app.appName, "athkar_favorites.json")
        self.load_favorites()
        layout = qt.QVBoxLayout(self)
        self.SL=qt.QLabel("البحث عن فئة أذكار")
        self.SL.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        search_layout = qt.QHBoxLayout()
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن فئة أذكار")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white;")
        self.fav_btn.clicked.connect(self.toggle_favorites)
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.fav_btn)
        layout.addWidget(self.SL)
        layout.addLayout(search_layout)
        self.athkerList = guiTools.QListWidget()
        self.athkerList.setSpacing(3)
        self.athkerList.clicked.connect(self.on_item_clicked)
        self.athkerList.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkerList.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.athkerList)
        self.info1 = qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("لخيارات فئة الأذكار المحددة، نستخدم مفتاح التطبيقات أو click الأيمن")
        layout.addWidget(self.info1)
        self.info2=qt.QLabel()
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info2.setText("يمكنكم تحميل الأذكار الصوتية لتشغيلها بدون انترنت من تحميل موارد إضافية من الإعدادات")
        layout.addWidget(self.info2)

    def load_favorites(self):
        try:
            if os.path.exists(self.fav_file_path):
                with open(self.fav_file_path, "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)
            else:
                self.favorites = []
        except Exception:
            self.favorites = []

    def save_favorites(self):
        try:
            os.makedirs(os.path.dirname(self.fav_file_path), exist_ok=True)
            with open(self.fav_file_path, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        if self.show_favorites_only:
            self.fav_btn.setText("عرض جميع فئات الأذكار")
        else:
            self.fav_btn.setText("فتح قائمة المفضلة")
        self.apply_filter()

    def showEvent(self, event):
        if event:
            super().showEvent(event)
        if not self.is_loaded:
            self.athkerList.clear()
            self.athkerList.addItem("جاري تحميل الأذكار...")
            if self.loader_thread is None:
                self.loader_thread = AthkarLoader()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()

    def on_data_loaded(self, data):
        self.all_athkars_data = data
        self.is_loaded = True
        self.apply_filter()

    def on_item_clicked(self):
        item = self.athkerList.currentItem()
        row = self.athkerList.currentRow()
        if item and self.data and 0 <= row < len(self.data):
            gui.AthkerDialog(self, item.text(), self.data[row]["content"]).exec()

    def open_context_menu(self, pos):
        item = self.athkerList.itemAt(pos)
        if not item:
            item = self.athkerList.currentItem()
        if not item:
            return
        self.athkerList.setCurrentItem(item)
        athkar_name = item.text()
        menu = qt.QMenu(self)
        if athkar_name in self.favorites:
            act = qt1.QAction("إزالة من المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(athkar_name, False))
        else:
            act = qt1.QAction("إضافة إلى المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(athkar_name, True))
        menu.addAction(act)
        path = os.path.join(os.getenv('appdata'), app.appName, "athkar", athkar_name)
        if os.path.exists(path):
            delete_action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("حذف الملفات الصوتية للفئة المحددة")
            btn.setStyleSheet("background-color: #8B0000; color: white;")
            btn.clicked.connect(lambda: (menu.close(), self.onDelete()))
            delete_action.setDefaultWidget(btn)
            menu.addAction(delete_action)
        menu.exec(qt1.QCursor.pos())

    def toggle_item_favorite(self, name, add):
        if add:
            if name not in self.favorites:
                self.favorites.append(name)
        else:
            if name in self.favorites:
                self.favorites.remove(name)
        self.save_favorites()
        self.apply_filter()

    def onDelete(self):
        itemText = self.athkerList.currentItem()
        if itemText:
            athkar_name = itemText.text()
            path = os.path.join(os.getenv('appdata'), app.appName, "athkar", athkar_name)
            if os.path.exists(path):
                confirm = guiTools.QQuestionMessageBox.view(
                    self,
                    "تأكيد الحذف",
                    f"هل أنت متأكد أنك تريد حذف فئة الأذكار '{athkar_name}'؟",
                    "نعم",
                    "لا"
                )
                if confirm == 0:
                    try:
                        shutil.rmtree(path)
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف فئة الأذكار بنجاح.")
                        self.refresh_athkar_list()
                    except Exception as e:
                        guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف فئة الأذكار: {e}")

    def normalize_arabic_text(self, text):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        return tashkeel_pattern.sub('', text)

    def onsearch(self, text):
        self.apply_filter(text)

    def apply_filter(self, text=None):
        if not self.all_athkars_data:
            return
        if text is None:
            text = self.search_bar.text()
        search_pattern = self.normalize_arabic_text(text).strip()
        filtered_athkars = []
        filtered_data_for_display = []
        for athker in self.all_athkars_data:
            name = athker["name"]
            if self.show_favorites_only and name not in self.favorites:
                continue
            if search_pattern:
                normalized_name = self.normalize_arabic_text(name)
                if search_pattern not in normalized_name:
                    continue
            filtered_athkars.append(name)
            filtered_data_for_display.append(athker)
        self.athkerList.clear()
        self.athkerList.addItems(filtered_athkars)
        self.data = filtered_data_for_display

    def refresh_athkar_list(self):
        self.is_loaded = False
        self.showEvent(None)
