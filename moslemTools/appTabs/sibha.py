import guiTools, os, json, winsound
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
class LimitInputDialog(qt.QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.resize(350, 200)
        self.setWindowTitle(title)
        layout = qt.QVBoxLayout(self)
        self.name_label = qt.QLabel("أدخل اسم الحد")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input = qt.QLineEdit()
        self.name_input.setAccessibleName("أدخل اسم الحد")
        self.name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input.textChanged.connect(self.validate_inputs)
        self.value_label = qt.QLabel("أدخل عدد التسبيحات")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_input = qt.QSpinBox()
        self.value_input.setRange(1, 1000000)
        self.value_input.setValue(1)
        self.value_input.setAccessibleName("أدخل عدد التسبيحات")
        self.value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_input.valueChanged.connect(self.validate_inputs)
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.value_label)
        layout.addWidget(self.value_input)
        self.OKBTN = guiTools.QPushButton("موافق")
        self.OKBTN.setDisabled(True)
        self.OKBTN.clicked.connect(self.accept)
        self.OKBTN.setStyleSheet("QPushButton {background-color: black; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px;}")
        self.cancelBTN = guiTools.QPushButton("إلغاء")
        self.cancelBTN.clicked.connect(self.reject)
        self.cancelBTN.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px;}")
        buttonsLayout = qt.QHBoxLayout()
        buttonsLayout.addWidget(self.OKBTN)
        buttonsLayout.addWidget(self.cancelBTN)
        wrapper = qt.QHBoxLayout()
        wrapper.addLayout(buttonsLayout)
        wrapper.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(wrapper)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
        self.name_input.setFocus()
    def validate_inputs(self):
        name_valid = bool(self.name_input.text().strip())
        value_valid = self.value_input.value() > 0
        is_valid = name_valid and value_valid
        self.OKBTN.setDisabled(not is_valid)
        if is_valid:
            self.OKBTN.setStyleSheet("QPushButton {background-color: #008000; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px;}")
        else:
            self.OKBTN.setStyleSheet("QPushButton {background-color: black; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px;}")
    def closeEvent(self, event):
        self.reject()
        event.accept()
    @staticmethod
    def getLimitData(parent):
        dlg = LimitInputDialog(parent, "إضافة حد أقصى جديد")
        result = dlg.exec()
        if result == qt.QDialog.DialogCode.Accepted:
            return dlg.name_input.text(), dlg.value_input.value(), True
        else:
            return "", 0, False
path = os.path.join(os.getenv('appdata'), app.appName, "athkar.json")
limits_path = os.path.join(os.getenv('appdata'), app.appName, "limits.json")
if not os.path.exists(path):
    with open(path, "w", encoding="utf-8") as file:
        file.write("[]")
if not os.path.exists(limits_path):
    with open(limits_path, "w", encoding="utf-8") as file:
        file.write('{"limits": {}, "active": null}')
