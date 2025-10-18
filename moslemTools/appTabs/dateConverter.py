import pyperclip, winsound,guiTools
from settings import *
from hijridate import Gregorian, Hijri
import PyQt6.QtWidgets as qt
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
            /* Style for disabled buttons */
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
        content_layout = qt.QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        content_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignTop)        
        content_layout.addStretch(1)
        conv_layout = qt.QHBoxLayout()
        conv_layout.setSpacing(10)
        conv_layout.addStretch(1)
        self.l_Converter = qt.QLabel("اختيار نوع التحويل")
        self.l_Converter.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.Converter_combo = qt.QComboBox()
        self.Converter_combo.setAccessibleName("اختيار نوع التحويل")
        self.Converter_combo.addItem("التحويل من هجري الى ميلادي")
        self.Converter_combo.addItem("التحويل من ميلادي الى هجري")
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
        self.Convert = guiTools.QPushButton("التحويل")
        self.Convert.setObjectName("convertButton")        
        self.Convert.clicked.connect(self.convert_date)        
        self.l_result = qt.QLabel("النتيجة")
        self.l_result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)                
        result_area_layout = qt.QVBoxLayout()
        result_area_layout.setSpacing(20)         
        self.result = qt.QLabel()
        self.result.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.result.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        result_area_layout.addWidget(self.result)                
        self.clear_result = guiTools.QPushButton("حذف النتيجة")
        self.clear_result.setStyleSheet("background-color: #8B0000; color: white;")
        self.clear_result.clicked.connect(self.clear_action)
        self.clear_result.setFixedWidth(180) 
        self.clear_result.setEnabled(False)
        self.clear_result.setVisible(False)                 
        clear_button_layout = qt.QHBoxLayout()
        clear_button_layout.addStretch()
        clear_button_layout.addWidget(self.clear_result)
        clear_button_layout.addStretch()
        result_area_layout.addLayout(clear_button_layout)        
        self.copy_result = guiTools.QPushButton("نسخ النتيجة")
        self.copy_result.setObjectName("copyButton")    
        self.copy_result.clicked.connect(self.copy)
        self.copy_result.setEnabled(False)        
        result_controls_layout.addWidget(self.Convert)
        result_controls_layout.addWidget(self.l_result)
        result_controls_layout.addLayout(result_area_layout, 1)
        result_controls_layout.addWidget(self.copy_result)        
        content_layout.addLayout(result_controls_layout)        
        content_layout.addStretch(1)                
        main_layout = qt.QHBoxLayout()
        main_layout.setContentsMargins(150, 20, 150, 20)
        main_layout.addLayout(content_layout)    
        self.setLayout(main_layout)                
        self.update_month_combo()        
        self.year.textChanged.connect(self._reset_result_state)
        self.day.textChanged.connect(self._reset_result_state)
        self.month_combo.currentIndexChanged.connect(self._reset_result_state)
        self.Converter_combo.currentIndexChanged.connect(self._reset_result_state)
        self.Converter_combo.currentIndexChanged.connect(self.update_month_combo)
        self.Converter_combo.currentIndexChanged.connect(self.update_button_text)    
    def clear_action(self):
        self._reset_result_state()
        self.Converter_combo.setFocus()
    def _reset_result_state(self):
        self.result.clear()
        self.copy_result.setEnabled(False)
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
        if not (year_text.isdigit() and day_text.isdigit()):
            self._reset_result_state()
            self.result.setText("الرجاء إدخال أرقام صحيحة.")
            self.result.setFocus()
            return
        year = int(year_text)
        day = int(day_text)
        month = self.month_combo.currentIndex() + 1    
        if not (year > 0 and day > 0):
            self._reset_result_state()
            self.result.setText("الرجاء إدخال أرقام موجبة.")
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
            self.copy_result.setEnabled(True)
            self.clear_result.setEnabled(True)
            self.clear_result.setVisible(True)
            self.result.setFocus()
        except Exception as e:
            self._reset_result_state()
            error_message = "تاريخ هجري غير صالح." if self.Converter_combo.currentIndex() == 0 else "تاريخ ميلادي غير صالح."
            if isinstance(e, ValueError):
                error_message = str(e)
            self.result.setText(error_message)
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