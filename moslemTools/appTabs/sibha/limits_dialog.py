import os, json, guiTools
from settings import app
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from .limit_input_dialog import LimitInputDialog

limits_path = os.path.join(os.getenv('appdata'), app.appName, "limits.json")


class LimitsDialog(qt.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab = parent
        self.setWindowTitle("قائمة الحدود")
        self.limits_data = parent.limits_data if parent and hasattr(parent, 'limits_data') else {"limits": {}, "active": None}
        qt1.QShortcut("Escape", self).activated.connect(self.close)
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.label = qt.QLabel("قائمة الحدود")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.label.setFont(font)
        layout.addWidget(self.label)
        self.combo = qt.QComboBox()
        self.combo.setAccessibleName("قائمة الحدود")
        self.combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.combo.setStyleSheet("QComboBox {min-height: 40px; font-size: 15px; font-weight: bold; padding: 4px 10px;}")
        self.combo.currentIndexChanged.connect(self.on_selection_changed)
        layout.addWidget(self.combo)
        btns_layout = qt.QHBoxLayout()
        btns_layout.setSpacing(10)
        self.add_btn = guiTools.QPushButton("إضافة حد")
        self.add_btn.setStyleSheet("QPushButton {background-color: #008000; color: white; min-height: 40px; font-size: 14px; font-weight: bold; border-radius: 4px; padding: 6px 14px;}")
        self.add_btn.clicked.connect(self.add_new_limit)
        self.delete_all_btn = guiTools.QPushButton("حذف كل الحدود")
        self.delete_all_btn.setStyleSheet("QPushButton {background-color: #8B0000; color: white; min-height: 40px; font-size: 14px; font-weight: bold; border-radius: 4px; padding: 6px 14px;}")
        self.delete_all_btn.clicked.connect(self.delete_all_limits)
        self.set_active_btn = guiTools.QPushButton("تعيين الحد المحدد")
        self.set_active_btn.setStyleSheet("QPushButton {background-color: #0000AA; color: white; min-height: 40px; font-size: 14px; font-weight: bold; border-radius: 4px; padding: 6px 14px;}")
        self.set_active_btn.clicked.connect(self.toggle_active_limit)
        self.delete_btn = guiTools.QPushButton("حذف الحد المحدد")
        self.delete_btn.setStyleSheet("QPushButton {background-color: #8B0000; color: white; min-height: 40px; font-size: 14px; font-weight: bold; border-radius: 4px; padding: 6px 14px;}")
        self.delete_btn.clicked.connect(self.delete_current_limit)
        for btn in (self.add_btn, self.delete_all_btn, self.set_active_btn, self.delete_btn):
            btn.setAutoDefault(False)
            btn.setDefault(False)
        btns_layout.addWidget(self.add_btn)
        btns_layout.addWidget(self.delete_all_btn)
        btns_layout.addWidget(self.set_active_btn)
        btns_layout.addWidget(self.delete_btn)
        layout.addLayout(btns_layout)
        self.populate_limits()
        self.update_window_size()

    def update_window_size(self):
        fm = self.fontMetrics()
        longest_combo_text = 0
        for i in range(self.combo.count()):
            longest_combo_text = max(longest_combo_text, fm.horizontalAdvance(self.combo.itemText(i)))
        combo_needed = longest_combo_text + 90
        buttons = [self.add_btn, self.delete_all_btn, self.set_active_btn, self.delete_btn]
        buttons_total = sum(b.sizeHint().width() for b in buttons) + 30 + 40
        label_needed = fm.horizontalAdvance(self.label.text()) + 40
        needed_width = max(combo_needed, buttons_total, label_needed, 540)
        self.setMinimumWidth(needed_width)
        self.resize(needed_width, self.sizeHint().height())

    def showEvent(self, event):
        super().showEvent(event)
        self.update_window_size()

    def populate_limits(self, select_name=None):
        self.combo.blockSignals(True)
        self.combo.clear()
        limits = self.limits_data.get("limits", {})
        active = self.limits_data.get("active")
        if not limits:
            self.combo.addItem("لا توجد حدود مضافة", userData=None)
            self.set_active_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.delete_all_btn.setEnabled(False)
            self.set_active_btn.setText("تعيين الحد المحدد")
        else:
            self.set_active_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.delete_all_btn.setEnabled(True)
            target_index = 0
            for idx, (name, value) in enumerate(limits.items()):
                if name == active:
                    display_text = f"{name} ({value}) - (مفعل)"
                else:
                    display_text = f"{name} ({value})"
                self.combo.addItem(display_text, userData=name)
                if select_name and name == select_name:
                    target_index = idx
                elif not select_name and name == active:
                    target_index = idx
            self.combo.setCurrentIndex(target_index)
        self.combo.blockSignals(False)
        self.on_selection_changed()
        self.update_window_size()

    def on_selection_changed(self):
        current_name = self.combo.currentData()
        if not current_name:
            self.set_active_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.set_active_btn.setText("تعيين الحد المحدد")
            return
        self.set_active_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        active = self.limits_data.get("active")
        if current_name == active:
            self.set_active_btn.setText("إلغاء تعيين الحد المحدد")
        else:
            self.set_active_btn.setText("تعيين الحد المحدد")
        self.update_window_size()

    def toggle_active_limit(self):
        current_name = self.combo.currentData()
        if not current_name:
            return
        active = self.limits_data.get("active")
        if current_name == active:
            self.limits_data["active"] = None
            self.save_data()
            self.populate_limits(select_name=current_name)
            guiTools.speak(f"تم إلغاء تعيين الحد الأقصى {current_name}")
        else:
            self.limits_data["active"] = current_name
            self.save_data()
            self.populate_limits(select_name=current_name)
            value = self.limits_data["limits"].get(current_name, "")
            guiTools.speak(f"تم تعيين الحد الأقصى {current_name} بقيمة {value}")

    def delete_current_limit(self):
        current_name = self.combo.currentData()
        if not current_name:
            return
        question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", f"هل تريد حذف الحد الأقصى {current_name}؟", "نعم", "لا")
        if question == 0:
            if current_name in self.limits_data.get("limits", {}):
                del self.limits_data["limits"][current_name]
            if self.limits_data.get("active") == current_name:
                self.limits_data["active"] = None
            self.save_data()
            guiTools.speak(f"تم حذف الحد الأقصى {current_name}")
            if not self.limits_data.get("limits"):
                self.close()
            else:
                self.populate_limits()

    def delete_all_limits(self):
        if not self.limits_data.get("limits"):
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا توجد حدود مضافة لحذفها")
            return
        question = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف الكلي", "هل تريد حذف جميع الحدود المضافة؟", "نعم", "لا")
        if question == 0:
            self.limits_data["limits"] = {}
            self.limits_data["active"] = None
            self.save_data()
            guiTools.speak("تم حذف جميع الحدود المضافة")
            self.close()

    def add_new_limit(self):
        name, value, ok = LimitInputDialog.getLimitData(self)
        if ok and name:
            if "limits" not in self.limits_data:
                self.limits_data["limits"] = {}
            self.limits_data["limits"][name] = value
            self.save_data()
            self.populate_limits(select_name=name)
            guiTools.speak(f"تم إضافة الحد الأقصى {name} بقيمة {value}")

    def save_data(self):
        with open(limits_path, "w", encoding="utf-8") as file:
            json.dump(self.limits_data, file, ensure_ascii=False, indent=4)
        if self.parent_tab and hasattr(self.parent_tab, 'limits_data'):
            self.parent_tab.limits_data = self.limits_data
        if self.parent_tab and hasattr(self.parent_tab, 'update_limit_button_text'):
            self.parent_tab.update_limit_button_text()
