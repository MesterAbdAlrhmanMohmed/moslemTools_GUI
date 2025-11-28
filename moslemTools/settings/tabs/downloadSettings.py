import guiTools, gui
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class DialogThread(qt2.QThread):
    finished = qt2.pyqtSignal()    
    def __init__(self, dialog_class, parent, args):
        super().__init__()
        self.dialog_class = dialog_class
        self.parent = parent
        self.args = args    
    def run(self):
        if self.args:
            self.dialog = self.dialog_class(self.parent, *self.args)
        else:
            self.dialog = self.dialog_class(self.parent)
        self.finished.emit()
class Download(qt.QDialog):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QListWidget, QLineEdit {color: #e0e0e0;border: 1px solid #555;padding: 4px;}")
        layout = qt.QVBoxLayout(self)
        self.types = guiTools.QListWidget()
        font = qt1.QFont()
        font.setBold(True)        
        self.types.addItems(["كتاب تفسير لتبويبة القرآن الكريم مكتوب", "ترجمة للقرآن الكريم لتبويبة القرآن الكريم مكتوب", "كتاب حديث", "قارئ للقرآن لتبويبة القرآن الكريم مكتوب", "أذكار وأدعية صوتية لتبويبة الأذكار", "الكتب الإسلامية"])
        self.types.setFont(font)
        self.types.clicked.connect(self.onItemClicked)
        self.types.setSpacing(3)
        self.adminstration = qt.QLabel()
        self.adminstration.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.adminstration.setText("تنبيه هام , لتثبيت موارد خارجية, يجب أولا منح صلاحيات المشرف للبرنامج")
        self.adminstration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.types)
        layout.addWidget(self.adminstration)
    def onItemClicked(self):
        index = self.types.currentRow()
        if index == 0:
            self.start_dialog_thread(gui.download.SelectItem, ("all_tafaseers.json", "tafaseer"))
        elif index == 1:
            self.start_dialog_thread(gui.download.SelectItem, ("all_translater.json", "Quran Translations"))
        elif index == 2:
            self.start_dialog_thread(gui.download.SelectItem, ("all_ahadeeth.json", "ahadeeth"))
        elif index == 3:
            self.start_dialog_thread(gui.download.SelectReciter, ())
        elif index == 4:
            self.start_dialog_thread(gui.download.SelectAthkar, ())
        elif index == 5:
            self.start_dialog_thread(gui.download.SelectItem, ("all_islamic_books.json", "islamicBooks"))
    def start_dialog_thread(self, dialog_class, args):
        self.dialog_thread = DialogThread(dialog_class, self, args)
        self.dialog_thread.finished.connect(self.show_dialog)
        self.dialog_thread.start()
    def show_dialog(self):
        self.dialog_thread.dialog.exec()