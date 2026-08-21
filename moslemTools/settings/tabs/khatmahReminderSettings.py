import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .. import settings_handler


class KhatmahReminderSettings(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)

        self.enable_checkbox = qt.QCheckBox("تفعيل التنبيه اليومي بالختمة القرآنية")
        self.enable_checkbox.setFont(font)
        self.enable_checkbox.setChecked(settings_handler.get("khatmah_reminder", "enabled") == "True")
        self.enable_checkbox.toggled.connect(self.toggle_controls)
        layout.addWidget(self.enable_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        time_box = qt.QGroupBox()
        time_box.setFont(font)
        time_box.setAccessibleName("")
        time_layout = qt.QHBoxLayout(time_box)
        time_layout.setSpacing(15)

        self.hour_label = qt.QLabel("الساعة:")
        self.hour_label.setFont(font)
        self.hour_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.hour_spin = qt.QSpinBox()
        self.hour_spin.setFont(font)
        self.hour_spin.setRange(1, 12)
        self.hour_spin.setAccessibleName("الساعة")
        self.hour_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        try:
            self.hour_spin.setValue(int(settings_handler.get("khatmah_reminder", "hour") or 8))
        except Exception:
            self.hour_spin.setValue(8)

        hour_v = qt.QVBoxLayout()
        hour_v.addWidget(self.hour_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        hour_v.addWidget(self.hour_spin, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.minute_label = qt.QLabel("الدقيقة:")
        self.minute_label.setFont(font)
        self.minute_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.minute_spin = qt.QSpinBox()
        self.minute_spin.setFont(font)
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setAccessibleName("الدقيقة")
        self.minute_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        try:
            self.minute_spin.setValue(int(settings_handler.get("khatmah_reminder", "minute") or 0))
        except Exception:
            self.minute_spin.setValue(0)

        minute_v = qt.QVBoxLayout()
        minute_v.addWidget(self.minute_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        minute_v.addWidget(self.minute_spin, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.period_label = qt.QLabel("الفترة:")
        self.period_label.setFont(font)
        self.period_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.period_combo = qt.QComboBox()
        self.period_combo.setFont(font)
        self.period_combo.addItems(["صباحاً", "مساءً"])
        self.period_combo.setAccessibleName("الفترة")
        saved_period = settings_handler.get("khatmah_reminder", "period") or "صباحاً"
        if saved_period in ["صباحاً", "مساءً"]:
            self.period_combo.setCurrentText(saved_period)

        period_v = qt.QVBoxLayout()
        period_v.addWidget(self.period_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        period_v.addWidget(self.period_combo, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        time_layout.addLayout(hour_v)
        time_layout.addLayout(minute_v)
        time_layout.addLayout(period_v)
        layout.addWidget(time_box)

        self.missed_alert_checkbox = qt.QCheckBox("تنبيهي بفوات موعد الورد اليومي إذا كان البرنامج مغلقاً وقت التنبيه")
        self.missed_alert_checkbox.setFont(font)
        self.missed_alert_checkbox.setChecked(settings_handler.get("khatmah_reminder", "missed_alert") != "False")
        layout.addWidget(self.missed_alert_checkbox, alignment=qt2.Qt.AlignmentFlag.AlignCenter)

        self.time_box = time_box
        self.toggle_controls(self.enable_checkbox.isChecked())

    def toggle_controls(self, enabled):
        self.time_box.setVisible(enabled)
        self.missed_alert_checkbox.setVisible(enabled)
