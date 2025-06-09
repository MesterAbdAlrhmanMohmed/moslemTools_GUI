import guiTools,pyperclip,winsound,functions
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
class StoryViewer(qt.QDialog):
    def __init__(self,p,text,type:int,category:str,stories:list,index=0):
        super().__init__(p)        
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        self.type=type
        self.stories=stories
        self.category=category
        self.CurrentIndex=list(self.stories.keys()).index(self.category)
        self.resize(1200,600)
        self.text=guiTools.QReadOnlyTextEdit()
        self.text.setText(text)
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.text.setFont(font)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLineEdit()
        self.show_font.setReadOnly(True)
        self.show_font.setAccessibleName("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)        
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self.info=qt.QLineEdit()        
        self.info.setReadOnly(True)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText(self.category)
        layout.addWidget(self.info)
        buttonsLayout=qt.QHBoxLayout()
        self.next=qt.QPushButton("التالي")
        self.next.clicked.connect(self.onNext)
        self.next.setShortcut("alt+right")
        self.next.setAccessibleDescription("alt زائد السهم الأيمن")
        self.next.setStyleSheet("background-color: #0000AA; color: white;")        
        self.previous=qt.QPushButton("السابق")
        self.previous.clicked.connect(self.onPreviouse)
        self.previous.setShortcut("alt+left")
        self.previous.setAccessibleDescription("alt زائد السهم الأيسر")
        self.previous.setStyleSheet("background-color: #0000AA; color: white;")        
        buttonsLayout.addWidget(self.previous)        
        buttonsLayout.addWidget(self.next)
        layout.addLayout(buttonsLayout)
        if not index==0:
            cerser=self.text.textCursor()
            cerser.movePosition(cerser.MoveOperation.Start)
            for i in range(index-1):
                cerser.movePosition(cerser.MoveOperation.Down)
            self.text.setTextCursor(cerser)
    def OnContextMenu(self):
        menu=qt.QMenu("الخيارات",self)
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        text_options=qt.QMenu("خيارات النص",self)
        state,self.nameOfBookmark=functions.bookMarksManager.getStoriesBookmarkName(self.category,self.getCurrentLine())
        if state:
            removeBookmarkAction=qt1.QAction("حذف العلامة المرجعية",self)
            removeBookmarkAction.setShortcut("ctrl+b")
            text_options.addAction(removeBookmarkAction)
            removeBookmarkAction.triggered.connect(self.onRemoveBookmark)
        else:
            addNewBookMark=qt1.QAction("إضافة علامة مرجعية",self)
            addNewBookMark.setShortcut("ctrl+b")
            text_options.addAction(addNewBookMark)
            addNewBookMark.triggered.connect(self.onAddBookMark)
        save=text_options.addAction("حفظ كملف نصي")
        save.setShortcut("ctrl+s")
        save.triggered.connect(self.save_text_as_txt)        
        print=text_options.addAction("طباعة")
        print.setShortcut("ctrl+p")
        print.triggered.connect(self.print_text)
        copy_all=text_options.addAction("نسخ النص كاملا")        
        copy_all.setShortcut("ctrl+a")
        copy_all.triggered.connect(self.copy_text)
        copy_selected_text=text_options.addAction("نسخ النص المحدد")
        copy_selected_text.setShortcut("ctrl+c")
        copy_selected_text.triggered.connect(self.copy_line)
        fontMenu=qt.QMenu("حجم الخط",self)
        incressFontAction=qt1.QAction("تكبير الخط",self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction=qt1.QAction("تصغير الخط",self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)        
        menu.addMenu(text_options)
        menu.addMenu(fontMenu)
        text_options.setFont(boldFont)
        fontMenu.setFont(boldFont)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def print_text(self):
        try:
            printer=QPrinter()
            dialog=QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.text.print(printer)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def save_text_as_txt(self):
        try:
            file_dialog=qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name=file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    text = self.text.toPlainText()
                    file.write(text)                 
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
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
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=self.text.font()
        font.setPointSize(self.font_size)
        self.text.setCurrentFont(font)        
        self.text.setTextCursor(cursor)
    def copy_line(self):
        try:
            cursor=self.text.textCursor()
            if cursor.hasSelection():
                selected_text=cursor.selectedText()
                pyperclip.copy(selected_text)                
                winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)            
            winsound.Beep(1000,100)
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))
    def getCurrentLine(self):
        cerser=self.text.textCursor()
        return cerser.blockNumber()
    def onAddBookMark(self):
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            functions.bookMarksManager.addNewStoriesBookMark(self.type,self.category,self.getCurrentLine(),name)
    def onNext(self):
        if self.CurrentIndex==len(self.stories)-1:
            self.CurrentIndex=0
        else:
            self.CurrentIndex+=1
        self.category=list(self.stories.keys())[self.CurrentIndex]
        self.text.setText(self.stories[self.category])
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(self.category))
        self.info.setText(self.category)
    def onPreviouse(self):
        if self.CurrentIndex==0:
            self.CurrentIndex=len(self.stories)-1
        else:
            self.CurrentIndex-=1
        self.category=list(self.stories.keys())[self.CurrentIndex]
        self.text.setText(self.stories[self.category])
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(self.category))
        self.info.setText(self.category)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeStoriesBookMark(self.nameOfBookmark)
            winsound.Beep(1000,100)
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state,self.nameOfBookmark=functions.bookMarksManager.getStoriesBookmarkName(self.category,self.getCurrentLine())
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()