import os,guiTools,random
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class IslamicQuestionsGame(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.base_path = os.path.join("data", "json", "Islamic_questions_game")
        self.categories_info = {
            "tafseer": {"name": "التفسير", "color": "#1B5E20", "file": "tafseer.json"},  # Dark Green
            "figh": {"name": "الفقه", "color": "#0D47A1", "file": "figh.json"},          # Dark Blue
            "hadith": {"name": "الحديث", "color": "#B71C1C", "file": "hadith.json"},    # Dark Red
            "akida": {"name": "العقيدة", "color": "#006064", "file": "akida.json"},      # Dark Teal
            "arabia": {"name": "اللغة العربية", "color": "#4A148C", "file": "arabia.json"}, # Dark Purple
            "history": {"name": "السيرة والتاريخ", "color": "#E65100", "file": "history.json"} # Dark Orange
        }        
        self.current_category = None
        self.current_topic = None
        self.current_level = None
        self.questions = []
        self.solved_count = 0
        self.total_questions = 0
        self.current_question_index = -1
        self.setup_ui()                
        qt1.QShortcut(qt2.Qt.Key.Key_Escape, self).activated.connect(self.handle_escape)
    def handle_escape(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            self.stacked_widget.setCurrentIndex(0)
        elif current_index == 2:
            self.stacked_widget.setCurrentIndex(1)
        elif current_index == 3:
            self.confirm_exit_game()
    def setup_ui(self):
        self.main_layout = qt.QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        self.stacked_widget = qt.QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)        
        self.categories_widget = qt.QWidget()
        self.categories_grid = qt.QGridLayout(self.categories_widget)
        self.categories_grid.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        row, col = 0, 0                                
        cats = list(self.categories_info.keys())
        for i, cat_key in enumerate(cats):
            cat_data = self.categories_info[cat_key]
            btn = guiTools.QPushButton(cat_data["name"])
            btn.setFixedSize(200, 80)
            btn.setStyleSheet(f"background-color: {cat_data['color']}; color: white; font-weight: bold; font-size: 16px; border-radius: 10px;")
            btn.clicked.connect(lambda checked, k=cat_key: self.show_topics(k))            
            self.categories_grid.addWidget(btn, i % 3, i // 3)
        self.stacked_widget.addWidget(self.categories_widget)        
        self.topics_widget = qt.QWidget()
        topics_layout = qt.QVBoxLayout(self.topics_widget)        
        self.topics_list = guiTools.QListWidget()
        self.topics_list.setSpacing(3)
        self.topics_list.itemActivated.connect(self.show_levels)
        topics_layout.addWidget(self.topics_list)        
        topics_back_btn = guiTools.QPushButton("رجوع")
        topics_back_btn.setAccessibleDescription("Escape")
        topics_back_btn.setFixedSize(150, 40)        
        topics_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 5px;")
        topics_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        topics_layout.addWidget(topics_back_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)        
        self.stacked_widget.addWidget(self.topics_widget)        
        self.levels_widget = qt.QWidget()
        levels_layout = qt.QVBoxLayout(self.levels_widget)
        levels_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)        
        self.level_btns = []
        levels_data = [
            ("سهل", "#2E7D32", 1),       # Green
            ("متوسط", "#E65100", 2),    # Yellow
            ("صعب", "#C62828", 3),      # Red
        ]        
        for name, color, lvl in levels_data:
            btn = guiTools.QPushButton(name)
            btn.setFixedSize(300, 60)
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;")
            btn.clicked.connect(lambda checked, l=lvl: self.start_game(l))
            levels_layout.addWidget(btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
            self.level_btns.append(btn)            
        self.all_levels_btn = guiTools.QPushButton("كل المستويات")
        self.all_levels_btn.setFixedSize(300, 60)
        self.all_levels_btn.setStyleSheet("background-color: #0056b3; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;") # Light Blue
        self.all_levels_btn.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.all_levels_btn.customContextMenuRequested.connect(self.show_all_levels_menu)
        self.all_levels_btn.clicked.connect(self.show_all_levels_menu_at_pos)
        levels_layout.addWidget(self.all_levels_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)        
        levels_back_btn = guiTools.QPushButton("رجوع")
        levels_back_btn .setAccessibleDescription("Escape")
        levels_back_btn.setFixedSize(300, 50)
        levels_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 8px;")
        levels_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        levels_layout.addWidget(levels_back_btn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)        
        self.stacked_widget.addWidget(self.levels_widget)        
        self.game_widget = qt.QWidget()
        game_layout = qt.QVBoxLayout(self.game_widget)        
        top_layout = qt.QHBoxLayout()
        self.game_back_btn = guiTools.QPushButton("رجوع")
        self.game_back_btn .setAccessibleDescription("Escape")
        self.game_back_btn.setFixedSize(80, 40)
        self.game_back_btn.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; border-radius: 5px;")
        self.game_back_btn.clicked.connect(self.confirm_exit_game)
        top_layout.addWidget(self.game_back_btn)        
        self.progress_label = qt.QLabel("تم حل 0 من 0 سؤال")
        self.progress_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progress_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        top_layout.addWidget(self.progress_label, 1)
        top_layout.addStretch()
        game_layout.addLayout(top_layout)        
        self.question_edit = guiTools.QReadOnlyTextEdit()
        self.question_edit.setFixedHeight(150)
        self.question_edit.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        game_layout.addWidget(self.question_edit)        
        game_layout.addStretch()
        self.answers_layout = qt.QVBoxLayout()
        game_layout.addLayout(self.answers_layout)        
        self.stacked_widget.addWidget(self.game_widget)
    def show_topics(self, category_key):
        self.current_category = category_key
        cat_data = self.categories_info[category_key]
        file_path = os.path.join(self.base_path, cat_data["file"])        
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)            
            self.topics_list.clear()
            self.topics_data = data.get("DataArray", [])
            for topic in self.topics_data:
                self.topics_list.addItem(topic.get("arabicName", topic.get("englishName", "بدون اسم")))            
            self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"فشل تحميل البيانات: {e}")
    def show_levels(self):
        row = self.topics_list.currentRow()
        if row < 0: return
        self.current_topic = self.topics_data[row]
        self.stacked_widget.setCurrentIndex(2)
    def show_all_levels_menu_at_pos(self):
        self.show_all_levels_menu(qt2.Qt.AlignmentFlag.AlignCenter)
    def show_all_levels_menu(self, pos):
        menu = qt.QMenu(self)
        random_action = menu.addAction("لعب بعشوائية")
        sequential_action = menu.addAction("من السهل إلى الصعب")        
        action = menu.exec(qt1.QCursor.pos())
        if action == random_action:
            self.start_game("all", mode="random")
        elif action == sequential_action:
            self.start_game("all", mode="sequential")
    def start_game(self, level, mode=None):
        self.current_level = level
        self.questions = []        
        try:
            if level == "all":
                all_files = []
                for f_info in self.current_topic.get("files", []):
                    all_files.append(f_info["path"])                
                if mode == "sequential":                    
                    sorted_files = sorted(self.current_topic.get("files", []), key=lambda x: x["level"])
                    for f_info in sorted_files:
                        self.load_questions_from_path(f_info["path"])
                else:
                    for path in all_files:
                        self.load_questions_from_path(path)
                    random.shuffle(self.questions)
            else:
                target_path = None
                for f_info in self.current_topic.get("files", []):
                    if f_info["level"] == level:
                        target_path = f_info["path"]
                        break                
                if target_path:
                    self.load_questions_from_path(target_path)
                    random.shuffle(self.questions)            
            if not self.questions:
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا توجد أسئلة متاحة لهذا القسم.")
                return            
            self.solved_count = 0
            self.total_questions = len(self.questions)
            self.current_question_index = 0
            self.show_question()
            self.stacked_widget.setCurrentIndex(3)            
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"فشل تحميل الأسئلة: {e}")
    def load_questions_from_path(self, json_path):        
        relative_path = json_path.replace("/database/", "").replace("/", os.sep)
        full_path = os.path.join(self.base_path, relative_path)        
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8-sig") as f:
                self.questions.extend(json.load(f))
    def get_arabic_count_text(self, n):
        if n == 0: return "صفر سؤال"
        if n == 1: return "سؤال واحد"
        if n == 2: return "سؤالان"
        if 3 <= n <= 10: return f"{n} أسئلة"
        if n >= 11: return f"{n} سؤالاً"
        return f"{n} سؤال"
    def show_question(self):
        if self.current_question_index >= self.total_questions:
            solved_text = self.get_arabic_count_text(self.solved_count)
            total_text = self.get_arabic_count_text(self.total_questions)            
            cat_name = self.categories_info[self.current_category]["name"]
            topic_name = self.current_topic.get("arabicName", self.current_topic.get("englishName", ""))            
            level_map = {1: "السهل", 2: "المتوسط", 3: "الصعب", "all": "كل المستويات"}
            level_name = level_map.get(self.current_level, "")            
            msg = f"أحسنت! لقد انتهى الاختبار.\nلقد قمت بحل {solved_text} من {total_text} في {cat_name} في فئة {topic_name}، المستوى {level_name}."
            guiTools.qMessageBox.MessageBox.view(self, "انتهى الاختبار", msg)
            self.stacked_widget.setCurrentIndex(2)
            return            
        q_data = self.questions[self.current_question_index]
        self.question_edit.setText(q_data.get("q", ""))        
        solved_text = self.get_arabic_count_text(self.solved_count)
        total_text = self.get_arabic_count_text(self.total_questions)        
        cat_name = self.categories_info[self.current_category]["name"]
        topic_name = self.current_topic.get("arabicName", self.current_topic.get("englishName", ""))        
        level_map = {1: "السهل", 2: "المتوسط", 3: "الصعب", "all": "كل المستويات"}
        level_name = level_map.get(self.current_level, "")        
        self.progress_label.setText(f"تم حل {solved_text} من {total_text} في {cat_name} في فئة {topic_name}، المستوى {level_name}")                
        while self.answers_layout.count():
            item = self.answers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()                
        answers = q_data.get("answers", [])                
        cat_color = self.categories_info[self.current_category]["color"]        
        for ans in answers:
            btn = guiTools.QPushButton(ans["answer"])
            btn.setStyleSheet(f"background-color: {cat_color}; color: white; font-weight: bold; font-size: 16px; border-radius: 5px; padding: 10px;")
            btn.clicked.connect(lambda checked, a=ans: self.check_answer(a))
            self.answers_layout.addWidget(btn)
    def check_answer(self, selected_answer):
        if selected_answer["t"] == 1:
            guiTools.qMessageBox.MessageBox.view(self, "إجابة صحيحة", "أحسنت، إجابتك صحيحة!")
            self.solved_count += 1
            self.current_question_index += 1
            self.show_question()
        else:            
            q_data = self.questions[self.current_question_index]
            correct_text = ""
            for ans in q_data.get("answers", []):
                if ans["t"] == 1:
                    correct_text = ans["answer"]
                    break            
            guiTools.qMessageBox.MessageBox.error(self, "إجابة خاطئة", f"للأسف الإجابة خاطئة.\nالإجابة الصحيحة هي: {correct_text}")                        
            self.current_question_index += 1
            self.show_question()                
        self.question_edit.setFocus()
    def confirm_exit_game(self):        
        self.stacked_widget.setCurrentIndex(2)
    def showEvent(self, event):
        super().showEvent(event)                