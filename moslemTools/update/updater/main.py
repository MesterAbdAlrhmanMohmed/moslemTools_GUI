from update.updater.thread import DownloadUpdateThread
import os ,shutil ,subprocess ,requests ,settings ,guiTools ,time 
import PyQt6 .QtWidgets as qt 
import PyQt6 .QtGui as qt1 
import PyQt6 .QtCore as qt2 




class DownloadUpdateGUI (qt .QDialog ):
    def __init__ (self ,p ,URL ):
        super ().__init__ (p )
        self .setWindowTitle ("جاري التحديث")
        self .setMinimumSize (500 ,220 )
        self .resize (650 ,280 )
        self .center ()
        layout =qt .QVBoxLayout (self )

        self .state =guiTools .QNavigableLabel ("يجري الآن تحميل التحديث")
        self .state .setAlignment (qt2 .Qt .AlignmentFlag .AlignCenter )
        self .state .setFocusPolicy (qt2 .Qt .FocusPolicy .StrongFocus )
        font =qt1 .QFont ()
        font .setBold (True )
        self .state .setFont (font )
        layout .addWidget (self .state )

        self .downloading =qt .QProgressBar ()
        self .downloading .setFocusPolicy (qt2 .Qt .FocusPolicy .StrongFocus )
        self .downloading .setRange (0 ,100 )
        self .downloading .setAccessibleName ("حالة التحميل")
        self .downloading .setValue (0 )
        layout .addWidget (self .downloading )

        btns_layout =qt .QHBoxLayout ()
        self .pause_button =guiTools .QPushButton ("إيقاف مؤقت")
        self .pause_button .setStyleSheet ("QPushButton {background-color: #0000AA; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px;} QPushButton:hover {background-color: #0000CC;}")
        self .pause_button .clicked .connect (self .toggle_pause )
        btns_layout .addWidget (self .pause_button )

        self .cancel =guiTools .QPushButton ("إلغاء")
        self .cancel .setStyleSheet ("QPushButton {background-color: #8B0000; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px;} QPushButton:hover {background-color: #A52A2A;}")
        self .cancel .clicked .connect (self .cancelBTN )
        btns_layout .addWidget (self .cancel )

        layout .addLayout (btns_layout )

        qt1 .QShortcut ("Escape",self ).activated .connect (self .cancelBTN )

        self .thread =DownloadUpdateThread (URL ,self )
        self .thread .progress .connect (self .change )
        self .thread .installing .connect (self .Installation )
        self .thread .finish .connect (self .finish )
        self .thread .network_error .connect (self .on_network_error )
        self .thread .start ()

    def center (self ):
        frame_geometry =self .frameGeometry ()
        screen_center =qt1 .QGuiApplication .primaryScreen ().availableGeometry ().center ()
        frame_geometry .moveCenter (screen_center )
        self .move (frame_geometry .topLeft ())

    def toggle_pause (self ):
        if self .thread and self .thread .isRunning ():
            if self .thread .is_paused :
                self .pause_button .setText ("إيقاف مؤقت")
                self .thread .resume ()
            else :
                self .pause_button .setText ("استئناف")
                self .thread .pause ()

    def on_network_error (self ,msg ):
        self .pause_button .setText ("استئناف")
        guiTools .MessageBox .error (self ,"انقطاع الاتصال",msg )

    def Installation (self ,choice ):
        if choice =="yes":
            self .state .setText ("جاري التثبيت")
            self .downloading .setValue (0 )

    def change (self ,progress ):
        self .downloading .setValue (progress )

    def finish (self ,c ):
        if c =="error":
            guiTools .MessageBox .error (self ,"خطأ","خطأ أثناء التحميل الرجاء المحاولة لاحقا")
            self .close ()
        elif c =="cancelled":
            self .close ()
        else :
            import sys 
            cmd =f'timeout /t 2 /nobreak > NUL && start "" "{c}"'
            subprocess .Popen (cmd ,shell =True )
            qt .QApplication .quit ()
            sys .exit (0 )

    def cancelBTN (self ):
        if self .thread and self .thread .isRunning ():
            result =guiTools .QQuestionMessageBox .view (self ,"تأكيد الإلغاء","هل تريد إلغاء عملية تحميل التحديث؟","نعم","لا")
            if result ==0 :
                self .thread .cancel ()
                self .thread .terminate ()
                self .close ()
        else :
            self .close ()

    def closeEvent (self ,a0 ):
        if self .thread and self .thread .isRunning ():
            result =guiTools .QQuestionMessageBox .view (self ,"تأكيد الإلغاء","هل تريد إلغاء عملية تحميل التحديث؟","نعم","لا")
            if result ==0 :
                self .thread .cancel ()
                self .thread .terminate ()
                a0 .accept ()
            else :
                a0 .ignore ()
        else :
            a0 .accept ()


