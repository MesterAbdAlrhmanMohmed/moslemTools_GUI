import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler
import guiTools, os, subprocess, sys
import ujson as json


class HiddenTabsSettings(qt.QWidget):
    ALL_TABS = [
        "مواقيت الصلاة والتاريخ",
        "القرآن الكريم مكتوب",
        "القرآن الكريم صوتي",
        "متابع الختمة القرآنية",
        "الأحاديث النبوية والقدسية",
        "الباحث في القرآن والأحاديث",
        "اسأل الذكاء الاصطناعي",
        "اختبر نفسك",
        "الكتب",
        "المتون",
        "إذاعات الراديو",
        "الأذكار والأدعية",
        "السبحة الإلكترونية",
        "أسماء الله الحُسْنى",
        "قصص الأنبياء وقصص القرآن الكريم",
        "مواضيع إسلامية مختلفة",
        "محول التاريخ"
    ]

    TAB_NAME_MAP = {
        "لعبة الأسئلة الإسلامية": "اختبر نفسك",
        "الكتب الإسلامية": "الكتب",
        "المتون الإسلامية": "المتون",
        "المتون الإسلامية المكتوبة": "المتون",
        "إذاعات الراديو الإسلامية": "إذاعات الراديو",
        "القصص الإسلامية": "قصص الأنبياء وقصص القرآن الكريم",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        self.title_label = guiTools.QNavigableLabel("اختر التبويبات التي تريد إخفاءها أو إظهارها في البرنامج:")
        self.title_label.setFont(font)        
        self.title_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.tab_list = guiTools.QListWidget()
        self.tab_list.setSpacing(3)
        self.tab_list.setFont(font)
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

        self.stats_label = guiTools.QNavigableLabel()
        self.stats_label.setFont(font)        
        self.stats_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)

        self.populate_list()

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_list()

    def get_hidden_tabs(self):
        val = settings_handler.get("g", "hidden_tabs") or ""
        if not val:
            return []
        try:
            tabs = json.loads(val)
        except Exception:
            tabs = [x.strip() for x in val.split(",") if x.strip()]
        return [self.TAB_NAME_MAP.get(x, x) for x in tabs]

    def save_hidden_tabs(self, tabs_list):
        settings_handler.set("g", "hidden_tabs", json.dumps(tabs_list, ensure_ascii=False))

    def update_stats(self):
        if not hasattr(self, "stats_label"):
            return
        hidden_tabs = self.get_hidden_tabs()
        hidden_count = sum(1 for name in self.ALL_TABS if name in hidden_tabs)
        total_count = len(self.ALL_TABS)
        visible_count = total_count - hidden_count
        self.stats_label.setText(
            f"عدد التبويبات المخفية: {hidden_count}، عدد التبويبات الظاهرة: {visible_count}، إجمالي عدد التبويبات: {total_count}"
        )
        self.stats_label.setCursorPosition(0)

    def populate_list(self):
        self.tab_list.clear()
        hidden_tabs = self.get_hidden_tabs()
        for name in self.ALL_TABS:
            if name in hidden_tabs:
                self.tab_list.addItem(f"{name}: تم الإخفاء")
            else:
                self.tab_list.addItem(name)
        self.update_stats()

    def on_item_selected(self, index=None):
        row = self.tab_list.currentRow()
        if row < 0 or row >= len(self.ALL_TABS):
            return
        tab_name = self.ALL_TABS[row]
        hidden_tabs = self.get_hidden_tabs()
        if tab_name in hidden_tabs:
            hidden_tabs.remove(tab_name)
            self.save_hidden_tabs(hidden_tabs)
            self.tab_list.item(row).setText(tab_name)
            self.update_stats()
            mb = guiTools.QQuestionMessageBox.view(
                self,
                "إعادة تشغيل البرنامج",
                f"تم إظهار تبويبة ({tab_name}). يتطلب تطبيق التغيير إعادة تشغيل البرنامج.\nهل تريد إعادة التشغيل الآن؟",
                "إعادة التشغيل الآن",
                "ليس الآن"
            )
            if mb == 0:
                self.restart_app()
        else:
            visible_count = len(self.ALL_TABS) - len(hidden_tabs)
            if visible_count <= 1:
                guiTools.MessageBox.view(self, "تنبيه", "لا يمكن إخفاء كل التبويبات. يجب إبقاء تبويبة واحدة على الأقل معروضة في البرنامج.")
                return
            saved_startup = settings_handler.get("g", "startup_tab")
            saved_name = settings_handler.get("g", "startup_tab_name")
            is_startup = False
            if saved_name == tab_name or saved_startup == tab_name:
                is_startup = True
            else:
                try:
                    startup_idx = int(saved_startup)
                    if 0 <= startup_idx < len(self.ALL_TABS) and self.ALL_TABS[startup_idx] == tab_name:
                        is_startup = True
                except Exception:
                    pass
            if is_startup:
                settings_handler.set("g", "startup_tab", "0")
                settings_handler.set("g", "startup_tab_name", "مواقيت الصلاة والتاريخ")
            hidden_tabs.append(tab_name)
            self.save_hidden_tabs(hidden_tabs)
            self.tab_list.item(row).setText(f"{tab_name}: تم الإخفاء")
            self.update_stats()
            mb = guiTools.QQuestionMessageBox.view(
                self,
                "إعادة تشغيل البرنامج",
                f"تم إخفاء تبويبة ({tab_name}). يتطلب تطبيق التغيير إعادة تشغيل البرنامج.\nهل تريد إعادة التشغيل الآن؟",
                "إعادة التشغيل الآن",
                "ليس الآن"
            )
            if mb == 0:
                self.restart_app()

    def restart_app(self):
        from .. import app
        app.exit = False
        try:
            app_instance = qt.QApplication.instance()
            if app_instance and hasattr(app_instance, "shared_memory"):
                app_instance.shared_memory.detach()
            shared = qt2.QSharedMemory("com.MTC.moslemTools")
            if shared.attach():
                shared.detach()
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            args = [sys.executable] + sys.argv[1:]
            cwd = os.path.dirname(sys.executable)
        else:
            args = [sys.executable, os.path.abspath(sys.argv[0])] + sys.argv[1:]
            cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
        subprocess.Popen(args, cwd=cwd)
        os._exit(0)