class sibha(qt.QWidget):
    def __init__(self):
        super().__init__()
        qt1.QShortcut("ctrl+s", self).activated.connect(self.speak_number)
        qt1.QShortcut("ctrl+c", self).activated.connect(self.speak_current_thecre)
        with open(path, "r", encoding="utf-8") as file:
            self.externalAthkar = json.load(file)
        with open(limits_path, "r", encoding="utf-8") as file:
            self.limits_data = json.load(file)
        self.athkar_laybol = qt.QLabel("قم بتحديد الذكر")
        self.athkar_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.athkar = qt.QComboBox()
        self.athkar.setAccessibleName("قم بتحديد الذكر")
        self.athkar.setAccessibleDescription("control plus c لنطق الذكر المحدد في أي مكان")
        self.athkar.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.athkar.customContextMenuRequested.connect(self.show_athkar_context_menu)
        qt1.QShortcut("delete", self).activated.connect(self.onDelete)
        qt1.QShortcut("shift+delete", self).activated.connect(self.onDeleteAllCustom)
        self.athkar.addItems([
            "سُبْحَانَ اللَّهِ", "الْحَمْدُ لِلَّهِ", "لَا إِلَهَ إِلَّا لَّهُ", "اللَّهُ أَكْبَرُ", "رَبِّ اغْفِرْ لِي",
            "أَسْتَغْفِرُ اللَّهَ", "لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ", "اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي",
            "اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ عَلَى سَيِّدِنَا مُحَمَّدٍ", "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ سُبْحَانَ اللَّهِ الْعَظِيمِ",
            "اللَّهُمَّ اغْفِرْ لِي ذَنْبِي كُلَّهُ، دِقَّهُ وَجِلَّهُ، عَلَانِيَتَهُ وَسِرَّهُ، وَأَوَّلَهُ وَآخِرَهُ",
            "اللَّهُ أَكْبَرُ كَبِيرًا وَالْحَمْدُ لِلَّهِ كَثِيرًا وَسُبْحَانَ اللَّهِ بُكْرَةً وَأَصِيلًا",
            "سُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ وَلَا إِلَهَ إِلَّا اللَّهُ وَاللَّهُ أَكْبَرُ",
            "أَسْتَغْفِرُ اللَّهَ الَّذِي لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ",
            "لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
            "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ عَدَدَ خَلْقِهِ وَرِضَا نَفْسِهِ وَزِنَةَ عَرْشِهِ وَمِدَادَ كَلِمَاتِهِ",
            "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ"
        ])
        self.athkar.addItems(self.externalAthkar)
        self.numbers = qt.QLabel("0")
        self.numbers.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.numbers.setAccessibleDescription("عدد التسبيحات. لنطق عدد التسبيحات في أي مكان نستخدم الاختصار control plus s")
        self.numbers.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.numbers.setStyleSheet("font-size:200px;")
        self.reset = guiTools.QPushButton("إعادة تعين")
        self.reset.setAccessibleDescription("control plus r")
        self.reset.setShortcut("ctrl+r")
        self.reset.clicked.connect(self.reset_count)
        self.reset.setObjectName("resetButton")
        self.add = guiTools.QPushButton("التسبيح")
        self.add.setAccessibleDescription("control plus equals")
        self.add.setShortcut("ctrl+=")
        self.add.clicked.connect(self.increment_count)
        self.add.setObjectName("addButton")
        self.minus = guiTools.QPushButton("إنقاص")
        self.minus.setAccessibleDescription("control plus minus")
        self.minus.setShortcut("ctrl+-")
        self.minus.clicked.connect(self.decrement_count)
        self.minus.setObjectName("minusButton")
        self.add_thecr = guiTools.QPushButton("إضافة ذكر")
        self.add_thecr.setAccessibleDescription("control plus a")
        self.add_thecr.setShortcut("ctrl+a")
        self.add_thecr.setMaximumHeight(30)
        self.add_thecr.setMaximumWidth(160)
        self.add_thecr.clicked.connect(self.onAddThakar)
        self.add_thecr.setStyleSheet("background-color: #008000; color: white;")
        self.limit_button = guiTools.QPushButton("تعيين حد أقصى لعدد التسبيحات")
        self.limit_button.setMaximumHeight(30)
        self.limit_button.setMaximumWidth(200)
        self.limit_button.clicked.connect(self.on_limit_button_clicked)
        self.limit_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.limit_button.setShortcut("ctrl+shift+s")
        self.limit_button.setAccessibleDescription("control plus shift plus s")
        self.update_limit_button_text()
        self.line_of_thecr = qt.QLineEdit()
        self.line_of_thecr.setAccessibleName("أكتب الذكر")
        self.line_of_thecr.textChanged.connect(self.onLineTextChanged)
        self.line_of_thecr.setPlaceholderText("أكتب الذكر")
        self.line_of_thecr.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.line_of_thecr.returnPressed.connect(self.onAddThkarCompeleted)
        self.done_thecr = guiTools.QPushButton("إضافة الذكر")
        self.done_thecr.clicked.connect(self.onAddThkarCompeleted)
        self.done_thecr.setStyleSheet("background-color: #008000; color: white;")
        self.cancel_add = guiTools.QPushButton("إلغاء")
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
        layout0.addWidget(self.limit_button)
        layout2 = qt.QHBoxLayout()
        layout2.addWidget(self.cancel_add)
        layout2.addWidget(self.line_of_thecr)
        layout2.addWidget(self.done_thecr)
        btn_layout = qt.QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addWidget(self.reset)
        btn_layout.addWidget(self.add)
        btn_layout.addWidget(self.minus)
        main_layout.addLayout(layout0)
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addWidget(self.numbers)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setStyleSheet("QPushButton#resetButton {background-color: #8B0000; color: white; min-height: 40px; font-size: 16px;} QPushButton#addButton {background-color: #008000; color: white; min-height: 40px; font-size: 16px;} QPushButton#minusButton {background-color: #0000AA; color: white; min-height: 40px; font-size: 16px;} QComboBox, QLineEdit, QSpinBox {min-height: 40px; font-size: 16px;} QLabel {font-size: 16px;}")
    def show_athkar_context_menu(self, pos):
        menu = qt.QMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        delete_action = menu.addAction("حذف الذكر المحدد")
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.onDelete)
        delete_all_action = menu.addAction("حذف جميع الأذكار المضافة")
        delete_all_action.setShortcut("Shift+Delete")
        delete_all_action.triggered.connect(self.onDeleteAllCustom)
        menu.exec(qt1.QCursor.pos())
    def update_limit_button_text(self):
        if not self.limits_data["limits"]:
            self.limit_button.setText("تعيين حد أقصى لعدد التسبيحات")
        else:
            self.limit_button.setText("فتح قائمة الحدود")
    def on_limit_button_clicked(self):
        if not self.limits_data["limits"]:
            self.add_new_limit()
        else:
            self.show_limits_menu()
    def add_new_limit(self):
        name, value, ok = LimitInputDialog.getLimitData(self)
        if ok and name:
            self.limits_data["limits"][name] = value
            self.save_limits()
            self.update_limit_button_text()
            guiTools.speak(f"تم إضافة الحد الأقصى {name} بقيمة {value}")
    def show_limits_menu(self):
        menu = qt.QMenu(self)
        font=qt1.QFont()
        font.setBold(True)
        for name, value in self.limits_data["limits"].items():
            limit_action = menu.addAction(f"{name} ({value})")
            limit_action.triggered.connect(lambda checked, n=name: self.on_limit_selected(n))
        menu.addSeparator()
        add_action = menu.addAction("إضافة حد")
        add_action.triggered.connect(self.add_new_limit)
        delete_all_limits_action = menu.addAction("حذف كل الحدود")
        delete_all_limits_action.triggered.connect(self.onDeleteAllLimits)
        menu.setFont(font)
        menu.exec(qt1.QCursor.pos())
    def on_limit_selected(self, name):
        menu = qt.QMenu(self)
        font=qt1.QFont()
        font.setBold(True)
        if self.limits_data["active"] == name:
            deactivate_action = menu.addAction("إلغاء التعيين")
            deactivate_action.triggered.connect(lambda: self.deactivate_limit(name))
        else:
            set_action = menu.addAction("تعيين")
            set_action.triggered.connect(lambda: self.set_active_limit(name))
        delete_action = menu.addAction("حذف")
        delete_action.triggered.connect(lambda: self.delete_limit(name))
        menu.setFont(font)
        menu.exec(qt1.QCursor.pos())
    def deactivate_limit(self, name):
        self.limits_data["active"] = None
        self.save_limits()
        guiTools.speak(f"تم إلغاء تعيين الحد الأقصى {name}")
    def set_active_limit(self, name):
        self.limits_data["active"] = name
        self.save_limits()
        guiTools.speak(f"تم تعيين الحد الأقصى إلى {name} بقيمة {self.limits_data['limits'][name]}")
    def delete_limit(self, name):
        question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف الحد الأقصى {name}؟", "نعم", "لا")
        if question == 0:
            del self.limits_data["limits"][name]
            if self.limits_data["active"] == name:
                self.limits_data["active"] = None
            self.save_limits()
            self.update_limit_button_text()
            guiTools.speak(f"تم حذف الحد الأقصى {name}")
    def onDeleteAllLimits(self):
        if not self.limits_data["limits"]:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا توجد حدود مضافة لحذفها")
            return
        question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل تريد حذف جميع الحدود المضافة؟", "نعم", "لا")
        if question == 0:
            self.limits_data["limits"] = {}
            self.limits_data["active"] = None
            self.save_limits()
            self.update_limit_button_text()
            guiTools.speak("تم حذف جميع الحدود المضافة")
    def save_limits(self):
        with open(limits_path, "w", encoding="utf-8") as file:
            json.dump(self.limits_data, file, ensure_ascii=False, indent=4)
    def check_limit(self):
        if self.limits_data["active"]:
            active_limit = self.limits_data["limits"][self.limits_data["active"]]
            current_count = int(self.numbers.text())
            if current_count >= active_limit:
                winsound.Beep(750, 300)
                guiTools.speak(f"لقد وصلت إلى الحد الأقصى {active_limit}")
                return True
        return False
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
        if self.check_limit():
            return
        current_count = int(self.numbers.text())
        current_count += 1
        self.numbers.setText(str(current_count))
        guiTools.speak(str(current_count))
    def decrement_count(self):
        current_count = int(self.numbers.text())
        if current_count > 0:
            current_count -= 1
            self.numbers.setText(str(current_count))
            guiTools.speak(str(current_count))
        else:
            guiTools.speak("لا يمكن الإنقاص أكثر من صفر")
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
        thkar = self.line_of_thecr.text().strip()
        if not thkar:
            return
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
        self.done_thecr.setDisabled(text.strip() == "")
    def onDelete(self):
        itemText = self.athkar.currentText()
        if itemText not in self.externalAthkar:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذا الذكر")
        else:
            question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل تريد حذف هذا الذكر", "نعم", "لا")
            if question == 0:
                self.externalAthkar.remove(itemText)
                self.athkar.removeItem(self.athkar.currentIndex())
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(self.externalAthkar, file, ensure_ascii=False, indent=4)
                guiTools.speak("تم الحذف")
    def onDeleteAllCustom(self):
        if not self.externalAthkar:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا توجد أذكار مضافة لحذفها")
            return
        question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل تريد حذف كل الأذكار التي قمت بإضافتها؟", "نعم", "لا")
        if question == 0:
            for text in self.externalAthkar:
                index = self.athkar.findText(text)
                if index != -1:
                    self.athkar.removeItem(index)
            self.externalAthkar = []
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.externalAthkar, file, ensure_ascii=False, indent=4)
            guiTools.speak("تم حذف جميع الأذكار المضافة")