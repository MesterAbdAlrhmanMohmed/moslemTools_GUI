import os
import re
from collections import Counter
import ujson as json
import PyQt6.QtWidgets as qt
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
import guiTools
import settings


class SelectBabDialog(qt.QDialog):
    def __init__(self, parent, book_file: str, book_name_ar: str = "", current_chapter_id=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار الباب")
        self.setMinimumSize(320, 200)
        self.resize(360, 220)
        self.selected_chapter_id = None
        self.selected_chapter_name = ""
        self.selected_raw_chapter_name = ""

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

        self.chapters_data = []
        full_path = os.path.join(os.getenv('appdata'), settings.app.appName, "ahadeeth", book_file)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    hadiths = data.get("hadiths", [])
                    counts = Counter(h.get("chapterId") for h in hadiths)
                    for c in data.get("chapters", []):
                        cid = c.get("id")
                        cname = c.get("arabic", "").strip()
                        cnt = counts.get(cid, 0)
                        display_text = f"{cname} ({cnt} حديث)"
                        self.chapters_data.append({
                            "id": cid,
                            "name": cname,
                            "display": display_text
                        })
            except Exception:
                pass

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)

        self.label = qt.QLabel("اختر الباب:")
        self.label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.search_bar = qt.QLineEdit()
        self.search_bar.setAccessibleName("ابحث في الأبواب")
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setMinimumHeight(32)
        self.search_bar.textChanged.connect(self.on_search)
        layout.addWidget(self.search_bar)

        self.bab_combo = qt.QComboBox()
        self.bab_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.bab_combo.setAccessibleName("اختر الباب")
        self.bab_combo.setMinimumHeight(35)
        self.bab_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.populate_combo(self.chapters_data)

        if current_chapter_id is not None:
            for i in range(self.bab_combo.count()):
                if self.bab_combo.itemData(i) == current_chapter_id:
                    self.bab_combo.setCurrentIndex(i)
                    break
        else:
            self.bab_combo.setCurrentIndex(0)

        layout.addWidget(self.bab_combo)

        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.select_button = guiTools.QPushButton("الذهاب")
        self.select_button.setStyleSheet("background-color:#006400;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.select_button.clicked.connect(self.on_select)
        self.select_button.setMinimumHeight(35)

        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(35)

        buttons_layout.addWidget(self.select_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.select_button.setDefault(True)
        self.search_bar.returnPressed.connect(self.on_select)
        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(self.reject)

    def keyPressEvent(self, event):
        if event.key() in (qt2.Qt.Key.Key_Return, qt2.Qt.Key.Key_Enter):
            if self.cancel_button.hasFocus():
                self.cancel_button.click()
                return
            else:
                self.on_select()
                return
        super().keyPressEvent(event)

    def normalize(self, text):
        t = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)
        t = re.sub(r'[إأآ]', 'ا', t)
        return t.replace('ى', 'ي').strip().lower()

    def populate_combo(self, items):
        self.bab_combo.blockSignals(True)
        self.bab_combo.clear()
        self.bab_combo.addItem("فتح الكتاب كاملا", None)
        for it in items:
            self.bab_combo.addItem(it["display"], it["id"])
        self.bab_combo.blockSignals(False)

    def on_search(self):
        query = self.normalize(self.search_bar.text())
        if query:
            filtered = [it for it in self.chapters_data if query in self.normalize(it["name"])]
        else:
            filtered = list(self.chapters_data)

        current_data = self.bab_combo.currentData()
        self.populate_combo(filtered)
        found = False
        if current_data is not None:
            for i in range(self.bab_combo.count()):
                if self.bab_combo.itemData(i) == current_data:
                    self.bab_combo.setCurrentIndex(i)
                    found = True
                    break
        if not found:
            self.bab_combo.setCurrentIndex(0)

    def on_select(self):
        self.selected_chapter_id = self.bab_combo.currentData()
        self.selected_chapter_name = self.bab_combo.currentText()
        if self.selected_chapter_id is not None:
            for it in self.chapters_data:
                if it["id"] == self.selected_chapter_id:
                    self.selected_raw_chapter_name = it["name"]
                    break
        else:
            self.selected_raw_chapter_name = ""
        self.accept()
