import guiTools, pyperclip, winsound, json, functions, re, os, settings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class Albaheth(qt.QWidget):
    def __init__(self):
        super().__init__()        
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        font_combo=qt1.QFont()
        font_combo.setBold(True)
        self.serch_laibol = qt.QLabel("ابحث في")
        self.serch_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch = qt.QComboBox()
        self.serch.addItem("القرآن الكريم")
        self.serch.addItem("الأحاديث")        
        self.serch.setFont(font_combo)
        self.serch.setAccessibleName("ابحث في")
        self.serch.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)        
        self.ahadeeth_laibol = qt.QLabel("إختيار الكتاب")
        self.ahadeeth_laibol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.ahadeeth = qt.QComboBox()        
        self.ahadeeth.addItems(functions.ahadeeth.ahadeeths.keys())
        self.ahadeeth.setFont(font_combo)
        self.ahadeeth.setAccessibleName("إختيار الكتاب")
        self.ahadeeth.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)        
        self.surahsList=functions.quranJsonControl.getSurahs()
        self.surahs_laybol=qt.QLabel("ابحث في")
        self.surahs_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahs=qt.QComboBox()
        self.surahs.addItems(["كل القرآن"] + list(self.surahsList.keys()))
        self.surahs.setFont(font_combo)
        self.surahs.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed)        
        self.surahs.setAccessibleName("ابحث في")
        self.islamicBooksLabel=qt.QLabel("اختر كتاب")
        self.islamicBooksLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.islamicBooksList=qt.QComboBox()
        self.islamicBooksList.setAccessibleName("اختر كتاب")
        self.serch.currentIndexChanged.connect(self.toggle_ahadeeth_visibility)                
        self.serch_laibol_content = qt.QLabel("أكتب محتوى البحث")
        self.serch_laibol_content.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.serch_input = qt.QLineEdit()
        self.serch_input.setAccessibleName("أكتب محتوى البحث")
        self.start = guiTools.QPushButton("البحث")
        self.start.setStyleSheet("background-color: green; color: white;")
        self.start.clicked.connect(self.onSearchClicked)        
        self.results = guiTools.QReadOnlyTextEdit()
        self.results.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.OnContextMenu)        
        self.font_size = 12
        font = self.font()
        font.setPointSize(self.font_size)
        self.results.setFont(font)        
        self.font_laybol = qt.QLabel("حجم الخط")
        self.font_laybol.setStyleSheet("font-size: 16px;")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setStyleSheet("font-size: 16px; padding: 4px;")
        self.show_font.setText(str(self.font_size))
        main_layout = qt.QVBoxLayout(self)
        self.top_combo_layout = qt.QHBoxLayout()
        self.search_layout_top = qt.QVBoxLayout()
        self.search_layout_top.addWidget(self.serch_laibol)
        self.search_layout_top.addWidget(self.serch)
        self.ahadeeth_layout_top = qt.QVBoxLayout()
        self.ahadeeth_layout_top.addWidget(self.ahadeeth_laibol)
        self.ahadeeth_layout_top.addWidget(self.ahadeeth)
        self.ahadeeth_layout_top.addWidget(self.surahs_laybol)
        self.ahadeeth_layout_top.addWidget(self.surahs)
        self.top_combo_layout.addLayout(self.search_layout_top, stretch=1)
        self.top_combo_layout.addLayout(self.ahadeeth_layout_top, stretch=1)        
        main_layout.addLayout(self.top_combo_layout)
        main_layout.addWidget(self.serch_laibol_content, alignment=qt2.Qt.AlignmentFlag.AlignCenter)        
        search_layout = qt.QHBoxLayout()
        search_layout.addWidget(self.serch_input)
        search_layout.addWidget(self.start)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.results)        
        font_layout = qt.QVBoxLayout()
        font_layout.addWidget(self.font_laybol)
        font_layout.addWidget(self.show_font)
        main_layout.addLayout(font_layout)
        self.ahadeeth_laibol.hide()
        self.ahadeeth.hide()        
    def OnContextMenu(self):
        menu = qt.QMenu("الخيارات", self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        copy_all = menu.addAction("نسخ النص كاملا")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text = menu.addAction("نسخ النص المحدد")
        copy_selected_text.triggered.connect(self.copy_line)        
        fontMenu = qt.QMenu("حجم الخط", self)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)        
        fontMenu.setFont(font)
        menu.addMenu(fontMenu)
        menu.setFont(font)
        menu.exec(self.mapToGlobal(self.cursor().pos()))        
    def increase_font_size(self):
        if self.font_size < 50:
            self.font_size += 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()            
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()            
    def update_font_size(self):
        cursor = self.results.textCursor()
        self.results.selectAll()
        font = self.results.font()
        font.setPointSize(self.font_size)
        self.results.setCurrentFont(font)
        self.results.setTextCursor(cursor)        
    def copy_line(self):
        try:
            cursor = self.results.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
                winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def copy_text(self):
        try:
            text = self.results.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000, 100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))            
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(
            r'[\u060C\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
        )
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches        
    def onSearchClicked(self):
        if not self.serch_input.text():
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        I = self.serch.currentIndex()
        if I == 0:
            if self.surahs.currentIndex()==0:
                listOfWords = functions.quranJsonControl.getQuran()
            else:
                listOfWords=self.surahsList[self.surahs.currentText()][1].split("\n")
        elif I == 1:
            book_name = functions.ahadeeth.ahadeeths[self.ahadeeth.currentText()]
            with open(os.path.join(os.getenv('appdata'), settings.app.appName, "ahadeeth", book_name),
                      "r", encoding="utf-8") as f:
                ahadeeth = json.load(f)
            listOfWords = []
            for item in ahadeeth:
                listOfWords.append(str(ahadeeth.index(item)+1) + item)                
        result = self.search(self.serch_input.text(), listOfWords)
        if result:
            self.results.setText("عدد نتائج البحث " + str(len(result)) + "\n" + "\n".join(result))
        else:
            self.results.setText("لم يتم العثور على نتائج")
        self.results.setFocus()        
    def toggle_ahadeeth_visibility(self):    
        if self.serch.currentText() == "الأحاديث":        
            self.ahadeeth_laibol.show()
            self.ahadeeth.show()        
            self.surahs_laybol.hide()
            self.surahs.hide()
        else:        
            self.ahadeeth_laibol.hide()
            self.ahadeeth.hide()        
            self.surahs_laybol.show()
            self.surahs.show()    
        self.top_combo_layout.setStretch(0, 1)
        self.top_combo_layout.setStretch(1, 1)