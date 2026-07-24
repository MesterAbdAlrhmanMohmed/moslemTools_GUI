import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler

class QuranDisplaySettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)
        layout.addStretch(1)
        mode_label = qt.QLabel("طريقة عرض أرقام الآيات:")
        mode_label.setFont(font)
        mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mode_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        saved_mode = settings_handler.get("quran_display", "verse_numbering_mode") or "by_surah"
        self.cb_by_surah = qt.QCheckBox("إظهار الأرقام بحسب السورة")
        self.cb_by_surah.setFont(font)
        self.cb_by_surah.setChecked(saved_mode == "by_surah")
        self.cb_by_surah.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_by_surah, checked))
        layout.addWidget(self.cb_by_surah, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_cumulative = qt.QCheckBox("إظهار الأرقام بحسب الفئة")
        self.cb_cumulative.setFont(font)
        self.cb_cumulative.setChecked(saved_mode == "cumulative")
        self.cb_cumulative.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_cumulative, checked))
        layout.addWidget(self.cb_cumulative, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_quran_wide = qt.QCheckBox("إظهار الأرقام بحسب القرآن كاملا")
        self.cb_quran_wide.setFont(font)
        self.cb_quran_wide.setChecked(saved_mode == "quran_wide")
        self.cb_quran_wide.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_quran_wide, checked))
        layout.addWidget(self.cb_quran_wide, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        self.cb_none = qt.QCheckBox("إخفاء أرقام الآيات")
        self.cb_none.setFont(font)
        self.cb_none.setChecked(saved_mode == "none")
        self.cb_none.clicked.connect(lambda checked: self.on_cb_clicked(self.cb_none, checked))
        layout.addWidget(self.cb_none, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        self.remove_tashkeel_checkbox = qt.QCheckBox("إزالة التشكيل")
        self.remove_tashkeel_checkbox.setFont(font)
        self.remove_tashkeel_checkbox.setChecked(settings_handler.get("quran_display", "remove_tashkeel") == "True")
        layout.addWidget(self.remove_tashkeel_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def on_cb_clicked(self, target_cb, checked):
        if not checked:
            target_cb.setChecked(True)
            return
        for cb in [self.cb_by_surah, self.cb_cumulative, self.cb_quran_wide, self.cb_none]:
            if cb != target_cb:
                cb.setChecked(False)

    def get_selected_mode(self):
        if self.cb_cumulative.isChecked():
            return "cumulative"
        elif self.cb_quran_wide.isChecked():
            return "quran_wide"
        elif self.cb_none.isChecked():
            return "none"
        return "by_surah"
