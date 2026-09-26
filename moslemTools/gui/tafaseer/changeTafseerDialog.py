import re, functions, settings, guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class ChangeTafseerDialog(qt.QDialog):
    def __init__(self, parent, current_index: str):
        super().__init__(parent)
        self.setWindowTitle("تغيير التفسير")
        self.min_dialog_width = 380
        self.setMinimumSize(self.min_dialog_width, 220)
        self.resize(self.min_dialog_width, 220)
        self.selected_tafseer = None

        functions.tafseer.reload_tafaseers()
        self.available_tafaseers = list(functions.tafseer.tafaseers.keys())

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)

        self.label = qt.QLabel("اختر التفسير:")
        self.label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("ابحث عن كتاب تفسير")
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setMinimumHeight(32)
        self.search_bar.textChanged.connect(self.on_search)
        layout.addWidget(self.search_bar)

        self.tafseer_combo = guiTools.QComboBox()
        self.tafseer_combo.setAccessibleName("اختر التفسير")
        self.tafseer_combo.setMinimumHeight(35)
        self.tafseer_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.tafseer_combo.addItems(self.available_tafaseers)
        self.tafseer_combo.currentIndexChanged.connect(self.update_sizes)

        current_tafseer_name = functions.tafseer.getTafaseerByIndex(current_index)
        if current_tafseer_name and current_tafseer_name in self.available_tafaseers:
            self.tafseer_combo.setCurrentText(current_tafseer_name)
        elif self.available_tafaseers:
            self.tafseer_combo.setCurrentIndex(0)

        layout.addWidget(self.tafseer_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.select_button = guiTools.QPushButton("اختيار التفسير")
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

        self.update_sizes()

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

    def update_sizes(self):
        text = self.tafseer_combo.currentText()
        fm = self.tafseer_combo.fontMetrics()
        text_w = fm.horizontalAdvance(text) if text else 0
        combo_w = max(180, text_w + 55)

        screen_w = self.screen().availableGeometry().width() if self.screen() else 1200
        combo_w = min(combo_w, screen_w - 60)
        self.tafseer_combo.setFixedWidth(combo_w)

        max_item_w = 0
        for i in range(self.tafseer_combo.count()):
            iw = fm.horizontalAdvance(self.tafseer_combo.itemText(i))
            if iw > max_item_w:
                max_item_w = iw
        popup_w = min(max(combo_w, max_item_w + 50), screen_w - 60)
        self.tafseer_combo.view().setMinimumWidth(popup_w)

        target_w = min(max(self.min_dialog_width, combo_w + 40), screen_w - 40)
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
                self.on_select()
                return
        super().keyPressEvent(event)

    def normalize(self, text):
        t = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)
        t = re.sub(r'[إأآ]', 'ا', t)
        return t.replace('ى', 'ي').strip().lower()

    def on_search(self):
        query = self.normalize(self.search_bar.text())
        if query:
            filtered = [t for t in self.available_tafaseers if query in self.normalize(t)]
        else:
            filtered = list(self.available_tafaseers)

        current = self.tafseer_combo.currentText()
        self.tafseer_combo.blockSignals(True)
        self.tafseer_combo.clear()
        self.tafseer_combo.addItems(filtered)
        if current in filtered:
            self.tafseer_combo.setCurrentText(current)
        elif filtered:
            self.tafseer_combo.setCurrentIndex(0)
        self.tafseer_combo.blockSignals(False)
        self.update_sizes()

    def on_select(self):
        selected = self.tafseer_combo.currentText()
        if selected:
            self.selected_tafseer = selected
            self.accept()
