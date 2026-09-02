import os
import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import settings_handler
from functions.moton_data import MotonDataLoader


class MotonRecitersSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                min-height: 36px;
            }
        """)
        self.data_loader = MotonDataLoader()
        self.categories = self.data_loader.get_categories()

        self.reader_idx_path = "data/DataMoton/DicQaseadReaderIndex"
        self.reader_type_path = "data/DataMoton/DicQaseadReaderIndexN"
        self.qari_ar_path = "data/DataMoton/ListQariArabic"
        self.qari_en_path = "data/DataMoton/ListQariEnglish"

        self.qari_ar_list = []
        self.qari_en_list = []
        if os.path.exists(self.qari_ar_path):
            with open(self.qari_ar_path, "r", encoding="utf-8") as f:
                self.qari_ar_list = [l.strip() for l in f if l.strip()]
        if os.path.exists(self.qari_en_path):
            with open(self.qari_en_path, "r", encoding="utf-8") as f:
                self.qari_en_list = [l.strip() for l in f if l.strip()]

        self.slug_to_ar = dict(zip(self.qari_en_list, self.qari_ar_list))

        self.matn_to_reciters = {}
        if os.path.exists(self.reader_idx_path):
            with open(self.reader_idx_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        self.matn_to_reciters[k] = [r.strip() for r in v.split(",") if r.strip()]

        self.matn_to_types = {}
        if os.path.exists(self.reader_type_path):
            with open(self.reader_type_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        self.matn_to_types[k] = [t.strip() for t in v.split(",") if t.strip()]

        self.selected_reciters_cache = {}

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)

        cat_layout = qt.QHBoxLayout()
        cat_layout.setSpacing(10)
        cat_layout.addStretch(1)
        self.category_combo = qt.QComboBox()
        self.category_combo.setFont(font)
        self.category_combo.setAccessibleName("الفئة")
        for cat in self.categories:
            self.category_combo.addItem(cat)
        self.category_label = qt.QLabel("الفئة:")
        self.category_label.setFont(font)
        self.category_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addWidget(self.category_label)
        cat_layout.addStretch(1)
        layout.addLayout(cat_layout)

        matn_layout = qt.QHBoxLayout()
        matn_layout.setSpacing(10)
        matn_layout.addStretch(1)
        self.matn_combo = qt.QComboBox()
        self.matn_combo.setFont(font)
        self.matn_combo.setAccessibleName("المتن")
        self.matn_label = qt.QLabel("المتن:")
        self.matn_label.setFont(font)
        self.matn_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        matn_layout.addWidget(self.matn_combo)
        matn_layout.addWidget(self.matn_label)
        matn_layout.addStretch(1)
        layout.addLayout(matn_layout)

        reciter_layout = qt.QHBoxLayout()
        reciter_layout.setSpacing(10)
        reciter_layout.addStretch(1)
        self.reciter_combo = qt.QComboBox()
        self.reciter_combo.setFont(font)
        self.reciter_combo.setAccessibleName("القارئ")
        self.reciter_label = qt.QLabel("القارئ:")
        self.reciter_label.setFont(font)
        self.reciter_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        reciter_layout.addWidget(self.reciter_combo)
        reciter_layout.addWidget(self.reciter_label)
        reciter_layout.addStretch(1)
        layout.addLayout(reciter_layout)

        layout.addStretch(1)

        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        self.matn_combo.currentIndexChanged.connect(self.on_matn_changed)
        self.reciter_combo.currentIndexChanged.connect(self.on_reciter_changed)

        if self.categories:
            self.on_category_changed(0)

    def adjust_combo_width(self, combo):
        fm = combo.fontMetrics()
        current_text = combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        combo.setFixedWidth(text_width + 65)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_combo_width(self.category_combo)
        self.adjust_combo_width(self.matn_combo)
        self.adjust_combo_width(self.reciter_combo)

    def on_category_changed(self, index):
        self.adjust_combo_width(self.category_combo)
        moton = self.data_loader.get_moton_for_category(index)
        self.matn_combo.blockSignals(True)
        self.matn_combo.clear()
        for m in moton:
            self.matn_combo.addItem(m)
        self.matn_combo.blockSignals(False)
        if moton:
            self.on_matn_changed(0)
        else:
            self.reciter_combo.blockSignals(True)
            self.reciter_combo.clear()
            self.reciter_combo.blockSignals(False)

    def on_matn_changed(self, index):
        self.adjust_combo_width(self.matn_combo)
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        reciter_slugs = self.matn_to_reciters.get(matn_slug, [])
        reciter_types = self.matn_to_types.get(matn_slug, [])

        verse_reciters = []
        for idx, r_slug in enumerate(reciter_slugs):
            r_type = reciter_types[idx] if idx < len(reciter_types) else "N"
            if r_type == "N":
                r_ar = self.slug_to_ar.get(r_slug, r_slug)
                verse_reciters.append((r_ar, r_slug))

        self.reciter_combo.blockSignals(True)
        self.reciter_combo.clear()

        if not verse_reciters:
            self.reciter_combo.addItem("لا يتوفر قراء مسجلين لهذا المتن", "")
            self.reciter_combo.setEnabled(False)
        else:
            self.reciter_combo.setEnabled(True)
            saved_reciter = self.selected_reciters_cache.get(matn_slug) or settings_handler.get("moton_reciters", matn_slug) or settings_handler.get("moton_reciters", "default")
            selected_idx = 0
            for i, (r_ar, r_slug) in enumerate(verse_reciters):
                self.reciter_combo.addItem(r_ar, r_slug)
                if saved_reciter and (r_slug == saved_reciter or r_ar == saved_reciter):
                    selected_idx = i
            if self.reciter_combo.count() > 0:
                self.reciter_combo.setCurrentIndex(selected_idx)

        self.reciter_combo.blockSignals(False)
        self.adjust_combo_width(self.reciter_combo)

    def on_reciter_changed(self, index):
        self.adjust_combo_width(self.reciter_combo)
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        reciter_slug = self.reciter_combo.currentData()
        if matn_slug and reciter_slug:
            self.selected_reciters_cache[matn_slug] = reciter_slug

    def save_settings(self):
        for matn_slug, reciter_slug in self.selected_reciters_cache.items():
            settings_handler.set("moton_reciters", matn_slug, reciter_slug)
        current_slug = self.reciter_combo.currentData()
        if current_slug:
            settings_handler.set("moton_reciters", "default", current_slug)
