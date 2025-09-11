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
            /* General QPushButton style - now applies the darker blue to all buttons by default */
            QPushButton {
                background-color: #0056b3; /* Darker blue for all general buttons */
                color: white;
                border: none; /* Removed border to be consistent with previous general style */
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #003d80; /* Even darker blue on hover for all general buttons */
            }
            
            /* Specific style for customButton (green) - overrides the general QPushButton style */
            QPushButton#customButton {
                background-color: #008000; /* Green color for custom button */
                color: white;
                border: none; /* Ensure no border is applied from general style */
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
        self.custom = guiTools.QPushButton("التصفح المخصص")
        self.custom.setMaximumHeight(30)
        self.custom.setMaximumWidth(160)
        self.custom.setObjectName("customButton")
        self.custom.setShortcut("ctrl+c")
        self.custom.setAccessibleDescription("control plus c")
        self.custom.clicked.connect(self.onCostumBTNClicked)                
        self.custom.setMaximumWidth(150)
        self.custom.setMaximumHeight(150)
        layout2=qt.QVBoxLayout()                
        layout2.addWidget(self.custom)        
        browse_layout.addLayout(layout1)        
        browse_layout.addLayout(layout2)
        layout.addLayout(browse_layout)
        self.serch = qt.QLabel("البحث عن محتوى فئة")
        self.serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن محتوى فئة")
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
        self.info_of_quran= guiTools.QPushButton("معلومات عن المصحف")                
        self.info_of_quran.setShortcut("ctrl+shift+q")
        self.info_of_quran.setAccessibleDescription("control plus shift plus Q")
        self.info_of_quran.setFixedSize(150, 40)                
        self.info_of_quran.clicked.connect(lambda: guiTools.TextViewer(
    self,
    "معلومات عن المصحف",
    (
        "معلومات عامة عن مصحف المدينة برواية حفص عن عاصم:\n"
        "عدد السور: 114 سورة (86 مكية + 28 مدنية).\n"
        "عدد الآيات: 6236 آية (بحسب رواية حفص، دون احتساب البسملة في السور ما عدا سورة الفاتحة).\n"
        "عدد الأجزاء: 30 جزءًا.\n"
        "عدد الأحزاب: 60 حزبًا.\n"
        "عدد الأرباع: 240 ربعًا (4 أرباع في الحزب، 8 أرباع في الجزء).\n"
        "عدد السجدات التلاوية: 15 سجدة.\n"
        "عدد الصفحات (في مصحف المدينة العادي): حوالي 604 صفحة.\n"
        "\n"
        "ملاحظات:\n"
        "عدد الكلمات تقريبي، حوالي 77430 كلمة حسب طرق العد الطباعية.\n"
        "عدد الحروف تقريبي، يتراوح بين 320000 و324000 حرف حسب احتساب النقاط والحركات.\n"
        "عدد الركوعات تقريبي (558 ركوعاً)، وهو رقم متداول حسب تقسيم السور في الطبعات.\n"
        "\n"
        "كل الأرقام المدونة تمثل الطبعة الرسمية لمصحف المدينة برواية حفص عن عاصم، الصادرة عن مجمع الملك فهد لطباعة المصحف الشريف."        
    )
).exec())        
        self.info1 = qt.QLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setText("لخيارات عنصر الفئة, نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        guide_layout.addWidget(self.info1)
        guide_layout.addWidget(self.info_of_quran)
        layout.addLayout(guide_layout)
        self.onTypeChanged(0)
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[^\u0621-\u063A\u0641-\u064A\s]+')
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
                            self.info.currentItem().text()).exec()
    def onTafseerActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.TafaseerViewer(self, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.translationViewer(self, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
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