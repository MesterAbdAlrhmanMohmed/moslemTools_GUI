import functions, gui, guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class FromToSurahWidget(qt.QDialog):
    def __init__(self, p, index:int):
        super().__init__()
        self.p = p
        self.index = index
        self.resize(350, 250) 
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font) 
        if index == 0:
            self.surahs = functions.quranJsonControl.getSurahs()
            self.setWindowTitle("تحديد سور القرآن الكريم")
        elif index == 1:
            self.surahs = functions.quranJsonControl.getPage()
            self.setWindowTitle("تحديد صفحات القرآن الكريم")
        elif index == 2:
            self.surahs = functions.quranJsonControl.getJuz()
            self.setWindowTitle("تحديد أجزاء القرآن الكريم")
        elif index == 3:
            self.surahs = functions.quranJsonControl.getHezb()
            self.setWindowTitle("تحديد أرباع القرآن الكريم")
        elif index == 4:
            self.surahs = functions.quranJsonControl.getHizb()
            self.setWindowTitle("تحديد أحزاب القرآن الكريم")
        self.label_from_surah = qt.QLabel("من")
        self.combo_from_surah = qt.QComboBox()
        self.combo_from_surah.addItems(self.surahs.keys()) 
        self.combo_from_surah.setAccessibleName("من")
        self.combo_from_surah.setFont(font)
        self.label_from_verse = qt.QLabel("من الآية")
        self.spin_from_verse = qt.QSpinBox()
        self.spin_from_verse.setAccessibleName("من الآية")
        self.spin_from_verse.setFont(font)
        self.label_to_surah = qt.QLabel("الى")
        self.combo_to_surah = qt.QComboBox()
        self.combo_to_surah.setAccessibleName("الى")
        self.combo_to_surah.addItems(self.surahs.keys()) 
        self.combo_to_surah.setFont(font)
        self.label_to_verse = qt.QLabel("الى الآية")
        self.spin_to_verse = qt.QSpinBox()
        self.spin_to_verse.setAccessibleName("الى الآية")
        self.spin_to_verse.setFont(font)
        self.go = guiTools.QPushButton("الذهاب")
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
        self.go.setFont(font)
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
        self.combo_from_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.combo_to_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.spin_from_verse.valueChanged.connect(self.validate_verse_ranges)
        self.spin_to_verse.valueChanged.connect(self.validate_verse_ranges)
        self.go.clicked.connect(self.onGo)        
        self.update_spin_boxes(set_to_verse_to_max=True)                
    def update_spin_boxes(self, set_to_verse_to_max=False):        
        self.spin_from_verse.blockSignals(True)
        self.spin_to_verse.blockSignals(True)
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()        
        if to_surah_index < from_surah_index:
            self.combo_to_surah.setCurrentIndex(from_surah_index)
            to_surah_index = from_surah_index
        surah_from_text = self.combo_from_surah.currentText()
        surah_to_text = self.combo_to_surah.currentText()        
        num_verses_from = len(self.surahs[surah_from_text][1].split("\n")) if len(self.surahs[surah_from_text]) > 1 else 1
        num_verses_to = len(self.surahs[surah_to_text][1].split("\n")) if len(self.surahs[surah_to_text]) > 1 else 1        
        self.spin_from_verse.setRange(1, num_verses_from)
        self.spin_to_verse.setRange(1, num_verses_to)        
        if self.spin_from_verse.value() > num_verses_from or self.spin_from_verse.value() < 1:
            self.spin_from_verse.setValue(1)
        if set_to_verse_to_max or self.spin_to_verse.value() > num_verses_to or self.spin_to_verse.value() < 1:
            self.spin_to_verse.setValue(num_verses_to)                
        self.spin_from_verse.blockSignals(False)
        self.spin_to_verse.blockSignals(False)                
        self.validate_verse_ranges()
    def validate_verse_ranges(self):
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()
        from_verse_val = self.spin_from_verse.value()
        to_verse_val = self.spin_to_verse.value()        
        if from_surah_index == to_surah_index:            
            if to_verse_val < from_verse_val:
                self.spin_to_verse.blockSignals(True)
                self.spin_to_verse.setValue(from_verse_val)
                self.spin_to_verse.blockSignals(False)                
        elif from_surah_index > to_surah_index:
             self.combo_to_surah.setCurrentIndex(from_surah_index)
             self.update_spin_boxes(set_to_verse_to_max=True)
    def get_range_label(self):
        from_item = self.combo_from_surah.currentText()
        to_item = self.combo_to_surah.currentText()
        from_ayah = self.spin_from_verse.value()
        to_ayah = self.spin_to_verse.value()
        item_type = ""
        if self.index == 0:
            item_type = "سورة"
        elif self.index == 1:
            item_type = "الصفحة"
        elif self.index == 2:
            item_type = "الجزء"
        elif self.index == 3:
            item_type = "الربع"
        elif self.index == 4:
            item_type = "الحزب"    
        if from_item == to_item:
            return f"من {item_type} {from_item} آية {from_ayah} إلى آية {to_ayah}"
        else:
            return f"من {item_type} {from_item} آية {from_ayah} إلى {item_type} {to_item} آية {to_ayah}"
    def onOpen(self):
        self.validate_verse_ranges() 
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        label = self.get_range_label()
        gui.QuranViewer(self.p, "\n".join(result), 5, label, enableNextPreviouseButtons=False, enableBookmarks=False).exec()        
    def onGo(self):
        self.validate_verse_ranges()        
        menu = qt.QMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("خيارات")
        menu.setFocus()
        menu.setFont(font) 
        readAction = qt1.QAction("قراءة", self)
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
    def onListenActionTriggert(self):
        self.validate_verse_ranges() 
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        label = self.get_range_label()
        gui.QuranPlayer(self.p, "\n".join(result), 0, 5, label).exec()
    def onTafseerActionTriggered(self):
        self.validate_verse_ranges() 
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض التفسير.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.TafaseerViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onTranslationActionTriggered(self):
        self.validate_verse_ranges() 
        result = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الترجمة.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.translationViewer(self.p, AyahNumber1, AyahNumber2).exec()
    def onIarabActionTriggered(self):
        self.validate_verse_ranges() 
        ayahList = functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self.p, "إعراب", result).exec()