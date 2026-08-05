import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler
import guiTools


class StartupTabSettings(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        self.title_label = qt.QLineEdit("اختر التبويبة الافتراضية التي تريد فتح البرنامج عليها عند التشغيل:")
        self.title_label.setReadOnly(True)
        self.title_label.setFont(font)
        self.title_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.title_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.tab_list = guiTools.QListWidget()
        self.tab_list.setSpacing(3)
        self.tab_list.setFont(font)
        tabs_names = []
        if self.p and hasattr(self.p, "p") and self.p.p and hasattr(self.p.p, "list_widget"):
            for i in range(self.p.p.list_widget.count()):
                tabs_names.append(self.p.p.list_widget.item(i).text())
        elif self.p and hasattr(self.p, "list_widget"):
            for i in range(self.p.list_widget.count()):
                tabs_names.append(self.p.list_widget.item(i).text())
        if not tabs_names:
            tabs_names = [
                "مواقيت الصلاة والتاريخ",
                "القرآن الكريم مكتوب",
                "القرآن الكريم صوتي",
                "متابع الختمة القرآنية",
                "الأحاديث النبوية والقدسية",
                "الباحث في القرآن والأحاديث",
                "اسأل الذكاء الاصطناعي",
                "لعبة الأسئلة الإسلامية",
                "الكتب الإسلامية",
                "إذاعات الراديو الإسلامية",
                "الأذكار والأدعية",
                "السبحة الإلكترونية",
                "أسماء الله الحُسْنى",
                "القصص الإسلامية المكتوبة",
                "مواضيع إسلامية مختلفة",
                "محول التاريخ"
            ]
        for name in tabs_names:
            self.tab_list.addItem(name)
        try:
            saved_index = int(settings_handler.get("g", "startup_tab"))
            if 0 <= saved_index < self.tab_list.count():
                self.tab_list.setCurrentRow(saved_index)
            else:
                self.tab_list.setCurrentRow(0)
        except Exception:
            self.tab_list.setCurrentRow(0)
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
        if row >= 0:
            tab_name = self.tab_list.item(row).text()
            settings_handler.set("g", "startup_tab", str(row))
            guiTools.MessageBox.view(self, "تم تحديد التبويبة", f"تم تحديد التبويبة ({tab_name}).\nهذه التبويبة هي التي سيتم فتح البرنامج عليها تلقائيًا عند تشغيله.")
