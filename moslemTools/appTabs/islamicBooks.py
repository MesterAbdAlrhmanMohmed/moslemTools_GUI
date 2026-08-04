import gui,guiTools,functions,os,re
import ujson as json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import threading


class Worker(qt2.QObject):
    finished = qt2.pyqtSignal()
    data_ready = qt2.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def refresh_books(self):
        try:
            functions.islamicBooks.reload_books()
            book_list = list(functions.islamicBooks.books.keys())
            self.data_ready.emit(book_list)
        except Exception as e:
            print(f"Error in refresh thread: {e}")
        finally:
            self.finished.emit()


class DeleteWorker(qt2.QObject):
    finished = qt2.pyqtSignal()
    deletion_complete = qt2.pyqtSignal(bool)

    def __init__(self, itemText):
        super().__init__()
        self.itemText = itemText

    def delete_book(self):
        try:
            name=functions.islamicBooks.books[self.itemText]
            os.remove(os.path.join(os.getenv('appdata'),app.appName,"islamicBooks",name))
            functions.islamicBooks.reload_books()
            self.deletion_complete.emit(True)
        except Exception as e:
            print(f"Error during deletion: {e}")
            self.deletion_complete.emit(False)
        finally:
            self.finished.emit()


class LoaderThread(qt2.QThread):
    data_loaded = qt2.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            functions.islamicBooks.load_books()
            book_list = list(functions.islamicBooks.books.keys())
            self.data_loaded.emit(book_list)
        except Exception as e:
            print(f"Error loading books: {e}")
            self.data_loaded.emit([])


class EditCategoriesDialog(qt.QDialog):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.setWindowTitle("تعديل اسم فئة")
        self.categories = list(categories)
        self.session_edits = {}
        layout = qt.QVBoxLayout(self)

        label = qt.QLabel("اختر الفئة المراد تعديل اسمها:")
        label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.combo = qt.QComboBox()
        self.combo.addItems(self.categories)
        layout.addWidget(self.combo)

        self.name_input = qt.QLineEdit()
        self.name_input.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_input)

        self.ok_btn = guiTools.QPushButton("حفظ")
        self.ok_btn.setStyleSheet("background-color: #006400; color: white; padding: 5px;")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = guiTools.QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("background-color: #8B0000; color: white; padding: 5px;")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout = qt.QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        self.name_input.textChanged.connect(self.on_text_changed)
        self.on_combo_changed(0)

    def on_combo_changed(self, index):
        cat = self.combo.currentText()
        if not cat:
            return
        prompt_text = f"قم بكتابة الاسم الجديد لتبويبة {cat}"
        self.name_input.setAccessibleName(prompt_text)
        self.name_input.setPlaceholderText(prompt_text)
        self.name_input.blockSignals(True)
        if cat in self.session_edits:
            self.name_input.setText(self.session_edits[cat])
        else:
            self.name_input.clear()
        self.name_input.blockSignals(False)
        self.adjustSize()

    def on_text_changed(self, text):
        cat = self.combo.currentText()
        if cat:
            self.session_edits[cat] = text.strip()
        self.adjustSize()


