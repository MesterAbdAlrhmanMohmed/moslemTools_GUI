import os
import shutil
import gui
import guiTools
from settings import settings_handler, app
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt


class QuranRecitersSettings(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = qt.QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet("""
            QComboBox {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        self.combos = []
        self.reciters_list = list(gui.reciters.keys())
        self.viewer_combo = self.create_row("تحديد القارئ الافتراضي لعارض القرآن الكريم", "تحديد القارئ الافتراضي لعارض القرآن الكريم")
        self.player_combo = self.create_row("تحديد القارئ الافتراضي لمشغل القرآن الكريم", "تحديد القارئ الافتراضي لمشغل القرآن الكريم")
        self.researcher_combo = self.create_row("تحديد القارئ الافتراضي للباحث", "تحديد القارئ الافتراضي للباحث")

        self.default_notice_text = "لحذف قارئ، نستخدم زر التطبيقات أو click الأيمن على أي قائمة من قوائم القراء"
        self.delete_notice = guiTools.QNavigableLabel(self.default_notice_text)
        self.delete_notice.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.delete_notice.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.layout.addSpacing(12)
        self.layout.addWidget(self.delete_notice, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.layout.addStretch(1)

        self.notice_timer = qt2.QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self.reset_notice)

        self.load_settings()

    def create_row(self, label_text, accessible_name):
        container = qt.QWidget()
        row_layout = qt.QVBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        label = qt.QLabel(label_text)
        label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        label.setFont(font)
        combo = qt.QComboBox()
        combo.setFont(font)
        self.combos.append(combo)
        combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.addItems(self.reciters_list)
        combo.setAccessibleName(accessible_name)
        combo.setAccessibleDescription("لحذف بيانات القارئ، نستخدم زر التطبيقات أو click الأيمن")
        fm = combo.fontMetrics()
        max_w = max([fm.horizontalAdvance(text) for text in self.reciters_list], default=100)
        combo.setMinimumWidth(max_w + 35)
        combo.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        combo.customContextMenuRequested.connect(lambda pos, c=combo: self.on_delete(c))
        combo.installEventFilter(self)
        row_layout.addWidget(label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(combo)
        self.layout.addWidget(container)
        return combo

    def eventFilter(self, obj, event):
        if hasattr(self, 'combos') and obj in self.combos:
            if event.type() == qt2.QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Menu:
                self.on_delete(obj)
                return True
        return super().eventFilter(obj, event)

    def on_delete(self, combo):
        item_text = combo.currentText()
        if not item_text or item_text not in gui.quranViewer.reciters:
            return
        reciter_url = gui.quranViewer.reciters[item_text]
        reciter_folder = reciter_url.split("/")[-3]
        path = os.path.join(os.getenv('appdata'), app.appName, "reciters", reciter_folder)
        is_local = os.path.exists(path) and (len(os.listdir(path)) > 0 if os.path.isdir(path) else False)
        if not is_local:
            guiTools.speak("هذا القارئ غير موجود محليا")
            self.delete_notice.setText("هذا القارئ غير موجود محليا")
            self.notice_timer.stop()
            self.notice_timer.start(3000)
        else:
            question = guiTools.QQuestionMessageBox.view(self, "تنبيه", "هل تريد حذف هذا القارئ", "نعم", "لا")
            if question == 0:
                shutil.rmtree(path)
                guiTools.speak("تم الحذف")

    def reset_notice(self):
        self.delete_notice.setText(self.default_notice_text)

    def load_settings(self):
        r_idx = int(settings_handler.get("quran_reciters", "researcher") or settings_handler.get("g", "reciter") or 0)
        p_idx = int(settings_handler.get("quran_reciters", "player") or settings_handler.get("g", "reciter") or 0)
        v_idx = int(settings_handler.get("quran_reciters", "viewer") or settings_handler.get("g", "reciter") or 0)
        if 0 <= r_idx < self.researcher_combo.count():
            self.researcher_combo.setCurrentIndex(r_idx)
        if 0 <= p_idx < self.player_combo.count():
            self.player_combo.setCurrentIndex(p_idx)
        if 0 <= v_idx < self.viewer_combo.count():
            self.viewer_combo.setCurrentIndex(v_idx)

    def save_settings(self):
        r_idx = str(self.researcher_combo.currentIndex())
        p_idx = str(self.player_combo.currentIndex())
        v_idx = str(self.viewer_combo.currentIndex())
        settings_handler.set("quran_reciters", "researcher", r_idx)
        settings_handler.set("quran_reciters", "player", p_idx)
        settings_handler.set("quran_reciters", "viewer", v_idx)
        settings_handler.set("g", "reciter", v_idx)
