import guiTools, gui
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class Download(qt.QDialog):
    def __init__(self):
        super().__init__()
        layout = qt.QVBoxLayout(self)
        self.types = guiTools.QListWidget()
        self.types.setIconSize(qt2.QSize(24, 24))
        font = qt1.QFont()
        font.setBold(True)
        items_data = [
            ("كتاب تفسير لتبويبة القرآن الكريم مكتوب", "القرآن الكريم مكتوب"),
            ("ترجمة لمعاني القرآن الكريم لتبويبة القرآن الكريم مكتوب", "القرآن الكريم مكتوب"),
            ("كتاب حديث", "الأحاديث"),
            ("قارئ قرآن آية بآية", "القرآن الكريم مكتوب"),
            ("قارئ للمتون", "المتون"),
            ("أذكار وأدعية صوتية لتبويبة الأذكار", "الأذكار والأدعية"),
            ("الكتب", "الكتب"),
        ]
        for text, tab_name in items_data:
            item = qt.QListWidgetItem(guiTools.theme.get_tab_icon(tab_name), text)
            self.types.addItem(item)
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
