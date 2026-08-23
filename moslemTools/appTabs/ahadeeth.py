import gui, guiTools, functions, os, re
from settings import settings_handler, app
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import threading


class AhadeethLoader(qt2.QThread):
    data_loaded = qt2.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            book_list = list(functions.ahadeeth.ahadeeths.keys())
            self.data_loaded.emit(book_list)
        except Exception as e:
            print(f"Error loading ahadeeth: {e}")
            self.data_loaded.emit([])


class hadeeth(qt.QWidget):
    def __init__(self):
        super().__init__()
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        qt1.QShortcut("f5", self).activated.connect(self.refresh)

        self.favorites = []
        self.show_favorites_only = False
        self.fav_file_path = os.path.join(os.getenv('appdata'), app.appName, "ahadeeth_favorites.json")
        self.load_favorites()

        self.all_books_list = []
        self.list_of_ahadeeth = guiTools.QListWidget()
        self.list_of_ahadeeth.setFont(font)
        self.list_of_ahadeeth.itemClicked.connect(self.open)
        layout = qt.QVBoxLayout(self)

        top_layout = qt.QHBoxLayout()

        search_v_layout = qt.QVBoxLayout()
        serch = qt.QLabel("البحث عن كتاب حديث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن كتاب حديث")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        search_v_layout.addWidget(serch)
        search_v_layout.addWidget(self.search_bar)

        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white; min-height: 50px; padding: 0 20px; font-weight: bold;")
        self.fav_btn.clicked.connect(self.toggle_favorites)

        view_mode_v_layout = qt.QVBoxLayout()
        self.view_mode_label = qt.QLabel("طريقة عرض العناصر")
        self.view_mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.view_mode_combo = qt.QComboBox()
        self.view_mode_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.view_mode_combo.setAccessibleName("طريقة عرض العناصر")
        self.view_mode_combo.addItems(["عمودي", "شبكي"])
        grid_enabled = settings_handler.get("ahadeeth", "grid_view") == "True"
        self.view_mode_combo.setCurrentIndex(1 if grid_enabled else 0)
        self.view_mode_combo.currentIndexChanged.connect(self.on_view_mode_changed)
        view_mode_v_layout.addWidget(self.view_mode_label)
        view_mode_v_layout.addWidget(self.view_mode_combo)

        top_layout.addLayout(search_v_layout, 1)
        top_layout.addWidget(self.fav_btn)
        top_layout.addLayout(view_mode_v_layout)
        layout.addLayout(top_layout)

        layout.addWidget(self.list_of_ahadeeth)
        bottom_widget = qt.QWidget()
        bottom_widget.setLayoutDirection(qt2.Qt.LayoutDirection.RightToLeft)
        bottom_layout = qt.QHBoxLayout(bottom_widget)
        self.info2 = guiTools.QNavigableLabel("يمكنكم تحميل المزيد من تحميل موارد إضافية من الإعدادات")
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        stacked_layout = qt.QVBoxLayout()
        stacked_layout.setSpacing(4)
        self.info = guiTools.QNavigableLabel("في حالة تحميل كتاب جديد, يرجى إعادة تحميل قائمة الكتب بالضغط على زر F5")
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1 = guiTools.QNavigableLabel("لمزيد من خيارات كتاب الحديث، نستخدم زر التطبيقات أو click الأيمن")
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        stacked_layout.addWidget(self.info)
        stacked_layout.addWidget(self.info1)
        bottom_layout.addWidget(self.info2, 1)
        bottom_layout.addSpacing(15)
        bottom_layout.addLayout(stacked_layout, 1)
        layout.addWidget(bottom_widget)
        self.list_of_ahadeeth.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_ahadeeth.setSpacing(3)
        self.list_of_ahadeeth.customContextMenuRequested.connect(self.open_context_menu)
        qt1.QShortcut("delete", self).activated.connect(self.onDelete)
        self.is_loaded = False
        self.loader_thread = None
        self.on_view_mode_changed(self.view_mode_combo.currentIndex())
        self.update_favorites_ui_state()

    def load_favorites(self):
        try:
            if os.path.exists(self.fav_file_path):
                with open(self.fav_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.favorites = data.get("favorites", [])
                        self.show_favorites_only = data.get("show_favorites_only", False)
                    else:
                        self.favorites = data
                        self.show_favorites_only = False
            else:
                self.favorites = []
                self.show_favorites_only = False
        except Exception:
            self.favorites = []
            self.show_favorites_only = False

    def save_favorites(self):
        try:
            os.makedirs(os.path.dirname(self.fav_file_path), exist_ok=True)
            with open(self.fav_file_path, "w", encoding="utf-8") as f:
                json.dump({"favorites": self.favorites, "show_favorites_only": self.show_favorites_only}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def update_favorites_ui_state(self):
        if self.show_favorites_only:
            self.fav_btn.setText("عرض جميع كتب الأحاديث")
        else:
            self.fav_btn.setText("فتح قائمة المفضلة")

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        self.save_favorites()
        self.update_favorites_ui_state()
        self.apply_filter()

    def open_context_menu(self, pos):
        item = self.list_of_ahadeeth.itemAt(pos)
        if not item:
            item = self.list_of_ahadeeth.currentItem()
        if not item:
            return
        self.list_of_ahadeeth.setCurrentItem(item)
        book_name = item.text()
        if book_name in ["جاري تحميل قائمة الكتب...", "لا توجد كتب أحاديث في قائمة المفضلة"]:
            return
        menu = guiTools.QCustomContextMenu(self)
        if book_name in self.favorites:
            act = qt1.QAction("إزالة من المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(book_name, False))
        else:
            act = qt1.QAction("إضافة إلى المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(book_name, True))
        menu.addAction(act)
        if book_name not in ["الأربعون نووية", "الأربعون قُدسية"]:
            delete_action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("حذف الكتاب المحدد: delete")
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

    def update_grid_size(self):
        if self.view_mode_combo.currentIndex() != 1:
            return
        fm = self.list_of_ahadeeth.fontMetrics()
        max_w = 0
        for i in range(self.list_of_ahadeeth.count()):
            txt = self.list_of_ahadeeth.item(i).text()
            w = fm.horizontalAdvance(txt) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(txt).width()
            if w > max_w:
                max_w = w
        cell_w = max(200, max_w + 60)
        cell_h = max(60, fm.height() * 2 + 20)
        self.list_of_ahadeeth.setGridSize(qt2.QSize(cell_w, cell_h))

    def on_view_mode_changed(self, index):
        is_grid = (index == 1)
        settings_handler.set("ahadeeth", "grid_view", "True" if is_grid else "False")
        if is_grid:
            self.list_of_ahadeeth.setStyleSheet("""
                QListWidget::item {
                    padding: 10px 18px;
                    margin: 4px;
                    border-radius: 6px;
                }
                QListWidget::item:selected {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
                QListWidget::item:focus {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
            """)
            self.list_of_ahadeeth.setViewMode(qt.QListView.ViewMode.IconMode)
            self.list_of_ahadeeth.setResizeMode(qt.QListView.ResizeMode.Adjust)
            self.update_grid_size()
            self.list_of_ahadeeth.setSpacing(6)
        else:
            self.list_of_ahadeeth.setStyleSheet("")
            self.list_of_ahadeeth.setViewMode(qt.QListView.ViewMode.ListMode)
            self.list_of_ahadeeth.setResizeMode(qt.QListView.ResizeMode.Fixed)
            self.list_of_ahadeeth.setGridSize(qt2.QSize())
            self.list_of_ahadeeth.setSpacing(3)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.is_loaded:
            self.list_of_ahadeeth.clear()
            self.list_of_ahadeeth.addItem("جاري تحميل قائمة الكتب...")
            if self.loader_thread is None:
                self.loader_thread = AhadeethLoader()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()

    def on_data_loaded(self, book_list):
        self.all_books_list = book_list
        self.is_loaded = True
        self.update_favorites_ui_state()
        self.apply_filter()

    def onDelete(self):
        selectedItem = self.list_of_ahadeeth.currentItem()
        if selectedItem:
            itemText = selectedItem.text()
            if itemText in ["جاري تحميل قائمة الكتب...", "لا توجد كتب أحاديث في قائمة المفضلة"]:
                return
            if itemText == "الأربعون نووية" or itemText == "الأربعون قُدسية":
                guiTools.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذا الكتاب ")
            else:
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا الكتاب", "نعم", "لا")
                if question == 0:
                    name = functions.ahadeeth.ahadeeths[itemText]
                    os.remove(os.path.join(os.getenv('appdata'), app.appName, "ahadeeth", name))
                    functions.ahadeeth.reload_ahadeeths()
                    self.all_books_list = list(functions.ahadeeth.ahadeeths.keys())
                    self.apply_filter()
                    guiTools.speak("تم الحذف")

    def open(self):
        item = self.list_of_ahadeeth.currentItem()
        if item and item.text() not in ["جاري تحميل قائمة الكتب...", "لا توجد كتب أحاديث في قائمة المفضلة"]:
            gui.hadeeth_viewer(self, functions.ahadeeth.ahadeeths[item.text()]).exec()

    def refresh(self):
        functions.ahadeeth.reload_ahadeeths()
        self.all_books_list = list(functions.ahadeeth.ahadeeths.keys())
        self.apply_filter()

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches

    def onsearch(self):
        self.apply_filter()

    def apply_filter(self, text=None):
        if not self.all_books_list:
            return
        if text is None:
            text = self.search_bar.text()
        search_text = self.normalize_arabic_text(text).strip() if hasattr(self, 'normalize_arabic_text') else text.lower().strip()
        filtered_books = []
        for book in self.all_books_list:
            if self.show_favorites_only and book not in self.favorites:
                continue
            if search_text:
                normalized_book = self.normalize_arabic_text(book) if hasattr(self, 'normalize_arabic_text') else book.lower()
                if search_text not in normalized_book:
                    continue
            filtered_books.append(book)
        self.list_of_ahadeeth.clear()
        if self.show_favorites_only and not filtered_books:
            self.list_of_ahadeeth.addItem("لا توجد كتب أحاديث في قائمة المفضلة")
        else:
            self.list_of_ahadeeth.addItems(filtered_books)
        self.update_grid_size()

    def normalize_arabic_text(self, text):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        return tashkeel_pattern.sub('', text)
