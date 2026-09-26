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
        self.types.addItems(["كتاب تفسير لتبويبة القرآن الكريم مكتوب", "ترجمة لمعاني القرآن الكريم لتبويبة القرآن الكريم مكتوب", "كتاب حديث", "قارئ قرآن آية بآية", "قارئ للمتون الإسلامية", "أذكار وأدعية صوتية لتبويبة الأذكار", "الكتب الإسلامية"])
        self.types.setFont(font)
        self.types.clicked.connect(self.onItemClicked)
        self.types.setSpacing(3)
        layout.addWidget(self.types)

    def onItemClicked(self):
        index = self.types.currentRow()
        if index == 0:
            self.show_dialog(gui.download.SelectTafaseerItem, ("all_tafaseers.json", "tafaseer"))
        elif index == 1:
            self.show_dialog(gui.download.SelectTranslationItem, ("all_translater.json", "Quran Translations"))
        elif index == 2:
            self.show_dialog(gui.download.SelectAhadeethItem, ("all_ahadeeth.json", "ahadeeth"))
        elif index == 3:
            self.show_dialog(gui.download.SelectReciter, ())
        elif index == 4:
            self.show_dialog(gui.download.DownloadMotonReciters, ())
        elif index == 5:
            self.show_dialog(gui.download.SelectAthkar, ())
        elif index == 6:
            self.show_dialog(gui.download.SelectIslamicBookItem, ("all_islamic_books.json", "islamicBooks"))

    def show_dialog(self, dialog_class, args):
        if args:
            dialog = dialog_class(self, *args)
        else:
            dialog = dialog_class(self)
        dialog.show()
