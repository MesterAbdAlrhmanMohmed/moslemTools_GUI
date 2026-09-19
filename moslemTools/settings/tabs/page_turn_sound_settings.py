import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler


class PageTurnSoundSettings(qt.QWidget):
    VIEWERS = [
        ("quranViewer", "عارض القرآن الكريم"),
        ("bookViewer", "عارض الكتب الإسلامية"),
        ("hadeethViewer", "عارض الأحاديث النبوية"),
        ("athkerDialog", "عارض الأذكار"),
        ("motonViewer", "عارض المتون الإسلامية"),
        ("storyViewer", "عارض قصص الأنبياء"),
        ("islamicTopicViewer", "عارض الموضوعات الإسلامية"),
    ]

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QCheckBox, QLabel {
                font-size: 14px;
            }
        """)
        self.viewer_checkboxes = {}
        self.updating_select_all = False

        main_layout = qt.QVBoxLayout(self)
        main_layout.addStretch()

        self.info_label = guiTools.QNavigableLabel("يمكنكم من هنا تفعيل أو تعطيل صوت تقليب الصفحات للعارضات المحددة")
        self.info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.info_label)
        main_layout.addSpacing(25)

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
            sound_setting = settings_handler.get("page_turn_sound", key)
            if sound_setting == "":
                is_checked = True
            else:
                is_checked = sound_setting == "True"

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

        self.check_select_all_state()

    def on_viewer_checkbox_changed(self, key, state):
        if not self.updating_select_all:
            self.check_select_all_state()

    def on_select_all_changed(self, state):
        if self.updating_select_all:
            return
        self.updating_select_all = True
        is_checked = (state == qt2.Qt.CheckState.Checked.value or state == True)
        for key, cb in self.viewer_checkboxes.items():
            cb.setChecked(is_checked)
        self.updating_select_all = False

    def check_select_all_state(self):
        if self.updating_select_all:
            return
        all_checked = all(cb.isChecked() for cb in self.viewer_checkboxes.values())
        self.updating_select_all = True
        self.select_all_checkbox.setChecked(all_checked)
        self.updating_select_all = False

    def save(self):
        for key, cb in self.viewer_checkboxes.items():
            settings_handler.set("page_turn_sound", key, str(cb.isChecked()))
        settings_handler.set("page_turn_sound", "all", str(self.select_all_checkbox.isChecked()))
