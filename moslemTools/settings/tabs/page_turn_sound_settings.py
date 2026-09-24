import os
import shutil
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
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 10px 24px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.viewer_checkboxes = {}
        self.updating_select_all = False

        self.sounds_dir = os.path.join("data", "sounds")
        if not os.path.exists(self.sounds_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.sounds_dir = os.path.join(base_dir, "data", "sounds")

        backup_next = os.path.join(self.sounds_dir, "default_next_page.wav")
        backup_prev = os.path.join(self.sounds_dir, "default_previous_page.wav")
        orig_next = os.path.join(self.sounds_dir, "next_page.wav")
        orig_prev = os.path.join(self.sounds_dir, "previous_page.wav")
        if os.path.exists(orig_next) and not os.path.exists(backup_next):
            shutil.copy2(orig_next, backup_next)
        if os.path.exists(orig_prev) and not os.path.exists(backup_prev):
            shutil.copy2(orig_prev, backup_prev)

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

        self.change_next_sound_btn = guiTools.QPushButton("تغيير صوت الصفحة التالية")
        self.change_next_sound_btn.setAccessibleName("تغيير صوت الصفحة التالية")
        self.change_next_sound_btn.clicked.connect(self.on_change_next_sound_clicked)
        self.change_next_sound_btn.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.change_next_sound_btn.customContextMenuRequested.connect(lambda pos: self.on_change_next_sound_clicked())

        self.change_prev_sound_btn = guiTools.QPushButton("تغيير صوت الصفحة السابقة")
        self.change_prev_sound_btn.setAccessibleName("تغيير صوت الصفحة السابقة")
        self.change_prev_sound_btn.clicked.connect(self.on_change_prev_sound_clicked)
        self.change_prev_sound_btn.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.change_prev_sound_btn.customContextMenuRequested.connect(lambda pos: self.on_change_prev_sound_clicked())

        self.buttons_widget = qt.QWidget()
        buttons_layout = qt.QHBoxLayout(self.buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.change_next_sound_btn)
        buttons_layout.addSpacing(20)
        buttons_layout.addWidget(self.change_prev_sound_btn)
        buttons_layout.addStretch()

        main_layout.addSpacing(25)
        main_layout.addWidget(self.buttons_widget)

        main_layout.addStretch()
        self.setLayout(main_layout)

        self.check_select_all_state()
        self.update_buttons_visibility()

    def on_viewer_checkbox_changed(self, key, state):
        if not self.updating_select_all:
            self.check_select_all_state()
            self.update_buttons_visibility()

    def on_select_all_changed(self, state):
        if self.updating_select_all:
            return
        self.updating_select_all = True
        is_checked = (state == qt2.Qt.CheckState.Checked.value or state == True)
        for key, cb in self.viewer_checkboxes.items():
            cb.setChecked(is_checked)
        self.updating_select_all = False
        self.update_buttons_visibility()

    def check_select_all_state(self):
        if self.updating_select_all:
            return
        all_checked = all(cb.isChecked() for cb in self.viewer_checkboxes.values())
        self.updating_select_all = True
        self.select_all_checkbox.setChecked(all_checked)
        self.updating_select_all = False

    def update_buttons_visibility(self):
        has_any_checked = any(cb.isChecked() for cb in self.viewer_checkboxes.values())
        self.buttons_widget.setVisible(has_any_checked)
        self.change_next_sound_btn.setVisible(has_any_checked)
        self.change_prev_sound_btn.setVisible(has_any_checked)

    def on_change_next_sound_clicked(self):
        soundMenu = guiTools.QCustomContextMenu("اختر صوت", self)
        soundMenu.setAccessibleName("اختر صوت")
        font1 = qt1.QFont()
        font1.setBold(True)
        soundMenu.setFont(font1)
        default_action = qt1.QAction("الصوت الافتراضي", self)
        default_action.triggered.connect(self.on_next_sound_default)
        soundMenu.addAction(default_action)
        choose_action = qt1.QAction("اختر من الجهاز", self)
        choose_action.triggered.connect(self.on_next_sound_choose_from_device)
        soundMenu.addAction(choose_action)
        soundMenu.setFocus()
        mouse_position = qt1.QCursor.pos()
        soundMenu.exec(mouse_position)

    def on_next_sound_default(self):
        backup_path = os.path.join(self.sounds_dir, "default_next_page.wav")
        dest_path = os.path.join(self.sounds_dir, "next_page.wav")
        current_file = settings_handler.get("page_turn_sound", "next_page_file")
        current_custom = settings_handler.get("page_turn_sound", "next_page_custom")
        if (not current_file or current_file == "next_page.wav") and current_custom != "True" and os.path.exists(dest_path) and os.path.exists(backup_path):
            if os.path.getsize(dest_path) == os.path.getsize(backup_path):
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "الصوت الافتراضي محدد بالفعل.")
                return
        try:
            for f in os.listdir(self.sounds_dir):
                if f.startswith("next_page."):
                    try:
                        os.remove(os.path.join(self.sounds_dir, f))
                    except Exception:
                        pass
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, dest_path)
            settings_handler.set("page_turn_sound", "next_page_file", "next_page.wav")
            settings_handler.set("page_turn_sound", "next_page_custom", "False")
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم استعادة الصوت الافتراضي بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")

    def on_next_sound_choose_from_device(self):
        fileDialog = qt.QFileDialog(self, "اختر ملف صوتي")
        fileDialog.setFileMode(qt.QFileDialog.FileMode.ExistingFile)
        fileDialog.setNameFilter("ملفات الصوت (*.wav *.mp3 *.wma *.aac *.m4a *.flac *.ogg *.opus *.ape *.mpga *.alac *.wv *.mka *.aiff *.au *.dss *.iff *.m4r *.m4b *.midi *.mid *.ac3 *.tta *.m3u *.amr *.awb *.caf *.mod *.s3m *.xm *.it *.ra *.rm *.bwf *.rf64 *.pcm *.asf *.dvf *.msv *.qcp *.slk *.vox *.voc *.snd *.adx *.aif *.aifc *.ast *.brstm *.dts *.gsm *.m4p *.mp1 *.mp2 *.mus *.sb0 *.smp *.spx *.w64 *.xma *.ac3 *.dct *.ec3 *.mka *.mlp *.ofr *.tak *.thd *.tta *.wv)")
        if fileDialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            try:
                selected_files = fileDialog.selectedFiles()
                if not selected_files or not selected_files[0]:
                    return
                selected_file = selected_files[0]
                file_ext = os.path.splitext(selected_file)[1].lower()
                new_filename = f"next_page{file_ext}"
                dest_path = os.path.join(self.sounds_dir, new_filename)
                for f in os.listdir(self.sounds_dir):
                    if f.startswith("next_page."):
                        try:
                            os.remove(os.path.join(self.sounds_dir, f))
                        except Exception:
                            pass
                shutil.copy2(selected_file, dest_path)
                settings_handler.set("page_turn_sound", "next_page_file", new_filename)
                settings_handler.set("page_turn_sound", "next_page_custom", "True")
                guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تغيير صوت الصفحة التالية بنجاح.")
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")

    def on_change_prev_sound_clicked(self):
        soundMenu = guiTools.QCustomContextMenu("اختر صوت", self)
        soundMenu.setAccessibleName("اختر صوت")
        font1 = qt1.QFont()
        font1.setBold(True)
        soundMenu.setFont(font1)
        default_action = qt1.QAction("الصوت الافتراضي", self)
        default_action.triggered.connect(self.on_prev_sound_default)
        soundMenu.addAction(default_action)
        choose_action = qt1.QAction("اختر من الجهاز", self)
        choose_action.triggered.connect(self.on_prev_sound_choose_from_device)
        soundMenu.addAction(choose_action)
        soundMenu.setFocus()
        mouse_position = qt1.QCursor.pos()
        soundMenu.exec(mouse_position)

    def on_prev_sound_default(self):
        backup_path = os.path.join(self.sounds_dir, "default_previous_page.wav")
        dest_path = os.path.join(self.sounds_dir, "previous_page.wav")
        current_file = settings_handler.get("page_turn_sound", "previous_page_file")
        current_custom = settings_handler.get("page_turn_sound", "previous_page_custom")
        if (not current_file or current_file == "previous_page.wav") and current_custom != "True" and os.path.exists(dest_path) and os.path.exists(backup_path):
            if os.path.getsize(dest_path) == os.path.getsize(backup_path):
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "الصوت الافتراضي محدد بالفعل.")
                return
        try:
            for f in os.listdir(self.sounds_dir):
                if f.startswith("previous_page."):
                    try:
                        os.remove(os.path.join(self.sounds_dir, f))
                    except Exception:
                        pass
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, dest_path)
            settings_handler.set("page_turn_sound", "previous_page_file", "previous_page.wav")
            settings_handler.set("page_turn_sound", "previous_page_custom", "False")
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم استعادة الصوت الافتراضي بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")

    def on_prev_sound_choose_from_device(self):
        fileDialog = qt.QFileDialog(self, "اختر ملف صوتي")
        fileDialog.setFileMode(qt.QFileDialog.FileMode.ExistingFile)
        fileDialog.setNameFilter("ملفات الصوت (*.wav *.mp3 *.wma *.aac *.m4a *.flac *.ogg *.opus *.ape *.mpga *.alac *.wv *.mka *.aiff *.au *.dss *.iff *.m4r *.m4b *.midi *.mid *.ac3 *.tta *.m3u *.amr *.awb *.caf *.mod *.s3m *.xm *.it *.ra *.rm *.bwf *.rf64 *.pcm *.asf *.dvf *.msv *.qcp *.slk *.vox *.voc *.snd *.adx *.aif *.aifc *.ast *.brstm *.dts *.gsm *.m4p *.mp1 *.mp2 *.mus *.sb0 *.smp *.spx *.w64 *.xma *.ac3 *.dct *.ec3 *.mka *.mlp *.ofr *.tak *.thd *.tta *.wv)")
        if fileDialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            try:
                selected_files = fileDialog.selectedFiles()
                if not selected_files or not selected_files[0]:
                    return
                selected_file = selected_files[0]
                file_ext = os.path.splitext(selected_file)[1].lower()
                new_filename = f"previous_page{file_ext}"
                dest_path = os.path.join(self.sounds_dir, new_filename)
                for f in os.listdir(self.sounds_dir):
                    if f.startswith("previous_page."):
                        try:
                            os.remove(os.path.join(self.sounds_dir, f))
                        except Exception:
                            pass
                shutil.copy2(selected_file, dest_path)
                settings_handler.set("page_turn_sound", "previous_page_file", new_filename)
                settings_handler.set("page_turn_sound", "previous_page_custom", "True")
                guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تغيير صوت الصفحة السابقة بنجاح.")
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ غير متوقع: {e}")

    def save(self):
        for key, cb in self.viewer_checkboxes.items():
            settings_handler.set("page_turn_sound", key, str(cb.isChecked()))
        settings_handler.set("page_turn_sound", "all", str(self.select_all_checkbox.isChecked()))
