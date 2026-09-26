import os
import re
import json
import functions
import settings
import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class ChangeTranslationDialog(qt.QDialog):
    ALL_LANGS_LABEL = "عرض جميع اللغات والترجمات المتاحة"

    def __init__(self, parent, current_index: str):
        super().__init__(parent)
        self.setWindowTitle("تغيير الترجمة")
        self.min_dialog_width = 400
        self.setMinimumSize(self.min_dialog_width, 340)
        self.resize(self.min_dialog_width, 340)
        self.selected_item = None
        self.lang_groups = {}
        self.all_translations = []

        functions.translater.reload_translations()
        downloaded = functions.translater.translations

        manifest_path = os.path.join("data", "json", "files", "all_translater.json")
        catalog = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
            except Exception:
                catalog = {}

        for display_name, rel_path in downloaded.items():
            norm_path = rel_path.replace("\\", "/")
            parts = norm_path.split("/")
            if len(parts) > 1 and parts[0]:
                lang = parts[0]
            else:
                cat_path = catalog.get(display_name, "")
                cat_parts = cat_path.replace("\\", "/").split("/")
                lang = cat_parts[0] if (len(cat_parts) > 1 and cat_parts[0]) else "الإنجليزية English"
            self.lang_groups.setdefault(lang, []).append(display_name)
            self.all_translations.append(display_name)

        self.all_translations = sorted(self.all_translations)
        self.sorted_langs = sorted(self.lang_groups.keys())

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(8)

        self.lang_label = qt.QLabel("اختر اللغة:")
        self.lang_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.lang_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lang_label)

        self.search_lang = qt.QLineEdit()
        self.search_lang.setPlaceholderText("ابحث عن لغة")
        self.search_lang.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_lang.setMinimumHeight(30)
        self.search_lang.textChanged.connect(self.on_search_lang)
        layout.addWidget(self.search_lang)

        self.lang_combo = guiTools.QComboBox()
        self.lang_combo.setAccessibleName("اختر اللغة")
        self.lang_combo.setMinimumHeight(35)
        self.lang_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        layout.addWidget(self.lang_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.trans_label = qt.QLabel("اختر الترجمة:")
        self.trans_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.trans_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.trans_label)

        self.search_trans = qt.QLineEdit()
        self.search_trans.setPlaceholderText("ابحث عن ترجمة")
        self.search_trans.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_trans.setMinimumHeight(30)
        self.search_trans.textChanged.connect(self.on_search_trans)
        layout.addWidget(self.search_trans)

        self.trans_combo = guiTools.QComboBox()
        self.trans_combo.setAccessibleName("اختر الترجمة")
        self.trans_combo.setMinimumHeight(35)
        self.trans_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.trans_combo.currentIndexChanged.connect(self.update_sizes)
        layout.addWidget(self.trans_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.translate_button = guiTools.QPushButton("ترجمة")
        self.translate_button.setStyleSheet("background-color:#006400;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.translate_button.clicked.connect(self.on_translate)
        self.translate_button.setMinimumHeight(35)

        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("background-color:#8B0000;color:white;padding:5px 15px;font-weight:bold;border-radius:4px;min-height:35px;")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(35)

        buttons_layout.addWidget(self.translate_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.translate_button.setDefault(True)
        self.search_lang.returnPressed.connect(self.on_translate)
        self.search_trans.returnPressed.connect(self.on_translate)
        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(self.reject)

        self.populate_lang_combo()

        curr_trans_name = functions.translater.gettranslationByIndex(current_index)
        target_lang = None
        for lang, trans_list in self.lang_groups.items():
            if curr_trans_name in trans_list:
                target_lang = lang
                break

        if target_lang and target_lang in self.sorted_langs:
            self.lang_combo.setCurrentText(target_lang)
        elif self.lang_combo.count() > 0:
            self.lang_combo.setCurrentIndex(0)

        self.on_lang_changed()

        if curr_trans_name:
            idx = self.trans_combo.findText(curr_trans_name)
            if idx >= 0:
                self.trans_combo.setCurrentIndex(idx)

        self.update_sizes()

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

    def update_combo_width(self, combo, min_w=180):
        text = combo.currentText()
        fm = combo.fontMetrics()
        text_w = fm.horizontalAdvance(text) if text else 0
        combo_w = max(min_w, text_w + 55)

        screen_w = self.screen().availableGeometry().width() if self.screen() else 1200
        combo_w = min(combo_w, screen_w - 60)
        combo.setFixedWidth(combo_w)

        max_item_w = 0
        for i in range(combo.count()):
            iw = fm.horizontalAdvance(combo.itemText(i))
            if iw > max_item_w:
                max_item_w = iw
        popup_w = min(max(combo_w, max_item_w + 50), screen_w - 60)
        combo.view().setMinimumWidth(popup_w)
        return combo_w

    def update_sizes(self):
        w_lang = self.update_combo_width(self.lang_combo)
        w_trans = self.update_combo_width(self.trans_combo)
        max_combo_w = max(w_lang, w_trans)

        screen_w = self.screen().availableGeometry().width() if self.screen() else 1200
        target_w = min(max(self.min_dialog_width, max_combo_w + 40), screen_w - 40)
        if target_w != self.width():
            old_center = self.frameGeometry().center()
            self.resize(target_w, self.height())
            fg = self.frameGeometry()
            fg.moveCenter(old_center)
            self.move(fg.topLeft())

    def keyPressEvent(self, event):
        if event.key() in (qt2.Qt.Key.Key_Return, qt2.Qt.Key.Key_Enter):
            if self.cancel_button.hasFocus():
                self.cancel_button.click()
                return
            else:
                self.on_translate()
                return
        super().keyPressEvent(event)

    def normalize(self, text):
        t = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)
        t = re.sub(r'[إأآ]', 'ا', t)
        return t.replace('ى', 'ي').strip().lower()

    def populate_lang_combo(self, search_query=""):
        current_text = self.lang_combo.currentText()
        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()

        items = []
        q = self.normalize(search_query) if search_query else ""
        for lang in self.sorted_langs:
            if not q or q in self.normalize(lang):
                items.append(lang)

        if not q or q in self.normalize(self.ALL_LANGS_LABEL) or "كل" in q or "جميع" in q:
            items.append(self.ALL_LANGS_LABEL)

        self.lang_combo.addItems(items)
        if current_text in items:
            self.lang_combo.setCurrentText(current_text)
        elif items:
            self.lang_combo.setCurrentIndex(0)
        self.lang_combo.blockSignals(False)

    def on_search_lang(self):
        query = self.search_lang.text()
        self.populate_lang_combo(query)
        self.on_lang_changed()

    def on_lang_changed(self):
        selected_lang = self.lang_combo.currentText()
        if selected_lang == self.ALL_LANGS_LABEL:
            active_list = list(self.all_translations)
        else:
            active_list = sorted(self.lang_groups.get(selected_lang, []))

        query_trans = self.normalize(self.search_trans.text())
        if query_trans:
            active_list = [t for t in active_list if query_trans in self.normalize(t)]

        current_trans = self.trans_combo.currentText()
        self.trans_combo.blockSignals(True)
        self.trans_combo.clear()
        self.trans_combo.addItems(active_list)
        if current_trans in active_list:
            self.trans_combo.setCurrentText(current_trans)
        elif active_list:
            self.trans_combo.setCurrentIndex(0)
        self.trans_combo.blockSignals(False)
        self.update_sizes()

    def on_search_trans(self):
        self.on_lang_changed()

    def on_translate(self):
        selected = self.trans_combo.currentText()
        if selected:
            self.selected_item = selected
            self.accept()
