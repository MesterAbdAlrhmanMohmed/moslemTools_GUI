import guiTools, pyperclip, winsound, json, functions, re, os, settings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from gui.quranViewer import QuranViewer
from gui.tafaseerViewer import TafaseerViewer
from gui.translationViewer import translationViewer
from gui.changeReciter import ChangeReciter
class SearchModeDialog(qt.QDialog):
    def __init__(self, parent=None, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True):
        super().__init__(parent)
        self.setWindowTitle("إعدادات نمط البحث")
        self.setFixedSize(350, 200)
        self.initial_ignore_tashkeel = ignore_tashkeel
        self.initial_ignore_hamza = ignore_hamza
        self.initial_ignore_symbols = ignore_symbols
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols
        self.init_ui()
    def init_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        self.tashkeel_checkbox = qt.QCheckBox("تجاهل التشكيل")
        self.tashkeel_checkbox.setChecked(self.initial_ignore_tashkeel)
        self.tashkeel_checkbox.setFont(bold_font)
        self.tashkeel_checkbox.stateChanged.connect(self._set_ignore_tashkeel)
        layout.addWidget(self.tashkeel_checkbox)
        self.hamza_checkbox = qt.QCheckBox("تجاهل الهمزات")
        self.hamza_checkbox.setChecked(self.initial_ignore_hamza)
        self.hamza_checkbox.setFont(bold_font)
        self.hamza_checkbox.stateChanged.connect(self._set_ignore_hamza)
        layout.addWidget(self.hamza_checkbox)
        self.symbols_checkbox = qt.QCheckBox("تجاهل الرموز والعلامات")
        self.symbols_checkbox.setChecked(self.initial_ignore_symbols)
        self.symbols_checkbox.setFont(bold_font)
        self.symbols_checkbox.stateChanged.connect(self._set_ignore_symbols)
        layout.addWidget(self.symbols_checkbox)
        layout.addStretch(1)
        buttons_layout = qt.QHBoxLayout()
        self.apply_button = guiTools.QPushButton("تطبيق التغييرات")
        self.apply_button.setObjectName("applySearchModeChangesButton")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setAutoDefault(False)
        self.cancel_button = guiTools.QPushButton("إلغاء")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setAutoDefault(False)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)
    def _set_ignore_tashkeel(self, state):
        self.ignore_tashkeel = bool(state)
    def _set_ignore_hamza(self, state):
        self.ignore_hamza = bool(state)
    def _set_ignore_symbols(self, state):
        self.ignore_symbols = bool(state)
    def get_settings(self):
        return {"ignore_tashkeel": self.ignore_tashkeel,"ignore_hamza": self.ignore_hamza,"ignore_symbols": self.ignore_symbols}
