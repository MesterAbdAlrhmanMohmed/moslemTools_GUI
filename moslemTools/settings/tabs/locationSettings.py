from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import os, shutil,guiTools,webbrowser
class LocationSettings(qt.QWidget):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("""            
            }
            QCheckBox, QLineEdit {                
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
            QPushButton {
                background-color: #0000AA; /* اللون الأزرق من شاشة الموت */
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
            }
        """)
        layout = qt.QVBoxLayout(self)
        self.autoDetectLocation=qt.QCheckBox("تحديد الموقع تلقائيا، ليس دقيقا في كل الحالات")
        self.autoDetectLocation.setChecked(p.cbts(settings_handler.get("location","autoDetect")))
        self.autoDetectLocation.stateChanged.connect(self.onStateChanged)
        layout.addWidget(self.autoDetectLocation)
        self.LT1l=qt.QLabel("خط الطول")
        self.LT1l.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.LT1=qt.QDoubleSpinBox()
        self.LT1.setAccessibleName("خط الطول")
        self.LT1.setRange(0.0001,360.0000)
        self.LT1.setDecimals(8)
        self.LT1.setValue(float(settings_handler.get("location","LT1")))
        self.LT1.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        layout.addWidget(self.LT1l)
        layout.addWidget(self.LT1)
        self.LT2l=qt.QLabel("خط الطول")
        self.LT2l.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.LT2=qt.QDoubleSpinBox()
        self.LT2.setAccessibleName("دائرة العرض")
        self.LT2.setRange(0,180)
        self.LT2.setValue(float(settings_handler.get("location","LT2")))
        self.LT2.setDecimals(8)
        self.LT2.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        layout.addWidget(self.LT2l)
        layout.addWidget(self.LT2)
        self.dl_app=qt.QPushButton("تحميل تطبيق معرفة خطوط الطول ودوائر العرض للأندرويد")
        self.dl_app.clicked.connect(lambda: webbrowser.open("https://play.google.com/store/apps/details?id=com.mylocation.latitudelongitude"))
        self.dl_app.setStyleSheet("background-color: #0000AA; color: #e0e0e0;")
        self.dl_app.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        self.LT2l.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        self.LT1l.setVisible(p.cbts(settings_handler.get("location","autoDetect"))==False)
        layout.addWidget(self.dl_app)
        self.dl_app1=qt.QPushButton("تحميل تطبيق معرفة خطوط الطول ودوائر العرض للios")
        self.dl_app1.clicked.connect(lambda: webbrowser.open("https://apps.apple.com/us/app/find-my-latitude-and-longitude/id668745605"))
        self.dl_app1.setStyleSheet("background-color: #0000AA; color: #e0e0e0;")
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