class IslamicBooks(qt.QWidget):
    def __init__(self):
        super().__init__()
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        layout=qt.QVBoxLayout(self)
        self.worker = None
        self.delete_worker = None
        self.loader_thread = None
        self.favorites = []
        self.categories = []
        self.book_map = {}
        self.show_favorites_only = False
        self.fav_file_path = os.path.join(os.getenv('appdata'), app.appName, "islamic_books_favorites.json")
        self.cat_file_path = os.path.join(os.getenv('appdata'), app.appName, "book_categories.json")
        self.load_favorites()
        self.load_categories()
        qt1.QShortcut("f5",self).activated.connect(self.start_threaded_refresh)
        self.search_label=qt.QLabel("البحث في كل الكتب")
        self.search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_label)
        search_layout = qt.QHBoxLayout()
        self.search_bar=qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث في كل الكتب")
        self.search_bar.setAccessibleName("البحث في كل الكتب")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white; min-height: 50px; padding: 0 20px; font-weight: bold;")
        self.fav_btn.clicked.connect(self.toggle_favorites)

        self.cat_btn = guiTools.QPushButton("إضافة فئة")
        self.cat_btn.setStyleSheet("background-color: #8E2405; color: white; min-height: 50px; padding: 0 20px; font-weight: bold;")
        self.cat_btn.clicked.connect(self.on_cat_btn_clicked)

        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.fav_btn)
        search_layout.addWidget(self.cat_btn)
        layout.addLayout(search_layout)

        self.category_tabs = qt.QTabBar()
        self.category_tabs.setElideMode(qt2.Qt.TextElideMode.ElideNone)
        self.category_tabs.setExpanding(False)
        self.category_tabs.setStyleSheet("""QTabBar::tab { background: #2b2b2b; color: white; padding: 10px 20px; border: 1px solid #444; border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; font-weight: bold; } QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } QTabBar::tab:hover { background: #3a3a3a; }""")
        self.category_tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.category_tabs)

        self.list_of_abook=guiTools.QListWidget()
        self.list_of_abook.setSpacing(3)
        self.list_of_abook.itemClicked.connect(self.open)
        layout.addWidget(self.list_of_abook)

        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText("في حالة تحميل كتاب جديد, يرجى إعادة تحميل قائمة الكتب بالضغت على زر F5")
        layout.addWidget(self.info)
        self.info1=qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info1.setText("تنبيه هام , مطور البرنامج غير مسؤول عن محتوى هذه الكتب")
        self.info2=qt.QLabel()
        self.info2.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info2.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info2.setText("لخيارات الكتاب المحدد، نستخدم مفتاح التطبيقات أو click الأيمن")
        layout.addWidget(self.info2)
        self.info4=qt.QLabel()
        self.info4.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info4.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info4.setText("يمكن استخدام زر الحذف delete لحذف الكتاب المحدد")
        layout.addWidget(self.info4)
        layout.addWidget(self.info1)
        self.info3=qt.QLabel()
        self.info3.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info3.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info3.setText("يمكنكم تحميل المزيد من تحميل موارد إضافية من الإعدادات")
        layout.addWidget(self.info3)
        self.list_of_abook.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_of_abook.customContextMenuRequested.connect(self.open_context_menu)
        qt1.QShortcut("delete",self).activated.connect(self.onDelete)
        self.is_loaded = False
        self.update_categories_ui()

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

    def load_categories(self):
        try:
            if os.path.exists(self.cat_file_path):
                with open(self.cat_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.categories = data.get("categories", [])
                    self.book_map = data.get("book_map", {})
            else:
                self.categories = []
                self.book_map = {}
        except Exception:
            self.categories = []
            self.book_map = {}

    def save_categories(self):
        try:
            os.makedirs(os.path.dirname(self.cat_file_path), exist_ok=True)
            with open(self.cat_file_path, "w", encoding="utf-8") as f:
                json.dump({"categories": self.categories, "book_map": self.book_map}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def update_categories_ui(self):
        if len(self.categories) == 0:
            self.cat_btn.setText("إضافة فئة")
            self.category_tabs.setVisible(False)
        else:
            self.cat_btn.setText("خيارات فئات الكتب")
            self.category_tabs.setVisible(not self.show_favorites_only)
        self.category_tabs.blockSignals(True)
        while self.category_tabs.count() > 0:
            self.category_tabs.removeTab(0)
        self.category_tabs.addTab("كل الكتب")
        for cat in self.categories:
            self.category_tabs.addTab(cat)
        self.category_tabs.blockSignals(False)
        if self.is_loaded:
            self.apply_filter()

    def on_tab_changed(self, index):
        self.apply_filter()

    def on_cat_btn_clicked(self):
        if len(self.categories) == 0:
            self.create_new_category()
        else:
            menu = qt.QMenu(self)
            act_add = qt1.QAction("إنشاء فئة جديدة", self)
            act_add.triggered.connect(self.create_new_category)
            menu.addAction(act_add)

            act_edit = qt1.QAction("تعديل اسم فئة", self)
            act_edit.triggered.connect(self.edit_category)
            menu.addAction(act_edit)

            del_action = qt.QWidgetAction(self)
            del_btn = guiTools.QPushButton("حذف فئة")
            del_btn.setStyleSheet("background-color: #8B0000; color: white;")
            del_btn.clicked.connect(lambda: (menu.close(), self.delete_category()))
            del_action.setDefaultWidget(del_btn)
            menu.addAction(del_action)

            menu.exec(qt1.QCursor.pos())

    def create_new_category(self):
        name, ok = guiTools.QInputDialog.getText(self, "إنشاء فئة جديدة", "قم بكتابة اسم الفئة الجديدة:")
        if ok and name.strip():
            name = name.strip()
            if name in self.categories or name == "كل الكتب":
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "هذه الفئة موجودة بالفعل أو غير صالحة.")
                return
            self.categories.append(name)
            self.save_categories()
            self.update_categories_ui()
            guiTools.MessageBox.view(self, "تمت الإضافة", f"تم إنشاء الفئة '{name}' بنجاح.")

    def delete_category(self):
        if not self.categories:
            return
        cat_name, ok = guiTools.QCustomListDialog.getItem(self, "حذف فئة", "اختر الفئة المراد حذفها:", self.categories, ok_text="إزالة", ok_style="background-color: #8B0000; color: white; padding: 5px;")
        if ok and cat_name:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد من حذف الفئة '{cat_name}'؟", "نعم", "لا")
            if confirm == 0:
                if cat_name in self.categories:
                    self.categories.remove(cat_name)
                for b_name in list(self.book_map.keys()):
                    if cat_name in self.book_map[b_name]:
                        self.book_map[b_name].remove(cat_name)
                        if not self.book_map[b_name]:
                            del self.book_map[b_name]
                self.save_categories()
                self.update_categories_ui()
                guiTools.MessageBox.view(self, "تم الحذف", f"تم حذف الفئة '{cat_name}' بنجاح.")

    def edit_category(self):
        if not self.categories:
            return
        dlg = EditCategoriesDialog(self, self.categories)
        if dlg.exec() == qt.QDialog.DialogCode.Accepted:
            has_changes = False
            for old_name, new_name in dlg.session_edits.items():
                if new_name and new_name != old_name and new_name not in self.categories and new_name != "كل الكتب":
                    if old_name in self.categories:
                        idx = self.categories.index(old_name)
                        self.categories[idx] = new_name
                    for b_name, cat_list in self.book_map.items():
                        if old_name in cat_list:
                            c_idx = cat_list.index(old_name)
                            cat_list[c_idx] = new_name
                    has_changes = True
            if has_changes:
                self.save_categories()
                self.update_categories_ui()
                guiTools.MessageBox.view(self, "تم التعديل", "تم تعديل أسماء الفئات بنجاح.")

    def update_favorites_ui_state(self):
        if self.show_favorites_only:
            self.fav_btn.setText("عرض جميع الكتب")
            if hasattr(self, 'category_tabs'):
                self.category_tabs.setVisible(False)
            if hasattr(self, 'cat_btn'):
                self.cat_btn.setVisible(False)
        else:
            self.fav_btn.setText("فتح قائمة المفضلة")
            if hasattr(self, 'category_tabs'):
                self.category_tabs.setVisible(len(self.categories) > 0)
            if hasattr(self, 'cat_btn'):
                self.cat_btn.setVisible(True)

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        self.save_favorites()
        self.update_favorites_ui_state()
        self.apply_filter()

    def showEvent(self, event):
        if event:
            super().showEvent(event)
        if not self.is_loaded:
            self.list_of_abook.clear()
            self.list_of_abook.addItem("جاري تحميل قائمة الكتب...")
            if self.loader_thread is None:
                self.loader_thread = LoaderThread()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()

    def on_data_loaded(self, book_list):
        self.is_loaded = True
        self.update_favorites_ui_state()
        self.apply_filter()

    def start_threaded_refresh(self):
        if self.worker is None:
            self.worker = Worker()
            self.worker.data_ready.connect(self.handle_data_ready)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(lambda: setattr(self, 'worker', None))
            thread = threading.Thread(target=self.worker.refresh_books)
            thread.daemon = True
            thread.start()

    def handle_data_ready(self, book_list):
        self.apply_filter()

    def start_threaded_delete(self, itemText):
        if self.delete_worker is None:
            self.delete_worker = DeleteWorker(itemText)
            self.delete_worker.deletion_complete.connect(self.handle_deletion_complete)
            self.delete_worker.finished.connect(self.delete_worker.deleteLater)
            self.delete_worker.finished.connect(lambda: setattr(self, 'delete_worker', None))
            thread = threading.Thread(target=self.delete_worker.delete_book)
            thread.daemon = True
            thread.start()

    def handle_deletion_complete(self, success):
        if success:
            self.apply_filter()
            guiTools.speak("تم الحذف")
        else:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف الملف ")

    def add_book_to_category(self, book_name):
        if not self.categories:
            return
        book_cats = self.book_map.get(book_name, [])
        available_cats = [c for c in self.categories if c not in book_cats]
        if not available_cats:
            guiTools.MessageBox.view(self, "تنبيه", f"الكتاب '{book_name}' مضاف بالفعل إلى جميع الفئات المتاحة.")
            return
        cat_name, ok = guiTools.QCustomListDialog.getItem(self, "إضافة إلى فئة", "اختر الفئة المراد إضافة الكتاب إليها:", available_cats, ok_text="إضافة", ok_style="background-color: #006400; color: white; padding: 5px;")
        if ok and cat_name:
            if cat_name in book_cats:
                guiTools.MessageBox.view(self, "تنبيه", f"الكتاب '{book_name}' موجود بالفعل في الفئة '{cat_name}'.")
                return
            if book_name not in self.book_map:
                self.book_map[book_name] = []
            self.book_map[book_name].append(cat_name)
            self.save_categories()
            self.apply_filter()
            guiTools.MessageBox.view(self, "تمت الإضافة", f"تم إضافة الكتاب '{book_name}' إلى الفئة '{cat_name}'.")

    def remove_book_from_specific_category(self, book_name):
        book_cats = self.book_map.get(book_name, [])
        if not book_cats:
            return
        cat_name, ok = guiTools.QCustomListDialog.getItem(self, "إزالة من فئة", "اختر الفئة المراد إزالة الكتاب منها:", book_cats, ok_text="إزالة", ok_style="background-color: #8B0000; color: white; padding: 5px;")
        if ok and cat_name:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الإزالة", f"هل تريد إزالة الكتاب '{book_name}' من الفئة '{cat_name}'؟", "نعم", "لا")
            if confirm == 0:
                if cat_name in self.book_map.get(book_name, []):
                    self.book_map[book_name].remove(cat_name)
                    if not self.book_map[book_name]:
                        del self.book_map[book_name]
                    self.save_categories()
                    self.apply_filter()
                    guiTools.MessageBox.view(self, "تمت الإزالة", f"تم إزالة الكتاب '{book_name}' من الفئة '{cat_name}'.")

    def remove_book_from_current_category(self, book_name, cat_name):
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الإزالة", f"هل تريد إزالة الكتاب '{book_name}' من الفئة '{cat_name}'؟", "نعم", "لا")
        if confirm == 0:
            if cat_name in self.book_map.get(book_name, []):
                self.book_map[book_name].remove(cat_name)
                if not self.book_map[book_name]:
                    del self.book_map[book_name]
                self.save_categories()
                self.apply_filter()
                guiTools.MessageBox.view(self, "تمت الإزالة", f"تم إزالة الكتاب '{book_name}' من الفئة '{cat_name}'.")

    def open_context_menu(self, pos):
        item = self.list_of_abook.itemAt(pos)
        if not item:
            item = self.list_of_abook.currentItem()
        if not item:
            return
        self.list_of_abook.setCurrentItem(item)
        book_name = item.text()
        if book_name in ["جاري تحميل قائمة الكتب...", "لا توجد كتب في قائمة المفضلة", "لا توجد كتب في هذه الفئة"]:
            return
        menu = qt.QMenu(self)
        if book_name in self.favorites:
            act = qt1.QAction("إزالة من المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(book_name, False))
        else:
            act = qt1.QAction("إضافة إلى المفضلة", self)
            act.triggered.connect(lambda: self.toggle_item_favorite(book_name, True))
        menu.addAction(act)

        current_tab_text = "كل الكتب"
        if hasattr(self, 'category_tabs') and self.category_tabs.count() > 0:
            current_tab_text = self.category_tabs.tabText(self.category_tabs.currentIndex())

        if self.categories:
            add_cat_act = qt1.QAction("إضافة إلى فئة", self)
            add_cat_act.triggered.connect(lambda: self.add_book_to_category(book_name))
            menu.addAction(add_cat_act)

            book_cats = self.book_map.get(book_name, [])

            if current_tab_text == "كل الكتب":
                if book_cats:
                    rem_action = qt.QWidgetAction(self)
                    rem_btn = guiTools.QPushButton("إزالة من فئة معينة")
                    rem_btn.setStyleSheet("background-color: #8B0000; color: white;")
                    rem_btn.clicked.connect(lambda: (menu.close(), self.remove_book_from_specific_category(book_name)))
                    rem_action.setDefaultWidget(rem_btn)
                    menu.addAction(rem_action)
            else:
                if current_tab_text in book_cats:
                    rem_action = qt.QWidgetAction(self)
                    rem_btn = guiTools.QPushButton("إزالة من هذه الفئة")
                    rem_btn.setStyleSheet("background-color: #8B0000; color: white;")
                    rem_btn.clicked.connect(lambda: (menu.close(), self.remove_book_from_current_category(book_name, current_tab_text)))
                    rem_action.setDefaultWidget(rem_btn)
                    menu.addAction(rem_action)

        if book_name != "حياة الصحابة" and book_name in functions.islamicBooks.books:
            file_name = functions.islamicBooks.books[book_name]
            file_path = os.path.join(os.getenv('appdata'), app.appName, "islamicBooks", file_name)
            if os.path.exists(file_path):
                delete_action = qt.QWidgetAction(self)
                btn = guiTools.QPushButton("حذف الكتاب المحدد")
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
        selectedItem=self.list_of_abook.currentItem()
        if selectedItem:
            itemText=selectedItem.text()
            if itemText in ["جاري تحميل قائمة الكتب...", "لا توجد كتب في قائمة المفضلة", "لا توجد كتب في هذه الفئة"]:
                return
            if itemText=="حياة الصحابة":
                guiTools.qMessageBox.MessageBox.error(self,"تنبيه","لا يمكنك حذف هذا الكتاب ")
            else:
                question=guiTools.QQuestionMessageBox.view(self,"تنبيه","هل تريد حذف هذا الكتاب","نعم","لا")
                if question==0:
                    self.start_threaded_delete(itemText)

    def open(self):
        item = self.list_of_abook.currentItem()
        if not item or item.text() in ["جاري تحميل قائمة الكتب...", "لا توجد كتب في قائمة المفضلة", "لا توجد كتب في هذه الفئة"]:
            return
        try:
            with open(os.path.join(os.getenv('appdata'),app.appName,"islamicBooks",functions.islamicBooks.books[item.text()]),"r",encoding="utf-8") as f:
                data=json.load(f)
                bookName=functions.islamicBooks.books[item.text()]
                if len(list(data.keys()))==1:
                    partName=list(data.keys())[0]
                    gui.islamicBooks.book_viewer(self,bookName,partName,data[partName]).exec()
                else:
                    gui.islamicBooks.PartSelection(self,bookName,data).exec()
        except Exception as error:
            print(error)
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر فتح الملف ")

    def refresh(self):
        self.start_threaded_refresh()

    def search(self,pattern,text_list):
        tashkeel_pattern=re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern=tashkeel_pattern.sub('', pattern)
        matches=[
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches

    def onsearch(self):
        self.apply_filter()

    def apply_filter(self, text=None):
        if not self.is_loaded:
            return
        all_books = list(functions.islamicBooks.books.keys())
        current_item = self.list_of_abook.currentItem()
        target_book = current_item.text() if current_item else None
        if text is None:
            text = self.search_bar.text()
        search_text = text.lower().strip()
        current_tab_text = "كل الكتب"
        if hasattr(self, 'category_tabs') and self.category_tabs.count() > 0:
            current_tab_text = self.category_tabs.tabText(self.category_tabs.currentIndex())
        if self.show_favorites_only:
            prompt = "البحث في المفضلة"
        elif current_tab_text == "كل الكتب":
            prompt = "البحث في كل الكتب"
        else:
            prompt = f"البحث في فئة {current_tab_text}"
        if hasattr(self, 'search_label'):
            self.search_label.setText(prompt)
        if hasattr(self, 'search_bar'):
            self.search_bar.setPlaceholderText(prompt)
            self.search_bar.setAccessibleName(prompt)
        filtered_books = []
        for book in all_books:
            if self.show_favorites_only:
                if book not in self.favorites:
                    continue
            elif current_tab_text != "كل الكتب":
                book_cats = self.book_map.get(book, [])
                if current_tab_text not in book_cats:
                    continue
            if search_text:
                if not self.search(search_text, [book]):
                    continue
            filtered_books.append(book)
        self.list_of_abook.clear()
        if self.show_favorites_only and not filtered_books:
            self.list_of_abook.addItem("لا توجد كتب في قائمة المفضلة")
        elif current_tab_text != "كل الكتب" and not filtered_books:
            self.list_of_abook.addItem("لا توجد كتب في هذه الفئة")
        else:
            self.list_of_abook.addItems(filtered_books)
            if target_book and target_book not in ["جاري تحميل قائمة الكتب...", "لا توجد كتب في قائمة المفضلة", "لا توجد كتب في هذه الفئة"]:
                items = self.list_of_abook.findItems(target_book, qt2.Qt.MatchFlag.MatchExactly)
                if items:
                    self.list_of_abook.setCurrentItem(items[0])
                    self.list_of_abook.scrollToItem(items[0])
                elif self.list_of_abook.count() > 0:
                    self.list_of_abook.setCurrentRow(0)
            elif self.list_of_abook.count() > 0:
                self.list_of_abook.setCurrentRow(0)