class SearchThread(qt2.QThread):
    searchFinished = qt2.pyqtSignal(list, dict, int)
    def __init__(self, parent, search_type, search_text, search_scope, ahadeeth_text, ignore_tashkeel, ignore_hamza, ignore_symbols):
        super().__init__(parent)
        self.parent_widget = parent
        self.search_type = search_type
        self.search_text = search_text
        self.search_scope = search_scope
        self.ahadeeth_text = ahadeeth_text
        self.ignore_tashkeel = ignore_tashkeel
        self.ignore_hamza = ignore_hamza
        self.ignore_symbols = ignore_symbols
    def _search(self, pattern, text_list):
        def remove_tashkeel(text):
            return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        def normalize_hamza(text):
            return re.sub(r'[أإآ]', 'ا', text)
        def normalize(text):
            normalized_text = text
            if self.ignore_tashkeel:
                normalized_text = remove_tashkeel(normalized_text)
            if self.ignore_hamza:
                normalized_text = normalize_hamza(normalized_text)
            return normalized_text
        normalized_pattern = normalize(pattern)
        results = []
        for display_text, search_text in text_list:
            if normalized_pattern in normalize(search_text):
                results.append(display_text)
        return results
    def run(self):
        display_text = []
        search_metadata = {}
        total_results_count = 0
        if self.search_type == 0:
            listOfWords = []
            data = functions.quranJsonControl.data
            def get_display(sn, sname, a):
                return f"{sn}{sname} {a['text']}({a['numberInSurah']})"
            if self.search_scope is None:
                for sn, sv in data.items():
                    sname = sv["name"]
                    for a in sv["ayahs"]:
                        listOfWords.append((get_display(sn, sname, a), a['text']))
            elif self.search_scope[0] == 'surah':
                surah_key_part = self.search_scope[1].split(' ')[0]
                for sn, sv in data.items():
                    sname = sv["name"]
                    if f"{sn}{sname}" == surah_key_part:
                        for a in sv["ayahs"]:
                            listOfWords.append((get_display(sn, sname, a), a['text']))
                        break
            else:
                stype, sval = self.search_scope
                for sn, sv in data.items():
                    sname = sv["name"]
                    for a in sv["ayahs"]:
                        match = False
                        if stype == 'page' and a['page'] == sval: match = True
                        elif stype == 'juz' and a['juz'] == sval: match = True
                        elif stype == 'quarter' and a['hizbQuarter'] == sval: match = True
                        elif stype == 'hizb' and (a['hizbQuarter']-1)//4+1 == sval: match = True
                        if match: listOfWords.append((get_display(sn, sname, a), a['text']))
            result = self._search(self.search_text, listOfWords)
            if result:
                header = "عدد نتائج البحث " + str(len(result))
                display_text.extend([header, ""])
                current_line_number = 3
                for line in result:
                    display_text.append(line)
                    metadata = self.parent_widget.get_metadata_from_result(line)
                    if metadata:
                        search_metadata[current_line_number] = metadata
                    current_line_number += 1
                total_results_count = len(result)
        else:
            search_books = {}
            if self.ahadeeth_text == "البحث في جميع كتب الأحاديث المتاحة":
                search_books = functions.ahadeeth.ahadeeths
            else:
                search_books = {self.ahadeeth_text: functions.ahadeeth.ahadeeths[self.ahadeeth_text]}
            for book_name_ar, file_name in search_books.items():
                try:
                    full_path = os.path.join(os.getenv("appdata"), settings.app.appName, "ahadeeth", file_name)
                    with open(full_path, "r", encoding="utf-8") as f:
                        ahadeeth_data = json.load(f)
                    if isinstance(ahadeeth_data, list):
                        listOfWords = [(str(i + 1) + ". " + item, item) for i, item in enumerate(ahadeeth_data)]
                        result = self._search(self.search_text, listOfWords)
                        if result:
                            display_text.append(f"عدد النتائج في كتاب {book_name_ar}, {len(result)} نتيجة")
                            display_text.append("")
                            display_text.extend(result)
                            display_text.append("")
                            total_results_count += len(result)
                    else:
                        qt.QMetaObject.invokeMethod(self.parent_widget, "handle_error", qt2.Qt.ConnectionType.QueuedConnection, qt2.Q_ARG(str, f"خطأ في البيانات: تنسيق ملف الأحاديث غير صحيح لكتاب: {book_name_ar}."))
                except Exception as e:
                    qt.QMetaObject.invokeMethod(self.parent_widget, "handle_error", qt2.Qt.ConnectionType.QueuedConnection, qt2.Q_ARG(str, f"خطأ غير متوقع أثناء تحميل الأحاديث لكتاب {book_name_ar}: {e}"))
            if display_text:
                if display_text[-1] == "":
                    display_text.pop()
                display_text.insert(0, f"إجمالي عدد النتائج: {total_results_count}")
                display_text.insert(1, "")
        self.searchFinished.emit(display_text, search_metadata, total_results_count)
