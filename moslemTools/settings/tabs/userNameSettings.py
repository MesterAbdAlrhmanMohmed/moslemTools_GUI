import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler

class UserNameSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)
        self.use_name_checkbox = qt.QCheckBox("استخدام اسمك في التذكير بالمناسبات وصيام السنن")
        self.use_name_checkbox.setFont(font)
        self.use_name_checkbox.setChecked(settings_handler.get("g", "use_name_in_occasions") != "False")
        self.use_name_checkbox.stateChanged.connect(self.on_use_name_toggled)
        layout.addWidget(self.use_name_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.name_options_widget = qt.QWidget()
        options_layout = qt.QVBoxLayout(self.name_options_widget)
        options_layout.setSpacing(10)
        options_layout.setContentsMargins(20, 5, 5, 5)
        saved_name_type = settings_handler.get("g", "name_type") or "custom_name"
        self.cb_os_user = qt.QCheckBox("استخدام اسم المستخدم الخاص بالجهاز")
        self.cb_os_user.setFont(font)
        self.cb_os_user.setChecked(saved_name_type == "os_username")
        self.cb_os_user.clicked.connect(lambda checked: self.on_name_cb_clicked(self.cb_os_user, checked))
        options_layout.addWidget(self.cb_os_user, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_personal_user = qt.QCheckBox("استخدام اسمك الشخصي")
        self.cb_personal_user.setFont(font)
        self.cb_personal_user.setChecked(saved_name_type == "personal_name")
        self.cb_personal_user.clicked.connect(lambda checked: self.on_name_cb_clicked(self.cb_personal_user, checked))
        options_layout.addWidget(self.cb_personal_user, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_custom_user = qt.QCheckBox("كتابة اسم مخصص")
        self.cb_custom_user.setFont(font)
        self.cb_custom_user.setChecked(saved_name_type == "custom_name")
        self.cb_custom_user.clicked.connect(lambda checked: self.on_name_cb_clicked(self.cb_custom_user, checked))
        options_layout.addWidget(self.cb_custom_user, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.custom_name_input = qt.QLineEdit()
        self.custom_name_input.setFont(font)
        self.custom_name_input.setPlaceholderText("اسمك في التذكير بالمناسبات")
        self.custom_name_input.setText(settings_handler.get("g", "user_name"))
        self.custom_name_input.setAccessibleName("اسمك في التذكير بالمناسبات")
        self.custom_name_input.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        options_layout.addWidget(self.custom_name_input, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_options_widget, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        self.on_use_name_toggled()
        self.custom_name_input.setVisible(self.cb_custom_user.isChecked())

    def on_use_name_toggled(self):
        self.name_options_widget.setVisible(self.use_name_checkbox.isChecked())

    def on_name_cb_clicked(self, target_cb, checked):
        if not checked:
            target_cb.setChecked(True)
            return
        for cb in [self.cb_os_user, self.cb_personal_user, self.cb_custom_user]:
            if cb != target_cb:
                cb.setChecked(False)
        self.custom_name_input.setVisible(self.cb_custom_user.isChecked())

    def get_selected_name_type(self):
        if self.cb_os_user.isChecked():
            return "os_username"
        elif self.cb_personal_user.isChecked():
            return "personal_name"
        return "custom_name"
