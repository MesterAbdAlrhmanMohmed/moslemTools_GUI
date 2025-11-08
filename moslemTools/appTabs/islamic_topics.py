import os,json,re
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
from collections import defaultdict
from guiTools.QListWidget import QListWidget
from gui.islamicTopicViewer import IslamicTopicViewer
class IslamicTopicsTab(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.DATA_PATH = os.path.join("data", "json", "IslamicTopics")
        self.initUI()
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[^\u0621-\u063A\u0641-\u064A\s]+')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches
    def initUI(self):
        self.tabs = qt.QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background: #2b2b2b;
                color: white;
                padding: 10px 20px;
                border: 1px solid #444;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                min-width: 100px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: white;
                border: 1px solid #0078d7;
            }
            QTabBar::tab:hover {
                background: #3a3a3a;
            }
        """)
        self.tabs.addTab(self.create_islamiyat_tab(), "إسلاميات")
        self.tabs.addTab(self.create_hajj_tab(), "الحج والعمرة")
        self.tabs.addTab(self.create_seerah_tab(), "السيرة النبوية")
        self.tabs.addTab(self.create_ramadan_tab(), "رمضان")
        self.tabs.addTab(self.create_ad3yah_tab(), "أدعية")
        main_layout = qt.QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    def load_json_data(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading {file_path}: {e}")
            return None
    def create_islamiyat_tab(self):
        widget = qt.QWidget()
        main_layout = qt.QVBoxLayout(widget)
        content_layout = qt.QHBoxLayout()
        left_column = qt.QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        main_list_label = qt.QLabel("القائمة الرئيسية")
        main_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(main_list_label)
        main_list = QListWidget()
        main_list.setSpacing(3)
        main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        main_list.setMaximumWidth(250)
        left_column.addWidget(main_list)
        content_layout.addLayout(left_column)
        right_column = qt.QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        search_layout = qt.QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_label = qt.QLabel("البحث في القائمة الفرعية:")
        sub_search = qt.QLineEdit()
        sub_search.setPlaceholderText("بحث...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(sub_search)
        right_column.addLayout(search_layout)
        sub_list_label = qt.QLabel("القائمة الفرعية")
        sub_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(sub_list_label)
        sub_list = QListWidget()
        sub_list.setSpacing(3)
        sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        right_column.addWidget(sub_list)
        content_layout.addLayout(right_column)
        main_layout.addLayout(content_layout)
        islamiyat_path = os.path.join(self.DATA_PATH, "إسلاميات")
        files_order = [
            "55 وصية من النبي.json", "الإيمان بالله تعالى.json", "الجنة ما هي وما درجاتها.json",
            "الرقية الشرعية.json", "رياض الصالحين.json", "علمنى شيء فى الإسلام.json",
            "فضائل الأعمال عند الله تعالى.json", "فرص ذهبية.json"
        ]
        file_mapping = {}
        for filename in files_order:
            base_name = os.path.splitext(filename)[0]
            main_list.addItem(base_name)
            file_mapping[base_name] = os.path.join(islamiyat_path, filename)    
        def filter_sub():
            search_text = sub_search.text()
            if not hasattr(sub_list, 'original_items'): return
            sub_list.clear()
            if not search_text:
                sub_list.addItems(sub_list.original_items)
            else:
                results = self.search(search_text, sub_list.original_items)
                sub_list.addItems(results)        
        def main_list_changed(current, previous):
            if not current:
                sub_list.clear()
                sub_search.hide()
                return
            item_text = current.text()
            file_path = file_mapping.get(item_text)
            if not file_path:
                sub_list.clear()
                sub_search.hide()
                return            
            sub_list.file_path = file_path
            if item_text in ["فرص ذهبية"]:
                sub_list.clear()
                sub_list.addItem("انقر نقراً مزدوجاً أو اضغط Enter لعرض المحتوى")
                sub_search.hide()
                return
            data = self.load_json_data(file_path)
            if not data:
                sub_list.clear()
                sub_search.hide()
                return
            sub_list.clear()
            sub_list.mapping = {}
            sub_list.original_items = []
            if item_text == "الرقية الشرعية":
                grouped_ruqya = defaultdict(list)
                for item in data:
                    key = (item.get("number"), item.get("hint"))
                    grouped_ruqya[key].append(item.get("text", ""))
                for (number, hint), texts in grouped_ruqya.items():
                    title = f'{hint} (تكرار: {number})'
                    sub_list.addItem(title)
                    sub_list.mapping[title] = "\n\n".join(texts)
                    sub_list.original_items.append(title)
            else:
                for item in data:
                    number = item.get("number", "")
                    label = item.get("label", "")
                    sub_list.addItem(str(number))
                    sub_list.mapping[str(number)] = label
                    sub_list.original_items.append(str(number))
            sub_search.show()        
        def main_list_activated(item):
            if not item: return
            item_text = item.text()
            if item_text in ["فرص ذهبية"]:
                file_path = file_mapping.get(item_text)
                data = self.load_json_data(file_path)
                if data:
                    all_topics = { "فرص ذهبية": "\n".join([d.get("text", "") for d in data]) }
                    content = all_topics["فرص ذهبية"]
                    relative_path = os.path.relpath(file_path, self.DATA_PATH).replace('\\', '/')
                    viewer = IslamicTopicViewer(self, relative_path, item_text, content, all_topics)
                    viewer.exec()
        def sub_list_activated(item):
            if not item: return
            title = item.text()
            file_path = getattr(sub_list, 'file_path', None)
            if not file_path: return
            data = self.load_json_data(file_path)
            if not data: return
            all_topics = {}
            if "الرقية الشرعية" in file_path:
                grouped_ruqya = defaultdict(list)
                for i in data:
                    key = (i.get("number"), i.get("hint"))
                    grouped_ruqya[key].append(i.get("text", ""))
                for (number, hint), texts in grouped_ruqya.items():
                    topic_title = f'{hint} (تكرار: {number})'
                    all_topics[topic_title] = "\n\n".join(texts)
            else:
                all_topics = {d.get("number", ""): d.get("label", "") for d in data}            
            content = all_topics.get(title)
            relative_path = os.path.relpath(file_path, self.DATA_PATH).replace('\\', '/')
            if content:
                viewer = IslamicTopicViewer(widget, relative_path, title, content, all_topics)
                viewer.exec()
        sub_search.textChanged.connect(filter_sub)
        main_list.currentItemChanged.connect(main_list_changed)
        main_list.itemDoubleClicked.connect(main_list_activated)
        main_list.itemActivated.connect(main_list_activated)
        sub_list.itemDoubleClicked.connect(sub_list_activated)
        sub_list.itemActivated.connect(sub_list_activated)
        widget.setTabOrder(main_list, sub_search)
        widget.setTabOrder(sub_search, sub_list)
        sub_search.hide()
        main_list.setFocus()
        return widget
    def create_hajj_tab(self):
        widget = qt.QWidget()
        layout = qt.QVBoxLayout(widget)
        search_layout = qt.QHBoxLayout()
        search_label = qt.QLabel("البحث:")
        search_edit = qt.QLineEdit()
        search_edit.setPlaceholderText("بحث...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        list_widget = QListWidget()
        list_widget.setSpacing(3)
        list_widget.setStyleSheet("QListWidget::item { font-weight: bold; }")
        layout.addWidget(list_widget)
        hajj_path = os.path.join(self.DATA_PATH, "الحج والعمرة")
        file_mapping = {}
        all_items = []
        if os.path.exists(hajj_path):
            files = sorted(os.listdir(hajj_path))
            for filename in files:
                if filename.endswith('.json'):
                    base_name = os.path.splitext(filename)[0]
                    list_widget.addItem(base_name)
                    file_mapping[base_name] = os.path.join(hajj_path, filename)
                    all_items.append(base_name)    
        def filter_list():
            search_text = search_edit.text()
            list_widget.clear()
            if not search_text:
                list_widget.addItems(all_items)
            else:
                results = self.search(search_text, all_items)
                list_widget.addItems(results)
        def item_activated(item):
            if not item: return
            base_name = item.text()
            file_path = file_mapping.get(base_name)
            if file_path:
                data = self.load_json_data(file_path)
                if data:
                    all_topics = {entry.get("title", f"بند {i+1}"): f"{entry.get('title', '')}\n\n{entry.get('text', '')}" for i, entry in enumerate(data)}
                    if not all_topics: return                    
                    first_title = list(all_topics.keys())[0]
                    first_content = all_topics[first_title]
                    relative_path = os.path.relpath(file_path, self.DATA_PATH).replace('\\', '/')                    
                    viewer = IslamicTopicViewer(widget, relative_path, first_title, first_content, all_topics)
                    viewer.exec()
        search_edit.textChanged.connect(filter_list)
        list_widget.itemDoubleClicked.connect(item_activated)
        list_widget.itemActivated.connect(item_activated)
        list_widget.setFocus()
        widget.setTabOrder(search_edit, list_widget)
        return widget
    def create_seerah_tab(self):
        files = [
            "نبذة عن حياة الرسول صلى الله عليه وسلم.json",
            "حياة الرسول صلى الله عليه وسلم.json",
            "سيرة زوجات وأولاد الرسول صلى الله عليه وسلم.json",
            "غزوات الرسول صلى الله عليه وسلم.json"
        ]
        return self._create_complex_list_tab("السيرة النبوية", files)
    def create_ramadan_tab(self):
        ramadan_path = os.path.join(self.DATA_PATH, "رمضان")
        files = sorted([f for f in os.listdir(ramadan_path) if f.endswith('.json')]) if os.path.exists(ramadan_path) else []
        return self._create_complex_list_tab("رمضان", files)
    def _create_complex_list_tab(self, dir_name, file_order):
        widget = qt.QWidget()
        main_layout = qt.QVBoxLayout(widget)
        content_layout = qt.QHBoxLayout()
        left_column = qt.QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        main_list_label = qt.QLabel("القائمة الرئيسية")
        main_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(main_list_label)
        main_list = QListWidget()
        main_list.setSpacing(3)
        main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        main_list.setMaximumWidth(250)
        left_column.addWidget(main_list)
        content_layout.addLayout(left_column)
        right_column = qt.QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        search_layout = qt.QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_label = qt.QLabel("البحث في القائمة الفرعية:")
        sub_search = qt.QLineEdit()
        sub_search.setPlaceholderText("بحث...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(sub_search)
        right_column.addLayout(search_layout)
        sub_list_label = qt.QLabel("القائمة الفرعية")
        sub_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(sub_list_label)
        sub_list = QListWidget()
        sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        right_column.addWidget(sub_list)
        content_layout.addLayout(right_column)
        main_layout.addLayout(content_layout)
        base_path = os.path.join(self.DATA_PATH, dir_name)
        file_mapping = {}
        for filename in file_order:
            base_name = os.path.splitext(filename)[0]
            main_list.addItem(base_name)
            file_mapping[base_name] = os.path.join(base_path, filename)    
        def show_sublist(current, previous):
            if not current:
                sub_list.clear()
                sub_search.hide()
                return
            item_text = current.text()
            file_path = file_mapping.get(item_text)
            if not file_path:
                sub_list.clear()
                sub_search.hide()
                return        
            data = self.load_json_data(file_path)
            if not data:
                sub_list.clear()
                sub_search.hide()
                return            
            sub_list.clear()
            sub_list.file_path = file_path
            sub_list.mapping = {}
            sub_list.original_items = []
            for entry in data:
                title = entry.get("number", "")
                sub_list.addItem(str(title))
                sub_list.mapping[str(title)] = entry.get("label", "")
                sub_list.original_items.append(str(title))
            sub_search.show()
        def filter_sub(text):
            if not hasattr(sub_list, 'original_items'): return
            sub_list.clear()
            if not text:
                sub_list.addItems(sub_list.original_items)
            else:
                results = self.search(text, sub_list.original_items)
                sub_list.addItems(results)
        def sub_list_activated(item):
            if not item: return
            title = item.text()
            file_path = getattr(sub_list, 'file_path', None)
            if not file_path: return            
            data = self.load_json_data(file_path)
            if not data: return            
            all_topics = {entry.get("number", ""): entry.get("label", "") for entry in data}
            content = all_topics.get(title)
            relative_path = os.path.relpath(file_path, self.DATA_PATH).replace('\\', '/')            
            if content:
                viewer = IslamicTopicViewer(widget, relative_path, title, content, all_topics)
                viewer.exec()
        main_list.currentItemChanged.connect(show_sublist)
        sub_search.textChanged.connect(filter_sub)
        sub_list.itemDoubleClicked.connect(sub_list_activated)
        sub_list.itemActivated.connect(sub_list_activated)
        widget.setTabOrder(main_list, sub_search)
        widget.setTabOrder(sub_search, sub_list)
        sub_search.hide()
        main_list.setFocus()
        return widget
    def create_ad3yah_tab(self):
        widget = qt.QWidget()
        main_layout = qt.QVBoxLayout(widget)
        content_layout = qt.QHBoxLayout()
        left_column = qt.QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        main_list_label = qt.QLabel("القائمة الرئيسية")
        main_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(main_list_label)
        main_list = QListWidget()
        main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        main_list.setMaximumWidth(250)
        left_column.addWidget(main_list)
        content_layout.addLayout(left_column)
        right_column = qt.QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        search_layout = qt.QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_label = qt.QLabel("البحث في القائمة الفرعية:")
        sub_search = qt.QLineEdit()
        sub_search.setPlaceholderText("بحث...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(sub_search)
        right_column.addLayout(search_layout)
        sub_list_label = qt.QLabel("القائمة الفرعية")
        sub_list_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(sub_list_label)
        sub_list = QListWidget()
        sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        right_column.addWidget(sub_list)
        content_layout.addLayout(right_column)
        main_layout.addLayout(content_layout)
        ad3yah_path = os.path.join(self.DATA_PATH, "أدعية")
        masael_folder_name = "مسائل الدعاء_"
        masael_path = os.path.join(ad3yah_path, masael_folder_name)
        file_mapping = {}
        if os.path.exists(ad3yah_path):
            files = sorted([f for f in os.listdir(ad3yah_path) if f.endswith('.json')])
            for filename in files:
                base_name = os.path.splitext(filename)[0]
                main_list.addItem(base_name)
                file_mapping[base_name] = {"type": "file", "path": os.path.join(ad3yah_path, filename)}
        main_list.addItem(masael_folder_name)
        file_mapping[masael_folder_name] = {"type": "folder", "path": masael_path}        
        def main_list_changed(current, previous):
            if not current:
                sub_list.clear()
                sub_search.hide()
                return
            item_text = current.text()
            info = file_mapping.get(item_text)
            if not info:
                sub_list.clear()
                sub_search.hide()
                return
            sub_list.clear()
            sub_list.mapping = {}
            sub_list.original_items = []
            if info["type"] == "folder":
                if os.path.exists(info["path"]):
                    for sub_filename in sorted(os.listdir(info["path"])):
                        if sub_filename.endswith('.json'):
                            sub_base_name = os.path.splitext(sub_filename)[0]
                            sub_list.addItem(sub_base_name)
                            sub_list.mapping[sub_base_name] = os.path.join(info["path"], sub_filename)
                            sub_list.original_items.append(sub_base_name)
                if sub_list.original_items:
                    sub_search.show()
                else:
                    sub_search.hide()
            else:
                sub_list.addItem("انقر نقراً مزدوجاً أو اضغط Enter لعرض المحتوى")
                sub_search.hide()    
        def filter_sub():
            search_text = sub_search.text()
            if not hasattr(sub_list, 'original_items'): return
            sub_list.clear()
            if not search_text:
                sub_list.addItems(sub_list.original_items)
            else:
                results = self.search(search_text, sub_list.original_items)
                sub_list.addItems(results)        
        def main_list_activated(item):
            if not item: return
            info = file_mapping.get(item.text())
            if not info or info["type"] != "file": return
            data = self.load_json_data(info["path"])
            if data:
                all_topics = { item.text(): "\n\n".join([d.get("text", "") for d in data]) }
                content = all_topics[item.text()]
                relative_path = os.path.relpath(info["path"], self.DATA_PATH).replace('\\', '/')
                viewer = IslamicTopicViewer(widget, relative_path, item.text(), content, all_topics)
                viewer.exec()
        def sub_list_activated(item):
            if not item: return
            if hasattr(sub_list, 'mapping') and item.text() in sub_list.mapping:
                file_path = sub_list.mapping[item.text()]
                data = self.load_json_data(file_path)
                if data:
                    all_topics = { item.text(): "\n\n".join([d.get("text", "") for d in data]) }
                    content = all_topics[item.text()]
                    relative_path = os.path.relpath(file_path, self.DATA_PATH).replace('\\', '/')
                    viewer = IslamicTopicViewer(widget, relative_path, item.text(), content, all_topics)
                    viewer.exec()
        sub_search.textChanged.connect(filter_sub)
        main_list.currentItemChanged.connect(main_list_changed)
        main_list.itemDoubleClicked.connect(main_list_activated)
        main_list.itemActivated.connect(main_list_activated)
        sub_list.itemDoubleClicked.connect(sub_list_activated)
        sub_list.itemActivated.connect(sub_list_activated)
        widget.setTabOrder(main_list, sub_search)
        widget.setTabOrder(sub_search, sub_list)
        sub_search.hide()
        main_list.setFocus()
        return widget