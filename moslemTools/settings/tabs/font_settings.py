import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler

class FontSettings(qt.QWidget):
    VIEWERS = [
        ("quranViewer", "عارض القرآن الكريم"),
        ("quranPlayer", "مشغل القرآن الكريم"),
        ("hadeethViewer", "عارض الأحاديث النبوية"),
        ("tafaseerViewer", "عارض التفسير"),
        ("translationViewer", "عارض ترجمة القرآن"),
        ("storyViewer", "عارض قصص الأنبياء"),
        ("islamicTopicViewer", "عارض الموضوعات الإسلامية"),
        ("bookViewer", "عارض الكتب الإسلامية"),
        ("athkerDialog", "عارض الأذكار"),
        ("textViewer", "عارض النصوص العام"),
        ("researcher", "الباحث في القرآن والأحاديث"),
        ("afterAzaan", "نافذة دعاء بعد الأذان"),
        ("qMessageBox", "مربعات الرسائل"),
        ("noteDialog", "عارض الملاحظات"),
        ("aiChat", "شاشة الذكاء الاصطناعي"),
    ]

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: Arial;
            }
            QCheckBox, QLabel {
                font-size: 14px;
            }
            QSpinBox {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.viewer_checkboxes = {}
        self.updating_select_all = False

        main_layout = qt.QVBoxLayout(self)
        main_layout.addStretch()

        top_controls_layout = qt.QHBoxLayout()
        top_controls_layout.addStretch()

        self.bold_checkbox = qt.QCheckBox("خط عريض (Bold)")
        self.bold_checkbox.setChecked(settings_handler.get("font", "bold") == "True")
        self.bold_checkbox.stateChanged.connect(self.on_bold_changed)

        font_size_label = qt.QLabel("حجم الخط:")
        self.font_size_spinbox = qt.QSpinBox()
        self.font_size_spinbox.setRange(1, 100)
        self.font_size_spinbox.setValue(int(settings_handler.get("font", "size") or 12))
        self.font_size_spinbox.setFixedWidth(80)
        self.font_size_spinbox.setAccessibleName("حجم الخط")
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)

        top_controls_layout.addWidget(self.bold_checkbox)
        top_controls_layout.addSpacing(20)
        top_controls_layout.addWidget(self.font_size_spinbox)
        top_controls_layout.addWidget(font_size_label)
        top_controls_layout.addStretch()

        main_layout.addLayout(top_controls_layout)
        main_layout.addSpacing(20)

        self.info_label = qt.QLabel("تحديد العارضات لتشغيل أو إيقاف وضع التفاف النص:\nهذا الخيار يعرض المحتوة الطويل على أكثر من سطر، وهذا الخيار للمبصرين فقط")
        self.info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.info_label)
        main_layout.addSpacing(15)

        select_all_layout = qt.QHBoxLayout()
        select_all_layout.addStretch()
        self.select_all_checkbox = qt.QCheckBox("تحديد الكل")
        self.select_all_checkbox.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        select_all_layout.addWidget(self.select_all_checkbox)
        select_all_layout.addStretch()
        main_layout.addLayout(select_all_layout)
        main_layout.addSpacing(15)

        grid_layout = qt.QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)

        cols = 3
        for index, (key, label_text) in enumerate(self.VIEWERS):
            row = index // cols
            col = index % cols

            cb = qt.QCheckBox(label_text)
            wrap_setting = settings_handler.get("font_wrap", key)
            if wrap_setting == "":
                is_checked = settings_handler.get("font", "wrap") == "True"
            else:
                is_checked = wrap_setting == "True"

            cb.setChecked(is_checked)
            cb.stateChanged.connect(lambda state, k=key: self.on_viewer_checkbox_changed(k, state))

            self.viewer_checkboxes[key] = cb
            grid_layout.addWidget(cb, row, col, alignment=qt2.Qt.AlignmentFlag.AlignRight)

        grid_widget = qt.QWidget()
        grid_widget.setLayout(grid_layout)
        grid_container = qt.QHBoxLayout()
        grid_container.addStretch()
        grid_container.addWidget(grid_widget)
        grid_container.addStretch()
        main_layout.addLayout(grid_container)

        main_layout.addStretch()
        self.setLayout(main_layout)

        self.update_checkbox_font()
        self.check_select_all_state()

    def update_checkbox_font(self):
        font = self.bold_checkbox.font()
        font.setBold(self.bold_checkbox.isChecked())
        self.bold_checkbox.setFont(font)

    def on_bold_changed(self, state):
        settings_handler.set("font", "bold", str(self.bold_checkbox.isChecked()))
        self.update_checkbox_font()

    def on_font_size_changed(self, value):
        settings_handler.set("font", "size", str(value))

    def on_viewer_checkbox_changed(self, key, state):
        is_checked = (state == qt2.Qt.CheckState.Checked.value or state == True)
        settings_handler.set("font_wrap", key, str(is_checked))
        if not self.updating_select_all:
            self.check_select_all_state()

    def on_select_all_changed(self, state):
        if self.updating_select_all:
            return
        self.updating_select_all = True
        is_checked = (state == qt2.Qt.CheckState.Checked.value or state == True)
        for key, cb in self.viewer_checkboxes.items():
            cb.setChecked(is_checked)
            settings_handler.set("font_wrap", key, str(is_checked))
        settings_handler.set("font", "wrap", str(is_checked))
        self.updating_select_all = False

    def check_select_all_state(self):
        if self.updating_select_all:
            return
        all_checked = all(cb.isChecked() for cb in self.viewer_checkboxes.values())
        self.updating_select_all = True
        self.select_all_checkbox.setChecked(all_checked)
        self.updating_select_all = False