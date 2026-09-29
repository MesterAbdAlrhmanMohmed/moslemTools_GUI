import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler
import guiTools
import ujson as json


class TabsOrderSettings(qt.QWidget):
    ALL_TABS = [
        "مواقيت الصلاة والتاريخ",
        "القرآن الكريم مكتوب",
        "القرآن الكريم صوتي",
        "متابع الختمة القرآنية",
        "الأحاديث النبوية والقدسية",
        "الباحث في القرآن والأحاديث",
        "اسأل الذكاء الاصطناعي",
        "لعبة الأسئلة الإسلامية",
        "الكتب الإسلامية",
        "المتون الإسلامية المكتوبة",
        "إذاعات الراديو الإسلامية",
        "الأذكار والأدعية",
        "السبحة الإلكترونية",
        "أسماء الله الحُسْنى",
        "القصص الإسلامية",
        "مواضيع إسلامية مختلفة",
        "محول التاريخ"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        self.initial_tabs_order = settings_handler.get("g", "tabs_order") or ""
        self.order_changed = False
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        self.title_label = guiTools.QNavigableLabel("يمكنك من هنا تعديل وترتيب ظهور تبويبات البرنامج حسب رغبتك:")
        self.title_label.setFont(font)
        self.title_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.title_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.tab_list = guiTools.QListWidget()
        self.tab_list.setSpacing(3)
        self.tab_list.setFont(font)
        self.tab_list.setDragDropMode(qt.QAbstractItemView.DragDropMode.InternalMove)
        self.tab_list.setDefaultDropAction(qt2.Qt.DropAction.MoveAction)
        self.tab_list.setSelectionMode(qt.QAbstractItemView.SelectionMode.SingleSelection)
        self.tab_list.setDragEnabled(True)
        self.tab_list.setAcceptDrops(True)
        self.tab_list.setDropIndicatorShown(True)
        self.tab_list.setVerticalScrollBarPolicy(qt2.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_list.setHorizontalScrollBarPolicy(qt2.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_list.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_list.customContextMenuRequested.connect(self.show_context_menu)
        self.tab_list.model().rowsMoved.connect(lambda *args: self.save_order())
        def list_drop_event(event):
            guiTools.QListWidget.dropEvent(self.tab_list, event)
            self.save_order()
        self.tab_list.dropEvent = list_drop_event
        def list_key_press(event):
            if event.key() == qt2.Qt.Key.Key_Menu or (event.key() == qt2.Qt.Key.Key_F10 and (event.modifiers() & qt2.Qt.KeyboardModifier.ShiftModifier)):
                self.show_context_menu()
                event.accept()
                return
            guiTools.QListWidget.keyPressEvent(self.tab_list, event)
        self.tab_list.keyPressEvent = list_key_press
        layout.addWidget(self.tab_list)
        self.hint_label = guiTools.QNavigableLabel("لمزيد من الخيارات نستخدم زر التطبيقات أو click الأيمن على تبويبة من التبويبات")
        self.hint_label.setFont(font)
        self.hint_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.hint_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label)
        self.mouse_hint_label = guiTools.QNavigableLabel("تنبيه للمستخدم المبصر: يمكن تمرير وسحب وإفلات عناصر القائمة بالماوس لتغيير ترتيب التبويبات مباشرة.")
        self.mouse_hint_label.setFont(font)
        self.mouse_hint_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.mouse_hint_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mouse_hint_label)
        self.populate_list()

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_list()

    def get_hidden_tabs(self):
        hidden_raw = settings_handler.get("g", "hidden_tabs") or ""
        if not hidden_raw:
            return []
        try:
            return json.loads(hidden_raw)
        except Exception:
            return [x.strip() for x in hidden_raw.split(",") if x.strip()]

    def get_saved_order(self):
        order_raw = settings_handler.get("g", "tabs_order") or ""
        if not order_raw:
            return []
        try:
            return json.loads(order_raw)
        except Exception:
            return [x.strip() for x in order_raw.split(",") if x.strip()]

    def populate_list(self):
        current_selection = None
        if self.tab_list.currentItem():
            current_selection = self.tab_list.currentItem().text()
        self.tab_list.clear()
        hidden_tabs = self.get_hidden_tabs()
        saved_order = self.get_saved_order()
        visible_tabs = [t for t in self.ALL_TABS if t not in hidden_tabs]
        final_tabs = []
        for name in saved_order:
            if name in visible_tabs and name not in final_tabs:
                final_tabs.append(name)
        for name in visible_tabs:
            if name not in final_tabs:
                final_tabs.append(name)
        for name in final_tabs:
            self.tab_list.addItem(name)
        if current_selection:
            items = self.tab_list.findItems(current_selection, qt2.Qt.MatchFlag.MatchExactly)
            if items:
                self.tab_list.setCurrentItem(items[0])
            elif self.tab_list.count() > 0:
                self.tab_list.setCurrentRow(0)
        elif self.tab_list.count() > 0:
            self.tab_list.setCurrentRow(0)

    def show_context_menu(self, pos=None):
        row = self.tab_list.currentRow()
        if row < 0 or row >= self.tab_list.count():
            return
        item = self.tab_list.item(row)
        if not item:
            return
        menu = guiTools.QCustomContextMenu("خيارات الترتيب", self)
        bold_font = qt1.QFont()
        bold_font.setBold(True)
        menu.setFont(bold_font)
        menu.setAccessibleName("خيارات الترتيب")
        act_first = menu.addAction("نقل إلى البداية")
        act_up = menu.addAction("تحريك لأعلى")
        act_down = menu.addAction("تحريك لأسفل")
        act_last = menu.addAction("نقل إلى النهاية")
        menu.addSeparator()
        act_reset = menu.addAction("استعادة الترتيب الافتراضي")
        if row == 0:
            act_first.setEnabled(False)
            act_up.setEnabled(False)
        if row == self.tab_list.count() - 1:
            act_down.setEnabled(False)
            act_last.setEnabled(False)
        act_first.triggered.connect(lambda: self.move_item_to(row, 0))
        act_up.triggered.connect(lambda: self.move_item_to(row, row - 1))
        act_down.triggered.connect(lambda: self.move_item_to(row, row + 1))
        act_last.triggered.connect(lambda: self.move_item_to(row, self.tab_list.count() - 1))
        act_reset.triggered.connect(self.reset_to_default_order)
        menu.exec(qt1.QCursor.pos())

    def is_default_order(self):
        hidden_tabs = self.get_hidden_tabs()
        default_order = [t for t in self.ALL_TABS if t not in hidden_tabs]
        current_order = [self.tab_list.item(i).text() for i in range(self.tab_list.count())]
        return current_order == default_order

    def reset_to_default_order(self):
        if self.is_default_order():
            if settings_handler.get("g", "tabs_order") != "":
                settings_handler.set("g", "tabs_order", "")
                if self.initial_tabs_order != "":
                    self.order_changed = True
            guiTools.MessageBox.view(
                self,
                "تنبيه",
                "الترتيب الافتراضي لتبويبات البرنامج هو المعمول به بالفعل."
            )
            return

        mb = guiTools.QQuestionMessageBox.view(
            self,
            "تأكيد استعادة الترتيب الافتراضي",
            "هل أنت متأكد من رغبتك في استعادة الترتيب الافتراضي لتبويبات البرنامج؟",
            "نعم",
            "إلغاء"
        )
        if mb == 0:
            if self.initial_tabs_order != "":
                self.order_changed = True
            settings_handler.set("g", "tabs_order", "")
            self.populate_list()

    def move_item_to(self, from_row, to_row):
        count = self.tab_list.count()
        if from_row < 0 or from_row >= count:
            return
        if to_row < 0 or to_row >= count:
            return
        if from_row == to_row:
            return
        item = self.tab_list.takeItem(from_row)
        self.tab_list.insertItem(to_row, item)
        self.tab_list.setCurrentRow(to_row)
        self.order_changed = True
        self.save_order()

    def save_order(self):
        visible_order = [self.tab_list.item(i).text() for i in range(self.tab_list.count())]
        full_order = list(visible_order)
        for t in self.ALL_TABS:
            if t not in full_order:
                full_order.append(t)
        if full_order == self.ALL_TABS:
            new_order = ""
        else:
            new_order = json.dumps(full_order, ensure_ascii=False)
        if new_order != self.initial_tabs_order:
            self.order_changed = True
        else:
            self.order_changed = False
        settings_handler.set("g", "tabs_order", new_order)
