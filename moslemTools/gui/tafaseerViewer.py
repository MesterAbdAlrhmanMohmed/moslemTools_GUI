import functions, settings, guiTools, winsound, pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer


class ChangeTafseerDialog(qt.QDialog):
    def __init__(self, parent, current_index: str):
        super().__init__(parent)
        self.setWindowTitle("تغيير التفسير")
        self.setMinimumSize(320, 200)
        self.resize(360, 220)
        self.selected_tafseer = None

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

        # Load available downloaded tafaseers strictly from functions.tafseer
        functions.tafseer.reload_tafaseers()
        self.available_tafaseers = list(functions.tafseer.tafaseers.keys())

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)

        self.label = qt.QLabel("اختر التفسير:")
        self.label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("ابحث عن كتاب تفسير...")
        self.search_bar.setAccessibleName("ابحث عن كتاب تفسير")
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setMinimumHeight(32)
        self.search_bar.textChanged.connect(self.on_search)
        layout.addWidget(self.search_bar)

        self.tafseer_combo = qt.QComboBox()
        self.tafseer_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.tafseer_combo.setAccessibleName("اختر التفسير")
        self.tafseer_combo.setMinimumHeight(35)
        self.tafseer_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.tafseer_combo.addItems(self.available_tafaseers)

        current_tafseer_name = functions.tafseer.getTafaseerByIndex(current_index)
        if current_tafseer_name and current_tafseer_name in self.available_tafaseers:
            self.tafseer_combo.setCurrentText(current_tafseer_name)
        elif self.available_tafaseers:
            self.tafseer_combo.setCurrentIndex(0)

        layout.addWidget(self.tafseer_combo)

        # Buttons side by side: "اختيار التفسير" and "إلغاء"
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

        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(self.reject)
        qt1.QShortcut(qt1.QKeySequence("return"), self).activated.connect(self.on_select)
        qt1.QShortcut(qt1.QKeySequence("enter"), self).activated.connect(self.on_select)

    def normalize(self, text):
        import re
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

    def on_select(self):
        selected = self.tafseer_combo.currentText()
        if selected:
            self.selected_tafseer = selected
            self.accept()


