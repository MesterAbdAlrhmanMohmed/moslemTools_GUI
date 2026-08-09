import os,guiTools,random,re,winsound,functions,traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from datetime import datetime
from settings import settings_handler
from custom_errors import log_error_to_file


class IslamicQuestionsGame(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.base_path = os.path.join("data", "json", "Islamic_questions_game")
        self.asked_file = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "asked_questions.json")
        self.game_settings_file = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "game_settings.json")
        self.stats_file = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "game_stats.json")
        try:
            with open(self.asked_file, "r", encoding="utf-8") as f: self.asked_questions = set(json.load(f))
        except Exception as e:
            log_error_to_file(traceback.format_exc())
            self.asked_questions = set()
        try:
            with open(self.game_settings_file, "r", encoding="utf-8") as f: self.game_settings = json.load(f)
        except Exception as e:
            log_error_to_file(traceback.format_exc())
            self.game_settings = {"sound_enabled": True, "stats_enabled": True}
        self.categories_info = {
            "tafseer": {"name": "التفسير", "color": "#1B5E20", "file": "tafseer.json"},
            "figh": {"name": "الفقه", "color": "#0D47A1", "file": "figh.json"},
            "hadith": {"name": "الحديث", "color": "#B71C1C", "file": "hadith.json"},
            "akida": {"name": "العقيدة", "color": "#006064", "file": "akida.json"},
            "arabia": {"name": "اللغة العربية", "color": "#4A148C", "file": "arabia.json"},
            "history": {"name": "السيرة والتاريخ", "color": "#8E2405", "file": "history.json"}
        }
        self.current_category = None
        self.current_topic = None
        self.current_level = None
        self.questions = []
        self.incorrect_questions = []
        self.solved_count = 0
        self.total_questions = 0
        self.current_question_index = -1
        self.filtered_topics_data = []
        self.font_size = int(settings_handler.get("font", "size") or 18)
        self.setup_ui()
        qt1.QShortcut(qt2.Qt.Key.Key_Escape, self).activated.connect(self.handle_escape)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)

    def handle_escape(self):
        current_widget = self.stacked_widget.currentWidget()
        if current_widget in (self.topics_widget, self.stats_widget):
            self.stacked_widget.setCurrentWidget(self.categories_widget)
            qt2.QTimer.singleShot(10, self.first_cat_btn.setFocus)
        elif current_widget == self.levels_widget:
            self.stacked_widget.setCurrentWidget(self.topics_widget)
        elif hasattr(self, 'all_levels_options_widget') and current_widget == self.all_levels_options_widget:
            self.stacked_widget.setCurrentWidget(self.levels_widget)
        elif current_widget == self.game_widget:
            self.confirm_exit_game()

    def setup_ui(self):
        self.main_layout = qt.QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        self.stacked_widget = qt.QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        self.categories_widget = qt.QWidget()
        categories_layout = qt.QVBoxLayout(self.categories_widget)
        categories_layout.addStretch()
        self.sound_checkbox = qt.QCheckBox("تفعيل المؤثرات الصوتية")
        self.sound_checkbox.setChecked(self.game_settings.get("sound_enabled", True))
        self.sound_checkbox.stateChanged.connect(self.save_game_settings)
        categories_layout.addWidget(self.sound_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.stats_checkbox = qt.QCheckBox("تفعيل إحصائيات اللعبة")
        self.stats_checkbox.setChecked(self.game_settings.get("stats_enabled", True))
        self.stats_checkbox.stateChanged.connect(self.save_game_settings)
        self.stats_checkbox.stateChanged.connect(self.toggle_stats_button)
        categories_layout.addWidget(self.stats_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        categories_layout.addSpacing(20)
        self.categories_grid = qt.QGridLayout()
        self.categories_grid.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        categories_layout.addLayout(self.categories_grid)
        cats = list(self.categories_info.keys())
        for i, cat_key in enumerate(cats):
            cat_data = self.categories_info[cat_key]
            btn = guiTools.QPushButton(cat_data["name"])
            btn.setMinimumSize(160, 60)
            btn.setStyleSheet(f"background-color: {cat_data['color']}; color: white; font-weight: bold; font-size: 16px; border-radius: 10px;")
            btn.clicked.connect(lambda checked, k=cat_key: self.show_topics(k))
            self.categories_grid.addWidget(btn, i % 3, i // 3)
            if i == 0: self.first_cat_btn = btn
        self.stats_btn = guiTools.QPushButton("إحصائيات اللعبة")
        self.stats_btn.setMinimumSize(330, 50)
        self.stats_btn.setStyleSheet("QPushButton{background-color: #0000AA; color: white; font-weight: bold; font-size: 16px; border-radius: 10px; border: none; padding: 10px;}QPushButton:hover{background-color: #0000CC;}")
        self.stats_btn.clicked.connect(self.show_game_stats_widget)
        self.stats_btn.setVisible(self.stats_checkbox.isChecked())
        categories_layout.addSpacing(15)
        categories_layout.addWidget(self.stats_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        categories_layout.addStretch()
        self.stacked_widget.addWidget(self.categories_widget)
        self.topics_widget = qt.QWidget()
        topics_layout = qt.QVBoxLayout(self.topics_widget)
        self.search_label = qt.QLabel("ابحث عن قسم اختبار في فئة")
        self.search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        topics_layout.addWidget(self.search_label)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("ابحث عن قسم اختبار في فئة")
        self.search_bar.textChanged.connect(self.on_topic_search)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        topics_layout.addWidget(self.search_bar)
        self.topics_list = guiTools.QListWidget()
        self.topics_list.setSpacing(3)
        self.topics_list.itemActivated.connect(self.show_levels)
        topics_layout.addWidget(self.topics_list)
        topics_back_btn = guiTools.QPushButton("رجوع")
        topics_back_btn.setAccessibleDescription("Escape")
        topics_back_btn.setMinimumSize(120, 35)
        topics_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 5px;")
        topics_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.categories_widget))
        topics_layout.addWidget(topics_back_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.topics_widget)
        self.levels_widget = qt.QWidget()
        levels_layout = qt.QVBoxLayout(self.levels_widget)
        levels_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.level_btns = []
        levels_data = [("سهل", "#2E7D32", 1), ("متوسط", "#E65100", 2), ("صعب", "#C62828", 3)]
        for name, color, lvl in levels_data:
            btn = guiTools.QPushButton(name)
            btn.setMinimumSize(220, 50)
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;")
            btn.clicked.connect(lambda checked, l=lvl: self.start_game(l))
            levels_layout.addWidget(btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
            self.level_btns.append(btn)
        self.all_levels_btn = guiTools.QPushButton("كل المستويات")
        self.all_levels_btn.setMinimumSize(220, 50)
        self.all_levels_btn.setStyleSheet("background-color: #0056b3; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;")
        self.all_levels_btn.clicked.connect(self.show_all_levels_options)
        levels_layout.addWidget(self.all_levels_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        levels_back_btn = guiTools.QPushButton("رجوع")
        levels_back_btn.setAccessibleDescription("Escape")
        levels_back_btn.setMinimumSize(220, 40)
        levels_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 8px;")
        levels_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.topics_widget))
        levels_layout.addWidget(levels_back_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.levels_widget)

        self.all_levels_options_widget = qt.QWidget()
        all_levels_layout = qt.QVBoxLayout(self.all_levels_options_widget)
        all_levels_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        all_levels_layout.setSpacing(15)
        self.random_mode_btn = guiTools.QPushButton("لعب بعشوائية")
        self.random_mode_btn.setMinimumSize(220, 50)
        self.random_mode_btn.clicked.connect(lambda: self.start_game("all", mode="random"))
        all_levels_layout.addWidget(self.random_mode_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.sequential_mode_btn = guiTools.QPushButton("من السهل إلى الصعب")
        self.sequential_mode_btn.setMinimumSize(220, 50)
        self.sequential_mode_btn.clicked.connect(lambda: self.start_game("all", mode="sequential"))
        all_levels_layout.addWidget(self.sequential_mode_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.all_levels_back_btn = guiTools.QPushButton("رجوع")
        self.all_levels_back_btn.setAccessibleDescription("Escape")
        self.all_levels_back_btn.setMinimumSize(220, 40)
        self.all_levels_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 8px;")
        self.all_levels_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.levels_widget))
        all_levels_layout.addWidget(self.all_levels_back_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.all_levels_options_widget)
        self.game_widget = qt.QWidget()
        game_layout = qt.QVBoxLayout(self.game_widget)
        top_layout = qt.QHBoxLayout()
        self.game_back_btn = guiTools.QPushButton("رجوع")
        self.game_back_btn.setAccessibleDescription("Escape")
        self.game_back_btn.setMinimumSize(80, 35)
        self.game_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 5px;")
        self.game_back_btn.clicked.connect(self.confirm_exit_game)
        top_layout.addWidget(self.game_back_btn)
        self.progress_label = guiTools.QNavigableLabel("تم حل 0 من 0 سؤال")
        self.progress_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progress_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        top_layout.addWidget(self.progress_label, 1)
        top_layout.addStretch()
        game_layout.addLayout(top_layout)
        self.question_edit = guiTools.QReadOnlyTextEdit(viewer_name="islamicQuestionsGame")
        self.question_edit.setMinimumHeight(120)
        self.question_edit.setStyleSheet("padding: 10px;")
        game_layout.addWidget(self.question_edit)
        game_layout.addStretch()
        self.answers_layout = qt.QVBoxLayout()
        game_layout.addLayout(self.answers_layout)
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        game_layout.addWidget(self.font_laybol)
        game_layout.addWidget(self.show_font)
        self.stacked_widget.addWidget(self.game_widget)
        self.stats_widget = qt.QWidget()
        stats_outer_layout = qt.QHBoxLayout(self.stats_widget)
        stats_outer_layout.setContentsMargins(10, 10, 10, 10)
        stats_outer_layout.addStretch(1)
        stats_container = qt.QWidget()
        stats_container.setMinimumWidth(800)
        stats_container.setMaximumWidth(1100)
        stats_layout = qt.QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(15)
        self.stats_text_viewer = guiTools.QReadOnlyTextEdit(viewer_name="gameStats")
        stats_layout.addWidget(self.stats_text_viewer)
        stats_btns_layout = qt.QHBoxLayout()
        self.stats_back_btn = guiTools.QPushButton("رجوع")
        self.stats_back_btn.setAccessibleDescription("Escape")
        self.stats_back_btn.setMinimumSize(120, 38)
        self.stats_back_btn.setStyleSheet("QPushButton{background-color: #0000AA; color: white; font-weight: bold; border-radius: 5px; font-size: 15px;}QPushButton:hover{background-color: #0000CC;}")
        self.stats_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.categories_widget))
        stats_btns_layout.addWidget(self.stats_back_btn)
        stats_btns_layout.addStretch()
        self.stats_delete_btn = guiTools.QPushButton("حذف الإحصائيات")
        self.stats_delete_btn.setShortcut("ctrl+del")
        self.stats_delete_btn.setAccessibleDescription("control plus delete")
        self.stats_delete_btn.setMinimumSize(140, 38)
        self.stats_delete_btn.setStyleSheet("QPushButton{background-color: #D32F2F; color: white; font-weight: bold; border-radius: 5px; font-size: 15px;}QPushButton:hover{background-color: #A52A2A;}")
        self.stats_delete_btn.clicked.connect(self.confirm_and_delete_stats)
        stats_btns_layout.addWidget(self.stats_delete_btn)
        stats_layout.addLayout(stats_btns_layout)
        stats_outer_layout.addWidget(stats_container, 10)
        stats_outer_layout.addStretch(1)
        self.stacked_widget.addWidget(self.stats_widget)

    def toggle_stats_button(self):
        self.stats_btn.setVisible(self.stats_checkbox.isChecked())

    def show_game_stats_widget(self):
        stats = self.load_game_stats()
        if stats.get("total_games", 0) == 0 or stats.get("total_answered", 0) == 0:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا يوجد إحصائيات حتى الآن.")
            return
        self.stats_text_viewer.setText(self.build_all_stats_text())
        self.stacked_widget.setCurrentWidget(self.stats_widget)
        qt2.QTimer.singleShot(10, self.stats_text_viewer.setFocus)

    def confirm_and_delete_stats(self):
        if guiTools.QQuestionMessageBox.view(self, "تأكيد حذف الإحصائيات", "هل أنت متأكد من حذف جميع إحصائيات اللعبة؟", "نعم", "لا") == 0:
            self.reset_game_stats()
            self.stats_text_viewer.setText(self.build_all_stats_text())
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم حذف جميع إحصائيات اللعبة بنجاح.")

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches

    def on_topic_search(self):
        search_text = self.search_bar.text().lower()
        self.topics_list.clear()
        self.filtered_topics_data = []
        tashkeel_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', search_text)
        for topic in self.topics_data:
            name = topic.get("arabicName", topic.get("englishName", "بدون اسم"))
            if normalized_pattern in tashkeel_pattern.sub('', name.lower()):
                self.topics_list.addItem(name)
                self.filtered_topics_data.append(topic)

    def show_topics(self, category_key):
        self.current_category = category_key
        cat_data = self.categories_info[category_key]
        self.search_label.setText(f"ابحث عن قسم اختبار في فئة {cat_data['name']}")
        self.search_bar.setPlaceholderText(f"ابحث عن قسم اختبار في فئة {cat_data['name']}")
        self.search_bar.clear()
        file_path = os.path.join(self.base_path, cat_data["file"])
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            self.topics_data = data.get("DataArray", [])
            self.on_topic_search()
            self.stacked_widget.setCurrentWidget(self.topics_widget)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"فشل تحميل البيانات: {e}")

    def show_levels(self):
        row = self.topics_list.currentRow()
        if row < 0: return
        self.current_topic = self.filtered_topics_data[row]
        self.stacked_widget.setCurrentWidget(self.levels_widget)

    def show_all_levels_options(self):
        cat_color = self.categories_info[self.current_category]["color"] if self.current_category in self.categories_info else "#0056b3"
        btn_style = f"background-color: {cat_color}; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;"
        self.random_mode_btn.setStyleSheet(btn_style)
        self.sequential_mode_btn.setStyleSheet(btn_style)
        self.stacked_widget.setCurrentWidget(self.all_levels_options_widget)
        qt2.QTimer.singleShot(10, self.random_mode_btn.setFocus)

    def show_game_stats_dialog(self):
        self.show_game_stats_widget()

    def load_game_stats(self):
        defaults = {
            "total_games": 0,
            "total_answered": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "unique_answered": [],
            "categories_count": {},
            "levels_count": {},
            "category_correct": {},
            "category_total": {},
            "highest_score": {"score": 0, "total": 0},
            "last_played": "",
            "question_errors": {},
            "level_total": {},
            "level_correct": {},
            "all_levels_games_count": 0,
            "all_levels_total": {},
            "all_levels_correct": {}
        }
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    defaults.update(data)
                    return defaults
        except Exception:
            pass
        return defaults

    def save_game_stats(self, stats):
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error_to_file(traceback.format_exc())

    def reset_game_stats(self):
        if os.path.exists(self.stats_file):
            try:
                os.remove(self.stats_file)
            except Exception as e:
                log_error_to_file(traceback.format_exc())

    def get_total_database_questions_count(self):
        total_unique = set()
        def _extract_from_obj(obj):
            if isinstance(obj, list):
                for item in obj:
                    _extract_from_obj(item)
            elif isinstance(obj, dict):
                if "q" in obj and isinstance(obj["q"], str) and obj["q"].strip():
                    total_unique.add(obj["q"].strip())
                if "DataArray" in obj:
                    _extract_from_obj(obj["DataArray"])
                if "files" in obj and isinstance(obj["files"], list):
                    for f_info in obj["files"]:
                        if isinstance(f_info, dict) and "path" in f_info:
                            rel_path = f_info["path"].replace("/database/", "").replace("/", os.sep)
                            f_full = os.path.join(self.base_path, rel_path)
                            if os.path.exists(f_full):
                                try:
                                    with open(f_full, "r", encoding="utf-8-sig") as f2:
                                        _extract_from_obj(json.load(f2))
                                except Exception:
                                    pass

        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.json'):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, "r", encoding="utf-8-sig") as f:
                                _extract_from_obj(json.load(f))
                        except Exception:
                            pass
        except Exception:
            pass
        return len(total_unique) if total_unique else None

    def format_now_last_played(self):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        period = "صباحاً" if now.hour < 12 else "مساءً"
        h = now.hour % 12
        if h == 0:
            h = 12
        time_str = f"{h:02d}:{now.minute:02d} {period}"
        return {"date": date_str, "time": time_str}

    def build_all_stats_text(self):
        stats = self.load_game_stats()
        total_games = stats.get("total_games", 0)
        total_ans = stats.get("total_answered", 0)
        if total_games == 0 or total_ans == 0:
            return "لا يوجد إحصائيات حتى الآن."
        correct = stats.get("correct_answers", 0)
        incorrect = stats.get("incorrect_answers", 0)
        success_rate = min(100.0, max(0.0, (correct / total_ans * 100))) if total_ans > 0 else 0.0
        unique_ans = len(stats.get("unique_answered", []))
        total_db_q = self.get_total_database_questions_count()
        if total_db_q and total_db_q > 0:
            unique_ratio = min(100.0, max(0.0, (unique_ans / total_db_q) * 100))
            unique_text = f"عدد الأسئلة الفريدة التي تمت الإجابة عنها: {unique_ans} من {total_db_q} سؤالاً (بنسبة {unique_ratio:.1f}%)."
        else:
            unique_text = f"عدد الأسئلة الفريدة التي تمت الإجابة عنها: {unique_ans} سؤالاً."
        hs = stats.get("highest_score", {"score": 0, "total": 0})
        hs_text = f"{hs.get('score', 0)} من {hs.get('total', 0)}" if hs.get("total", 0) > 0 else "0 من 0"
        lp = stats.get("last_played", "")
        if isinstance(lp, dict):
            lp_date = lp.get("date", "لم تلعب بعد")
            lp_time = lp.get("time", "لم تلعب بعد")
        elif isinstance(lp, str) and lp and lp != "لم تلعب بعد":
            try:
                dt = datetime.strptime(lp, "%Y-%m-%d %H:%M")
                period = "صباحاً" if dt.hour < 12 else "مساءً"
                h = dt.hour % 12
                if h == 0: h = 12
                lp_date = dt.strftime("%Y-%m-%d")
                lp_time = f"{h:02d}:{dt.minute:02d} {period}"
            except:
                lp_date = lp
                lp_time = "لم تلعب بعد"
        else:
            lp_date = "لم تلعب بعد"
            lp_time = "لم تلعب بعد"
        cats_count = stats.get("categories_count", {})
        top_cat_key = max(cats_count, key=cats_count.get) if cats_count else None
        top_cat_name = self.categories_info[top_cat_key]["name"] if top_cat_key in self.categories_info else "لا يوجد"
        levels_count = stats.get("levels_count", {})
        filtered_levels = {k: v for k, v in levels_count.items() if str(k) not in ("all", "all_levels")}
        level_map = {"1": "السهل", "2": "المتوسط", "3": "الصعب", 1: "السهل", 2: "المتوسط", 3: "الصعب"}
        top_lvl_key = max(filtered_levels, key=filtered_levels.get) if filtered_levels else None
        top_lvl_name = level_map.get(top_lvl_key, "لا يوجد") if top_lvl_key is not None else "لا يوجد"
        cat_correct = stats.get("category_correct", {})
        cat_total = stats.get("category_total", {})
        eligible_cat_rates = {}
        for cat_key, cat_info in self.categories_info.items():
            tot = cat_total.get(cat_key, 0)
            cor = cat_correct.get(cat_key, 0)
            if tot >= 10:
                rate = min(100.0, max(0.0, (cor / tot) * 100))
                eligible_cat_rates[cat_key] = rate
        if len(eligible_cat_rates) == 0:
            strongest_text = "لا توجد بيانات كافية لتحديد الأقوى والأضعف."
            weakest_text = "لا توجد بيانات كافية لتحديد الأقوى والأضعف."
        elif len(eligible_cat_rates) == 1:
            only_key = list(eligible_cat_rates.keys())[0]
            strongest_text = f"{self.categories_info[only_key]['name']} (نسبة الإتقان: {eligible_cat_rates[only_key]:.1f}%)"
            weakest_text = "يتطلب لعب المزيد من الفئات لتحديد الفئة الأضعف"
        else:
            max_rate = max(eligible_cat_rates.values())
            min_rate = min(eligible_cat_rates.values())
            strongest_keys = [k for k, v in eligible_cat_rates.items() if v == max_rate]
            weakest_keys = [k for k, v in eligible_cat_rates.items() if v == min_rate]
            strongest_cat_key = strongest_keys[0]
            strongest_text = f"{self.categories_info[strongest_cat_key]['name']} (نسبة الإتقان: {max_rate:.1f}%)"
            if min_rate == max_rate:
                weakest_text = "لا توجد فئة ضعيفة (نسب الإتقان متساوية)"
            else:
                weakest_cat_key = weakest_keys[0]
                weakest_text = f"{self.categories_info[weakest_cat_key]['name']} (نسبة الإتقان: {min_rate:.1f}%)"
        q_errors = stats.get("question_errors", {})
        if q_errors:
            top_wrong_q = max(q_errors, key=q_errors.get)
            top_wrong_count = q_errors[top_wrong_q]
            wrong_q_formatted = f"أكثر سؤال أخطأت فيه:\n\n{top_wrong_q}\nعدد الأخطاء: {top_wrong_count}"
        else:
            wrong_q_formatted = "أكثر سؤال أخطأت فيه:\n\nلا يوجد"
        played_mastery_lines = []
        unplayed_cat_lines = []
        for cat_key, cat_info in self.categories_info.items():
            tot = cat_total.get(cat_key, 0)
            cor = cat_correct.get(cat_key, 0)
            if tot > 0:
                rate = min(100.0, max(0.0, (cor / tot) * 100))
                played_mastery_lines.append(f"{cat_info['name']}: {rate:.1f}%")
            else:
                unplayed_cat_lines.append(f"{cat_info['name']}")
        mastery_section = []
        if played_mastery_lines:
            mastery_section.extend(played_mastery_lines)
        else:
            mastery_section.append("لم يتم لعب أي فئة بعد")
        if unplayed_cat_lines:
            mastery_section.append("")
            mastery_section.append("الفئات التي لم يتم لعبها بعد:")
            mastery_section.extend(unplayed_cat_lines)

        level_total = stats.get("level_total", {})
        level_correct = stats.get("level_correct", {})
        level_lines = []
        for lvl_id, lvl_name in [("1", "المستوى السهل"), ("2", "المستوى المتوسط"), ("3", "المستوى الصعب")]:
            tot = level_total.get(lvl_id, 0)
            cor = level_correct.get(lvl_id, 0)
            if tot > 0:
                rate = min(100.0, max(0.0, (cor / tot) * 100))
                level_lines.append(f"{lvl_name}: {cor} إجابة صحيحة من {tot} (نسبة الإتقان: {rate:.1f}%)")
            else:
                level_lines.append(f"{lvl_name}: لم تلعب أسئلة من هذا المستوى بعد")

        all_levels_games = stats.get("all_levels_games_count", 0)
        all_levels_total = stats.get("all_levels_total", {})
        all_levels_correct = stats.get("all_levels_correct", {})
        all_levels_section = []
        if all_levels_games > 0 or any(v > 0 for v in all_levels_total.values()):
            all_levels_section.append(f"لقد لعبت خيار (كل المستويات) بعدد {all_levels_games} مرة، وكانت التقسيمات كالتالي (من السهل إلى الصعب):")
            for lvl_id, lvl_name in [("1", "المستوى السهل"), ("2", "المستوى المتوسط"), ("3", "المستوى الصعب")]:
                tot = all_levels_total.get(lvl_id, 0)
                cor = all_levels_correct.get(lvl_id, 0)
                if tot > 0:
                    rate = min(100.0, max(0.0, (cor / tot) * 100))
                    all_levels_section.append(f"{lvl_name}: {cor} صحيحة من {tot} (نسبة الإتقان: {rate:.1f}%)")
                else:
                    all_levels_section.append(f"{lvl_name}: 0 أسئلة")

        lines = [
            "الإحصائيات العامة",
            "",
            f"إجمالي عدد مرات اللعب: {total_games}",
            f"إجمالي عدد الأسئلة التي أجبت عنها: {total_ans}",
            f"إجمالي الإجابات الصحيحة: {correct}",
            f"إجمالي الإجابات الخاطئة: {incorrect}",
            f"نسبة النجاح العامة: {success_rate:.1f}%",
            unique_text,
            f"أفضل أداء في اختبار واحد: {hs_text}",
            "آخر مرة لعبت فيها:",
            f"التاريخ: {lp_date}",
            f"الساعة: {lp_time}",
            "",
            "",
            "تحليل الأداء",
            "",
            f"أكثر فئة لعبت فيها: {top_cat_name}",
            f"أكثر مستوى لعبت فيه: {top_lvl_name}",
            f"أقوى فئة لديك: {strongest_text}",
            f"أضعف فئة لديك: {weakest_text}",
            "",
            "الإتقان مقارنة بين المستويات (من السهل إلى الصعب):",
            ""
        ]
        lines.extend(level_lines)
        if all_levels_section:
            lines.extend(["", "إحصائيات خيار كل المستويات:"])
            lines.extend(all_levels_section)
        lines.extend([
            "",
            wrong_q_formatted,
            "",
            "",
            "الإتقان حسب الفئة",
            ""
        ])
        lines.extend(mastery_section)
        return "\n".join(lines)

    def start_game(self, level, mode=None):
        self.current_level = level
        self.questions = []
        self.round_level_solved = {1: 0, 2: 0, 3: 0}
        self.round_level_total = {1: 0, 2: 0, 3: 0}
        try:
            if level == "all":
                if mode == "sequential":
                    sorted_files = sorted(self.current_topic.get("files", []), key=lambda x: x["level"])
                    for f_info in sorted_files:
                        self.load_questions_from_path(f_info["path"], lvl=f_info["level"])
                else:
                    for f_info in self.current_topic.get("files", []):
                        self.load_questions_from_path(f_info["path"], lvl=f_info["level"])
                    random.shuffle(self.questions)
            else:
                target_path = None
                for f_info in self.current_topic.get("files", []):
                    if f_info["level"] == level:
                        target_path = f_info["path"]
                        break
                if target_path:
                    self.load_questions_from_path(target_path, lvl=level)
                    random.shuffle(self.questions)
            if not self.questions:
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا توجد أسئلة متاحة لهذا القسم.")
                return
            u_qs, seen = [], set()
            for q in self.questions:
                if q.get("q") not in seen:
                    u_qs.append(q)
                    seen.add(q.get("q"))
            self.questions = u_qs
            temp_qs = [q for q in self.questions if q.get("q") not in self.asked_questions]
            if temp_qs: self.questions = temp_qs
            else:
                for q in self.questions: self.asked_questions.discard(q.get("q"))
                try:
                    with open(self.asked_file, "w", encoding="utf-8") as f: json.dump(list(self.asked_questions), f, ensure_ascii=False)
                except Exception as e:
                    log_error_to_file(traceback.format_exc())
            self.solved_count = 0
            self.incorrect_questions = []
            self.total_questions = len(self.questions)
            self.current_question_index = 0

            for q in self.questions:
                l_val = q.get("_level", 1 if level != "all" else 1)
                try:
                    l_int = int(l_val)
                    if l_int in self.round_level_total:
                        self.round_level_total[l_int] += 1
                except Exception as e:
                    log_error_to_file(traceback.format_exc())

            if self.stats_checkbox.isChecked():
                stats = self.load_game_stats()
                stats["total_games"] = stats.get("total_games", 0) + 1
                cat_counts = stats.get("categories_count", {})
                if self.current_category:
                    cat_counts[self.current_category] = cat_counts.get(self.current_category, 0) + 1
                stats["categories_count"] = cat_counts

                lvl_counts = stats.get("levels_count", {})
                if level == "all":
                    stats["all_levels_games_count"] = stats.get("all_levels_games_count", 0) + 1
                else:
                    lvl_key = str(level)
                    lvl_counts[lvl_key] = lvl_counts.get(lvl_key, 0) + 1
                stats["levels_count"] = lvl_counts

                stats["last_played"] = self.format_now_last_played()
                self.save_game_stats(stats)
            self.show_question()
            self.stacked_widget.setCurrentWidget(self.game_widget)
            qt2.QTimer.singleShot(10, self.question_edit.setFocus)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"فشل تحميل الأسئلة: {e}")

    def load_questions_from_path(self, json_path, lvl=None):
        relative_path = json_path.replace("/database/", "").replace("/", os.sep)
        full_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8-sig") as f:
                items = json.load(f)
                if isinstance(items, list):
                    if lvl is not None:
                        for q in items:
                            if isinstance(q, dict):
                                q["_level"] = lvl
                    self.questions.extend(items)

    def get_arabic_count_text(self, n):
        if n == 0: return "صفر سؤال"
        if n == 1: return "سؤال واحد"
        if n == 2: return "سؤالان"
        if 3 <= n <= 10: return f"{n} أسئلة"
        if n >= 11: return f"{n} سؤالاً"
        return f"{n} سؤال"

    def show_question(self):
        cat_name = self.categories_info[self.current_category]["name"]
        topic_name = self.current_topic.get("arabicName", self.current_topic.get("englishName", ""))
        level_map = {1: "السهل", 2: "المتوسط", 3: "الصعب", "all": "كل المستويات"}
        level_name = level_map.get(self.current_level, "")
        if self.current_question_index >= self.total_questions:
            if self.stats_checkbox.isChecked():
                stats = self.load_game_stats()
                hs = stats.get("highest_score", {"score": 0, "total": 0})
                prev_score = hs.get("score", 0)
                prev_total = hs.get("total", 0)
                prev_ratio = (prev_score / prev_total) if prev_total > 0 else -1.0
                curr_ratio = (self.solved_count / self.total_questions) if self.total_questions > 0 else 0.0
                if curr_ratio > prev_ratio or (abs(curr_ratio - prev_ratio) < 1e-5 and self.total_questions > prev_total):
                    stats["highest_score"] = {"score": self.solved_count, "total": self.total_questions}
                    self.save_game_stats(stats)
            solved_text = self.get_arabic_count_text(self.solved_count)
            total_text = self.get_arabic_count_text(self.total_questions)
            if self.current_level == "all":
                s1 = self.get_arabic_count_text(self.round_level_solved.get(1, 0))
                t1 = self.get_arabic_count_text(self.round_level_total.get(1, 0))
                s2 = self.get_arabic_count_text(self.round_level_solved.get(2, 0))
                t2 = self.get_arabic_count_text(self.round_level_total.get(2, 0))
                s3 = self.get_arabic_count_text(self.round_level_solved.get(3, 0))
                t3 = self.get_arabic_count_text(self.round_level_total.get(3, 0))
                msg = (f"أحسنت! لقد انتهى الاختبار.\n"
                       f"لقد قمت بحل {solved_text} من {total_text} في {cat_name} في فئة {topic_name} (لعب كل المستويات).\n\n"
                       f"التقسيمات حسب المستويات (من السهل إلى الصعب):\n"
                       f"المستوى السهل: {s1} من {t1}\n"
                       f"المستوى المتوسط: {s2} من {t2}\n"
                       f"المستوى الصعب: {s3} من {t3}")
            else:
                msg = f"أحسنت! لقد انتهى الاختبار.\nلقد قمت بحل {solved_text} من {total_text} في {cat_name} في فئة {topic_name}، المستوى {level_name}."
            if self.incorrect_questions:
                incorrect_text = self.get_arabic_count_text(len(self.incorrect_questions))
                msg += f"\n\nالأسئلة التي تم حلها بشكل خاطئ: {incorrect_text}\n\n"
                msg += "\n\n".join([f"{item['q']}\nالإجابة الصحيحة: {item['correct']}" for item in self.incorrect_questions])
            guiTools.qMessageBox.MessageBox.view(self, "انتهى الاختبار", msg)
            self.clear_asked_questions()
            self.stacked_widget.setCurrentWidget(self.categories_widget)
            qt2.QTimer.singleShot(10, self.first_cat_btn.setFocus)
            return
        q_data = self.questions[self.current_question_index]
        if q_data.get("q") not in self.asked_questions:
            self.asked_questions.add(q_data.get("q"))
            try:
                with open(self.asked_file, "w", encoding="utf-8") as f: json.dump(list(self.asked_questions), f, ensure_ascii=False)
            except Exception as e:
                log_error_to_file(traceback.format_exc())
        self.question_edit.setText(q_data.get("q", ""))
        self.update_question_font()
        solved_text = self.get_arabic_count_text(self.solved_count)
        seen_text = self.get_arabic_count_text(self.current_question_index)
        total_text = self.get_arabic_count_text(self.total_questions)
        self.progress_label.setText(f"لقد قمت بحل {solved_text} من {seen_text} عُرِضَتْ عَلَيْكَ، وإجمالي الجولة {total_text} في {cat_name} في فئة {topic_name}، المستوى {level_name}")
        while self.answers_layout.count():
            item = self.answers_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        answers = q_data.get("answers", [])
        shuffled_answers = random.sample(answers, len(answers))
        cat_color = self.categories_info[self.current_category]["color"]
        answer_buttons = []
        for ans in shuffled_answers:
            btn = guiTools.QPushButton(ans["answer"])
            btn.setStyleSheet(f"background-color: {cat_color}; color: white; font-weight: bold; font-size: 16px; border-radius: 5px; padding: 10px;")
            btn.clicked.connect(lambda checked, a=ans: self.check_answer(a))
            self.answers_layout.addWidget(btn)
            answer_buttons.append(btn)
        if answer_buttons:
            self.setTabOrder(self.question_edit, answer_buttons[0])
            for i in range(len(answer_buttons) - 1):
                self.setTabOrder(answer_buttons[i], answer_buttons[i + 1])
            self.setTabOrder(answer_buttons[-1], self.show_font)

    def check_answer(self, selected_answer):
        sound_enabled = self.sound_checkbox.isChecked()
        stats_enabled = self.stats_checkbox.isChecked()
        q_data = self.questions[self.current_question_index]
        q_text = q_data.get("q", "")
        q_lvl = str(q_data.get("_level", 1))

        if stats_enabled:
            stats = self.load_game_stats()
            stats["total_answered"] = stats.get("total_answered", 0) + 1

            unique = set(stats.get("unique_answered", []))
            if q_text and q_text.strip():
                unique.add(q_text.strip())
            stats["unique_answered"] = list(unique)

            cat_tot = stats.get("category_total", {})
            if self.current_category:
                cat_tot[self.current_category] = cat_tot.get(self.current_category, 0) + 1
            stats["category_total"] = cat_tot

            level_tot = stats.get("level_total", {})
            level_tot[q_lvl] = level_tot.get(q_lvl, 0) + 1
            stats["level_total"] = level_tot

            if self.current_level == "all":
                all_tot = stats.get("all_levels_total", {})
                all_tot[q_lvl] = all_tot.get(q_lvl, 0) + 1
                stats["all_levels_total"] = all_tot

        if selected_answer["t"] == 1:
            if sound_enabled: winsound.PlaySound(r"data\sounds\game\true.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.solved_count += 1
            if stats_enabled:
                stats["correct_answers"] = stats.get("correct_answers", 0) + 1

                cat_cor = stats.get("category_correct", {})
                if self.current_category:
                    cat_cor[self.current_category] = cat_cor.get(self.current_category, 0) + 1
                stats["category_correct"] = cat_cor

                level_cor = stats.get("level_correct", {})
                level_cor[q_lvl] = level_cor.get(q_lvl, 0) + 1
                stats["level_correct"] = level_cor

                if self.current_level == "all":
                    all_cor = stats.get("all_levels_correct", {})
                    all_cor[q_lvl] = all_cor.get(q_lvl, 0) + 1
                    stats["all_levels_correct"] = all_cor

            try:
                int_l = int(q_lvl)
                if int_l in self.round_level_solved:
                    self.round_level_solved[int_l] += 1
            except Exception as e:
                log_error_to_file(traceback.format_exc())
        else:
            correct_text = ""
            for ans in q_data.get("answers", []):
                if ans["t"] == 1:
                    correct_text = ans["answer"]
                    break
            self.incorrect_questions.append({"q": q_data.get("q"), "correct": correct_text})
            if stats_enabled:
                stats["incorrect_answers"] = stats.get("incorrect_answers", 0) + 1
                q_err = stats.get("question_errors", {})
                if q_text and q_text.strip():
                    q_err[q_text.strip()] = q_err.get(q_text.strip(), 0) + 1
                stats["question_errors"] = q_err
            guiTools.MessageBoxForGame.error(self, "إجابة خاطئة", f"للأسف الإجابة خاطئة.\nالإجابة الصحيحة هي: {correct_text}", sound_enabled=sound_enabled)

        if stats_enabled:
            self.save_game_stats(stats)
        self.current_question_index += 1
        self.show_question()
        if self.current_question_index < self.total_questions:
            self.question_edit.setFocus()

    def save_game_settings(self):
        self.game_settings["sound_enabled"] = self.sound_checkbox.isChecked()
        self.game_settings["stats_enabled"] = self.stats_checkbox.isChecked()
        try:
            os.makedirs(os.path.dirname(self.game_settings_file), exist_ok=True)
            with open(self.game_settings_file, "w", encoding="utf-8") as f: json.dump(self.game_settings, f, ensure_ascii=False)
        except Exception as e:
            log_error_to_file(traceback.format_exc())

    def clear_asked_questions(self):
        self.asked_questions.clear()
        if os.path.exists(self.asked_file):
            try: os.remove(self.asked_file)
            except Exception as e: log_error_to_file(traceback.format_exc())

    def confirm_exit_game(self):
        if guiTools.QQuestionMessageBox.view(self, "تأكيد الخروج", "هل أنت متأكد من الخروج من الجولة؟", "نعم", "لا") == 0:
            self.clear_asked_questions()
            self.stacked_widget.setCurrentWidget(self.categories_widget)
            qt2.QTimer.singleShot(10, self.first_cat_btn.setFocus)

    def font_size_changed(self, value):
        self.font_size = value
        settings_handler.set("font", "size", str(value))
        self.update_question_font()
        guiTools.speak(str(self.font_size))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def update_question_font(self):
        font_is_bold = settings_handler.get("font", "bold") == "True"
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(font_is_bold)
        self.question_edit.setFont(font)
        cursor = self.question_edit.textCursor()
        self.question_edit.selectAll()
        self.question_edit.setCurrentFont(font)
        self.question_edit.setTextCursor(cursor)
        if hasattr(self, "show_font") and self.show_font.value() != self.font_size:
            self.show_font.blockSignals(True)
            self.show_font.setValue(self.font_size)
            self.show_font.blockSignals(False)
        wrap_val = settings_handler.get("font_wrap", "islamicQuestionsGame")
        if wrap_val == "True" or (wrap_val == "" and settings_handler.get("font", "wrap") == "True"):
            self.question_edit.setLineWrapMode(qt.QTextEdit.LineWrapMode.WidgetWidth)
            self.question_edit.setWordWrapMode(qt1.QTextOption.WrapMode.WordWrap)
        else:
            self.question_edit.setLineWrapMode(qt.QTextEdit.LineWrapMode.NoWrap)

    def showEvent(self, event):
        super().showEvent(event)
        self.font_size = int(settings_handler.get("font", "size") or 18)
        if hasattr(self, "show_font"):
            self.show_font.setValue(self.font_size)
        self.update_question_font()
