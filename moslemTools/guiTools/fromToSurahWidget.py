import functions, gui, guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
class FromToSurahWidget(qt.QDialog):
    def __init__(self, p,index:int):
        super().__init__()
        self.p = p
        self.index=index
        self.resize(300,200)
        if index==0:
            self.surahs = functions.quranJsonControl.getSurahs()            
        elif index==1:
            self.surahs = functions.quranJsonControl.getPage()            
        elif index==2:
            self.surahs = functions.quranJsonControl.getJuz()            
        elif index==3:
            self.surahs = functions.quranJsonControl.getHezb()            
        elif index==4:
            self.surahs = functions.quranJsonControl.getHizb()            
        self.label_from_surah = qt.QLabel("من")
        self.combo_from_surah = qt.QComboBox()
        font=qt1.QFont()
        font.setBold(True)
        self.combo_from_surah.addItems(self.surahs)        
        self.combo_from_surah.setAccessibleName("من")
        self.combo_from_surah.setFont(font)
        self.label_from_verse = qt.QLabel("من الآية")
        self.spin_from_verse = qt.QSpinBox()        
        self.spin_from_verse.setAccessibleName("من الآية")
        self.label_to_surah = qt.QLabel("الى")
        self.combo_to_surah = qt.QComboBox()
        self.combo_to_surah.setAccessibleName("الى")
        self.combo_to_surah.addItems(self.surahs)        
        self.label_to_verse = qt.QLabel("الى الآية")
        self.spin_to_verse = qt.QSpinBox()        
        self.spin_to_verse.setAccessibleName("الى الآية")
        self.go = qt.QPushButton("الذهاب")                            
        self.go.setStyleSheet("""
    QPushButton {
        background-color: #1e7e34;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #19692c;
    }
""")
        h_layout1 = qt.QHBoxLayout()
        h_layout1.addWidget(self.label_from_surah)
        h_layout1.addWidget(self.combo_from_surah)        
        h_layout2 = qt.QHBoxLayout()
        h_layout2.addWidget(self.label_from_verse)
        h_layout2.addWidget(self.spin_from_verse)        
        h_layout3 = qt.QHBoxLayout()
        h_layout3.addWidget(self.label_to_surah)
        h_layout3.addWidget(self.combo_to_surah)        
        h_layout4 = qt.QHBoxLayout()
        h_layout4.addWidget(self.label_to_verse)
        h_layout4.addWidget(self.spin_to_verse)                
        main_layout = qt.QVBoxLayout()
        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)
        main_layout.addLayout(h_layout3)
        main_layout.addLayout(h_layout4)
        main_layout.addWidget(self.go)        
        self.setLayout(main_layout)                        
        self.combo_from_surah.currentIndexChanged.connect(self.handle_surah_change)
        self.combo_to_surah.currentIndexChanged.connect(self.handle_to_surah_change)
        self.spin_from_verse.valueChanged.connect(self.handle_verse_change)
        self.spin_to_verse.valueChanged.connect(self.handle_verse_change)
        self.go.clicked.connect(self.onGo)        
        self.handle_surah_change()        
    def handle_surah_change(self):        
        if self.combo_to_surah.currentIndex() < self.combo_from_surah.currentIndex():
            self.combo_to_surah.setCurrentIndex(self.combo_from_surah.currentIndex())        
        surah_from_text = self.combo_from_surah.currentText()
        surah_to_text = self.combo_to_surah.currentText()
        num_verses_from = len(self.surahs[surah_from_text][1].split("\n"))
        num_verses_to = len(self.surahs[surah_to_text][1].split("\n"))
        self.spin_from_verse.setRange(1, num_verses_from)
        self.spin_from_verse.setValue(1)
        self.spin_to_verse.setRange(1, num_verses_to)
        self.spin_to_verse.setValue(num_verses_to)
        self.handle_verse_change()    
    def handle_verse_change(self):        
        if self.combo_from_surah.currentIndex() == self.combo_to_surah.currentIndex():
            if self.spin_to_verse.value() <= self.spin_from_verse.value():
                self.spin_to_verse.setValue(len(self.surahs[self.combo_to_surah.currentText()][1].split("\n")))    
    def onOpen(self):
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        gui.QuranViewer(self.p, "\n".join(result), 5, 0, enableBookmarks=False).exec()
    def handle_to_surah_change(self):        
        if self.combo_to_surah.currentIndex() < self.combo_from_surah.currentIndex():
            self.combo_to_surah.setCurrentIndex(self.combo_from_surah.currentIndex())        
        surah_from_text = self.combo_from_surah.currentText()
        surah_to_text = self.combo_to_surah.currentText()
        num_verses_to = len(self.surahs[surah_to_text][1].split("\n"))
        self.spin_to_verse.setRange(1, num_verses_to)
        self.spin_to_verse.setValue(num_verses_to)
        self.handle_verse_change()    
    def onGo(self):
        menu = qt.QMenu(self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("خيارات")
        menu.setFocus()
        readAction=qt1.QAction("قراءة",self)
        menu.addAction(readAction)
        menu.setDefaultAction(readAction)
        readAction.triggered.connect(self.onOpen)
        listenAction = qt1.QAction("تشغيل", self)
        menu.addAction(listenAction)
        listenAction.triggered.connect(self.onListenActionTriggert)
        tafseerAction = qt1.QAction("تفسير", self)
        menu.addAction(tafseerAction)
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        translationAction = qt1.QAction("ترجمة", self)
        menu.addAction(translationAction)
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        iarabAction = qt1.QAction("إعراب", self)
        menu.addAction(iarabAction)
        iarabAction.triggered.connect(self.onIarabActionTriggered)
        menu.exec(qt1.QCursor.pos())
        menu.setFont(font)
    def onListenActionTriggert(self):
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        gui.QuranPlayer(self.p, "\n".join(result), 0,5, 0, enableBookMarks=False).exec()
    def onTafseerActionTriggered(self):
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.TafaseerViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.translationViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        ayahList =         functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self.p, "إعراب", result).exec()