import pyperclip, winsound,guiTools
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
                font-size: 12px;
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
            /* General QPushButton style - Kept as original (gray) */
            QPushButton {
                background-color: #3e3e42;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 10px 15px; /* Increased padding for larger buttons */
                min-height: 38px; /* Reduced min-height for less vertical length */
            }
            QPushButton:hover {
                background-color: #505055;
            }
            QPushButton:pressed {
                background-color: #505055;
            }            
            /* Specific style for copyButton - Still using darker blue */
            QPushButton#copyButton {
                background-color: #0056b3; /* Darker blue */
                color: white;
            }
            QPushButton#copyButton:hover {
                background-color: #003d80; /* Even darker blue on hover */
            }
            QPushButton#copyButton:pressed {
                background-color: #003d80; /* Consistent pressed state with hover */
            }

            /* Specific style for convertButton - Now back to green like the search button */
            QPushButton#convertButton {
                background-color: #008000; /* Green color changed to match quran.py custom button */
                color: white;
            }
            QPushButton#convertButton:hover {
                background-color: #006600; /* Darker green on hover */
            }
            QPushButton#convertButton:pressed {
                background-color: #006600; /* Consistent pressed state with hover */
            }
        """)        
        content_layout = qt.QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)
        content_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignTop)        
        conv_layout = qt.QHBoxLayout()
        conv_layout.setSpacing(10)
        conv_layout.addStretch(1)
        self.l_Converter = qt.QLabel("إختيار نوع التحويل")
        self.l_Converter.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.Converter_combo = qt.QComboBox()
        self.Converter_combo.setAccessibleName("إختيار نوع التحويل")
        self.Converter_combo.addItem("التحويل من هجري الى ميلادي")
        self.Converter_combo.addItem("التحويل من ميلادي الى هجري")
        self.Converter_combo.currentIndexChanged.connect(self.update_month_combo)
        self.Converter_combo.currentIndexChanged.connect(self.update_button_text)
        conv_layout.addWidget(self.Converter_combo)
        conv_layout.addWidget(self.l_Converter)
        conv_layout.addStretch(1)
        content_layout.addLayout(conv_layout)        
        year_layout = qt.QHBoxLayout()
        year_layout.setSpacing(10)
        self.l_year = qt.QLabel("العام")
        self.l_year.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.year = qt.QLineEdit()
        self.year.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.year.setAccessibleName("العام")
        self.year.setInputMask("9999")
        year_layout.addWidget(self.year, 2)
        year_layout.addWidget(self.l_year, 1)
        content_layout.addLayout(year_layout)
        month_layout = qt.QHBoxLayout()
        month_layout.setSpacing(10)
        self.l_month = qt.QLabel("الشهر")
        self.l_month.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.month_combo = qt.QComboBox()
        self.month_combo.setAccessibleName("الشهر")
        month_layout.addWidget(self.month_combo, 2)
        month_layout.addWidget(self.l_month, 1)
        content_layout.addLayout(month_layout)
        day_layout = qt.QHBoxLayout()
        day_layout.setSpacing(10)
        self.l_day = qt.QLabel("اليوم")
        self.l_day.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.day = qt.QLineEdit()
        self.day.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.day.setAccessibleName("اليوم")
        self.day.textChanged.connect(self.max_number)
        day_layout.addWidget(self.day, 2)
        day_layout.addWidget(self.l_day, 1)
        content_layout.addLayout(day_layout)
        result_controls_layout = qt.QHBoxLayout()
        result_controls_layout.setSpacing(10)
        self.Convert = guiTools.QPushButton("التحويل الى ميلادي")
        self.Convert.setObjectName("convertButton")        
        self.Convert.clicked.connect(self.convert_date)
        self.result = qt.QLabel()
        self.result.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        spacer = qt.QSpacerItem(10, 0, qt.QSizePolicy.Policy.Fixed, qt.QSizePolicy.Policy.Minimum)
        self.l_result = qt.QLabel("النتيجة")
        self.l_result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.copy_result = guiTools.QPushButton("نسخ النتيجة")
        self.copy_result.setObjectName("copyButton")    
        self.copy_result.clicked.connect(self.copy)
        result_controls_layout.addWidget(self.Convert)
        result_controls_layout.addWidget(self.result)
        result_controls_layout.addSpacing(10)
        result_controls_layout.addWidget(self.l_result)
        result_controls_layout.addWidget(self.copy_result)
        content_layout.addLayout(result_controls_layout)        
        container = qt.QWidget()
        container.setLayout(content_layout)
        container.setMaximumWidth(600)
        right_layout = qt.QHBoxLayout()
        right_layout.addStretch()
        right_layout.addWidget(container)
        right_layout.addStretch()
        self.setLayout(right_layout)
        self.update_month_combo()
    def max_number(self):
        if self.day.text() > "31":
            self.day.clear()
            self.day.setText("0")
    def copy(self):
        pyperclip.copy(self.result.text())
        winsound.Beep(1000, 100)
    def update_button_text(self):
        if self.Converter_combo.currentIndex() == 0:
            self.Convert.setText("التحويل الى ميلادي")
        else:
            self.Convert.setText("التحويل الى هجري")
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
        month = self.month_combo.currentIndex() + 1
        if not (year_text.isdigit() and day_text.isdigit()):
            self.result.setFocus()
            self.result.setText("الرجاء إدخال أرقام صحيحة.")
            return
        year = int(year_text)
        day = int(day_text)
        if self.Converter_combo.currentIndex() == 0:
            try:
                hijri_date = Hijri(year, month, day)
                gregorian_date = hijri_date.to_gregorian()
                result_str = f"{days_of_week[gregorian_date.weekday()]} - {gregorian_date.day} {self.get_gregorian_month_name(gregorian_date.month)} {gregorian_date.year}"
                self.result.setFocus()
                self.result.setText(result_str)
            except Exception:
                self.result.setFocus()
                self.result.setText("تاريخ هجري غير صالح.")
        else:
            try:
                gregorian_date = Gregorian(year, month, day)
                hijri_date = gregorian_date.to_hijri()
                result_str = f"{days_of_week[gregorian_date.weekday()]} - {hijri_date.day} {self.get_hijri_month_name(hijri_date.month)} {hijri_date.year}"
                self.result.setFocus()
                self.result.setText(result_str)
            except Exception:
                self.result.setFocus()
                self.result.setText("تاريخ ميلادي غير صالح.")
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