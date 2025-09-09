import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import app
import functions.notesManager as notesManager
import guiTools.note_dialog as note_dialog
import functions.quranJsonControl as quranJsonControl
from gui import quranViewer, hadeeth_viewer, storyViewer
from gui.islamicBooks import book_viewer
import json,os,guiTools,re
from guiTools import QPushButton
class NotesDialog(qt.QDialog):
    def __init__(self, p):
        super().__init__(p)
        self.setWindowTitle("الملاحظات")
        qt1.QShortcut(qt1.QKeySequence("Delete"), self).activated.connect(self.handle_delete)
        qt1.QShortcut(qt1.QKeySequence("Ctrl+G"), self).activated.connect(self.handle_goto)
        qt1.QShortcut(qt1.QKeySequence("Ctrl+E"), self).activated.connect(self.handle_edit)
        qt1.QShortcut(qt1.QKeySequence("Ctrl+O"), self).activated.connect(self.handle_view)
        self.resize(800,450)
        layout = qt.QVBoxLayout(self)                
        self.tabWidget = qt.QTabWidget()
        self.tabWidget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background: #2b2b2b;
                color: white;
                padding: 10px 20px;
                border: 1px solid #444;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin: 2px;
                min-width: 100px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: white;
                border: 1px solid #0078d7;
            }
            QTabBar::tab:hover {
                background: #3a3a3a;
            }
        """)                
        self.tabs = []
        self.notes_lists = []        
        categories = ["القرآن الكريم", "الأحاديث", "الكتب الإسلامية", "القصص الإسلامية"]
        for i, category in enumerate(categories):
            tab = qt.QWidget()
            tab_layout = qt.QVBoxLayout(tab)            
            search_label = qt.QLabel("البحث عن ملاحظة")
            search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar = qt.QLineEdit()
            search_bar.setAccessibleName("البحث عن ملاحظة")
            search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar.textChanged.connect(lambda text, idx=i: self.on_search_tab(text, idx))            
            notes_list = qt.QListWidget()
            font = qt1.QFont()
            font.setBold(True)
            notes_list.setFont(font)            
            tab_layout.addWidget(search_label)
            tab_layout.addWidget(search_bar)
            tab_layout.addWidget(notes_list)            
            self.tabWidget.addTab(tab, category)
            self.tabs.append(tab)
            self.notes_lists.append(notes_list)                    
            notes_list.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
            notes_list.customContextMenuRequested.connect(
                lambda pos, idx=i: self.show_context_menu(pos, idx))
            notes_list.itemActivated.connect(
                lambda item, idx=i: self.on_item_activated(item, idx))        
        layout.addWidget(self.tabWidget)        
        buttons_layout = qt.QHBoxLayout()
        self.dl_all_current = QPushButton("حذف كل الملاحظات من الفئة الحالية")        
        self.dl_all_current.setAutoDefault(False)
        self.dl_all_current.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
        """)
        self.dl_all_current.clicked.connect(self.onRemoveAllCurrentCategory)
        self.dl_all_current.setShortcut("Ctrl+Delete")
        self.dl_all_current.setAccessibleDescription("control plus delete")        
        buttons_layout.addWidget(self.dl_all_current)                
        self.dl_all_all = QPushButton("حذف كل الملاحظات من كل الفئات")
        self.dl_all_all.setAutoDefault(False)
        self.dl_all_all.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
        """)
        self.dl_all_all.clicked.connect(self.onRemoveAllCategories)
        self.dl_all_all.setShortcut("Ctrl+Shift+Delete")
        self.dl_all_all.setAccessibleDescription("control plus shift plus delete")        
        buttons_layout.addWidget(self.dl_all_all)        
        layout.addLayout(buttons_layout)                
        self.tabWidget.currentChanged.connect(self.load_notes)                
        self.all_notes_in_current_category = [[] for _ in range(4)]
        self.load_notes(0)            
    def load_notes(self, index):
        category_map = {
            0: "quran",
            1: "ahadeeth",
            2: "islamicBooks",
            3: "stories"
        }
        category_type = category_map.get(index, "quran")
        notes_list = self.notes_lists[index]
        notes_list.clear()
        notes = notesManager.openNotesFile().get(category_type, [])
        self.all_notes_in_current_category[index] = [note["name"] for note in notes]
        notes_list.addItems(self.all_notes_in_current_category[index])    
    def show_context_menu(self, pos, tab_index):
        font = qt1.QFont()
        font.setBold(True)
        notes_list = self.notes_lists[tab_index]
        item = notes_list.itemAt(pos)
        if not item:
            return    
        note_name = item.text()
        menu = qt.QMenu(self)
        menu.setFont(font)
        view_action = qt1.QAction("عرض الملاحظة", self)
        view_action.triggered.connect(lambda: self.view_note(item, tab_index))
        view_action.setShortcut("ctrl+o")
        menu.addAction(view_action)                
        edit_action = qt1.QAction("تعديل الملاحظة", self)
        edit_action.triggered.connect(lambda: self.edit_note(note_name, tab_index))
        edit_action.setShortcut("ctrl+e")
        menu.addAction(edit_action)                
        goto_action = qt1.QAction("الانتقال إلى موضع الملاحظة", self)
        goto_action.triggered.connect(lambda: self.goto_note_position(note_name, tab_index))
        goto_action.setShortcut("ctrl+g")
        menu.addAction(goto_action)                
        delete_action = qt1.QAction("حذف الملاحظة", self)
        delete_action.triggered.connect(lambda: self.onRemove(note_name, tab_index))
        delete_action.setShortcut("delete")
        menu.addAction(delete_action)
        menu.exec(notes_list.mapToGlobal(pos))        
    def view_note(self, item, tab_index):
        try:
            note_name = item.text()
            category_map = {
                0: "quran",
                1: "ahadeeth",
                2: "islamicBooks",
                3: "stories"
            }
            category_type = category_map.get(tab_index, "quran")
            note = notesManager.getNoteByName(category_type, note_name)
            if note:
                dialog = note_dialog.NoteDialog(
                    self,
                    title=note["name"],
                    content=note["content"],
                    mode="view",
                    old_name=note["name"]
                )
                dialog.edit_requested.connect(self.re_open_for_editing)
                dialog.exec()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على الملاحظة '{note_name}'.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء عرض الملاحظة: {e}")        
    def re_open_for_editing(self, note_name):
        current_index = self.tabWidget.currentIndex()
        self.edit_note(note_name, current_index)        
    def edit_note(self, note_name, tab_index):
        try:
            category_map = {
                0: "quran",
                1: "ahadeeth",
                2: "islamicBooks",
                3: "stories"
            }
            category_type = category_map.get(tab_index, "quran")
            note = notesManager.getNoteByName(category_type, note_name)
            if note:
                dialog = note_dialog.NoteDialog(
                    self,
                    title=note["name"],
                    content=note["content"],
                    mode="edit",
                    old_name=note["name"]
                )
                dialog.saved.connect(lambda old_name, new_name, new_content: self.update_note(category_type, old_name, new_name, new_content, tab_index))
                dialog.exec()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على الملاحظة '{note_name}' للتعديل.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء تعديل الملاحظة: {e}")        
    def update_note(self, category_type, old_name, new_name, new_content, tab_index):
        try:            
            if old_name != new_name and notesManager.getNoteByName(category_type, new_name):
                guiTools.qMessageBox.MessageBox.error(
                    self,
                    "خطأ",
                    f"الملاحظة بعنوان '{new_name}' موجودة بالفعل. الرجاء اختيار عنوان مختلف."
                )
                return            
            note_to_update = notesManager.getNoteByName(category_type, old_name)
            if not note_to_update:
                guiTools.qMessageBox.MessageBox.error(
                    self,
                    "خطأ",
                    f"لم يتم العثور على الملاحظة '{old_name}' للتحديث."
                )
                return
            update_data = {
                "name": new_name,
                "content": new_content
            }            
            if "position_data" in note_to_update:
                update_data["position_data"] = note_to_update["position_data"]
            success = notesManager.updateNote(category_type, old_name, update_data)
            if success:
                self.load_notes(tab_index)
                guiTools.speak(f"تم تحديث الملاحظة '{new_name}' بنجاح.")
            else:                                
                guiTools.qMessageBox.MessageBox.error(
                    self,
                    "خطأ",
                    "فشل في تحديث الملاحظة. قد تكون الملاحظة غير موجودة."
                )
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(
                self,
                "خطأ",
                f"حدث خطأ أثناء تحديث الملاحظة: {str(e)}"
            )        
    def goto_note_position(self, note_name, tab_index):
        try:
            category_map = {
                0: "quran",
                1: "ahadeeth",
                2: "islamicBooks",
                3: "stories"
            }
            category_type = category_map.get(tab_index, "quran")
            note = notesManager.getNoteByName(category_type, note_name)
            if note and "position_data" in note:
                position_data = note["position_data"]
                if tab_index == 0:
                    self.open_quran_note(position_data)
                elif tab_index == 1:
                    self.open_hadeeth_note(position_data)
                elif tab_index == 2:
                    self.open_book_note(position_data)
                elif tab_index == 3:
                    self.open_story_note(position_data)
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على الملاحظة '{note_name}' للانتقال إلى موضعها.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء الانتقال إلى موضع الملاحظة: {e}")        
    def open_quran_note(self, position_data):
        try:            
            if not all(key in position_data for key in ["surah", "ayah_number"]):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات موضع السورة أو الآية غير مكتملة.")
                return                
            surah_name = position_data["surah"]
            ayah_number = position_data["ayah_number"]
            surahs = quranJsonControl.getSurahs()            
            if surah_name in surahs:
                surah_content = surahs[surah_name][1]                
                quranViewer.QuranViewer(
                    self,
                    surah_content,
                    type=0,
                    category=surah_name,
                    index=ayah_number
                ).exec()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على سورة '{surah_name}'.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح ملاحظة القرآن: {e}")    
    def open_hadeeth_note(self, position_data):
        try:            
            if not all(key in position_data for key in ["bookName", "hadeethNumber"]):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات موضع كتاب الحديث أو رقم الحديث غير مكتملة.")
                return
            book_name = position_data["bookName"]
            hadeeth_number = position_data["hadeethNumber"]
            hadeeth_viewer(
                self,
                book_name,
                index=hadeeth_number
            ).exec()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح ملاحظة الحديث: {e}")        
    def open_book_note(self, position_data):
        try:            
            if not all(key in position_data for key in ["bookName", "partName", "pageNumber"]):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات موضع الكتاب أو الجزء أو رقم الصفحة غير مكتملة.")
                return
            book_name = position_data["bookName"]
            part_name = position_data["partName"]
            page_number = position_data["pageNumber"]
            book_path = os.path.join(os.getenv('appdata'), app.appName, "islamicBooks", book_name)
            if os.path.exists(book_path):
                with open(book_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if part_name in data:
                    part_content = data[part_name]
                    book_viewer(
                        self,
                        book_name,
                        part_name,
                        part_content,
                        index=page_number
                    ).exec()
                else:
                    guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على جزء '{part_name}' في الكتاب '{book_name}'.")
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على الكتاب '{book_name}' في المسار المحدد.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح ملاحظة الكتاب: {e}")        
    def open_story_note(self, position_data):
        try:            
            if not all(key in position_data for key in ["type", "category", "line"]):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات موضع القصة أو الفئة أو رقم السطر غير مكتملة.")
                return
            story_type = position_data["type"]
            category = position_data["category"]
            line_number = position_data["line"]
            stories = {}
            if story_type == 0:
                with open("data/json/prophetStories.json", "r", encoding="utf-8-sig") as f:
                    stories = json.load(f)
            elif story_type == 1:
                with open("data/json/quranStories.json", "r", encoding="utf-8-sig") as f:
                    stories = json.load(f)
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"نوع القصة غير صالح: {story_type}.")
                return
            if category in stories:
                story_content = stories[category]
                storyViewer.StoryViewer(
                    self,
                    story_content,
                    story_type,
                    category,
                    stories,
                    index=line_number
                ).exec()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لم يتم العثور على فئة القصة '{category}'.")
        except FileNotFoundError:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "ملف القصص غير موجود.")
        except json.JSONDecodeError:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "خطأ في قراءة ملف القصص (تنسيق JSON غير صالح).")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح ملاحظة القصة: {e}")        
    def onRemove(self, note_name=None, tab_index=None):
        try:
            if tab_index is None:
                tab_index = self.tabWidget.currentIndex()                
            notes_list = self.notes_lists[tab_index]
            if not note_name:
                item = notes_list.currentItem()
                if not item:
                    guiTools.qMessageBox.MessageBox.error(self, "تحذير", "الرجاء تحديد ملاحظة لحذفها.")
                    return
                note_name = item.text()
            category_map = {
                0: "quran",
                1: "ahadeeth",
                2: "islamicBooks",
                3: "stories"
            }
            category_type = category_map.get(tab_index, "quran")
            confirm = guiTools.QQuestionMessageBox.view(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد أنك تريد حذف الملاحظة '{note_name}'؟",
                "نعم",
                "لا"
            )
            if confirm == 0:
                notesManager.removeNote(category_type, note_name)
                self.load_notes(tab_index)
                guiTools.speak("تم حذف الملاحظة")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف الملاحظة: {e}")        
    def onRemoveAllCurrentCategory(self):
        try:
            tab_index = self.tabWidget.currentIndex()
            category_map = {
                0: "quran",
                1: "ahadeeth",
                2: "islamicBooks",
                3: "stories"
            }
            category_type = category_map.get(tab_index, "quran")
            current_category_name = self.tabWidget.tabText(tab_index)
            confirm = guiTools.QQuestionMessageBox.view(
                self,
                "تأكيد الحذف الكلي",
                f"هل أنت متأكد أنك تريد حذف جميع الملاحظات من فئة '{current_category_name}'؟ هذا الإجراء لا يمكن التراجع عنه.",
                "نعم",
                "لا"
            )
            if confirm == 0:
                notesManager.removeAllNotesForCategory(category_type)
                self.load_notes(tab_index)
                guiTools.speak(f"تم حذف جميع الملاحظات من فئة '{current_category_name}'.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع الملاحظات من الفئة الحالية: {e}")        
    def onRemoveAllCategories(self):
        try:
            confirm = guiTools.QQuestionMessageBox.view(
                self,
                "تأكيد الحذف الكلي",
                "هل أنت متأكد أنك تريد حذف جميع الملاحظات من كل الفئات؟ هذا الإجراء لا يمكن التراجع عنه.",
                "نعم",
                "لا"
            )
            if confirm == 0:
                notesManager.removeAllNotes()
                for i in range(4):
                    self.load_notes(i)
                guiTools.speak("تم حذف جميع الملاحظات من كل الفئات.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء حذف جميع الملاحظات من كل الفئات: {e}")        
    def search_notes(self, pattern, note_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            note for note in note_list
            if normalized_pattern.lower() in tashkeel_pattern.sub('', note).lower()
        ]
        return matches        
    def on_search_tab(self, text, tab_index):
        notes_list = self.notes_lists[tab_index]
        notes_list.clear()
        if text:
            result = self.search_notes(text, self.all_notes_in_current_category[tab_index])
            notes_list.addItems(result)
        else:
            notes_list.addItems(self.all_notes_in_current_category[tab_index])        
    def handle_delete(self):
        tab_index = self.tabWidget.currentIndex()
        notes_list = self.notes_lists[tab_index]
        item = notes_list.currentItem()
        if item:
            self.onRemove(item.text(), tab_index)        
    def handle_goto(self):
        tab_index = self.tabWidget.currentIndex()
        notes_list = self.notes_lists[tab_index]
        item = notes_list.currentItem()
        if item:
            self.goto_note_position(item.text(), tab_index)        
    def handle_edit(self):
        tab_index = self.tabWidget.currentIndex()
        notes_list = self.notes_lists[tab_index]
        item = notes_list.currentItem()
        if item:
            self.edit_note(item.text(), tab_index)        
    def handle_view(self):
        tab_index = self.tabWidget.currentIndex()
        notes_list = self.notes_lists[tab_index]
        item = notes_list.currentItem()
        if item:
            self.view_note(item, tab_index)        
    def on_item_activated(self, item, tab_index):        
        notes_list = self.notes_lists[tab_index]
        rect = notes_list.visualItemRect(item)
        pos = rect.center()        
        self.show_context_menu(pos, tab_index)