class TafaseerViewer(qt.QDialog):
    def __init__(self, p, From, to):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.on_change_tafaseer)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        functions.tafseer.reload_tafaseers()
        default_index = settings.settings_handler.get("tafaseer", "tafaseer")
        available_indices = list(functions.tafseer.tafaseers.values())
        if default_index in available_indices:
            self.index = default_index
        elif "muyassar.json" in available_indices:
            self.index = "muyassar.json"
        elif available_indices:
            self.index = available_indices[0]
        else:
            self.index = default_index
        self.context_menu_active = False
        self.saved_text = ""
        self.From = From
        self.to = to
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.setMinimumSize(700, 400)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit(viewer_name="tafaseerViewer")
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        layout = qt.QVBoxLayout(self)
        self.permanent_stabilizer_bar = qt.QWidget()
        self.permanent_stabilizer_bar.setFixedHeight(0)
        self.permanent_stabilizer_bar.setAccessibleName(" ")
        self.permanent_stabilizer_bar.setAccessibleDescription(" ")
        layout.addWidget(self.permanent_stabilizer_bar)
        self.current_tafaseer_label = guiTools.QNavigableLabel(f"التفسير المحدد هو: {functions.tafseer.getTafaseerByIndex(self.index)}")
        self.current_tafaseer_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.current_tafaseer_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_tafaseer_label)
        layout.addWidget(self.text)
        bottomLayout = qt.QHBoxLayout()
        bottomLayout.addSpacing(15)
        self.changeTafaseer = qt.QPushButton("تغيير التفسير")
        self.changeTafaseer.setStyleSheet("background-color: #0000AA; color: white; padding: 8px 18px; font-weight: bold; border-radius: 6px; min-width: 130px; min-height: 38px;")
        self.changeTafaseer.setAccessibleDescription("control plus g")
        self.changeTafaseer.clicked.connect(self.on_change_tafaseer)
        bottomLayout.addWidget(self.changeTafaseer, 0, qt2.Qt.AlignmentFlag.AlignCenter)
        bottomLayout.addStretch(1)
        fontLayout = qt.QVBoxLayout()
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        fontLayout.addWidget(self.font_laybol)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        fontLayout.addWidget(self.show_font)
        bottomLayout.addLayout(fontLayout)
        bottomLayout.addStretch(1)
        self.more_options_label = guiTools.QNavigableLabel("لمزيد من الخيارات، نستخدم زر التطبيقات أو click الأيمن")
        self.more_options_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.more_options_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.warning_label = guiTools.QNavigableLabel("تنبيه: إذا غيرت التفسير ولم يظهر النص، اختر نفس التفسير مرة أخرى.")
        self.warning_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.warning_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Preferred)
        warningsLayout = qt.QVBoxLayout()
        warningsLayout.addWidget(self.more_options_label)
        warningsLayout.addWidget(self.warning_label)
        bottomLayout.addLayout(warningsLayout, 1)
        bottomLayout.addSpacing(15)
        layout.addLayout(bottomLayout)
        self.getResult()

    def OnContextMenu(self):
        menu = guiTools.QCustomContextMenu("الخيارات", self)
        menu.setAccessibleName("الخيارات")
        save = menu.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)
        printerAction = menu.addAction("طباعة")
        printerAction.setShortcut("ctrl+p")
        printerAction.triggered.connect(self.print_text)
        copy_all = menu.addAction("نسخ النص كاملا")
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text = menu.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_current_selection)        
        menu.exec(qt1.QCursor.pos())

    def on_change_tafaseer(self):
        dialog = ChangeTafseerDialog(self, current_index=self.index)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted and dialog.selected_tafseer:
            self.onTafaseerChanged(dialog.selected_tafseer)

    def onTafaseerChanged(self, name: str):
        new_index = functions.tafseer.tafaseers.get(name)
        if new_index is not None and self.index != new_index:
            self.index = new_index
            self.current_tafaseer_label.setText(f"التفسير المحدد هو: {functions.tafseer.getTafaseerByIndex(self.index)}")
            self.getResult()

    def print_text(self):
        tafaseer_name = functions.tafseer.getTafaseerByIndex(self.index)
        functions.text_actions.print_text_content(self, self.text, header_text=f"تفسير: {tafaseer_name}")

    def save_text_as_txt(self):
        tafaseer_name = functions.tafseer.getTafaseerByIndex(self.index)
        functions.text_actions.save_text_file(self, self.text, header_text=f"تفسير: {tafaseer_name}")

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def update_font_size(self):
        cursor = self.text.textCursor()
        self.text.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
        if self.show_font.value() != self.font_size:
            self.show_font.blockSignals(True)
            self.show_font.setValue(self.font_size)
            self.show_font.blockSignals(False)

    def copy_text(self):
        tafaseer_name = functions.tafseer.getTafaseerByIndex(self.index)
        functions.text_actions.copy_all_text(self, self.text, header_text=f"تفسير: {tafaseer_name}")

    def copy_current_selection(self):
        functions.text_actions.copy_current_selection(self, self.text)

    def getResult(self):
        self.full_content = functions.tafseer.getTafaseer(functions.tafseer.getTafaseerByIndex(self.index), self.From, self.to)
        lines = self.full_content.split('\n')
        self.text.setText('\n'.join(lines[:40]))
        self.update_font_size()
        if len(lines) > 40:
            QTimer.singleShot(500, self.display_full_content)

    def display_full_content(self):
        if not self.context_menu_active:
            self.text.setText(self.full_content)
            self.update_font_size()
            if self.saved_cursor_position is not None:
                cursor = self.text.textCursor()
                cursor.setPosition(self.saved_cursor_position)
                self.text.setTextCursor(cursor)
