import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt


class LimitInputDialog(qt.QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setMinimumSize(300, 180)
        self.resize(350, 220)
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
