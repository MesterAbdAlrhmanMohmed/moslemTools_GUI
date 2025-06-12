import guiTools,pyperclip,winsound,gettext,json,functions,settings,os
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
class hadeeth_viewer(qt.QDialog):
    def __init__(self,p,book_name,index:int=0):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        try:
            with open(os.path.join(os.getenv('appdata'),settings.app.appName,"ahadeeth",book_name),"r",encoding="utf-8") as f:
                self.data=json.load(f)    
            self.index=index
            self.bookName=book_name
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر فتح الملف ")
            self.close()
        qt1.QShortcut("ctrl+c", self).activated.connect(self.copy_line)
        qt1.QShortcut("ctrl+a", self).activated.connect(self.copy_text)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+s", self).activated.connect(self.save_text_as_txt)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.print_text)                        
        qt1.QShortcut("alt+right",self).activated.connect(self.next_hadeeth)
        qt1.QShortcut("alt+left",self).activated.connect(self.previous_hadeeth)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.go_to_hadeeth)
        qt1.QShortcut("ctrl+b",self).activated.connect(self.onAddOrRemoveBookmark)
        self.resize(1200,600)
        self.text=guiTools.QReadOnlyTextEdit()        
        self.text.setText(self.data[self.index])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.font_size=12
        font=self.font()
        font.setBold(True)
        font.setPointSize(self.font_size)
        self.text.setFont(font)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")        
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.N_hadeeth=qt.QPushButton("الحديث التالي")
        self.N_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_hadeeth.setAccessibleDescription("alt زائد السهم الأيمن")
        self.N_hadeeth.clicked.connect(self.next_hadeeth)
        self.P_hadeeth=qt.QPushButton("الحديث السابق")
        self.P_hadeeth.setAccessibleDescription("alt زائد السهم الأيسر")
        self.P_hadeeth.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_hadeeth.clicked.connect(self.previous_hadeeth)
        self.hadeeth_number_laybol=qt.QLabel("رقم الحديث")
        self.hadeeth_number_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_hadeeth_number=qt.QLabel()
        self.show_hadeeth_number.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_hadeeth_number.setAccessibleDescription("رقم الحديث")
        self.show_hadeeth_number.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_hadeeth_number.setText(str(self.index+1))
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)        
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.hadeeth_number_laybol)
        layout.addWidget(self.show_hadeeth_number)
        layout1=qt.QHBoxLayout()        
        layout1.addWidget(self.P_hadeeth)
        layout1.addWidget(self.N_hadeeth)
        layout.addLayout(layout1)
    def next_hadeeth(self):
        if self.index == len(self.data)-1:
            self.index=0
        else:
            self.index+=1
        self.text.setText(self.data[self.index])
        guiTools.speak(str(self.index+1))
        self.show_hadeeth_number.setText(str(self.index+1))
        winsound.PlaySound("data/sounds/next_page.wav",1)
    def previous_hadeeth(self):
        if self.index == 0:
            self.index=len(self.data)-1
        else:
            self.index-=1
        self.text.setText(self.data[self.index])
        guiTools.speak(str(self.index+1))
        self.show_hadeeth_number.setText(str(self.index+1))
        winsound.PlaySound("data/sounds/previous_page.wav",1)
    def go_to_hadeeth(self):        
        hadeeth,OK=guiTools.QInputDialog.getInt(self,"الذهاب إلى حديث","أكتب رقم الحديث",self.index+1,1,len(self.data))
        if OK:                    
            self.index=hadeeth-1
            self.text.setText(self.data[self.index])
            self.show_hadeeth_number.setText(str(self.index+1))
    def OnContextMenu(self):
        menu=qt.QMenu("الخيارات", self)
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        menu.setAccessibleName("الخيارات")
        menu.setFocus()
        hadeeth_menu=qt.QMenu("خيارات الحديث", self)
        next_action=hadeeth_menu.addAction("الحديث التالي")
        next_action.setShortcut("alt+right")
        next_action.triggered.connect(self.next_hadeeth)
        previous_action=hadeeth_menu.addAction("الحديث السابق")
        previous_action.setShortcut("alt+left")
        previous_action.triggered.connect(self.previous_hadeeth)
        go_action=hadeeth_menu.addAction("الذهاب إلى حديث")
        go_action.setShortcut("ctrl+g")
        go_action.triggered.connect(self.go_to_hadeeth)
        state,self.nameOfBookmark=functions.bookMarksManager.getAhdeethBookmarkName(self.bookName,self.index)
        if state:
            removeBookmarkAction=qt1.QAction("حذف العلامة المرجعية",self)
            removeBookmarkAction.setShortcut("ctrl+b")
            hadeeth_menu.addAction(removeBookmarkAction)
            removeBookmarkAction.triggered.connect(self.onRemoveBookmark)
        else:
            addBookMarkAction=qt1.QAction("إضافة علامة مرجعية",self)
            addBookMarkAction.setShortcut("ctrl+b")
            hadeeth_menu.addAction(addBookMarkAction)
            addBookMarkAction.triggered.connect(self.onAddBookMark)
        menu.addMenu(hadeeth_menu)
        text_options_menu=qt.QMenu("خيارات النص", self)
        save_action=text_options_menu.addAction("حفظ كملف نصي")
        save_action.setShortcut("ctrl+s")
        save_action.triggered.connect(self.save_text_as_txt)
        text_options_menu.setDefaultAction(save_action)
        print_action=text_options_menu.addAction("طباعة")
        print_action.setShortcut("ctrl+p")
        print_action.triggered.connect(self.print_text)
        copy_all_action=text_options_menu.addAction("نسخ النص كاملاً")
        copy_all_action.setShortcut("ctrl+a")
        copy_all_action.triggered.connect(self.copy_text)
        copy_selected_action=text_options_menu.addAction("نسخ النص المحدد")
        copy_selected_action.setShortcut("ctrl+c")
        copy_selected_action.triggered.connect(self.copy_line)    
        font_menu=qt.QMenu("حجم الخط", self)
        increase_font_action=qt1.QAction("تكبير الخط", self)
        increase_font_action.setShortcut("ctrl+=")
        font_menu.addAction(increase_font_action)
        increase_font_action.triggered.connect(self.increase_font_size)
        decrease_font_action=qt1.QAction("تصغير الخط", self)
        decrease_font_action.setShortcut("ctrl+-")
        font_menu.addAction(decrease_font_action)
        decrease_font_action.triggered.connect(self.decrease_font_size)            
        menu.addMenu(text_options_menu)
        menu.addMenu(font_menu)
        text_options_menu.setFont(boldFont)
        font_menu.setFont(boldFont)
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
    def onAddBookMark(self):
        name,OK=guiTools.QInputDialog.getText(self,"إضافة علامة مرجعية","أكتب أسم للعلامة المرجعية")
        if OK:
            functions.bookMarksManager.addNewHadeethBookMark(self.bookName,self.index,name)
    def onRemoveBookmark(self):
        try:
            functions.bookMarksManager.removeAhadeethBookMark(self.nameOfBookmark)
            winsound.Beep(1000,100)
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر حذف العلامة المرجعية")
    def onAddOrRemoveBookmark(self):
        state,self.nameOfBookmark=functions.bookMarksManager.getAhdeethBookmarkName(self.bookName,self.index)
        if state:
            self.onRemoveBookmark()
        else:
            self.onAddBookMark()