from functions import tafseer, translater
from settings import settings_handler, app
import os, guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class TafaseerSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""            
            QComboBox, QLineEdit, QLabel {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)                
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)                
        group_box = qt.QGroupBox()
        group_layout = qt.QVBoxLayout(group_box)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(12, 15, 12, 15)                
        tafaseer_layout = qt.QHBoxLayout()
        tafaseer_layout.setSpacing(10)        
        self.selectTafaseer_laybol = qt.QLabel("اختر تفسير للقرآن الكريم")
        self.selectTafaseer = qt.QComboBox()
        self.selectTafaseer.addItems(tafseer.tafaseers.keys())
        self.selectTafaseer.setCurrentText(tafseer.getTafaseerByIndex(settings_handler.get("tafaseer", "tafaseer")))
        self.selectTafaseer.setAccessibleName("اختر تفسير للقرآن الكريم")
        tafaseer_layout.addWidget(self.selectTafaseer)
        tafaseer_layout.addWidget(self.selectTafaseer_laybol)
        tafaseer_layout.addStretch()
        group_layout.addLayout(tafaseer_layout)                
        translation_layout = qt.QHBoxLayout()
        translation_layout.setSpacing(10)        
        self.selecttranslation_laybol = qt.QLabel("اختر ترجمة للقرآن الكريم")
        self.selecttranslation = qt.QComboBox()
        self.selecttranslation.addItems(translater.translations.keys())
        self.selecttranslation.setCurrentText(translater.gettranslationByIndex(settings_handler.get("translation", "translation")))
        self.selecttranslation.setAccessibleName("اختر ترجمة للقرآن الكريم")        
        translation_layout.addWidget(self.selecttranslation)
        translation_layout.addWidget(self.selecttranslation_laybol)
        translation_layout.addStretch()
        group_layout.addLayout(translation_layout)                
        self.selectTafaseer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selectTafaseer.customContextMenuRequested.connect(self.onDelete)
        self.selectTafaseer.setAccessibleDescription("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")        
        self.selecttranslation.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selecttranslation.customContextMenuRequested.connect(self.onDelete1)
        self.selecttranslation.setAccessibleDescription("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")        
        main_layout.addWidget(group_box)
        main_layout.addStretch()                
        self.info = qt.QLabel("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.info)                
        self.selectTafaseer.currentTextChanged.connect(
            lambda text: settings_handler.set("tafaseer", "tafaseer", str(list(tafseer.tafaseers.keys()).index(text)))
        )
        self.selecttranslation.currentTextChanged.connect(
            lambda text: settings_handler.set("translation", "translation", str(list(translater.translations.keys()).index(text)))
        )    
    def onDelete1(self):
        selectedItem = self.selecttranslation.currentText()
        if selectedItem:
            itemText = selectedItem
            if itemText == "English by Talal Itani":
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا يمكنك حذف هذا الكتاب ")
            else:
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا الكتاب","نعم","لا")
                if question == 0:
                    name = translater.translations[itemText]
                    os.remove(os.path.join(os.getenv('appdata'), app.appName, "Quran Translations", name))
                    translater.settranslation()
                    self.selecttranslation.clear()
                    self.selecttranslation.addItems(translater.translations.keys())
                    guiTools.speak("تم الحذف")    
    def onDelete(self):
        selectedItem = self.selectTafaseer.currentText()
        if selectedItem:
            itemText = selectedItem
            if itemText == "الميصر":
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا يمكنك حذف هذا الكتاب ")
            else:
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا الكتاب","نعم","لا")
                if question == 0:
                    name = tafseer.tafaseers[itemText]
                    os.remove(os.path.join(os.getenv('appdata'), app.appName, "tafaseer", name))
                    tafseer.setTafaseer()
                    self.selectTafaseer.clear()
                    self.selectTafaseer.addItems(tafseer.tafaseers.keys())
                    guiTools.speak("تم الحذف")