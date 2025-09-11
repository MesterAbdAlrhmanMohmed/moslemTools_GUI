import os,json
import PyQt6.QtWidgets as qt
from collections import defaultdict
from guiTools.QListWidget import QListWidget
from guiTools.textViewer import TextViewer
class IslamicTopicsTab(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.DATA_PATH = os.path.join("data", "json", "IslamicTopics")
        self.initUI()
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
        layout = qt.QHBoxLayout(widget)                
        self.islamiyat_main_list = QListWidget()
        self.islamiyat_main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        self.islamiyat_main_list.setMaximumWidth(250)                
        self.islamiyat_sub_list = QListWidget()
        self.islamiyat_sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")        
        layout.addWidget(self.islamiyat_main_list)
        layout.addWidget(self.islamiyat_sub_list)                
        islamiyat_path = os.path.join(self.DATA_PATH, "إسلاميات")
        files_order = [
            "55 وصية من النبي.json",
            "الإيمان بالله تعالى.json",
            "الجنة ماهى وما درجاتها ووصفها.json",
            "الرقية الشرعية.json",
            "رياض الصالحين.json",
            "سنن مؤكدة.json",
            "علمنى شيء فى الإسلام.json",
            "فضائل الاعمال عند الله تعالى.json",
            "فرص ذهبية.json"
        ]
        self.islamiyat_file_mapping = {}
        for filename in files_order:
            base_name = os.path.splitext(filename)[0]
            self.islamiyat_main_list.addItem(base_name)
            self.islamiyat_file_mapping[base_name] = os.path.join(islamiyat_path, filename)        
        self.islamiyat_main_list.currentItemChanged.connect(self.islamiyat_main_list_changed)
        self.islamiyat_main_list.itemDoubleClicked.connect(self.islamiyat_main_list_activated)
        self.islamiyat_main_list.itemActivated.connect(self.islamiyat_main_list_activated)
        self.islamiyat_sub_list.itemDoubleClicked.connect(self.islamiyat_sub_list_activated)
        self.islamiyat_sub_list.itemActivated.connect(self.islamiyat_sub_list_activated)
        return widget
    def islamiyat_main_list_changed(self, current, previous):
        if not current:
            self.islamiyat_sub_list.clear()
            return
        item_text = current.text()
        file_path = self.islamiyat_file_mapping.get(item_text)
        if not file_path:
            self.islamiyat_sub_list.clear()
            return        
        if item_text in ["سنن مؤكدة", "فرص ذهبية"]:
            self.islamiyat_sub_list.clear()
            self.islamiyat_sub_list.addItem("انقر نقراً مزدوجاً أو اضغط Enter لعرض المحتوى")
            return
        data = self.load_json_data(file_path)
        if not data:
            self.islamiyat_sub_list.clear()
            return
        self.islamiyat_sub_list.clear()
        self.islamiyat_sub_list_mapping = {}
        if item_text == "الرقية الشرعية":
            grouped_ruqya = defaultdict(list)
            for item in data:
                key = (item.get("number"), item.get("hint"))
                grouped_ruqya[key].append(item.get("text", ""))            
            for (number, hint), texts in grouped_ruqya.items():
                title = f'{hint} (تكرار: {number})'
                self.islamiyat_sub_list.addItem(title)
                self.islamiyat_sub_list_mapping[title] = "\n\n".join(texts)
        else:
            for item in data:
                number = item.get("number", "")
                label = item.get("label", "")
                self.islamiyat_sub_list.addItem(str(number))
                self.islamiyat_sub_list_mapping[str(number)] = label
    def islamiyat_main_list_activated(self, item):
        if not item:
            return
        item_text = item.text()
        if item_text in ["سنن مؤكدة", "فرص ذهبية"]:
            file_path = self.islamiyat_file_mapping.get(item_text)
            data = self.load_json_data(file_path)
            if data:
                content = "\n\n".join([d.get("text", "") for d in data])
                viewer = TextViewer(self, item_text, content)
                viewer.exec()
    def islamiyat_sub_list_activated(self, item):
        if not item:
            
            return            
        item_text = item.text()
        if hasattr(self, 'islamiyat_sub_list_mapping') and item_text in self.islamiyat_sub_list_mapping:
            content = self.islamiyat_sub_list_mapping[item_text]
            viewer = TextViewer(self, item_text, content)
            viewer.exec()
    def create_hajj_tab(self):
        widget = qt.QWidget()
        layout = qt.QVBoxLayout(widget)
        list_widget = QListWidget()
        list_widget.setStyleSheet("QListWidget::item { font-weight: bold; }")        
        hajj_path = os.path.join(self.DATA_PATH, "الحج والعمرة")
        file_mapping = {}
        if os.path.exists(hajj_path):
            files = sorted(os.listdir(hajj_path))
            for filename in files:
                if filename.endswith('.json'):
                    base_name = os.path.splitext(filename)[0]
                    list_widget.addItem(base_name)
                    file_mapping[base_name] = os.path.join(hajj_path, filename)
        def item_activated(item):
            if not item: return
            base_name = item.text()
            file_path = file_mapping.get(base_name)
            if file_path:
                data = self.load_json_data(file_path)
                if data:
                    content = []
                    for entry in data:
                        title = entry.get("title", "")
                        text = entry.get("text", "")
                        content.append(f"{title}\n\n{text}")
                    full_content = "\n\n---\n\n".join(content)
                    viewer = TextViewer(self, base_name, full_content)
                    viewer.exec()
        list_widget.itemDoubleClicked.connect(item_activated)
        list_widget.itemActivated.connect(item_activated)
        layout.addWidget(list_widget)
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
        layout = qt.QHBoxLayout(widget)                
        main_list = QListWidget()
        main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        main_list.setMaximumWidth(250)                
        sub_list = QListWidget()
        sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")        
        layout.addWidget(main_list)
        layout.addWidget(sub_list)        
        base_path = os.path.join(self.DATA_PATH, dir_name)
        file_mapping = {}        
        for filename in file_order:
            base_name = os.path.splitext(filename)[0]
            main_list.addItem(base_name)
            file_mapping[base_name] = os.path.join(base_path, filename)        
        def show_sublist(current, previous):
            if not current:
                sub_list.clear()
                return
            item_text = current.text()
            file_path = file_mapping.get(item_text)
            if not file_path:
                sub_list.clear()
                return
            data = self.load_json_data(file_path)
            if not data:
                sub_list.clear()
                return
            sub_list.clear()
            sub_list.mapping = {}
            for entry in data:
                title = entry.get("number", "")
                sub_list.addItem(str(title))
                sub_list.mapping[str(title)] = entry.get("label", "")            
        def sub_list_activated(item):
            if not item: return
            if hasattr(sub_list, 'mapping') and item.text() in sub_list.mapping:
                content = sub_list.mapping[item.text()]
                viewer = TextViewer(widget, item.text(), content)
                viewer.exec()
        main_list.currentItemChanged.connect(show_sublist)
        sub_list.itemDoubleClicked.connect(sub_list_activated)
        sub_list.itemActivated.connect(sub_list_activated)        
        return widget
    def create_ad3yah_tab(self):
        widget = qt.QWidget()
        layout = qt.QHBoxLayout(widget)                
        main_list = QListWidget()
        main_list.setStyleSheet("QListWidget::item { font-weight: bold; }")
        main_list.setMaximumWidth(250)                
        sub_list = QListWidget()
        sub_list.setStyleSheet("QListWidget::item { font-weight: bold; }")                
        layout.addWidget(main_list)
        layout.addWidget(sub_list)                
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)        
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
                return
            item_text = current.text()
            info = file_mapping.get(item_text)            
            if not info:
                sub_list.clear()
                return
            sub_list.clear()
            sub_list.mapping = {}            
            if info["type"] == "folder":                
                if os.path.exists(info["path"]):
                    for sub_filename in sorted(os.listdir(info["path"])):
                        if sub_filename.endswith('.json'):
                            sub_base_name = os.path.splitext(sub_filename)[0]
                            sub_list.addItem(sub_base_name)
                            sub_list.mapping[sub_base_name] = os.path.join(info["path"], sub_filename)
            else:                
                sub_list.addItem("انقر نقراً مزدوجاً أو اضغط Enter لعرض المحتوى")
        def main_list_activated(item):
            if not item: return
            info = file_mapping.get(item.text())
            if not info: return            
            if info["type"] == "file":
                data = self.load_json_data(info["path"])
                if data:
                    content = "\n\n".join([d.get("text", "") for d in data])
                    viewer = TextViewer(widget, item.text(), content)
                    viewer.exec()
        def sub_list_activated(item):
            if not item: return
            if hasattr(sub_list, 'mapping') and item.text() in sub_list.mapping:
                file_path = sub_list.mapping[item.text()]
                data = self.load_json_data(file_path)
                if data:
                    content = "\n\n".join([d.get("text", "") for d in data])
                    viewer = TextViewer(widget, item.text(), content)
                    viewer.exec()
        main_list.currentItemChanged.connect(main_list_changed)
        main_list.itemDoubleClicked.connect(main_list_activated)
        main_list.itemActivated.connect(main_list_activated)
        sub_list.itemDoubleClicked.connect(sub_list_activated)
        sub_list.itemActivated.connect(sub_list_activated)        
        return widget