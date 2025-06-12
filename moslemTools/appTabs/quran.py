import gui.translationViewer
import gui, guiTools, functions, re
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class Quran(qt.QWidget):
    def __init__(self):
        super().__init__()        
        qt1.QShortcut("ctrl+p",self).activated.connect(self.onListenActionTriggert)
        qt1.QShortcut("ctrl+t",self).activated.connect(self.onTafseerActionTriggered)
        qt1.QShortcut("ctrl+l",self).activated.connect(self.onTranslationActionTriggered)
        qt1.QShortcut("ctrl+i",self).activated.connect(self.onIarabActionTriggered)
        self.infoData = []
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.setStyleSheet("""
            QWidget {
                /* background-color: #000000; */
                color: #f0f0f0;
                font: bold 12px; 
            }
            QLineEdit {
                background-color: #3e3e3e;
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox, QLabel {
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: blue;
                color: white;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #005fa1;
            }
            QPushButton#customButton {
                background-color: #008000;
                color: white;
            }
            QPushButton#customButton:hover {
                background-color: #006600;
            }
            QListWidget {
                background-color: #000000;
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: red;
            }
            QMenu {
                background-color: #3e3e3e;
                color: #f0f0f0;
            }
            QMenu::item:selected {
                background-color: #0078d7;
            }
        """)
        browse_layout = qt.QHBoxLayout()        
        browse_layout.setSpacing(10)
        layout1=qt.QVBoxLayout()
        self.by = qt.QLabel("التصفح ب")
        self.by.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout1.addWidget(self.by)
        self.type = qt.QComboBox()
        self.type.setFixedWidth(100)
        self.type.setAccessibleName("التصفح ب")
        self.type.addItems(["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"])
        self.type.currentIndexChanged.connect(self.onTypeChanged)
        layout1.addWidget(self.type)
        self.custom_laybol=qt.QLabel("CTRL+C")
        self.custom_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.custom = guiTools.QPushButton("مخصص")
        self.custom.setObjectName("customButton")
        self.custom.setShortcut("ctrl+c")
        self.custom.setAccessibleDescription("control plus c")
        self.custom.clicked.connect(self.onCostumBTNClicked)                
        self.custom.setMaximumWidth(150)
        self.custom.setMaximumHeight(150)
        layout2=qt.QVBoxLayout()
        layout2.addWidget(self.custom_laybol)
        layout2.addWidget(self.custom)        
        browse_layout.addLayout(layout1)        
        browse_layout.addLayout(layout2)
        layout.addLayout(browse_layout)
        self.serch = qt.QLabel("بحث")
        self.serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.info = guiTools.QListWidget()
        font=qt1.QFont()
        font.setBold(True)        
        self.info.setFont(font)
        self.info.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.info.customContextMenuRequested.connect(self.onContextMenu)
        self.info.itemActivated.connect(self.onItemTriggered)
        layout.addWidget(self.info)
        guide_layout = qt.QHBoxLayout()
        self.user_guide = qt.QPushButton("دليل الاختصارات")
        self.user_guide.setDefault(True)
        self.user_guide.setShortcut("ctrl+f1")
        self.user_guide.setAccessibleDescription("control plus f1")
        self.user_guide.setFixedSize(150, 40)                
        self.user_guide.clicked.connect(lambda: guiTools.TextViewer(
            self,
            "دليل الاختصارات",
            (
                "اختصارات الآية الحالية\n"
                "space: تشغيل الآية\n"
                "ctrl+t: تفسير الآية الحالية\n"
                "ctrl+i: إعراب الآية الحالية\n"
                "ctrl+r: أسباب نزول الآية الحالية\n"
                "ctrl+l: ترجمة الآية الحالية\n"
                "ctrl+f: معلومات الآية الحالية\n"
                "ctrl+b: إضافة علامة مرجعية\n"
                "\n"
                "اختصارات الفئة\n"
                "ctrl+a: نسخ الفئة\n"
                "ctrl+s: حفظ الفئة كملف نصي\n"
                "ctrl+p: طباعة الفئة\n"
                "ctrl+shift+t: تفسير الفئة\n"
                "ctrl+shift+i: إعراب الفئة\n"
                "ctrl+shift+f: معلومات السورة\n"
                "ctrl+shift+l: ترجمة الفئة\n"
                "ctrl+shift+p: التشغيل إلى نهاية الفئة\n"
                "ctrl+alt+t: التفسير من آية إلى آية\n"
                "ctrl+alt+l: الترجمة من آية إلى آية\n"
                "ctrl+alt+i: الإعراب من آية إلى آية\n"
                "ctrl+alt+p: التشغيل من آية إلى آية\n"
                "\n"
                "اختصارات حجم الخط\n"
                "ctrl+=: تكبير الخط\n"
                "ctrl+-: تصغير الخط\n"
                "\n"
                "اختصارات التنقل\n"
                "alt + السهم الأيسر: الفئة السابقة\n"
                "alt + السهم الأيمن: الفئة التالية\n"
                "ctrl+shift+g: الذهاب إلى محتوى فئة\n"
                "ctrl+alt+g: تغيير الفئة\n"
                "ctrl+shift+r: تغيير القارئ\n"
                "ctrl+f1: دليل الاختصارات"
            )
        ).exec())
        guide_layout.addWidget(self.user_guide)
        self.info1 = qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setText("لخيارات عنصر الفئة, نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        guide_layout.addWidget(self.info1)
        layout.addLayout(guide_layout)
        self.onTypeChanged(0)
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches
    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.info.clear()
        result = self.search(search_text, self.infoData)
        self.info.addItems(result)
    def onItemTriggered(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        gui.QuranViewer(self, result[self.info.currentItem().text()][1], index,
                            self.info.currentItem().text(),
                            enableNextPreviouseButtons=True,
                            typeResult=result,
                            CurrentIndex=self.info.currentRow()).exec()
    def onTypeChanged(self, index: int):
        self.info.clear()
        self.infoData = []
        if index == 0:
            self.infoData = functions.quranJsonControl.getSurahs().keys()
        elif index == 1:
            for i in range(1, 605):
                self.infoData.append(str(i))
        elif index == 2:
            for i in range(1, 31):
                self.infoData.append(str(i))
        elif index == 3:
            for i in range(1, 241):
                self.infoData.append(str(i))
        elif index == 4:
            for i in range(1, 61):
                self.infoData.append(str(i))
        self.info.addItems(self.infoData)
    def getResult(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        return result[self.info.currentItem().text()][1]
    def onContextMenu(self):
        menu = qt.QMenu(self)
        menu.setAccessibleName("خيارات عنصر الفئة")
        menu.setFocus()
        listenAction = qt1.QAction("تشغيل", self)
        listenAction.setShortcut("ctrl+p")
        menu.addAction(listenAction)
        listenAction.triggered.connect(self.onListenActionTriggert)
        menu.setDefaultAction(listenAction)
        tafseerAction = qt1.QAction("تفسير", self)
        tafseerAction.setShortcut("ctrl+t")
        menu.addAction(tafseerAction)
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        translationAction = qt1.QAction("ترجمة", self)
        translationAction.setShortcut("ctrl+l")
        menu.addAction(translationAction)
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        iarabAction = qt1.QAction("إعراب", self)
        iarabAction.setShortcut("ctrl+i")
        menu.addAction(iarabAction)
        iarabAction.triggered.connect(self.onIarabActionTriggered)
        menu.exec(qt1.QCursor.pos())
    def onListenActionTriggert(self):
        if not self.info.currentItem():
            return
        result = self.getResult()
        gui.QuranPlayer(self, result, 0, self.type.currentIndex(),
                            self.info.currentItem().text(), enableBookMarks=True).exec()
    def onTafseerActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        gui.TafaseerViewer(self, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        gui.translationViewer(self, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self, "إعراب", result).exec()
    def onCostumBTNClicked(self):
        categories=["من سورة الى سورة", "من صفحة الى صفحة", "من جزء الى جزء", "من ربع الى ربع", "من حزب الى حزب"]
        menu=qt.QMenu("اختر فئة",self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        for category in categories:
            action=qt1.QAction(category,self)
            menu.addAction(action)
            action.triggered.connect(self.onCostumBTNRequested)
        menu.exec(qt1.QCursor.pos())
        menu.setFont(font)
    def onCostumBTNRequested(self):
        categories=["من سورة الى سورة", "من صفحة الى صفحة", "من جزء الى جزء", "من ربع الى ربع", "من حزب الى حزب"]
        index=categories.index(self.sender().text())
        guiTools.FromToSurahWidget(self,index).exec()