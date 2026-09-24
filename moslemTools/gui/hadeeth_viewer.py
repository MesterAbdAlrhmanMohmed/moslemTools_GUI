from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings, os, re
import ujson as json
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
from collections import Counter


class SelectBabDialog(qt.QDialog):
    def __init__(self, parent, book_file: str, book_name_ar: str = "", current_chapter_id=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار الباب")
        self.setMinimumSize(320, 200)
        self.resize(360, 220)
        self.selected_chapter_id = None
        self.selected_chapter_name = ""
        self.selected_raw_chapter_name = ""

        if parent:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(parent.frameGeometry().center())
            self.move(frame_geometry.topLeft())

        self.chapters_data = []
        full_path = os.path.join(os.getenv('appdata'), settings.app.appName, "ahadeeth", book_file)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    hadiths = data.get("hadiths", [])
                    counts = Counter(h.get("chapterId") for h in hadiths)
                    for c in data.get("chapters", []):
                        cid = c.get("id")
                        cname = c.get("arabic", "").strip()
                        cnt = counts.get(cid, 0)
                        display_text = f"{cname} ({cnt} حديث)"
                        self.chapters_data.append({
                            "id": cid,
                            "name": cname,
                            "display": display_text
                        })
            except Exception:
                pass

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(10)

        self.label = qt.QLabel("اختر الباب:")
        self.label.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("ابحث في الأبواب...")
        self.search_bar.setAccessibleName("ابحث في الأبواب")
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setMinimumHeight(32)
        self.search_bar.textChanged.connect(self.on_search)
        layout.addWidget(self.search_bar)

        self.bab_combo = qt.QComboBox()
        self.bab_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.bab_combo.setAccessibleName("اختر الباب")
        self.bab_combo.setMinimumHeight(35)
        self.bab_combo.setStyleSheet("QComboBox { padding: 4px 12px; font-weight: bold; font-size: 13px; }")
        self.populate_combo(self.chapters_data)

        if current_chapter_id is not None:
            for i in range(self.bab_combo.count()):
                if self.bab_combo.itemData(i) == current_chapter_id:
                    self.bab_combo.setCurrentIndex(i)
                    break
        else:
            self.bab_combo.setCurrentIndex(0)

        layout.addWidget(self.bab_combo)

        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.select_button = guiTools.QPushButton("الذهاب")
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
        t = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)
        t = re.sub(r'[إأآ]', 'ا', t)
        return t.replace('ى', 'ي').strip().lower()

    def populate_combo(self, items):
        self.bab_combo.blockSignals(True)
        self.bab_combo.clear()
        self.bab_combo.addItem("فتح الكتاب كاملا", None)
        for it in items:
            self.bab_combo.addItem(it["display"], it["id"])
        self.bab_combo.blockSignals(False)

    def on_search(self):
        query = self.normalize(self.search_bar.text())
        if query:
            filtered = [it for it in self.chapters_data if query in self.normalize(it["name"])]
        else:
            filtered = list(self.chapters_data)

        current_data = self.bab_combo.currentData()
        self.populate_combo(filtered)
        found = False
        if current_data is not None:
            for i in range(self.bab_combo.count()):
                if self.bab_combo.itemData(i) == current_data:
                    self.bab_combo.setCurrentIndex(i)
                    found = True
                    break
        if not found:
            self.bab_combo.setCurrentIndex(0)

    def on_select(self):
        self.selected_chapter_id = self.bab_combo.currentData()
        self.selected_chapter_name = self.bab_combo.currentText()
        if self.selected_chapter_id is not None:
            for it in self.chapters_data:
                if it["id"] == self.selected_chapter_id:
                    self.selected_raw_chapter_name = it["name"]
                    break
        else:
            self.selected_raw_chapter_name = ""
        self.accept()


