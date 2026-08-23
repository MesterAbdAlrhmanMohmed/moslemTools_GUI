import functions, settings, guiTools, winsound, pyperclip
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer


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
        copy_selected_text .setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_current_selection)        
        menu.exec(qt1.QCursor.pos())

    def on_change_translation(self):
        menu = guiTools.QCustomContextMenu("اختر ترجمة", self)
        menu.setAccessibleName("اختر ترجمة")
        action_group = qt1.QActionGroup(self)
        action_group.setExclusive(True)
        current_translation_name = functions.translater.gettranslationByIndex(self.index)
        all_translations = list(functions.translater.translations.keys())
        if current_translation_name in all_translations:
            all_translations.remove(current_translation_name)
            all_translations.insert(0, current_translation_name)
        for name in all_translations:
            action = qt1.QAction(name, self)
            action.setCheckable(True)
            if name == current_translation_name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, n=name: self.on_translation_changed(n) if checked else None)
            menu.addAction(action)
            action_group.addAction(action)
        menu.exec(qt1.QCursor.pos())

    def on_translation_changed(self, name: str):
        new_index = functions.translater.translations.get(name)
        if new_index is not None and self.index != new_index:
            self.index = new_index
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
        self.full_content = functions.translater.gettranslation(functions.translater.gettranslationByIndex(self.index),self.From, self.to)
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
