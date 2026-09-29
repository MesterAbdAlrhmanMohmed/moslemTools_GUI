import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler
import guiTools
import ujson as json


class StartupTabSettings(qt.QWidget):
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
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        self.title_label = guiTools.QNavigableLabel("اختر التبويبة الافتراضية التي تريد فتح البرنامج عليها عند التشغيل:")
        self.title_label.setFont(font)        
        self.title_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.tab_list = guiTools.QListWidget()
        self.tab_list.setSpacing(3)
        self.tab_list.setFont(font)

        hidden_raw = settings_handler.get("g", "hidden_tabs") or ""
        hidden_tabs = []
        if hidden_raw:
            try:
                hidden_tabs = json.loads(hidden_raw)
            except Exception:
                hidden_tabs = [x.strip() for x in hidden_raw.split(",") if x.strip()]

        tabs_names = [t for t in self.ALL_TABS if t not in hidden_tabs]
        if not tabs_names:
            tabs_names = ["مواقيت الصلاة والتاريخ"]

        saved_val = settings_handler.get("g", "startup_tab") or "0"
        saved_name = settings_handler.get("g", "startup_tab_name") or ""
        is_saved_hidden = False
        if saved_name and saved_name in hidden_tabs:
            is_saved_hidden = True
        elif saved_val in hidden_tabs:
            is_saved_hidden = True
        else:
            try:
                idx = int(saved_val)
                if 0 <= idx < len(self.ALL_TABS) and self.ALL_TABS[idx] in hidden_tabs:
                    is_saved_hidden = True
            except Exception:
                pass

        if is_saved_hidden:
            settings_handler.set("g", "startup_tab", "0")
            settings_handler.set("g", "startup_tab_name", "مواقيت الصلاة والتاريخ")
            saved_name = "مواقيت الصلاة والتاريخ"
            saved_val = "0"

        for name in tabs_names:
            self.tab_list.addItem(name)

        target_row = 0
        if saved_name and saved_name in tabs_names:
            target_row = tabs_names.index(saved_name)
        else:
            try:
                saved_idx = int(saved_val)
                if 0 <= saved_idx < len(tabs_names):
                    target_row = saved_idx
            except Exception:
                pass
        self.tab_list.setCurrentRow(target_row)

        def list_key_press(event):
            if event.key() == qt2.Qt.Key.Key_Return or event.key() == qt2.Qt.Key.Key_Enter:
                if self.tab_list.currentItem():
                    self.on_item_selected()
                event.accept()
                return
            guiTools.QListWidget.keyPressEvent(self.tab_list, event)
        self.tab_list.keyPressEvent = list_key_press
        self.tab_list.clicked.connect(self.on_item_selected)
        layout.addWidget(self.tab_list)

    def on_item_selected(self, index=None):
        row = self.tab_list.currentRow()
        if row >= 0 and row < self.tab_list.count():
            tab_name = self.tab_list.item(row).text()
            current_name = settings_handler.get("g", "startup_tab_name")
            if current_name == tab_name:
                guiTools.MessageBox.view(self, "تنبيه", f"التبويبة ({tab_name}) محددة بالفعل.")
                return
            settings_handler.set("g", "startup_tab", str(row))
            settings_handler.set("g", "startup_tab_name", tab_name)
            guiTools.MessageBox.view(self, "تم تحديد التبويبة", f"تم تحديد التبويبة ({tab_name}).\nهذه التبويبة هي التي سيتم فتح البرنامج عليها تلقائيًا عند تشغيله.")
