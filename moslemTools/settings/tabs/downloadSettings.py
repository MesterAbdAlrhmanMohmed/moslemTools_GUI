import guiTools, gui
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class Download(qt.QDialog):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QListWidget, QLineEdit {color: #e0e0e0;border: 1px solid #555;padding: 4px;}")
        layout = qt.QVBoxLayout(self)
        self.types = guiTools.QListWidget()
        font = qt1.QFont()
        font.setBold(True)
        self.types.addItems(["كتاب تفسير لتبويبة القرآن الكريم مكتوب", "ترجمة لمعاني القرآن الكريم لتبويبة القرآن الكريم مكتوب", "كتاب حديث", "قارئ للقرآن لتبويبة القرآن الكريم مكتوب", "أذكار وأدعية صوتية لتبويبة الأذكار", "الكتب الإسلامية"])
        self.types.setFont(font)
        self.types.clicked.connect(self.onItemClicked)
        self.types.setSpacing(3)
        self.adminstration = qt.QLineEdit()
        self.adminstration.setReadOnly(True)
        self.adminstration.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.adminstration.setText("تنبيه هام , لتثبيت موارد خارجية, يجب أولا منح صلاحيات المشرف للبرنامج")
        self.adminstration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.admin_help = guiTools.QReadOnlyTextEdit()
        self.admin_help.setText("طرق تشغيل البرنامج كمشرف (كمسؤول):\n\nالطريقة الأولى:\n1. افتح نافذة التشغيل Run بالضغط على اختصار Windows + R.\n2. اكتب الأمر mt في المربع.\n3. اضغط على اختصار Ctrl + Shift + Enter لتشغيل البرنامج كمشرف.\n\nالطريقة الثانية:\nاضغط بزر الفأرة الأيمن أو زر التطبيقات على أيقونة البرنامج أو اختصاره، ثم اختر تشغيل كمسؤول (Run as administrator).\n\nالطريقة الثالثة: تشغيل البرنامج كمسؤول دائما:\nاضغط بزر الفأرة الأيمن أو مفتاح التطبيقات على اختصار البرنامج ثم اختر خصائص (Properties)، وانتقل لتبويبة التوافق (Compatibility)، وقم بتفعيل خيار تشغيل هذا البرنامج كمسؤول (Run this program as an administrator)، ثم اضغط على موافق (OK).\nملاحظة هامة: في حالة ضبط البرنامج للتشغيل كمسؤول دائماً، لن يستطيع النظام تشغيله تلقائياً عند بدء تشغيل الويندوز، حتى وإن كان خيار التشغيل مع النظام مفعلاً في الإعدادات.")        
        layout.addWidget(self.types)
        layout.addWidget(self.adminstration)
        layout.addWidget(self.admin_help)

    def onItemClicked(self):
        index = self.types.currentRow()
        if index == 0:
            self.show_dialog(gui.download.SelectItem, ("all_tafaseers.json", "tafaseer"))
        elif index == 1:
            self.show_dialog(gui.download.SelectItem, ("all_translater.json", "Quran Translations"))
        elif index == 2:
            self.show_dialog(gui.download.SelectItem, ("all_ahadeeth.json", "ahadeeth"))
        elif index == 3:
            self.show_dialog(gui.download.SelectReciter, ())
        elif index == 4:
            self.show_dialog(gui.download.SelectAthkar, ())
        elif index == 5:
            self.show_dialog(gui.download.SelectItem, ("all_islamic_books.json", "islamicBooks"))

    def show_dialog(self, dialog_class, args):
        if args:
            dialog = dialog_class(self, *args)
        else:
            dialog = dialog_class(self)
        dialog.show()
