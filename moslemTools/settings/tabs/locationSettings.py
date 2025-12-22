from settings import settings_handler
from guiTools import speak
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import pyperclip,winsound
class LocationSettings(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""
            QCheckBox, QLineEdit {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
            QPushButton {
                background-color: #0000AA;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 10px;
            }
        """)
        layout = qt.QVBoxLayout(self)
        self.autoDetectLocation=qt.QCheckBox("تحديد الموقع تلقائيا، ليس دقيقا في كل الحالات")
        self.autoDetectLocation.setChecked(p.cbts(settings_handler.get("location","autoDetect")))
        self.autoDetectLocation.stateChanged.connect(self.onStateChanged)
        layout.addWidget(self.autoDetectLocation)
        coords_layout = qt.QHBoxLayout()
        lon_layout = qt.QVBoxLayout()
        self.LT1l=qt.QLabel("خط الطول")
        self.LT1l.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.LT1=qt.QDoubleSpinBox()
        self.LT1.setAccessibleName("خط الطول")
        self.LT1.setRange(0.0001,360.0000)
        self.LT1.setDecimals(8)
        self.LT1.setValue(float(settings_handler.get("location","LT1")))
        self.LT1.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        self.LT1l.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        lon_layout.addWidget(self.LT1l)
        lon_layout.addWidget(self.LT1)
        lat_layout = qt.QVBoxLayout()
        self.LT2l=qt.QLabel("دائرة العرض") 
        self.LT2l.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.LT2=qt.QDoubleSpinBox()
        self.LT2.setAccessibleName("دائرة العرض")
        self.LT2.setRange(0,180)
        self.LT2.setValue(float(settings_handler.get("location","LT2")))
        self.LT2.setDecimals(8)
        self.LT2.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        self.LT2l.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        lat_layout.addWidget(self.LT2l)
        lat_layout.addWidget(self.LT2)
        coords_layout.addLayout(lon_layout)
        coords_layout.addLayout(lat_layout)
        layout.addLayout(coords_layout)
        method_row = qt.QHBoxLayout()
        method_row.setSpacing(20)
        self.methodLabel = qt.QLabel("طريقة حساب مواقيت الصلاة")
        font = qt1.QFont()
        font.setBold(True)
        self.methodCombo = qt.QComboBox()
        self.methodCombo.setFont(font)
        self.methodCombo.setAccessibleName("طريقة حساب مواقيت الصلاة")
        self.methodCombo.setAccessibleDescription("اختر الهيئة المناسبة لبلدك لضمان دقة مواقيت الصلاة")
        self.methods = {
            "5": "مصر وشمال أفريقيا - الهيئة المصرية العامة للمساحة",
            "4": "السعودية والخليج - جامعة أم القرى (مكة المكرمة)",
            "3": "أوروبا وأمريكا والعالم - رابطة العالم الإسلامي",
            "1": "باكستان والهند - جامعة العلوم الإسلامية بكراتشي",
            "2": "أمريكا الشمالية وكندا - الجمعية الإسلامية (ISNA)",
            "12": "فرنسا - اتحاد المنظمات الإسلامية",
            "13": "تركيا - رئاسة الشؤون الدينية",
            "8": "دول الخليج العربي",
            "9": "الكويت - وزارة الأوقاف",
            "10": "قطر - وزارة الأوقاف",
            "11": "سنغافورة (MUIS)",
            "14": "روسيا - الإدارة الدينية للمسلمين"
        }
        current_method_id = settings_handler.get("location", "calculationMethod")
        if not current_method_id: current_method_id = "5"
        index_to_select = 0
        for i, (method_id, method_name) in enumerate(self.methods.items()):
            self.methodCombo.addItem(method_name, method_id)
            if method_id == current_method_id:
                index_to_select = i
        self.methodCombo.setCurrentIndex(index_to_select)
        method_row.addWidget(self.methodCombo, 1)
        method_row.addWidget(self.methodLabel)
        layout.addLayout(method_row)
        def copy_and_beep(link):
            pyperclip.copy(link)
            winsound.Beep(1000, 100)
            speak("تم نسخ رابط التحميل بنجاح")
        self.dl_app=qt.QPushButton("نسخ رابط تحميل تطبيق معرفة خطوط الطول ودوائر العرض للأندرويد")
        self.dl_app.setMinimumHeight(45)
        self.dl_app.clicked.connect(lambda: copy_and_beep("https://play.google.com/store/apps/details?id=com.mylocation.latitudelongitude"))
        self.dl_app.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        layout.addWidget(self.dl_app)
        self.dl_app1=qt.QPushButton("نسخ رابط تحميل تطبيق معرفة خطوط الطول ودوائر العرض للـ iOS")
        self.dl_app1.setMinimumHeight(45)
        self.dl_app1.clicked.connect(lambda: copy_and_beep("https://apps.apple.com/us/app/find-my-latitude-and-longitude/id668745605"))
        self.dl_app1.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        layout.addWidget(self.dl_app1)
        self.info=qt.QLabel("تنبيه هام، عند تحديد الموقع الجغرافي يجب إعادة تحميل مواقيت الصلاة")
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.info)
    def onStateChanged(self,state):
        self.LT1.setVisible(state==False)
        self.LT2.setVisible(state==False)
        self.LT1l.setVisible(state==False)
        self.LT2l.setVisible(state==False)
        self.dl_app.setVisible(state==False)
        self.dl_app1.setVisible(state==False)