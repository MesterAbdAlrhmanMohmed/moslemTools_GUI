import os, json, functions, settings, guiTools, winsound, pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer


class ChangeTranslationDialog(qt.QDialog):
    ALL_LANGS_LABEL = "عرض جميع اللغات المتاحة"

    def __init__(self, parent, current_index: str):
        super().__init__(parent)
        self.setWindowTitle("تغيير الترجمة")
        self.setMinimumSize(360, 320)
        self.resize(400, 360)
        self.selected_item = None
        self.lang_groups = {}  # {lang_name: [translation_name, ...]}
        self.all_translations = []

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

        # Load downloaded translations strictly from functions.translater
        functions.translater.reload_translations()
        downloaded = functions.translater.translations  # {display_name: rel_path}

        # Catalog lookup for proper language folder grouping
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

        # 1. Language Section
        self.lang_label = qt.QLabel("اختر اللغة:")
        self.lang_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.lang_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lang_label)

        self.search_lang = qt.QLineEdit()
        self.search_lang.setPlaceholderText("ابحث عن لغة...")
        self.search_lang.setAccessibleName("ابحث عن لغة")
        self.search_lang.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_lang.setMinimumHeight(30)
        self.search_lang.textChanged.connect(self.on_search_lang)
        layout.addWidget(self.search_lang)

        self.lang_combo = qt.QComboBox()
        self.lang_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.lang_combo.setAccessibleName("اختر اللغة")
        self.lang_combo.setMinimumHeight(35)
        self.lang_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        layout.addWidget(self.lang_combo)

        # 2. Translation Section
        self.trans_label = qt.QLabel("اختر الترجمة:")
        self.trans_label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.trans_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.trans_label)

        self.search_trans = qt.QLineEdit()
        self.search_trans.setPlaceholderText("ابحث عن ترجمة...")
        self.search_trans.setAccessibleName("ابحث عن ترجمة")
        self.search_trans.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_trans.setMinimumHeight(30)
        self.search_trans.textChanged.connect(self.on_search_trans)
        layout.addWidget(self.search_trans)

        self.trans_combo = qt.QComboBox()
        self.trans_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.trans_combo.setAccessibleName("اختر الترجمة")
        self.trans_combo.setMinimumHeight(35)
        self.trans_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        layout.addWidget(self.trans_combo)

        # 3. Bottom Buttons: "ترجمة" and "إلغاء" side by side
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

        # Shortcuts
        qt1.QShortcut(qt1.QKeySequence("escape"), self).activated.connect(self.reject)
        qt1.QShortcut(qt1.QKeySequence("return"), self).activated.connect(self.on_translate)
        qt1.QShortcut(qt1.QKeySequence("enter"), self).activated.connect(self.on_translate)

        # Populate combo boxes
        self.populate_lang_combo()

        # Determine current selection
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

    def normalize(self, text):
        import re
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

    def on_search_trans(self):
        self.on_lang_changed()

    def on_translate(self):
        selected = self.trans_combo.currentText()
        if selected:
            self.selected_item = selected
            self.accept()


class translationViewer(qt.QDialog):
    def __init__(self, p, From, to):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_astxt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_current_selection)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.on_change_translation)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.index = settings.settings_handler.get("translation", "translation")
        self.context_menu_active = False
        self.saved_text = ""
        self.From = From
        self.to = to
        self.saved_cursor_position = None
        self.saved_selection_start = -1
        self.saved_selection_end = -1
        self.setMinimumSize(700, 400)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit(viewer_name="translationViewer")
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        layout = qt.QVBoxLayout(self)
        self.permanent_stabilizer_bar = qt.QWidget()
        self.permanent_stabilizer_bar.setFixedHeight(0)
        self.permanent_stabilizer_bar.setAccessibleName(" ")
        self.permanent_stabilizer_bar.setAccessibleDescription(" ")
        layout.addWidget(self.permanent_stabilizer_bar)
        self.current_translation_label = guiTools.QNavigableLabel(f"الترجمة المحددة هي: {functions.translater.gettranslationByIndex(self.index)}")
        self.current_translation_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.current_translation_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_translation_label)
        layout.addWidget(self.text)
        bottomLayout = qt.QHBoxLayout()
        bottomLayout.addSpacing(15)
        self.changeTranslation = qt.QPushButton("تغيير الترجمة")
        self.changeTranslation.setStyleSheet("background-color: #0000AA; color: white; padding: 8px 18px; font-weight: bold; border-radius: 6px; min-width: 130px; min-height: 38px;")
        self.changeTranslation.setAccessibleDescription("control plus g")
        self.changeTranslation.clicked.connect(self.on_change_translation)
        bottomLayout.addWidget(self.changeTranslation, 0, qt2.Qt.AlignmentFlag.AlignCenter)
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
        self.warning_label = guiTools.QNavigableLabel("تنبيه: إذا غيرت الترجمة ولم يظهر النص، اختر نفس الترجمة مرة أخرى.")
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
        save.triggered.connect(self.save_text_astxt)
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

    def on_change_translation(self):
        dialog = ChangeTranslationDialog(self, current_index=self.index)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted and dialog.selected_item:
            self.on_translation_changed(dialog.selected_item)

    def on_translation_changed(self, name: str):
        new_index = functions.translater.translations.get(name)
        if new_index is not None:
            self.index = new_index
            try:
                settings.settings_handler.set("translation", "translation", self.index)
            except Exception:
                pass
            self.current_translation_label.setText(f"الترجمة المحددة هي: {functions.translater.gettranslationByIndex(self.index)}")
            self.getResult()

    def print_text(self):
        translation_name = functions.translater.gettranslationByIndex(self.index)
        functions.text_actions.print_text_content(self, self.text, header_text=f"ترجمة: {translation_name}")

    def save_text_astxt(self):
        translation_name = functions.translater.gettranslationByIndex(self.index)
        functions.text_actions.save_text_file(self, self.text, header_text=f"ترجمة: {translation_name}")

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
        translation_name = functions.translater.gettranslationByIndex(self.index)
        functions.text_actions.copy_all_text(self, self.text, header_text=f"ترجمة: {translation_name}")

    def copy_current_selection(self):
        functions.text_actions.copy_current_selection(self, self.text)

    def getResult(self):
        self.full_content = functions.translater.gettranslation(functions.translater.gettranslationByIndex(self.index), self.From, self.to)
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