class Albaheth(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.quran_data = functions.quranJsonControl.data
        self.search_metadata = {}
        self.currentReciter = int(settings.settings_handler.get("g", "reciter"))
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.was_playing_before_action = False
        self.current_search_thread = None
        self.setStyleSheet("""QPushButton {background-color: #007bff; color: white; border: none; border-radius: 6px; padding: 10px 15px; min-height: 40px; font-weight: bold; outline: none; } QPushButton:hover { background-color: #0056b3; } QPushButton:pressed { background-color: #003d80; } QPushButton#searchModeButton { background-color: #0056b3; } QPushButton#searchModeButton:hover { background-color: #003d80; } QPushButton#searchModeButton:pressed { background-color: #003d80; } QPushButton#startButton { background-color: #28a745; } QPushButton#startButton:hover { background-color: #218838; } QPushButton#startButton:pressed { background-color: #218838; } QPushButton#applySearchModeChangesButton { background-color: #28a745; } QPushButton#applySearchModeChangesButton:hover { background-color: #218838; } QPushButton#applySearchModeChangesButton:pressed { background-color: #218838; } QPushButton#cancelButton { background-color: #dc3545; } QPushButton#cancelButton:hover { background-color: #c82333; } QPushButton#cancelButton:pressed { background-color: #bd2130; } QPushButton#clearResultsButton { background-color: #dc3545; color: white; border: none; border-radius: 6px; padding: 10px 15px; min-height: 40px; font-weight: bold; outline: none; } QPushButton#clearResultsButton:hover { background-color: #c82333; } QPushButton#clearResultsButton:pressed { background-color: #bd2130; } """)
        self.init_ui()
        self.create_shortcuts()
        self.media_player.mediaStatusChanged.connect(self.on_media_state_changed)
        self.media_player.durationChanged.connect(self.update_slider_and_time)
        self.media_player.positionChanged.connect(self.update_slider_and_time)
    def create_shortcuts(self):
        qt1.QShortcut(qt2.Qt.Key.Key_Space, self).activated.connect(self.on_spacebar_pressed)
        qt1.QShortcut("Ctrl+T", self).activated.connect(self.on_tafseer_shortcut)
        qt1.QShortcut("Ctrl+L", self).activated.connect(self.on_translation_shortcut)
        qt1.QShortcut("Ctrl+I", self).activated.connect(self.on_iarab_shortcut)
        qt1.QShortcut("Ctrl+R", self).activated.connect(self.on_tanzil_shortcut)
        qt1.QShortcut("Ctrl+G", self).activated.connect(self.on_goto_surah_shortcut)
        qt1.QShortcut("Ctrl+F", self).activated.connect(self.on_ayah_info_shortcut)
        qt1.QShortcut("Ctrl+Shift+R", self).activated.connect(self.on_change_reciter_requested)
        qt1.QShortcut("Ctrl+C", self).activated.connect(self.copy_line)
        qt1.QShortcut("Ctrl+A", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
    def t10(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.1))
    def t20(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.2))
    def t30(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.3))
    def t40(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.4))
    def t50(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.5))
    def t60(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.6))
    def t70(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.7))
    def t80(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.8))
    def t90(self):
        if self.media_player.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media_player.duration()
        self.media_player.setPosition(int(total_duration * 0.9))
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
    def on_shortcut_activated(self, action_func):
        cursor = self.results.textCursor()
        line_number = cursor.blockNumber() + 1
        metadata = self.search_metadata.get(line_number)
        if not metadata:
            guiTools.speak("يرجى تحديد آية أولاً لتطبيق الإجراء")
            return
        action_func(metadata)
    def on_spacebar_pressed(self):
        if self.results.hasFocus():
            cursor = self.results.textCursor()
            line_number = cursor.blockNumber() + 1
            selected_metadata = self.search_metadata.get(line_number)
            if selected_metadata:
                self.handle_play_toggle(selected_metadata)
    def on_tafseer_shortcut(self):
        self.on_shortcut_activated(self.show_tafseer)
    def on_translation_shortcut(self):
        self.on_shortcut_activated(self.show_translation)
    def on_iarab_shortcut(self):
        self.on_shortcut_activated(self.show_iarab)
    def on_tanzil_shortcut(self):
        self.on_shortcut_activated(self.show_tanzil)
    def on_goto_surah_shortcut(self):
        self.on_shortcut_activated(self.go_to_surah)
    def on_ayah_info_shortcut(self):
        self.on_shortcut_activated(self.show_ayah_info)
    def init_ui(self):
        font_combo = qt1.QFont()
        font_combo.setBold(True)
        self.serch_laibol = qt.QLabel("ابحث في")
        self.serch_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch = qt.QComboBox()
        self.serch.addItem("القرآن الكريم")
        self.serch.addItem("الأحاديث")
        self.serch.setFont(font_combo)
        self.serch.setAccessibleName("ابحث في")
        self.serch.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)
        self.ahadeeth_laibol = qt.QLabel("اختيار الكتاب")
        self.ahadeeth_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.ahadeeth = qt.QComboBox()
        ahadeeth_items = ["البحث في جميع كتب الأحاديث المتاحة"] + list(functions.ahadeeth.ahadeeths.keys())
        self.ahadeeth.addItems(ahadeeth_items)
        self.ahadeeth.setFont(font_combo)
        self.ahadeeth.setAccessibleName("اختيار الكتاب")
        self.ahadeeth.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)
        self.surahsList = functions.quranJsonControl.getSurahs()
        self.surahs_laybol = qt.QLabel("ابحث في")
        self.surahs_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahs = qt.QComboBox()
        self.surahs.addItems(["كل القرآن", "سور", "صفحات", "أجزاء", "أرباع", "أحزاب"])
        self.surahs.setFont(font_combo)
        self.surahs.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)
        self.surahs.setAccessibleName("ابحث في")
        self.surahs.activated.connect(self.on_scope_changed)
        self.specific_scope_label = qt.QLabel("اختر")
        self.specific_scope_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.specific_scope_combo = qt.QComboBox()
        self.specific_scope_combo.setFont(font_combo)
        self.specific_scope_combo.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)
        self.specific_scope_combo.setAccessibleName("اختر القيمة")
        self.specific_scope_label.setVisible(False)
        self.specific_scope_combo.setVisible(False)
        self.current_scope = None
        self.serch.currentIndexChanged.connect(self.toggle_ahadeeth_visibility)
        self.serch_laibol_content = qt.QLabel("أكتب محتوى البحث")
        self.serch_laibol_content.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch_input = qt.QLineEdit()
        self.serch_input.setAccessibleName("أكتب محتوى البحث")
        self.serch_input.returnPressed.connect(self.onSearchClicked)
        self.ignore_tashkeel = True
        self.ignore_hamza = True
        self.ignore_symbols = True
        self.search_mode_button = guiTools.QPushButton("نمط البحث")
        self.search_mode_button.setShortcut("ctrl+q")
        self.search_mode_button.setAccessibleDescription("control plus Q")
        self.search_mode_button.setObjectName("searchModeButton")
        self.search_mode_button.clicked.connect(self.show_search_mode_dialog)
        self.start = guiTools.QPushButton("البحث")
        self.start.setObjectName("startButton")
        self.start.clicked.connect(self.onSearchClicked)
        self.results = guiTools.QReadOnlyTextEdit()
        self.results.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.OnContextMenu)
        self.results.viewport().installEventFilter(self)
        self.player_widget = qt.QWidget()
        player_layout = qt.QHBoxLayout(self.player_widget)
        player_layout.setContentsMargins(0, 5, 0, 5)
        self.media_progress = qt.QSlider(qt2.Qt.Orientation.Horizontal)        
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.media_progress.setRange(0, 100)
        self.media_progress.valueChanged.connect(self.set_media_position)
        self.time_label = qt.QLabel("00:00 / 00:00")
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        player_layout.addWidget(self.media_progress)
        player_layout.addWidget(self.time_label)
        self.player_widget.setVisible(False)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم الخط")
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.clear_results_button = guiTools.QPushButton("حذف النتائج")
        self.clear_results_button.setShortcut("ctrl+del")
        self.clear_results_button.setAccessibleDescription("control plus delete")
        self.clear_results_button.setObjectName("clearResultsButton")
        self.clear_results_button.setDisabled(True)
        self.clear_results_button.clicked.connect(self.clear_results)
        main_layout = qt.QVBoxLayout(self)
        top_combo_layout = qt.QHBoxLayout()
        search_layout_top = qt.QVBoxLayout()
        search_layout_top.addWidget(self.serch_laibol)
        search_layout_top.addWidget(self.serch)
        ahadeeth_layout_top = qt.QVBoxLayout()
        ahadeeth_layout_top.addWidget(self.ahadeeth_laibol)
        ahadeeth_layout_top.addWidget(self.ahadeeth)
        quran_scope_layout = qt.QHBoxLayout()
        surahs_vbox = qt.QVBoxLayout()
        surahs_vbox.addWidget(self.surahs_laybol)
        surahs_vbox.addWidget(self.surahs)
        specific_vbox = qt.QVBoxLayout()
        specific_vbox.addWidget(self.specific_scope_label)
        specific_vbox.addWidget(self.specific_scope_combo)
        quran_scope_layout.addLayout(surahs_vbox)
        quran_scope_layout.addLayout(specific_vbox)
        ahadeeth_layout_top.addLayout(quran_scope_layout)
        top_combo_layout.addLayout(search_layout_top)
        top_combo_layout.addLayout(ahadeeth_layout_top)
        main_layout.addLayout(top_combo_layout)
        main_layout.addWidget(self.serch_laibol_content)
        search_layout = qt.QHBoxLayout()
        search_layout.addWidget(self.search_mode_button)
        search_layout.addWidget(self.serch_input)
        search_layout.addWidget(self.start)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.results)
        main_layout.addWidget(self.player_widget)
        bottom_layout = qt.QHBoxLayout()
        bottom_layout.addWidget(self.clear_results_button)
        bottom_layout.addStretch(1)
        font_layout = qt.QVBoxLayout()
        font_layout.addWidget(self.font_laybol)
        font_layout.addWidget(self.show_font)
        bottom_layout.addLayout(font_layout)
        bottom_layout.addStretch(1)
        main_layout.addLayout(bottom_layout)
        self.ahadeeth_laibol.hide()
        self.ahadeeth.hide()
        self.update_font_size()
    def pause_for_action(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media_player.pause()
        else:
            self.was_playing_before_action = False
    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media_player.play()
    def eventFilter(self, obj, event):
        if obj == self.results.viewport() and event.type() == qt2.QEvent.Type.MouseButtonPress:
            if event.button() == qt2.Qt.MouseButton.LeftButton:
                cursor = self.results.cursorForPosition(event.position().toPoint())
                self.results.setTextCursor(cursor)
                line_number = cursor.blockNumber() + 1
                metadata = self.search_metadata.get(line_number)
                if metadata:
                    self.handle_play_toggle(metadata)
                    return True
        return super().eventFilter(obj, event)
    def handle_play_toggle(self, selected_metadata):
        current_media_src = self.media_player.source().fileName().split('/')[-1]
        expected_filename = f'{str(selected_metadata["surah_number"]).zfill(3)}{str(selected_metadata["ayah_number_in_surah"]).zfill(3)}.mp3'
        is_playing_this_verse = self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState and current_media_src == expected_filename
        if is_playing_this_verse:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            elif self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.media_player.play()
        else:
            self.start_playback(selected_metadata)
    def show_search_mode_dialog(self):
        self.pause_for_action()
        dialog = SearchModeDialog(self, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            settings_values = dialog.get_settings()
            self.ignore_tashkeel = settings_values["ignore_tashkeel"]
            self.ignore_hamza = settings_values["ignore_hamza"]
            self.ignore_symbols = settings_values["ignore_symbols"]
            guiTools.speak("تم تطبيق إعدادات البحث بنجاح")
        else:
            guiTools.speak("تم إلغاء التغييرات")
        self.resume_after_action()
    @qt2.pyqtSlot(str)
    def handle_error(self, error_msg):
        if "خطأ في البيانات" in error_msg:
            guiTools.MessageBox.error(self, "خطأ في البيانات", error_msg.split(': ', 1)[1])
        elif "خطأ غير متوقع" in error_msg:
            guiTools.MessageBox.error(self, "خطأ غير متوقع", error_msg.split(': ', 1)[1])
    def on_scope_changed(self, index):
        self.specific_scope_combo.clear()
        if index == 0:
            self.specific_scope_label.setVisible(False)
            self.specific_scope_combo.setVisible(False)
            self.current_scope = None
        else:
            self.specific_scope_label.setVisible(True)
            self.specific_scope_combo.setVisible(True)
            items = []
            label = ""
            if index == 1:
                items = list(self.surahsList.keys())
                label = "اختر السورة"
            elif index == 2:
                items = [str(i) for i in range(1, 605)]
                label = "اختر الصفحة"
            elif index == 3:
                items = [str(i) for i in range(1, 31)]
                label = "اختر الجزء"
            elif index == 4:
                items = [str(i) for i in range(1, 241)]
                label = "اختر الربع"
            elif index == 5:
                items = [str(i) for i in range(1, 61)]
                label = "اختر الحزب"
            self.specific_scope_label.setText(label)
            self.specific_scope_combo.setAccessibleName(label)
            self.specific_scope_combo.addItems(items)
    def onSearchClicked(self):
        if not self.serch_input.text():
            guiTools.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        if self.current_search_thread and self.current_search_thread.isRunning():
            guiTools.speak("جاري تنفيذ عملية بحث أخرى. يرجى الانتظار")
            return
        self.results.clear()
        self.search_metadata.clear()
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        self.start.setEnabled(False)
        self.start.setText("جاري البحث...")
        search_type = self.serch.currentIndex()
        search_text = self.serch_input.text()
        ahadeeth_text = self.ahadeeth.currentText()
        scope_index = self.surahs.currentIndex()
        if scope_index == 0:
            self.current_scope = None
        else:
            item = self.specific_scope_combo.currentText()
            if scope_index == 1:
                self.current_scope = ('surah', item)
            else:
                stype = ['page', 'juz', 'quarter', 'hizb'][scope_index-2]
                self.current_scope = (stype, int(item))
        self.current_search_thread = SearchThread(self, search_type, search_text, self.current_scope, ahadeeth_text, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        self.current_search_thread.searchFinished.connect(self.onSearchFinished)
        self.current_search_thread.start()
    @qt2.pyqtSlot(list, dict, int)
    def onSearchFinished(self, display_text, search_metadata, total_results_count):
        self.start.setEnabled(True)
        self.start.setText("البحث")
        self.search_metadata = search_metadata
        if total_results_count > 0:
            self.results.setText("\n".join(display_text))
            self.update_font_size()
            self.clear_results_button.setDisabled(False)
        else:
            guiTools.MessageBox.view(self,"تنبيه","لم يتم العثور على نتائج")
            self.clear_results_button.setDisabled(True)
        self.results.setFocus()
    def get_metadata_from_result(self, result_text):
        match = re.search(r'^(\d+)(.+?)\s(.+)\((\d+)\)$', result_text)
        if match:
            surah_number = int(match.group(1))
            surah_name = match.group(2).strip()
            ayah_number_in_surah = int(match.group(4))
            try:
                ayah_data = self.quran_data[str(surah_number)]['ayahs'][ayah_number_in_surah - 1]
                overall_ayah_number = ayah_data['number']
                return {"surah_number": surah_number,"surah_name": surah_name,"ayah_number_in_surah": ayah_number_in_surah,"overall_ayah_number": overall_ayah_number}
            except (KeyError, IndexError):
                return None
        return None
    def clear_results(self):
        if self.results.toPlainText():
            self.results.clear()
            self.search_metadata.clear()
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
            self.player_widget.setVisible(False)
            self.clear_results_button.setDisabled(True)
            guiTools.speak("تم حذف نتائج البحث")
        else:
            self.clear_results_button.setDisabled(True)
    def toggle_ahadeeth_visibility(self):
        if self.serch.currentText() == "الأحاديث":
            self.ahadeeth_laibol.show()
            self.ahadeeth.show()
            self.surahs_laybol.hide()
            self.surahs.hide()
        else:
            self.ahadeeth_laibol.hide()
            self.ahadeeth.hide()
            self.surahs_laybol.show()
            self.surahs.show()
    def OnContextMenu(self):
        self.pause_for_action()
        cursor = self.results.textCursor()
        line_number = cursor.blockNumber() + 1
        metadata = self.search_metadata.get(line_number)
        menu = qt.QMenu("الخيارات", self)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        menu.setFont(bold_font)
        if metadata:
            ayah_menu = qt.QMenu("خيارات الآية", self)
            ayah_menu.setFont(bold_font)
            play_action = qt1.QAction("تشغيل الآية", self)
            play_action.setShortcut(qt1.QKeySequence(qt2.Qt.Key.Key_Space))
            play_action.triggered.connect(lambda: self.start_playback(metadata))
            ayah_menu.addAction(play_action)
            change_reciter_action = qt1.QAction("تغيير القارئ", self)
            change_reciter_action.setShortcut("Ctrl+Shift+R")
            change_reciter_action.triggered.connect(self.on_change_reciter_requested)
            ayah_menu.addAction(change_reciter_action)
            goto_surah_action = qt1.QAction("الذهاب الى السورة التي تحتوي على هذه الآية", self)
            goto_surah_action.setShortcut("Ctrl+G")
            goto_surah_action.triggered.connect(lambda: self.go_to_surah(metadata))
            ayah_menu.addAction(goto_surah_action)
            tafseer_action = qt1.QAction("تفسير الآية", self)
            tafseer_action.setShortcut("Ctrl+T")
            tafseer_action.triggered.connect(lambda: self.show_tafseer(metadata))
            ayah_menu.addAction(tafseer_action)
            translation_action = qt1.QAction("ترجمة الآية", self)
            translation_action.setShortcut("Ctrl+L")
            translation_action.triggered.connect(lambda: self.show_translation(metadata))
            ayah_menu.addAction(translation_action)
            iarab_action = qt1.QAction("إعراب الآية", self)
            iarab_action.setShortcut("Ctrl+I")
            iarab_action.triggered.connect(lambda: self.show_iarab(metadata))
            ayah_menu.addAction(iarab_action)
            tanzil_action = qt1.QAction("أسباب نزول الآية", self)
            tanzil_action.setShortcut("Ctrl+R")
            tanzil_action.triggered.connect(lambda: self.show_tanzil(metadata))
            ayah_menu.addAction(tanzil_action)
            info_action = qt1.QAction("معلومات الآية", self)
            info_action.setShortcut("Ctrl+F")
            info_action.triggered.connect(lambda: self.show_ayah_info(metadata))
            ayah_menu.addAction(info_action)
            menu.addMenu(ayah_menu)
            menu.addSeparator()
        text_menu = qt.QMenu("خيارات النص", self)
        text_menu.setFont(bold_font)
        copy_all = qt1.QAction("نسخ النص كاملا", self)
        copy_all.setShortcut("Ctrl+A")
        copy_all.triggered.connect(self.copy_text)
        text_menu.addAction(copy_all)
        copy_selected = qt1.QAction("نسخ النص المحدد", self)
        copy_selected.setShortcut("Ctrl+C")
        copy_selected.triggered.connect(self.copy_line)
        text_menu.addAction(copy_selected)
        menu.addMenu(text_menu)
        font_menu = qt.QMenu("حجم الخط", self)
        font_menu.setFont(bold_font)
        inc_font = qt1.QAction("تكبير الخط", self)
        inc_font.setShortcut("Ctrl+=")
        inc_font.triggered.connect(self.increase_font_size)
        dec_font = qt1.QAction("تصغير الخط", self)
        dec_font.setShortcut("Ctrl+-")
        dec_font.triggered.connect(self.decrease_font_size)
        font_menu.addAction(inc_font)
        font_menu.addAction(dec_font)
        menu.addMenu(font_menu)
        menu.exec(qt1.QCursor.pos())
        self.resume_after_action()
    def start_playback(self, metadata):
        with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
            reciters = json.load(file)
        reciter_url = list(reciters.values())[self.currentReciter]
        reciter_folder = reciter_url.split('/')[-3]
        surah_num_str = str(metadata["surah_number"]).zfill(3)
        ayah_num_str = str(metadata["ayah_number_in_surah"]).zfill(3)
        filename = f"{surah_num_str}{ayah_num_str}.mp3"
        local_path = os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciter_folder,filename)
        if os.path.exists(local_path):
            path = qt2.QUrl.fromLocalFile(local_path)
        else:
            path = qt2.QUrl(reciter_url + filename)
        self.media_player.setSource(path)
        self.media_player.play()
        self.player_widget.setVisible(True)
    def on_media_state_changed(self, state):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player_widget.setVisible(False)
    def update_slider_and_time(self):
        self.media_progress.blockSignals(True)
        position = self.media_player.position()
        duration = self.media_player.duration()
        if duration > 0:
            progress_value = int((position * 100) / duration)
            self.media_progress.setValue(progress_value)
            position_sec = position // 1000
            duration_sec = duration // 1000
            remaining_sec = duration_sec - position_sec
            position_str = f"{position_sec // 60}:{position_sec % 60:02d}"
            duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
            remaining_str = f"{remaining_sec // 60}:{remaining_sec % 60:02d}"
            self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")
        self.media_progress.blockSignals(False)
    def set_media_position(self, value):
        duration = self.media_player.duration()
        if duration > 0:
            new_position = int((value / 100) * duration)
            self.media_player.setPosition(new_position)
            guiTools.speak(f"{value}%")
    def go_to_surah(self, metadata):
        self.pause_for_action()
        surah_name_key = f"{metadata['surah_number']}{metadata['surah_name']}"
        if surah_name_key in self.surahsList:
            surah_text = self.surahsList[surah_name_key][1]
            ayah_index = metadata["ayah_number_in_surah"] - 1
            QuranViewer(self, text=surah_text, type=5, category=surah_name_key, index=ayah_index, enableNextPreviouseButtons=False, enableBookmarks=False).exec()
        else:
            guiTools.MessageBox.error(self, "خطأ", f"لم يتم العثور على بيانات السورة: {surah_name_key}")
        self.resume_after_action()
    def show_ayah_info(self, metadata):
        self.pause_for_action()
        surah_number = metadata["surah_number"]
        ayah_number_in_surah = metadata["ayah_number_in_surah"]
        ayah_data = self.quran_data[str(surah_number)]['ayahs'][ayah_number_in_surah - 1]
        sajda_text = "الآية تحتوي على سجدة" if ayah_data.get("sajda") else ""
        info_text = f"رقم الآية: {ayah_number_in_surah}\n"
        info_text += f"رقم السورة: {surah_number} ({metadata['surah_name']})\n"
        info_text += f"رقم الآية في المصحف: {ayah_data['number']}\n"
        info_text += f"الجزء: {ayah_data['juz']}\n"
        info_text += f"الربع: {ayah_data['hizbQuarter']}\n"
        info_text += f"الصفحة: {ayah_data['page']}\n{sajda_text}"
        guiTools.MessageBox.view(self, "معلومات الآية", info_text)
        self.resume_after_action()
    def show_tafseer(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        TafaseerViewer(self, ayah_num, ayah_num).exec()
        self.resume_after_action()
    def show_translation(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        translationViewer(self, ayah_num, ayah_num).exec()
        self.resume_after_action()
    def show_iarab(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        result = functions.iarab.getIarab(ayah_num, ayah_num)
        guiTools.TextViewer(self, "إعراب", result).exec()
        self.resume_after_action()
    def show_tanzil(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        result = functions.tanzil.gettanzil(ayah_num)
        if result:
            guiTools.TextViewer(self, "أسباب النزول", result).exec()
        else:
            guiTools.MessageBox.view(self, "تنبيه", "لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))
    def increase_font_size(self):
        if self.show_font.value() < 100:
            self.show_font.setValue(self.show_font.value() + 1)
    def decrease_font_size(self):
        if self.show_font.value() > 1:
            self.show_font.setValue(self.show_font.value() - 1)
    def update_font_size(self):
        cursor = self.results.textCursor()
        self.results.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.results.setCurrentFont(font)
        self.results.setTextCursor(cursor)
    def copy_line(self):
        try:
            cursor = self.results.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
            else:
                cursor.select(qt1.QTextCursor.SelectionType.BlockUnderCursor)
                pyperclip.copy(cursor.selectedText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))
    def copy_text(self):
        try:
            pyperclip.copy(self.results.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))
    def on_change_reciter_requested(self):
        self.pause_for_action()
        with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
            reciters = json.load(file)
        reciter_list = list(reciters.keys())
        dlg = ChangeReciter(self, reciter_list, self.currentReciter)
        if dlg.exec() == qt.QDialog.DialogCode.Accepted:
            self.currentReciter = dlg.recitersListWidget.currentRow()
        self.resume_after_action()