import pyperclip, winsound, guiTools
from settings import *
from hijridate import Gregorian, Hijri
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class DateConverter(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton {
                background-color: #3e3e42;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 10px 15px;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #505055;
            }
            QPushButton:pressed {
                background-color: #505055;
            }
            QPushButton:disabled {
                background-color: #2a2a2d;
                border: 1px solid #4a4a4a;
                color: #787878;
            }
            QPushButton#copyButton {
                background-color: #0056b3;
                color: white;
            }
            QPushButton#copyButton:hover {
                background-color: #003d80;
            }
            QPushButton#copyButton:pressed {
                background-color: #003d80;
            }
            QPushButton#convertButton {
                background-color: #008000;
                color: white;
            }
            QPushButton#convertButton:hover {
                background-color: #006600;
            }
            QPushButton#convertButton:pressed {
                background-color: #006600;
            }
        """)
        container = qt.QWidget()
        container.setMaximumWidth(550)
        content_layout = qt.QVBoxLayout(container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)
        content_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignTop)
        grid_layout = qt.QGridLayout()
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(12)
        self.l_Converter = qt.QLabel("اختيار نوع التحويل")
        self.l_Converter.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft | qt2.Qt.AlignmentFlag.AlignVCenter)
        self.Converter_combo = qt.QComboBox()
        self.Converter_combo.setAccessibleName("اختيار نوع التحويل")
        self.Converter_combo.addItem("التحويل من هجري إلى ميلادي")
        self.Converter_combo.addItem("التحويل من ميلادي إلى هجري")
        grid_layout.addWidget(self.Converter_combo, 0, 0)
        grid_layout.addWidget(self.l_Converter, 0, 1)
        self.l_year = qt.QLabel("العام")
        self.l_year.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft | qt2.Qt.AlignmentFlag.AlignVCenter)
        self.year = qt.QLineEdit()
        self.year.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.year.setAccessibleName("العام")
        self.year.setInputMask("9999")
        grid_layout.addWidget(self.year, 1, 0)
        grid_layout.addWidget(self.l_year, 1, 1)
        self.l_month = qt.QLabel("الشهر")
        self.l_month.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft | qt2.Qt.AlignmentFlag.AlignVCenter)
        self.month_combo = qt.QComboBox()
        self.month_combo.setAccessibleName("الشهر")
        grid_layout.addWidget(self.month_combo, 2, 0)
        grid_layout.addWidget(self.l_month, 2, 1)
        self.l_day = qt.QLabel("اليوم")
        self.l_day.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft | qt2.Qt.AlignmentFlag.AlignVCenter)
        self.day = qt.QLineEdit()
        self.day.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.day.setAccessibleName("اليوم")
        self.day.textChanged.connect(self.max_number)
        grid_layout.addWidget(self.day, 3, 0)
        grid_layout.addWidget(self.l_day, 3, 1)
        grid_layout.setColumnStretch(0, 3)
        grid_layout.setColumnStretch(1, 1)
        content_layout.addLayout(grid_layout)
        self.Convert = guiTools.QPushButton("التحويل إلى ميلادي")
        self.Convert.setObjectName("convertButton")
        self.Convert.clicked.connect(self.convert_date)
        content_layout.addWidget(self.Convert)
        result_area_layout = qt.QVBoxLayout()
        result_area_layout.setSpacing(6)
        result_display_layout = qt.QHBoxLayout()
        result_display_layout.setSpacing(15)
        result_display_layout.addStretch(1)
        self.l_result = qt.QLabel("النتيجة:")
        self.l_result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.l_result.setVisible(False)
        self.result = guiTools.QNavigableLabel()
        self.result.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.result.setVisible(False)
        result_display_layout.addWidget(self.result)
        result_display_layout.addWidget(self.l_result)
        result_display_layout.addStretch(1)
        result_area_layout.addLayout(result_display_layout)
        result_buttons_layout = qt.QHBoxLayout()
        result_buttons_layout.setSpacing(10)
        result_buttons_layout.addStretch(1)
        self.copy_result = guiTools.QPushButton("نسخ النتيجة")
        self.copy_result.setObjectName("copyButton")
        self.copy_result.clicked.connect(self.copy)
        self.copy_result.setEnabled(False)
        self.copy_result.setVisible(False)
        result_buttons_layout.addWidget(self.copy_result)
        self.clear_result = guiTools.QPushButton("حذف النتيجة")
        self.clear_result.setStyleSheet("background-color: #8B0000; color: white;")
        self.clear_result.clicked.connect(self.clear_action)
        self.clear_result.setMinimumWidth(140)
        self.clear_result.setEnabled(False)
        self.clear_result.setVisible(False)
        result_buttons_layout.addWidget(self.clear_result)
        result_buttons_layout.addStretch(1)
        result_area_layout.addLayout(result_buttons_layout)
        content_layout.addLayout(result_area_layout)
        main_layout = qt.QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignTop)
        main_layout.addStretch(1)
        main_layout.addWidget(container)
        main_layout.addStretch(1)
        self.update_month_combo()
        self.adjust_converter_combo_width()
        self.year.textChanged.connect(self._reset_result_state)
        self.day.textChanged.connect(self._reset_result_state)
        self.month_combo.currentIndexChanged.connect(self._reset_result_state)
        self.Converter_combo.currentIndexChanged.connect(self._reset_result_state)
        self.Converter_combo.currentIndexChanged.connect(self.update_month_combo)
        self.Converter_combo.currentIndexChanged.connect(self.update_button_text)
        self.Converter_combo.currentIndexChanged.connect(self.adjust_converter_combo_width)

    def adjust_converter_combo_width(self, index=None):
        fm = qt1.QFontMetrics(self.Converter_combo.font())
        current_text = self.Converter_combo.currentText()
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        self.Converter_combo.setFixedWidth(text_width + 65)

    def clear_action(self):
        self._reset_result_state()
        self.Converter_combo.setFocus()

    def _reset_result_state(self):
        self.result.clear()
        self.l_result.setVisible(False)
        self.result.setVisible(False)
        self.copy_result.setEnabled(False)
        self.copy_result.setVisible(False)
        self.clear_result.setEnabled(False)
        self.clear_result.setVisible(False)

    def max_number(self):
        try:
            if int(self.day.text()) > 31:
                self.day.setText("31")
        except (ValueError, TypeError):
            pass

    def copy(self):
        if self.result.text():
            pyperclip.copy(self.result.text())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النتيجة")

    def update_button_text(self):
        if self.Converter_combo.currentIndex() == 0:
            self.Convert.setText("التحويل إلى ميلادي")
        else:
            self.Convert.setText("التحويل إلى هجري")

    def update_month_combo(self):
        self.month_combo.clear()
        if self.Converter_combo.currentIndex() == 0:
            months = [
                "مُحرَّم", "صَفَر", "رَبيع الأوَّل", "رَبيع الآخِر",
                "جُمادى الأُولى", "جُمادى الآخِرة", "رَجَب", "شَعبان",
                "رَمَضان", "شَوَّال", "ذو القَعدة", "ذو الحِجَّة"
            ]
        else:
            months = [
                "يَنايِر", "فَبرايِر", "مارِس", "أبريل",
                "مايو", "يونيو", "يوليو", "أغسطس",
                "سِبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
            ]
        self.month_combo.addItems(months)

    def convert_date(self):
        days_of_week = [
            "الإثنين", "الثلثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"
        ]
        year_text = self.year.text()
        day_text = self.day.text()
        if not (year_text.isdigit() and day_text.isdigit()):
            self._reset_result_state()
            self.result.setText("الرجاء إدخال أرقام صحيحة.")
            self.l_result.setVisible(True)
            self.result.setVisible(True)
            self.result.setFocus()
            return
        year = int(year_text)
        day = int(day_text)
        month = self.month_combo.currentIndex() + 1
        if not (year > 0 and day > 0):
            self._reset_result_state()
            self.result.setText("الرجاء إدخال أرقام موجبة.")
            self.l_result.setVisible(True)
            self.result.setVisible(True)
            self.result.setFocus()
            return
        try:
            if self.Converter_combo.currentIndex() == 0:
                if year < 1:
                    raise ValueError("التاريخ الهجري يجب أن يكون بعد العام 1.")
                hijri_date = Hijri(year, month, day)
                gregorian_date = hijri_date.to_gregorian()
                result_str = f"{days_of_week[gregorian_date.weekday()]} - {gregorian_date.day} {self.get_gregorian_month_name(gregorian_date.month)} {gregorian_date.year}"
            else:
                gregorian_date = Gregorian(year, month, day)
                hijri_date = gregorian_date.to_hijri()
                result_str = f"{days_of_week[gregorian_date.weekday()]} - {hijri_date.day} {self.get_hijri_month_name(hijri_date.month)} {hijri_date.year}"
            self.result.setText(result_str)
            self.l_result.setVisible(True)
            self.result.setVisible(True)
            self.copy_result.setEnabled(True)
            self.copy_result.setVisible(True)
            self.clear_result.setEnabled(True)
            self.clear_result.setVisible(True)
            self.result.setFocus()
        except Exception as e:
            self._reset_result_state()
            error_message = "تاريخ هجري غير صالح." if self.Converter_combo.currentIndex() == 0 else "تاريخ ميلادي غير صالح."
            if isinstance(e, ValueError):
                error_message = str(e)
            self.result.setText(error_message)
            self.l_result.setVisible(True)
            self.result.setVisible(True)
            self.result.setFocus()

    def get_gregorian_month_name(self, month):
        months = [
            "يَنايِر", "فَبرايِر", "مارِس", "أبريل",
            "مايو", "يونيو", "يوليو", "أغسطس",
            "سِبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
        ]
        return months[month - 1]

    def get_hijri_month_name(self, month):
        months = [
            "مُحرَّم", "صَفَر", "رَبيع الأوَّل", "رَبيع الآخِر",
            "جُمادى الأُولى", "جُمادى الآخِرة", "رَجَب", "شَعبان",
            "رَمَضان", "شَوَّال", "ذو القَعدة", "ذو الحِجَّة"
        ]
        return months[month - 1]
