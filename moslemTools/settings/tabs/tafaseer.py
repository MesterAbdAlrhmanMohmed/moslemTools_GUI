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
            }
            QComboBox, QLineEdit, QLabel {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                font-size: 13px;
            }
        """)
        layout = qt.QVBoxLayout(self)
        self.selectTafaseer = qt.QComboBox()
        self.selectTafaseer.addItems(tafseer.tafaseers.keys())
        self.selectTafaseer.setCurrentText(tafseer.getTafaseerByIndex(settings_handler.get("tafaseer", "tafaseer")))
        self.selectTafaseer.setAccessibleName("اختر تفسير")
        self.selectTafaseer_laybol = qt.QLabel("اختر تفسير")
        self.selectTafaseer_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selectTafaseer_laybol)
        layout.addWidget(self.selectTafaseer)
        self.selectTafaseer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selectTafaseer.customContextMenuRequested.connect(self.onDelete)
        self.selecttranslation = qt.QComboBox()
        self.selecttranslation.addItems(translater.translations.keys())
        self.selecttranslation.setCurrentText(translater.gettranslationByIndex(settings_handler.get("translation", "translation")))
        self.selecttranslation.setAccessibleName("اختر ترجمة للقرآن الكريم")
        self.selectTafaseer.setAccessibleDescription("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")
        self.selecttranslation.setAccessibleDescription("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")
        self.selecttranslation_laybol = qt.QLabel("اختر ترجمة للقرآن الكريم")
        self.selecttranslation_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selecttranslation_laybol)
        layout.addWidget(self.selecttranslation)
        self.selecttranslation.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selecttranslation.customContextMenuRequested.connect(self.onDelete1)
        self.info = qt.QLineEdit()
        self.info.setReadOnly(True)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setText("لحذف أيا من التفاسير والترجمات, قم باستخدام زر التطبيقات")
        layout.addWidget(self.info)
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