import guiTools, os, json
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
path = os.path.join(os.getenv('appdata'), app.appName, "athkar.json")
if not os.path.exists(path):
    with open(path, "w", encoding="utf-8") as file:
        file.write("[]")
class sibha(qt.QWidget):
    def __init__(self):
        super().__init__()
        qt1.QShortcut("ctrl+s", self).activated.connect(self.speak_number)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.speak_current_thecre)
        with open(path, "r", encoding="utf-8") as file:
            self.externalAthkar = json.load(file)
        self.athkar_laybol = qt.QLabel("قم بتحديد الذكر")
        self.athkar_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.athkar = qt.QComboBox()
        self.athkar.setAccessibleDescription("control plus c لنطق الذكر المحدد")
        self.athkar.setAccessibleName("قم بتحديد الذكر")
        self.athkar.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkar.customContextMenuRequested.connect(self.onDelete)
        qt1.QShortcut("delete", self).activated.connect(self.onDelete)
        self.athkar.addItems([
            "سبحان الله", "الحمد لله ", "لا إلاه إلا الله", "الله أكبر", "ربي اغفر لي",
            "أستغفر الله", "لا حول ولا قوة إلا بالله", "اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ العَفْوَ فَاعْفُ عَنِّي",
            "اللهم صل وسلم وبارك على سيدنا محمد", "سبحان الله وبحمده سبحان الله العظيم",
            "اللَّهُمَّ ٱغْفِرْ لِي ذَنْبِي كُلَّهُ، دِقَّهُ وَجِلَّهُ، عَلَانِيَتَهُ وَسِرَّهُ، وَأَوَّلَهُ وَآخِرَهُ",
            "الله أكبر كبيرا والحمد لله كثيرا وسبحان الله بُكرةً وأصيلا",
            "سبحان الله والحمد لله ولا إلاه إلا الله والله أكبر",
            "أستغفر الله الذي لا إلاه إلا هو الحي القيوم وأتوب إليه",
            "لا إلاه إلا أنت سبحانك إني كنت من الظالمين",
            "سبحان الله وبحمده عدد خلقه ورضى نفسه وزنة عرشه ومداد كلماته",
            "لا إلاه إلا الله وحده لا شريك لهُ ، لهُ الملك ، ولهُ الحمدُ ، وهو على كل شيء قدير"
        ])
        self.athkar.addItems(self.externalAthkar)
        self.numbers = qt.QLabel("0")
        self.numbers.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.numbers.setAccessibleDescription("عدد التسبيحات")
        self.numbers.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.numbers.setStyleSheet("font-size:300px;")
        self.reset = qt.QPushButton("إعادة تعين")
        self.reset.setAccessibleDescription("control plus R")
        self.reset.setDefault(True)
        self.reset.setShortcut("ctrl+r")
        self.reset.clicked.connect(self.reset_count)
        self.reset.setObjectName("resetButton")
        self.add = qt.QPushButton("التسبيح")
        self.add.setAccessibleDescription("control plus equals")
        self.add.setShortcut("ctrl+=")
        self.add.setDefault(True)
        self.add.clicked.connect(self.increment_count)
        self.add.setObjectName("addButton")
        self.add_thecr = qt.QPushButton("إضافة ذكر")
        self.add_thecr.setDefault(True)
        self.add_thecr.setAccessibleDescription("control plus a")
        self.add_thecr.setShortcut("ctrl+a")
        self.add_thecr.setMaximumHeight(30)
        self.add_thecr.setMaximumWidth(160)
        self.add_thecr.clicked.connect(self.onAddThakar)
        self.add_thecr.setStyleSheet("background-color: green; color: white;")
        self.line_of_thecr = qt.QLineEdit()
        self.line_of_thecr.textChanged.connect(self.onLineTextChanged)
        self.line_of_thecr.setPlaceholderText("أكتب الذكر")
        self.line_of_thecr.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.done_thecr = qt.QPushButton("إضافة الذكر")
        self.done_thecr.setDefault(True)
        self.done_thecr.clicked.connect(self.onAddThkarCompeleted)
        self.done_thecr.setStyleSheet("background-color: green; color: white;")
        self.cancel_add = qt.QPushButton("إلغاء")
        self.cancel_add.setDefault(True)
        self.cancel_add.setShortcut("shift+c")
        self.cancel_add.setAccessibleDescription("shift plus c")
        self.cancel_add.clicked.connect(self.cansel_add_thecr)
        self.cancel_add.setStyleSheet("background-color: #8B0000; color: white;")
        self.line_of_thecr.setVisible(False)
        self.done_thecr.setVisible(False)
        self.cancel_add.setVisible(False)
        main_layout = qt.QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        layout1 = qt.QVBoxLayout()
        layout1.addWidget(self.athkar_laybol)
        layout1.addWidget(self.athkar)
        layout0 = qt.QHBoxLayout()
        layout0.addLayout(layout1)
        layout0.addWidget(self.add_thecr)
        layout2 = qt.QHBoxLayout()
        layout2.addWidget(self.cancel_add)
        layout2.addWidget(self.line_of_thecr)
        layout2.addWidget(self.done_thecr)
        btn_layout = qt.QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addWidget(self.reset)
        btn_layout.addWidget(self.add)
        main_layout.addLayout(layout0)
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addWidget(self.numbers)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QPushButton#resetButton {
                background-color: #8B0000;
                color: white;
                min-height: 40px;
                font-size: 16px;
            }
            QPushButton#addButton {
                background-color: green;
                color: white;
                min-height: 40px;
                font-size: 16px;
            }
            QComboBox, QLineEdit {
                min-height: 40px;
                font-size: 16px;
            }
            QLabel {
                font-size: 16px;
            }
        """)
    def cansel_add_thecr(self):
        self.add_thecr.setVisible(True)
        self.line_of_thecr.setVisible(False)
        self.done_thecr.setVisible(False)
        self.cancel_add.setVisible(False)
        self.line_of_thecr.clear()
    def reset_count(self):
        self.numbers.setText("0")
        guiTools.speak("تم إعادة التعيين الى 0")
    def increment_count(self):
        current_count = int(self.numbers.text())
        current_count += 1
        self.numbers.setText(str(current_count))
        guiTools.speak(str(current_count))
    def speak_number(self):
        guiTools.speak(self.numbers.text())
    def speak_current_thecre(self):
        guiTools.speak(self.athkar.currentText())
    def onAddThakar(self):
        self.add_thecr.setVisible(False)
        self.line_of_thecr.setVisible(True)
        self.done_thecr.setVisible(True)
        self.cancel_add.setVisible(True)
        self.done_thecr.setDisabled(True)
        self.line_of_thecr.setFocus()
    def onAddThkarCompeleted(self):
        thkar = self.line_of_thecr.text()
        self.line_of_thecr.setText("")
        self.externalAthkar.append(thkar)
        self.athkar.addItem(thkar)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.externalAthkar, file, ensure_ascii=False, indent=4)
        self.add_thecr.setVisible(True)
        self.line_of_thecr.setVisible(False)
        self.done_thecr.setVisible(False)
        self.cancel_add.setVisible(False)
        self.athkar.setFocus()
    def onLineTextChanged(self, text):
        self.done_thecr.setDisabled(text == "")
    def onDelete(self):
        itemText = self.athkar.currentText()
        if itemText not in self.externalAthkar:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذا الذكر")
        else:
            question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا الذكر", "نعم", "لا")
            if question == 0:
                self.externalAthkar.remove(itemText)
                self.athkar.removeItem(self.athkar.currentIndex())
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(self.externalAthkar, file, ensure_ascii=False, indent=4)
                guiTools.speak("تم الحذف")