class hadeeth_viewer(qt.QDialog):
    def __init__(self, p, book_name, index: int = 0, chapter_id=None, chapter_name: str = ""):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size"))
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.bookName = book_name
        self.current_chapter_id = chapter_id
        self.current_chapter_name = chapter_name
        self.is_english = False
        try:
            with open(os.path.join(os.getenv('appdata'), settings.app.appName, "ahadeeth", book_name), "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            if isinstance(self.raw_data, dict):
                self.chapters = self.raw_data.get("chapters", [])
                self.all_hadiths = self.raw_data.get("hadiths", [])
            elif isinstance(self.raw_data, list):
                self.chapters = []
                self.all_hadiths = [{"arabic": item, "english": {}, "chapterId": None, "idInBook": idx + 1} for idx, item in enumerate(self.raw_data)]
            else:
                self.chapters = []
                self.all_hadiths = []

            self.hadith_chapter_info = []
            if self.all_hadiths:
                chapters_map = {c.get("id"): c.get("arabic", "").strip() for c in self.chapters}
                counts = Counter(h.get("chapterId") for h in self.all_hadiths)
                chap_counters = {}
                for h in self.all_hadiths:
                    cid = h.get("chapterId")
                    chap_counters[cid] = chap_counters.get(cid, 0) + 1
                    pos = chap_counters[cid]
                    cname = chapters_map.get(cid, "")
                    tot = counts.get(cid, 0)
                    self.hadith_chapter_info.append({
                        "chapter_id": cid,
                        "chapter_name": cname,
                        "pos_in_chap": pos,
                        "total_in_chap": tot
                    })

            if self.current_chapter_id is not None:
                self.current_hadiths = [h for h in self.all_hadiths if h.get("chapterId") == self.current_chapter_id]
                if not self.current_chapter_name:
                    for c in self.chapters:
                        if c.get("id") == self.current_chapter_id:
                            self.current_chapter_name = c.get("arabic", "").strip()
                            break
            else:
                self.current_hadiths = self.all_hadiths

            self.index = min(max(0, index), max(0, len(self.current_hadiths) - 1)) if self.current_hadiths else 0
        except Exception:
            guiTools.MessageBox.error(self, "خطأ", "تعذر فتح الملف ")
            self.close()
            return

        try:
            self.display_book_name = functions.ahadeeth.getahadeethByIndex(book_name)
        except Exception:
            self.display_book_name = book_name

        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+shift+n", self).activated.connect(self.onDeleteNoteShortcut)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("alt+right", self).activated.connect(self.next_hadeeth)
        qt1.QShortcut("alt+left", self).activated.connect(self.previous_hadeeth)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.go_to_hadeeth)
        qt1.QShortcut("ctrl+shift+g", self).activated.connect(self.choose_bab)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.toggle_english_text)
        qt1.QShortcut("ctrl+b", self).activated.connect(self.onAddOrRemoveBookmark)
        qt1.QShortcut("ctrl+n", self).activated.connect(self.onAddOrRemoveNote)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onViewNote)
        qt1.QShortcut("ctrl+alt+c", self).activated.connect(self.copy_page_range)
        qt1.QShortcut("ctrl+alt+s", self).activated.connect(self.save_page_range_as_txt)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.save_page_range_as_docx)
        self.resize(1200, 600)
        self.text = guiTools.QReadOnlyTextEdit(viewer_name="hadeethViewer")
        self.text.setText(self.get_hadith_text(self.index))
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
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
        self.more_options_label = guiTools.QNavigableLabel("لمزيد من الخيارات، نستخدم زر التطبيقات أو click الأيمن")
        self.more_options_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.more_options_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.N_hadeeth = guiTools.QPushButton("الحديث التالي")
        self.N_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_hadeeth.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_hadeeth.clicked.connect(self.next_hadeeth)
        self.N_hadeeth.setAutoDefault(False)

        self.P_hadeeth = guiTools.QPushButton("الحديث السابق")
        self.P_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_hadeeth.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_hadeeth.clicked.connect(self.previous_hadeeth)
        self.P_hadeeth.setAutoDefault(False)

        self.go_to_bab_btn = guiTools.QPushButton("الذهاب إلى باب")
        self.go_to_bab_btn.setStyleSheet("background-color: #0000AA; color: white;")
        self.go_to_bab_btn.setAccessibleName("الذهاب إلى باب")
        self.go_to_bab_btn.setAccessibleDescription("control plus shift plus g")
        self.go_to_bab_btn.clicked.connect(self.choose_bab)
        self.go_to_bab_btn.setAutoDefault(False)

        self.toggle_lang_btn = guiTools.QPushButton("عرض النص الإنجليزي")
        self.toggle_lang_btn.setStyleSheet("background-color: #0000AA; color: white;")
        self.toggle_lang_btn.setAccessibleName("عرض النص الإنجليزي")
        self.toggle_lang_btn.setAccessibleDescription("control plus t")
        self.toggle_lang_btn.clicked.connect(self.toggle_english_text)
        self.toggle_lang_btn.setAutoDefault(False)

        self.show_book_name = guiTools.QNavigableLabel("")
        self.show_book_name.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_book_name.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.hadeeth_number_laybol = qt.QLabel("رقم الحديث")
        self.hadeeth_number_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.show_hadeeth_number = guiTools.QNavigableLabel("")
        self.show_hadeeth_number.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_hadeeth_number.setAccessibleDescription("رقم الحديث")
        self.show_hadeeth_number.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.update_labels()

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.more_options_label)
        layout.addWidget(self.show_book_name)
        layout.addWidget(self.hadeeth_number_laybol)
        layout.addWidget(self.show_hadeeth_number)

        layout1 = qt.QHBoxLayout()
        layout1.addWidget(self.P_hadeeth)
        layout1.addWidget(self.go_to_bab_btn)
        layout1.addWidget(self.toggle_lang_btn)
        layout1.addWidget(self.N_hadeeth)
        layout.addLayout(layout1)

        self.update_font_size()

    def update_labels(self):
        g_idx = self.get_current_global_index()
        if self.current_chapter_id is None and self.hadith_chapter_info:
            if 0 <= g_idx < len(self.hadith_chapter_info):
                info = self.hadith_chapter_info[g_idx]
                cname = info["chapter_name"]
                chap_title = cname if cname.startswith(("باب", "أبواب", "كتاب")) else (f"باب {cname}" if cname else "")
                if chap_title:
                    self.show_book_name.setText(f"{self.display_book_name}: {chap_title}")
                    self.show_hadeeth_number.setText(f"الحديث {info['pos_in_chap']} من {info['total_in_chap']} في {chap_title}، رقم الحديث في كامل الكتاب: {g_idx + 1} من {len(self.all_hadiths)}")
                else:
                    self.show_book_name.setText(self.display_book_name)
                    self.show_hadeeth_number.setText(f"{g_idx + 1} من {len(self.all_hadiths)}")
            else:
                self.show_book_name.setText(self.display_book_name)
                self.show_hadeeth_number.setText(f"{self.index + 1} من {len(self.current_hadiths)}")
        else:
            if self.current_chapter_name:
                self.show_book_name.setText(f"{self.display_book_name}: {self.current_chapter_name}")
            else:
                self.show_book_name.setText(self.display_book_name)
            self.show_hadeeth_number.setText(f"{self.index + 1} من {len(self.current_hadiths)}")

    def get_hadith_text(self, idx):
        if 0 <= idx < len(self.current_hadiths):
            item = self.current_hadiths[idx]
            if isinstance(item, dict):
                return item.get("arabic", "")
            return str(item)
        return ""

    def get_hadith_english(self, idx):
        if 0 <= idx < len(self.current_hadiths):
            item = self.current_hadiths[idx]
            if isinstance(item, dict):
                eng = item.get("english", {})
                if isinstance(eng, dict):
                    narrator = eng.get("narrator", "").strip()
                    text = eng.get("text", "").strip()
                    if narrator and text:
                        return f"{narrator}\n\n{text}"
                    return text or narrator
                elif isinstance(eng, str):
                    return eng
        return ""

    def get_current_global_index(self):
        if 0 <= self.index < len(self.current_hadiths):
            item = self.current_hadiths[self.index]
            if isinstance(item, dict) and "idInBook" in item:
                return item["idInBook"] - 1
        return self.index

    def choose_bab(self):
        if not self.chapters:
            guiTools.speak("لا توجد أبواب لهذا الكتاب")
            return
        dialog = SelectBabDialog(self, self.bookName, self.display_book_name, current_chapter_id=self.current_chapter_id)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            self.set_chapter(dialog.selected_chapter_id, dialog.selected_raw_chapter_name)

    def set_chapter(self, chapter_id, raw_chap_name):
        self.current_chapter_id = chapter_id
        if chapter_id is not None:
            self.current_chapter_name = raw_chap_name
            self.current_hadiths = [h for h in self.all_hadiths if h.get("chapterId") == chapter_id]
            guiTools.speak(f"{self.display_book_name}: {self.current_chapter_name}")
        else:
            self.current_chapter_name = ""
            self.current_hadiths = self.all_hadiths
            guiTools.speak("فتح الكتاب كاملا")
        self.index = 0
        self.is_english = False
        self.toggle_lang_btn.setText("عرض النص الإنجليزي")
        self.text.setText(self.get_hadith_text(self.index))
        self.update_font_size()
        self.update_labels()

    def toggle_english_text(self):
        if not self.is_english:
            self.is_english = True
            self.toggle_lang_btn.setText("العودة للنص الأصلي")
            eng_text = self.get_hadith_english(self.index)
            if not eng_text:
                eng_text = "لا يتوفر نص إنجليزي لهذا الحديث."
            self.text.setText(eng_text)
            self.update_font_size()
            guiTools.speak("تم عرض النص الإنجليزي")
        else:
            self.is_english = False
            self.toggle_lang_btn.setText("عرض النص الإنجليزي")
            self.text.setText(self.get_hadith_text(self.index))
            self.update_font_size()
            guiTools.speak("تمت العودة للنص الأصلي")

    def OnContextMenu(self):
        menu = guiTools.QCustomContextMenu("الخيارات", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        hadeeth_menu = guiTools.QCustomContextMenu("خيارات الحديث", self)
        hadeeth_menu.setFont(boldFont)
        next_action = hadeeth_menu.addAction("الحديث التالي")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.next_hadeeth)
        previous_action = hadeeth_menu.addAction("الحديث السابق")
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.previous_hadeeth)
        go_action = hadeeth_menu.addAction("الذهاب إلى حديث")
        go_action.setShortcut("ctrl+g")
        go_action.triggered.connect(self.go_to_hadeeth)
        go_bab_action = hadeeth_menu.addAction("الذهاب إلى باب")
        go_bab_action.setShortcut("ctrl+shift+g")
        go_bab_action.triggered.connect(self.choose_bab)
        menu.addMenu(hadeeth_menu)
        book_options_menu = guiTools.QCustomContextMenu("خيارات الكتاب", self)
        book_options_menu.setFont(boldFont)
        copy_range_action = book_options_menu.addAction("نسخ الأحاديث")
        copy_range_action.setShortcut("ctrl+alt+c")
        copy_range_action.triggered.connect(self.copy_page_range)
        save_txt_range_action = book_options_menu.addAction("حفظ الأحاديث كملف نصي")
        save_txt_range_action.setShortcut("ctrl+alt+s")
        save_txt_range_action.triggered.connect(self.save_page_range_as_txt)
        save_docx_range_action = book_options_menu.addAction("حفظ الأحاديث كملف Word")
        save_docx_range_action.setShortcut("ctrl+alt+d")
        save_docx_range_action.triggered.connect(self.save_page_range_as_docx)
        menu.addMenu(book_options_menu)
        text_options_menu = guiTools.QCustomContextMenu("خيارات النص", self)
        text_options_menu.setFont(boldFont)
        save_action = text_options_menu.addAction("حفظ كملف نصي")
        save_action.setShortcut("ctrl+s")
        save_action.triggered.connect(self.save_text_as_txt)
        print_action = text_options_menu.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all_action = text_options_menu.addAction("نسخ النص كاملاً")
        copy_all_action.setShortcut("ctrl+a")
        copy_all_action.triggered.connect(self.copy_text)
        copy_selected_action = text_options_menu.addAction("نسخ النص المحدد")
        copy_selected_action.setShortcut("ctrl+c")
        copy_selected_action.triggered.connect(self.copy_line)
        lang_text = "العودة للنص الأصلي" if self.is_english else "عرض النص الإنجليزي"
        toggle_lang_action = text_options_menu.addAction(lang_text)
        toggle_lang_action.setShortcut("ctrl+t")
        toggle_lang_action.triggered.connect(self.toggle_english_text)
        menu.addMenu(text_options_menu)
        hadeeth_position = {"bookName": self.bookName, "hadeethNumber": self.get_current_global_index()}
        note_exists = notesManager.getNotesForPosition("ahadeeth", hadeeth_position)
        if note_exists:
            note_action = qt1.QAction("عرض ملاحظة الحديث الحالي", self)
            note_action.setShortcut("ctrl+o")
            note_action.triggered.connect(lambda: self.onNoteAction(hadeeth_position))
            hadeeth_menu.addAction(note_action)
            delete_note_action = qt.QWidgetAction(self)
            delete_button = qt.QPushButton("حذف ملاحظة الحديث الحالي:   ctrl+shift+n")
            delete_button.setDefault(True)
            delete_button.setShortcut("ctrl+shift+n")
            delete_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_button.clicked.connect(lambda: self.onDeleteNote(hadeeth_position))
            delete_note_action.setDefaultWidget(delete_button)
            hadeeth_menu.addAction(delete_note_action)
        else:
            note_action = qt1.QAction("إضافة ملاحظة للحديث الحالي", self)
            note_action.setShortcut("ctrl+n")
            note_action.triggered.connect(lambda: self.onAddNote(hadeeth_position))
            hadeeth_menu.addAction(note_action)
        state, self.nameOfBookmark = functions.bookMarksManager.getAhdeethBookmarkName(self.bookName, self.get_current_global_index())
        if state:
            delete_bookmark_action = qt.QWidgetAction(self)
            delete_bookmark_button = qt.QPushButton("حذف العلامة المرجعية للحديث الحالي: ctrl+b")
            delete_bookmark_button.setDefault(True)
            delete_bookmark_button.setShortcut("ctrl+b")
            delete_bookmark_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_bookmark_button.clicked.connect(self.onRemoveBookmark)
            delete_bookmark_action.setDefaultWidget(delete_bookmark_button)
            hadeeth_menu.addAction(delete_bookmark_action)
        else:
            add_bookmark_action = qt1.QAction("إضافة علامة مرجعية للحديث الحالي", self)
            add_bookmark_action.setShortcut("ctrl+b")
            add_bookmark_action.triggered.connect(self.onAddBookMark)
            hadeeth_menu.addAction(add_bookmark_action)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def get_page_range(self):
        total = len(self.current_hadiths)
        if total == 0:
            return None, None
        start_page, ok1 = guiTools.QInputDialog.getInt(self, "بداية النطاق", "أدخل رقم حديث البداية:", value=self.index + 1, min=1, max=total)
        if not ok1:
            return None, None
        end_page, ok2 = guiTools.QInputDialog.getInt(self, "نهاية النطاق", f"أدخل رقم حديث النهاية (1-{total}):", value=total, min=1, max=total)
        if not ok2:
            return None, None
        if start_page > end_page:
            guiTools.MessageBox.error(self, "خطأ", "حديث البداية لا يمكن أن يكون أكبر من حديث النهاية")
            return None, None
        return start_page, end_page

    def copy_page_range(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        content = ""
        for i in range(start-1, end):
            content += self.get_hadith_text(i) + "\n\n"
        try:
            pyperclip.copy(content)
            winsound.Beep(1000, 100)
            guiTools.MessageBox.view(self, "تم النسخ", f"تم نسخ المحتوى من الحديث {start} إلى الحديث {end}")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في النسخ", str(e))

    def save_page_range_as_txt(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    for i in range(start-1, end):
                        file.write(self.get_hadith_text(i) + "\n\n")
                guiTools.speak(f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف نصي")
                guiTools.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف نصي")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في الحفظ", str(e))

    def save_page_range_as_docx(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Word Documents (*.docx);;All Files (*)")
            file_dialog.setDefaultSuffix("docx")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                doc = Document()
                for i in range(start-1, end):
                    p = doc.add_paragraph(self.get_hadith_text(i))
                    if i < end-1:
                        doc.add_page_break()
                doc.save(file_name)
                guiTools.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الحديث {start} إلى الحديث {end} في ملف Word")
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ في الحفظ", str(e))

    def onAddNote(self, position_data):
        dialog = note_dialog.NoteDialog(self, mode="add")
        dialog.saved.connect(lambda old, new, content: self.saveNote(position_data, new, content))
        dialog.exec()

    def onEditNote(self, position_data, note_name):
        note = notesManager.getNoteByName("ahadeeth", note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.updateNote(position_data, old, new, content))
            dialog.exec()

    def saveNote(self, position_data, name, content):
        existing_note = notesManager.getNoteByName("ahadeeth", name)
        if existing_note is not None:
            guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
            return
        notesManager.addNewNote("ahadeeth", {"name": name, "content": content, "position_data": position_data})
        guiTools.speak("تمت إضافة الملاحظة")

    def updateNote(self, position_data, old_name, new_name, new_content):
        if old_name != new_name:
            existing_note = notesManager.getNoteByName("ahadeeth", new_name)
            if existing_note is not None:
                guiTools.MessageBox.error(self, "خطأ", "اسم الملاحظة موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
        update_data = {"name": new_name, "content": new_content, "position_data": position_data}
        success = notesManager.updateNote("ahadeeth", old_name, update_data)
        if success:
            guiTools.speak("تم تحديث الملاحظة بنجاح")
        else:
            guiTools.MessageBox.error(self, "خطأ", "فشل في تحديث الملاحظة")

    def onAddOrRemoveNote(self):
        position_data = {"bookName": self.bookName, "hadeethNumber": self.get_current_global_index()}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onEditNote(position_data, note_exists["name"])
        else:
            self.onAddNote(position_data)

    def onViewNote(self):
        position_data = {"bookName": self.bookName, "hadeethNumber": self.get_current_global_index()}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onNoteAction(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لهذا الحديث")

    def onNoteAction(self, position_data):
        note = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(lambda note_name: self.onEditNote(position_data, note_name))
            dialog.exec()

    def onDeleteNote(self, position_data):
        note = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف الملاحظة '{note['name']}'؟", "نعم", "لا")
            if confirm == 0:
                notesManager.removeNote("ahadeeth", note["name"])
                guiTools.speak("تم حذف الملاحظة")

    def next_hadeeth(self):
        if not self.current_hadiths:
            return
        old_g_idx = self.get_current_global_index()
        if self.index == len(self.current_hadiths) - 1:
            self.index = 0
        else:
            self.index += 1
        new_g_idx = self.get_current_global_index()
        self.is_english = False
        self.toggle_lang_btn.setText("عرض النص الإنجليزي")
        self.text.setText(self.get_hadith_text(self.index))
        self.update_font_size()
        self.update_labels()
        if settings.settings_handler.get("page_turn_sound", "hadeethViewer") != "False":
            winsound.PlaySound("data/sounds/next_page.wav", 1)
        chapter_changed = False
        new_chap_name = ""
        if self.current_chapter_id is None and self.hadith_chapter_info:
            if 0 <= old_g_idx < len(self.hadith_chapter_info) and 0 <= new_g_idx < len(self.hadith_chapter_info):
                if self.hadith_chapter_info[old_g_idx]["chapter_id"] != self.hadith_chapter_info[new_g_idx]["chapter_id"]:
                    chapter_changed = True
                    new_chap_name = self.hadith_chapter_info[new_g_idx]["chapter_name"]
        if chapter_changed and new_chap_name:
            guiTools.speak(f"تم الانتقال إلى {new_chap_name}")
        else:
            guiTools.speak(str(self.index + 1))

    def previous_hadeeth(self):
        if not self.current_hadiths:
            return
        old_g_idx = self.get_current_global_index()
        if self.index == 0:
            self.index = len(self.current_hadiths) - 1
        else:
            self.index -= 1
        new_g_idx = self.get_current_global_index()
        self.is_english = False
        self.toggle_lang_btn.setText("عرض النص الإنجليزي")
        self.text.setText(self.get_hadith_text(self.index))
        self.update_font_size()
        self.update_labels()
        if settings.settings_handler.get("page_turn_sound", "hadeethViewer") != "False":
            winsound.PlaySound("data/sounds/previous_page.wav", 1)
        chapter_changed = False
        new_chap_name = ""
        if self.current_chapter_id is None and self.hadith_chapter_info:
            if 0 <= old_g_idx < len(self.hadith_chapter_info) and 0 <= new_g_idx < len(self.hadith_chapter_info):
                if self.hadith_chapter_info[old_g_idx]["chapter_id"] != self.hadith_chapter_info[new_g_idx]["chapter_id"]:
                    chapter_changed = True
                    new_chap_name = self.hadith_chapter_info[new_g_idx]["chapter_name"]
        if chapter_changed and new_chap_name:
            guiTools.speak(f"تم الانتقال إلى {new_chap_name}")
        else:
            guiTools.speak(str(self.index + 1))

    def go_to_hadeeth(self):
        if not self.current_hadiths:
            return
        old_g_idx = self.get_current_global_index()
        hadeeth, OK = guiTools.QInputDialog.getInt(self, "الذهاب إلى حديث", "أكتب رقم الحديث", self.index + 1, 1, len(self.current_hadiths))
        if OK:
            self.index = hadeeth - 1
            new_g_idx = self.get_current_global_index()
            self.is_english = False
            self.toggle_lang_btn.setText("عرض النص الإنجليزي")
            self.text.setText(self.get_hadith_text(self.index))
            self.update_font_size()
            self.update_labels()
            if self.current_chapter_id is None and self.hadith_chapter_info:
                if 0 <= old_g_idx < len(self.hadith_chapter_info) and 0 <= new_g_idx < len(self.hadith_chapter_info):
                    if self.hadith_chapter_info[old_g_idx]["chapter_id"] != self.hadith_chapter_info[new_g_idx]["chapter_id"]:
                        guiTools.speak(f"تم الانتقال إلى {self.hadith_chapter_info[new_g_idx]['chapter_name']}")

    def print_text(self):
        functions.text_actions.print_text_content(self, self.text)

    def save_text_as_txt(self):
        functions.text_actions.save_text_file(self, self.text)

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))

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

    def copy_line(self):
        functions.text_actions.copy_current_selection(self, self.text)

    def copy_text(self):
        functions.text_actions.copy_all_text(self, self.text)

    def onAddBookMark(self):
        name, OK = guiTools.QInputDialog.getText(self, "إضافة علامة مرجعية", "أكتب أسم للعلامة المرجعية")
        if OK:
            bookmarks = functions.bookMarksManager.getAhadeethBookmarks()
            if any(bookmark['name'] == name for bookmark in bookmarks):
                guiTools.MessageBox.error(self, "خطأ", "اسم العلامة المرجعية موجود بالفعل، الرجاء اختيار اسم آخر.")
                return
            functions.bookMarksManager.addNewHadeethBookMark(self.bookName, self.get_current_global_index(), name)
            guiTools.speak("تمت إضافة العلامة المرجعية")

    def onRemoveBookmark(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف العلامة المرجعية '{self.nameOfBookmark}'؟", "نعم", "لا")
            if confirm == 0:
                functions.bookMarksManager.removeAhadeethBookMark(self.nameOfBookmark)
                guiTools.speak("تم حذف العلامة المرجعية")
        except Exception:
            guiTools.MessageBox.error(self, "خطأ", "تعذر حذف العلامة المرجعية")

    def onAddOrRemoveBookmark(self):
        state, self.nameOfBookmark = functions.bookMarksManager.getAhdeethBookmarkName(self.bookName, self.get_current_global_index())
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()

    def onDeleteNoteShortcut(self):
        position_data = {"bookName": self.bookName, "hadeethNumber": self.get_current_global_index()}
        note_exists = notesManager.getNotesForPosition("ahadeeth", position_data)
        if note_exists:
            self.onDeleteNote(position_data)
        else:
            guiTools.speak("لا توجد ملاحظة لحذفها")
