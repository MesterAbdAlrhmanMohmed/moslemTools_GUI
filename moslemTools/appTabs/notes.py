import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import app
import functions.notesManager as notesManager
import guiTools.note_dialog as note_dialog
import functions.quranJsonControl as quranJsonControl
from gui import quranViewer, hadeeth_viewer, storyViewer
from gui.islamicBooks import book_viewer
from gui.islamicTopicViewer import IslamicTopicViewer
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
        categories = ["القرآن الكريم", "الأحاديث", "الكتب الإسلامية", "القصص الإسلامية", "المواضيع الإسلامية المنوعة"]
        for i, category in enumerate(categories):
            tab = qt.QWidget()
            tab_layout = qt.QVBoxLayout(tab)            
            search_label = qt.QLabel("البحث عن ملاحظة")
            search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar = qt.QLineEdit()
            search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
            search_bar.textChanged.connect(lambda text, idx=i: self.on_search_tab(text, idx))            
            notes_list = qt.QListWidget()
            notes_list.setSpacing(1)
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
            notes_list.customContextMenuRequested.connect(lambda pos, idx=i: self.show_context_menu(pos, idx))
            notes_list.itemActivated.connect(lambda item, idx=i: self.on_item_activated(item, idx))        
        layout.addWidget(self.tabWidget)                
        buttons_layout = qt.QHBoxLayout()
        self.dl_all_current = QPushButton("حذف كل الملاحظات من الفئة الحالية")        
        self.dl_all_current.setAutoDefault(False)
        self.dl_all_current.setStyleSheet("background-color: #8B0000; color: white;")
        self.dl_all_current.clicked.connect(self.onRemoveAllCurrentCategory)
        self.dl_all_current.setShortcut("Ctrl+Delete")
        self.dl_all_current.setAccessibleDescription("control plus delete")
        buttons_layout.addWidget(self.dl_all_current)        
        self.dl_all_all = QPushButton("حذف كل الملاحظات من كل الفئات")
        self.dl_all_all.setAutoDefault(False)
        self.dl_all_all.setStyleSheet("background-color: #8B0000; color: white;")
        self.dl_all_all.clicked.connect(self.onRemoveAllCategories)
        self.dl_all_all.setShortcut("Ctrl+Shift+Delete")
        self.dl_all_all.setAccessibleDescription("control plus shift plus delete")
        buttons_layout.addWidget(self.dl_all_all)        
        layout.addLayout(buttons_layout)        
        self.tabWidget.currentChanged.connect(self.load_notes)
        self.all_notes_in_current_category = [[] for _ in range(5)]
        self.load_notes(0)
    def on_item_activated(self, item, tab_index):
        notes_list = self.notes_lists[tab_index]
        rect = notes_list.visualItemRect(item)
        pos = rect.center()
        self.show_context_menu(pos, tab_index)
    def get_category_type(self, index):
        category_map = {0: "quran", 1: "ahadeeth", 2: "islamicBooks", 3: "stories", 4: "islamicTopics"}
        return category_map.get(index)
    def load_notes(self, index):
        category_type = self.get_category_type(index)
        if not category_type: return
        notes_list = self.notes_lists[index]
        notes_list.clear()
        notes = notesManager.openNotesFile().get(category_type, [])
        self.all_notes_in_current_category[index] = [note["name"] for note in notes]
        notes_list.addItems(self.all_notes_in_current_category[index])    
    def show_context_menu(self, pos, tab_index):
        notes_list = self.notes_lists[tab_index]
        item = notes_list.itemAt(pos)
        if not item: return    
        menu = qt.QMenu(self)            
        view_action = menu.addAction("عرض الملاحظة")
        view_action.setShortcut("Ctrl+O")
        view_action.triggered.connect(lambda: self.view_note(item.text(), tab_index))
        edit_action = menu.addAction("تعديل الملاحظة")
        edit_action.setShortcut("Ctrl+E")
        edit_action.triggered.connect(lambda: self.edit_note(item.text(), tab_index))
        goto_action = menu.addAction("الانتقال إلى موضع الملاحظة")
        goto_action.setShortcut("Ctrl+G")
        goto_action.triggered.connect(lambda: self.goto_note_position(item.text(), tab_index))
        delete_action = menu.addAction("حذف الملاحظة")
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(lambda: self.onRemove(item.text(), tab_index))                
        menu.exec(notes_list.mapToGlobal(pos))
    def view_note(self, note_name, tab_index):
        category_type = self.get_category_type(tab_index)
        note = notesManager.getNoteByName(category_type, note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="view", old_name=note["name"])
            dialog.edit_requested.connect(self.re_open_for_editing)
            dialog.exec()        
    def re_open_for_editing(self, note_name):
        self.edit_note(note_name, self.tabWidget.currentIndex())        
    def edit_note(self, note_name, tab_index):
        category_type = self.get_category_type(tab_index)
        note = notesManager.getNoteByName(category_type, note_name)
        if note:
            dialog = note_dialog.NoteDialog(self, title=note["name"], content=note["content"], mode="edit", old_name=note["name"])
            dialog.saved.connect(lambda old, new, content: self.update_note(category_type, old, new, content, tab_index))
            dialog.exec()        
    def update_note(self, category_type, old_name, new_name, new_content, tab_index):
        if old_name != new_name and notesManager.getNoteByName(category_type, new_name):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"الملاحظة '{new_name}' موجودة بالفعل.")
            return        
        note_to_update = notesManager.getNoteByName(category_type, old_name)
        if not note_to_update: return        
        update_data = {"name": new_name, "content": new_content}
        if "position_data" in note_to_update:
            update_data["position_data"] = note_to_update["position_data"]            
        if notesManager.updateNote(category_type, old_name, update_data):
            self.load_notes(tab_index)
            guiTools.speak("تم تحديث الملاحظة")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشل تحديث الملاحظة.")            
    def goto_note_position(self, note_name, tab_index):
        category_type = self.get_category_type(tab_index)
        note = notesManager.getNoteByName(category_type, note_name)
        if note and "position_data" in note:
            pd = note["position_data"]
            if tab_index == 0: self.open_quran_note(pd)
            elif tab_index == 1: self.open_hadeeth_note(pd)
            elif tab_index == 2: self.open_book_note(pd)
            elif tab_index == 3: self.open_story_note(pd)
            elif tab_index == 4: self.open_islamic_topic_note(pd)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات الموضع غير موجودة لهذه الملاحظة.")
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
    def open_islamic_topic_note(self, position_data):
        try:
            if not all(k in position_data for k in ["file", "title"]):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "بيانات الموضع غير مكتملة.")
                return            
            file_path = position_data["file"]
            title = position_data["title"]
            line = position_data.get("line", 0)            
            full_path = file_path 
            if not os.path.exists(full_path):
                 base_dir = os.path.join("data", "json", "IslamicTopics")
                 for root, _, files in os.walk(base_dir):
                     if os.path.basename(file_path) in files:
                         full_path = os.path.join(root, os.path.basename(file_path))
                         break
            if not os.path.exists(full_path):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"الملف '{file_path}' غير موجود.")
                return
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_topics = {item.get("number", str(i)): item.get("label", "") for i, item in enumerate(data)}
            content = all_topics.get(title)
            if content:
                IslamicTopicViewer(self, file_path, title, content, all_topics, index=line).exec()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"الموضوع '{title}' غير موجود في الملف.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء فتح الملاحظة: {e}")
    def onRemove(self, note_name=None, tab_index=None):
        if tab_index is None: tab_index = self.tabWidget.currentIndex()
        if not note_name:
            item = self.notes_lists[tab_index].currentItem()
            if not item: return
            note_name = item.text()        
        category_type = self.get_category_type(tab_index)
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف '{note_name}'؟", "نعم", "لا")
        if confirm == 0:
            notesManager.removeNote(category_type, note_name)
            self.load_notes(tab_index)
            guiTools.speak("تم حذف الملاحظة")
    def onRemoveAllCurrentCategory(self):
        tab_index = self.tabWidget.currentIndex()
        category_type = self.get_category_type(tab_index)
        category_name = self.tabWidget.tabText(tab_index)
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف كل ملاحظات '{category_name}'؟", "نعم", "لا")
        if confirm == 0:
            notesManager.removeAllNotesForCategory(category_type)
            self.load_notes(tab_index)
            guiTools.speak(f"تم حذف جميع ملاحظات '{category_name}'")
    def onRemoveAllCategories(self):
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل تريد حذف كل الملاحظات؟", "نعم", "لا")
        if confirm == 0:
            notesManager.removeAllNotes()
            for i in range(5): self.load_notes(i)
            guiTools.speak("تم حذف جميع الملاحظات")

    def search_notes(self, pattern, note_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern).lower()
        return [note for note in note_list if normalized_pattern in tashkeel_pattern.sub('', note).lower()]
    def on_search_tab(self, text, tab_index):
        notes_list = self.notes_lists[tab_index]
        notes_list.clear()
        if text:
            result = self.search_notes(text, self.all_notes_in_current_category[tab_index])
            notes_list.addItems(result)
        else:
            notes_list.addItems(self.all_notes_in_current_category[tab_index])
    def handle_delete(self):
        self.onRemove()
    def handle_goto(self):
        item = self.notes_lists[self.tabWidget.currentIndex()].currentItem()
        if item: self.goto_note_position(item.text(), self.tabWidget.currentIndex())
    def handle_edit(self):
        item = self.notes_lists[self.tabWidget.currentIndex()].currentItem()
        if item: self.edit_note(item.text(), self.tabWidget.currentIndex())
    def handle_view(self):
        item = self.notes_lists[self.tabWidget.currentIndex()].currentItem()
        if item: self.view_note(item.text(), self.tabWidget.currentIndex())