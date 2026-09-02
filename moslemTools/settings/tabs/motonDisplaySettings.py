import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler


class MotonDisplaySettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)
        mode_label = qt.QLabel("طريقة عرض أرقام الأبيات:")
        mode_label.setFont(font)
        mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mode_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        saved_mode = settings_handler.get("motonViewer", "verse_numbering_mode") or "by_chapter"
        self.cb_by_chapter = qt.QCheckBox("إظهار الأرقام بحسب الباب")
        self.cb_by_chapter.setFont(font)
        self.cb_by_chapter.setChecked(saved_mode == "by_chapter")
        self.cb_by_chapter.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_by_chapter, checked))
        layout.addWidget(self.cb_by_chapter, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_by_matn = qt.QCheckBox("إظهار الأرقام بحسب المتن كاملا")
        self.cb_by_matn.setFont(font)
        self.cb_by_matn.setChecked(saved_mode == "by_matn")
        self.cb_by_matn.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_by_matn, checked))
        layout.addWidget(self.cb_by_matn, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_none = qt.QCheckBox("إخفاء أرقام الأبيات")
        self.cb_none.setFont(font)
        self.cb_none.setChecked(saved_mode == "none")
        self.cb_none.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_none, checked))
        layout.addWidget(self.cb_none, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        self.remove_tashkeel_checkbox = qt.QCheckBox("إزالة التشكيل")
        self.remove_tashkeel_checkbox.setFont(font)
        self.remove_tashkeel_checkbox.setChecked(settings_handler.get("motonViewer", "remove_tashkeel") == "True")
        layout.addWidget(self.remove_tashkeel_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def on_cb_clicked(self, target_cb, checked):
        if not checked:
            target_cb.setChecked(True)
            return
        for cb in [self.cb_by_chapter, self.cb_by_matn, self.cb_none]:
            if cb != target_cb:
                cb.setChecked(False)

    def get_selected_mode(self):
        if self.cb_by_matn.isChecked():
            return "by_matn"
        elif self.cb_none.isChecked():
            return "none"
        return "by_chapter"
