from settings import settings_handler
from settings import app
import guiTools, gui, re
import win32com.client
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import os, shutil, sys
startUpPath = os.path.join(os.getenv('appdata'), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "moslemTools.lnk")
class Genral(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""         
            QComboBox, QCheckBox {          
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
        """)                           
        main_layout = qt.QVBoxLayout(self)        
        self.ExitDialog = qt.QCheckBox("عرض نافذة الخروج عند الخروج من البرنامج")
        self.ExitDialog.setChecked(p.cbts(settings_handler.get("g", "exitDialog")))
        main_layout.addWidget(self.ExitDialog)        
        self.startup = qt.QCheckBox("بدء تشغيل البرنامج عند بدء تشغيل النظام")
        self.startup.setChecked(self.check_in_startup())
        self.startup.checkStateChanged.connect(self.onStartupChanged)
        main_layout.addWidget(self.startup)               
        reciter_section_layout = qt.QVBoxLayout()
        reciter_section_layout.setContentsMargins(0, 0, 0, 0)
        reciter_section_layout.setSpacing(5)
        reciter_laybol = qt.QLabel("تحديد القارئ لتبويبة القرآن الكريم مكتوب")
        reciter_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        reciter_section_layout.addWidget(reciter_laybol)        
        delete_laybol = qt.QLabel("لحذف القارئ المحدد قم بالضغط على زر الحذف أو زر التطبيقات")
        delete_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        reciter_section_layout.addWidget(delete_laybol)         
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن قارئ")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)         
        reciter_section_layout.addWidget(self.search_bar)
        self.reciter = qt.QComboBox()
        font = qt1.QFont()
        font.setBold(True)         
        self.reciter.addItems(gui.reciters.keys())
        self.reciter.setCurrentIndex(int(settings_handler.get("g", "reciter")))
        self.reciter.setAccessibleName("تحديد القارئ لتبويبة القرآن الكريم مكتوب")
        self.reciter.setAccessibleDescription("لحذف القارئ المحدد قم بالضغط على زر الحذف أو زر التطبيقات")
        self.reciter.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.reciter.customContextMenuRequested.connect(self.onDelete)
        self.reciter.setFont(font)
        qt1.QShortcut("delete", self).activated.connect(self.onDelete)
        reciter_section_layout.addWidget(self.reciter)        
        main_layout.addStretch(1)
        main_layout.addLayout(reciter_section_layout)
        main_layout.addStretch(1)        
        self.tray_note = qt.QLabel("تنبيه هام، يمكنكم إظهار أو إخفاء البرنامج عبر استخدام الاختصار windows+alt+h أو من قائمة علبة النظام system tray")
        self.tray_note.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.tray_note.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.tray_note)        
        self.run_note = qt.QLabel("تنبيه هام، يمكنكم تشغيل البرنامج من قائمة run بكتابة الأمر (mt)")
        self.run_note.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.run_note.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)        
        main_layout.addWidget(self.run_note)        
    def add_to_startup(self):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(startUpPath)
            shortcut.TargetPath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.Description = "a shortcut for opening moslem tools when windows start"
            shortcut.Save()
        except Exception as e:
            print(e)
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر إتمام العملية")    
    def check_in_startup(self):
        try:
            return os.path.exists(startUpPath)
        except Exception as e:
            return False    
    def remove_from_startup(self):
        try:
            os.remove(startUpPath)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر إتمام العملية")    
    def onStartupChanged(self, value):
        if self.check_in_startup():
            self.remove_from_startup()
        else:
            self.add_to_startup()    
    def onDelete(self):
        itemText = self.reciter.currentText()
        if itemText:
            reciterText = gui.quranViewer.reciters[itemText].split("/")[-3]
            path = os.path.join(os.getenv('appdata'), app.appName, "reciters", reciterText)
            if os.path.exists(path):
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا القارئ","نعم","لا")
                if question == 0:
                    shutil.rmtree(path)
                    guiTools.speak("تم الحذف")    
    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches    
    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.reciter.clear()
        result = self.search(search_text, gui.reciters.keys())
        self.reciter.addItems(result)