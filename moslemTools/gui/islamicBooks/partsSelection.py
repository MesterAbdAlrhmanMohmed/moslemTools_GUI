import os
import re
import PyQt6.QtWidgets as qt
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
import guiTools
from .bookViewer import book_viewer


class PartSelection(qt.QDialog):
    def __init__(self, p, bookName: str, content: dict):
        super().__init__(p)
        self.setWindowTitle("اختيار الجزء")
        self.setMinimumSize(320, 200)
        self.resize(360, 220)
        self.bookName = bookName
        self.content = content

        if p:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(p.frameGeometry().center())
            self.move(frame_geometry.topLeft())

        def part_sort_key(name):
            nums = re.findall(r'\d+', str(name))
            return int(nums[0]) if nums else 0

        self.parts_list = sorted(list(content.keys()), key=part_sort_key)

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)

        self.label = qt.QLabel("اختر الجزء:")
        self.label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        self.label.setFont(font)
        layout.addWidget(self.label)

        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("ابحث في الأجزاء...")
        self.search_bar.setAccessibleName("ابحث في الأجزاء")
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setMinimumHeight(32)
        self.search_bar.textChanged.connect(self.on_search)
        layout.addWidget(self.search_bar)

        self.parts_combo = qt.QComboBox()
        self.parts_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.parts_combo.setAccessibleName("اختر الجزء")
        self.parts_combo.setMinimumHeight(35)
        self.parts_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.populate_combo(self.parts_list)
        layout.addWidget(self.parts_combo)

        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.select_button = guiTools.QPushButton("الذهاب")
        self.select_button.setStyleSheet("background-color:#006400;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.select_button.clicked.connect(self.openPart)
        self.select_button.setMinimumHeight(35)

        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(35)

        buttons_layout.addWidget(self.select_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(self.reject)
        qt1.QShortcut(qt1.QKeySequence("return"), self).activated.connect(self.openPart)
        qt1.QShortcut(qt1.QKeySequence("enter"), self).activated.connect(self.openPart)

    def normalize(self, text):
        t = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)
        t = re.sub(r'[إأآٱ]', 'ا', t)
        return t.replace('ى', 'ي').replace('ة', 'ه').strip().lower()

    def populate_combo(self, items):
        self.parts_combo.blockSignals(True)
        self.parts_combo.clear()
        for it in items:
            pages = self.content.get(it, [])
            pages_count = len(pages) if isinstance(pages, list) else 0
            display_text = f"{it} ({pages_count} صفحة)" if pages_count > 0 else it
            self.parts_combo.addItem(display_text, it)
        self.parts_combo.blockSignals(False)

    def on_search(self):
        query = self.normalize(self.search_bar.text())
        if query:
            filtered = [it for it in self.parts_list if query in self.normalize(it)]
        else:
            filtered = list(self.parts_list)

        current_data = self.parts_combo.currentData()
        self.populate_combo(filtered)
        if current_data is not None:
            for i in range(self.parts_combo.count()):
                if self.parts_combo.itemData(i) == current_data:
                    self.parts_combo.setCurrentIndex(i)
                    return
        if self.parts_combo.count() > 0:
            self.parts_combo.setCurrentIndex(0)

    def openPart(self):
        if self.parts_combo.count() == 0:
            return
        partName = self.parts_combo.currentData()
        if not partName:
            partName = self.parts_combo.currentText()
        if partName not in self.content:
            return
        partContent = self.content[partName]
        self.accept()
        book_viewer(self.parent(), self.bookName, partName, partContent).exec()
