import os
import shutil
import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from settings import settings_handler
from functions.moton_data import MotonDataLoader, get_moton_appdata_dir


class MotonRecitersSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                min-height: 36px;
            }
        """)
        self.data_loader = MotonDataLoader()
        self.categories = self.data_loader.get_categories()

        from functions.moton_data import get_all_moton_reciters, get_moton_reciters_for_matn
        self.all_reciters_data = get_all_moton_reciters()
        self.slug_to_ar = self.all_reciters_data.get("reciters", {})

        self.viewer_reciters_cache = {}
        self.player_reciters_cache = {}

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)

        target_layout = qt.QHBoxLayout()
        target_layout.setSpacing(10)
        target_layout.addStretch(1)
        self.target_combo = qt.QComboBox()
        self.target_combo.setFont(font)
        self.target_combo.setAccessibleName("تخصيص القارئ ل")
        self.target_combo.addItem("عارض المتون", "viewer")
        self.target_combo.addItem("مشغل المتون", "player")
        self.target_label = qt.QLabel("تخصيص القارئ ل:")
        self.target_label.setFont(font)
        self.target_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        target_layout.addWidget(self.target_combo)
        target_layout.addWidget(self.target_label)
        target_layout.addStretch(1)
        layout.addLayout(target_layout)

        cat_layout = qt.QHBoxLayout()
        cat_layout.setSpacing(10)
        cat_layout.addStretch(1)
        self.category_combo = qt.QComboBox()
        self.category_combo.setFont(font)
        self.category_combo.setAccessibleName("الفئة")
        for cat in self.categories:
            self.category_combo.addItem(cat)
        self.category_label = qt.QLabel("الفئة:")
        self.category_label.setFont(font)
        self.category_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addWidget(self.category_label)
        cat_layout.addStretch(1)
        layout.addLayout(cat_layout)

        matn_layout = qt.QHBoxLayout()
        matn_layout.setSpacing(10)
        matn_layout.addStretch(1)
        self.matn_combo = qt.QComboBox()
        self.matn_combo.setFont(font)
        self.matn_combo.setAccessibleName("المتن")
        self.matn_label = qt.QLabel("المتن:")
        self.matn_label.setFont(font)
        self.matn_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        matn_layout.addWidget(self.matn_combo)
        matn_layout.addWidget(self.matn_label)
        matn_layout.addStretch(1)
        layout.addLayout(matn_layout)

        reciter_layout = qt.QHBoxLayout()
        reciter_layout.setSpacing(10)
        reciter_layout.addStretch(1)
        self.reciter_combo = qt.QComboBox()
        self.reciter_combo.setFont(font)
        self.reciter_combo.setAccessibleName("القارئ")
        self.reciter_combo.setAccessibleDescription("لحذف بيانات القارئ، نستخدم زر التطبيقات أو click الأيمن")
        self.reciter_combo.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.reciter_combo.customContextMenuRequested.connect(lambda pos: self.on_delete(self.reciter_combo))
        self.reciter_combo.installEventFilter(self)
        self.reciter_label = qt.QLabel("القارئ:")
        self.reciter_label.setFont(font)
        self.reciter_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        reciter_layout.addWidget(self.reciter_combo)
        reciter_layout.addWidget(self.reciter_label)
        reciter_layout.addStretch(1)
        layout.addLayout(reciter_layout)

        self.default_notice_text = "لحذف قارئ، نستخدم زر التطبيقات أو click الأيمن على قائمة القراء"
        self.delete_notice = guiTools.QNavigableLabel(self.default_notice_text)
        self.delete_notice.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.delete_notice.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        layout.addSpacing(25)
        layout.addWidget(self.delete_notice)
        layout.addStretch(1)

        self.notice_timer = qt2.QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self.reset_notice)

        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        self.matn_combo.currentIndexChanged.connect(self.on_matn_changed)
        self.target_combo.currentIndexChanged.connect(self.on_target_changed)
        self.reciter_combo.currentIndexChanged.connect(self.on_reciter_changed)

        if self.categories:
            self.on_category_changed(0)

    def eventFilter(self, obj, event):
        if hasattr(self, 'reciter_combo') and obj == self.reciter_combo:
            if event.type() == qt2.QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Menu:
                self.on_delete(self.reciter_combo)
                return True
        return super().eventFilter(obj, event)

    def reset_notice(self):
        self.delete_notice.setText(self.default_notice_text)

    def on_delete(self, combo):
        reciter_slug = combo.currentData()
        if not reciter_slug:
            return
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        if not matn_slug:
            return

        appdata_path = get_moton_appdata_dir(reciter_slug, matn_slug)
        local_data_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", reciter_slug, matn_slug))

        is_appdata_local = os.path.exists(appdata_path) and (len(os.listdir(appdata_path)) > 0 if os.path.isdir(appdata_path) else False)
        is_data_local = os.path.exists(local_data_path) and (len(os.listdir(local_data_path)) > 0 if os.path.isdir(local_data_path) else False)

        if not (is_appdata_local or is_data_local):
            guiTools.speak("هذا القارئ غير موجود محليا")
            self.delete_notice.setText("هذا القارئ غير موجود محليا")
            self.notice_timer.stop()
            self.notice_timer.start(3000)
        else:
            question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا القارئ", "نعم", "لا")
            if question == 0:
                deleted = False
                if is_appdata_local:
                    try:
                        shutil.rmtree(appdata_path)
                        deleted = True
                    except Exception as e:
                        print(f"Error deleting appdata folder: {e}")
                if is_data_local:
                    try:
                        shutil.rmtree(local_data_path)
                        deleted = True
                    except Exception as e:
                        print(f"Error deleting local data folder: {e}")
                if deleted:
                    guiTools.speak("تم الحذف")
                    self.delete_notice.setText("تم الحذف بنجاح")
                    self.notice_timer.stop()
                    self.notice_timer.start(3000)


    def adjust_combo_width(self, combo):
        fm = combo.fontMetrics()
        current_text = combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        combo.setFixedWidth(text_width + 65)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_combo_width(self.category_combo)
        self.adjust_combo_width(self.matn_combo)
        self.adjust_combo_width(self.target_combo)
        self.adjust_combo_width(self.reciter_combo)

    def on_category_changed(self, index):
        self.adjust_combo_width(self.category_combo)
        moton = self.data_loader.get_moton_for_category(index)
        self.matn_combo.blockSignals(True)
        self.matn_combo.clear()
        for m in moton:
            self.matn_combo.addItem(m)
        self.matn_combo.blockSignals(False)
        if moton:
            self.on_matn_changed(0)
        else:
            self.reciter_combo.blockSignals(True)
            self.reciter_combo.clear()
            self.reciter_combo.blockSignals(False)

    def on_target_changed(self, index):
        self.adjust_combo_width(self.target_combo)
        self.on_matn_changed(self.matn_combo.currentIndex())

    def on_matn_changed(self, index):
        self.adjust_combo_width(self.matn_combo)
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        from functions.moton_data import get_moton_reciters_for_matn
        reciter_list = get_moton_reciters_for_matn(matn_slug)

        verse_reciters = []
        for r_ar, r_slug, r_type, r_url in reciter_list:
            if r_type == "N":
                verse_reciters.append((r_ar, r_slug))

        self.reciter_combo.blockSignals(True)
        self.reciter_combo.clear()

        if not verse_reciters:
            self.reciter_combo.addItem("لا يتوفر قراء مسجلين لهذا المتن", "")
            self.reciter_combo.setEnabled(False)
        else:
            self.reciter_combo.setEnabled(True)
            target = self.target_combo.currentData() if hasattr(self, 'target_combo') else "viewer"
            if target == "player":
                saved_reciter = self.player_reciters_cache.get(matn_slug) or settings_handler.get("moton_player_reciters", matn_slug) or settings_handler.get("moton_player_reciters", "default") or settings_handler.get("moton_reciters", matn_slug) or settings_handler.get("moton_reciters", "default")
            else:
                saved_reciter = self.viewer_reciters_cache.get(matn_slug) or settings_handler.get("moton_viewer_reciters", matn_slug) or settings_handler.get("moton_viewer_reciters", "default") or settings_handler.get("moton_reciters", matn_slug) or settings_handler.get("moton_reciters", "default")
            selected_idx = 0
            for i, (r_ar, r_slug) in enumerate(verse_reciters):
                self.reciter_combo.addItem(r_ar, r_slug)
                if saved_reciter and (r_slug == saved_reciter or r_ar == saved_reciter):
                    selected_idx = i
            if self.reciter_combo.count() > 0:
                self.reciter_combo.setCurrentIndex(selected_idx)

        self.reciter_combo.blockSignals(False)
        self.adjust_combo_width(self.reciter_combo)

    def on_reciter_changed(self, index):
        self.adjust_combo_width(self.reciter_combo)
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        reciter_slug = self.reciter_combo.currentData()
        target = self.target_combo.currentData() if hasattr(self, 'target_combo') else "viewer"
        if matn_slug and reciter_slug:
            if target == "player":
                self.player_reciters_cache[matn_slug] = reciter_slug
            else:
                self.viewer_reciters_cache[matn_slug] = reciter_slug

    def save_settings(self):
        matn_name = self.matn_combo.currentText()
        if matn_name:
            matn_slug = self.data_loader.get_matn_slug(matn_name)
            current_slug = self.reciter_combo.currentData()
            target = self.target_combo.currentData() if hasattr(self, 'target_combo') else "viewer"
            if matn_slug and current_slug:
                if target == "player":
                    self.player_reciters_cache[matn_slug] = current_slug
                else:
                    self.viewer_reciters_cache[matn_slug] = current_slug
        for matn_slug, reciter_slug in self.viewer_reciters_cache.items():
            settings_handler.set("moton_viewer_reciters", matn_slug, reciter_slug)
            settings_handler.set("moton_reciters", matn_slug, reciter_slug)
        for matn_slug, reciter_slug in self.player_reciters_cache.items():
            settings_handler.set("moton_player_reciters", matn_slug, reciter_slug)
        current_slug = self.reciter_combo.currentData()
        target = self.target_combo.currentData() if hasattr(self, 'target_combo') else "viewer"
        if current_slug:
            if target == "player":
                settings_handler.set("moton_player_reciters", "default", current_slug)
            else:
                settings_handler.set("moton_viewer_reciters", "default", current_slug)
                settings_handler.set("moton_reciters", "default", current_slug)

