import os
import datetime
import ctypes
from ctypes import wintypes
from hijridate import Gregorian
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from settings import settings_handler, app
import guiTools
from appTabs import AboutDeveloper
from .display_name import get_smart_display_name


class WindowEventsMixin:
    def showEvent(self, event):
        super().showEvent(event)
        MF_BYCOMMAND = 0x00000000
        SC_SIZE = 0xF000
        SC_MOVE = 0xF010
        SC_MINIMIZE = 0xF020
        SC_MAXIMIZE = 0xF030
        SC_RESTORE = 0xF120
        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_SYSMENU = 0x00080000
        user32 = ctypes.windll.user32
        GetWindowLong = user32.GetWindowLongW
        SetWindowLong = user32.SetWindowLongW
        hwnd = self.winId().__int__()
        hMenu = user32.GetSystemMenu(hwnd, False)
        if hMenu:
            for cmd in (SC_SIZE, SC_MOVE, SC_MINIMIZE, SC_MAXIMIZE, SC_RESTORE):
                user32.RemoveMenu(hMenu, cmd, MF_BYCOMMAND)
            user32.DrawMenuBar(hwnd)
        style = GetWindowLong(hwnd, GWL_STYLE)
        new_style = WS_CAPTION | WS_SYSMENU
        SetWindowLong(hwnd, GWL_STYLE, new_style)
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0020)

    def _restore(self):
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.show_action.setText("إظهار البرنامج")
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.show_action.setText("إخفاء البرنامج")

    def closeEvent(self, event):
        if app.exit:
            if settings_handler.get("g", "exitDialog") == "True":
                m = guiTools.ExitApp(self)
                m.exec()
                if m:
                    event.ignore()
            else:
                self.close()
        else:
            self.close()

    def open_developers_window(self):
        self.developers_window = AboutDeveloper()
        self.developers_window.exec()

    def viewInfoTextEdit(self):
        use_name_enabled = (settings_handler.get("g", "use_name_in_occasions") == "True")
        username1 = get_smart_display_name() if use_name_enabled else ""
        gender = settings_handler.get("g", "user_gender") or "ذكر"
        is_female = (gender == "أنثى")
        if use_name_enabled:
            ya_name = f" يا {username1}" if username1 else ""
            if is_female:
                la_tansa_comma = f"يا {username1}، لا تَنْسِ، " if username1 else "لا تَنْسِ، "
                la_tansa_no_comma = f"يا {username1} لا تَنْسِ، " if username1 else "لا تَنْسِ، "
                la_tansa_direct = f"يا {username1}، لا تَنْسِ " if username1 else "لا تَنْسِ "
                la_tansa_direct_no_comma = f"يا {username1} لا تَنْسِ " if username1 else "لا تَنْسِ "
                default_dhikr = f"لا تَنْسِ يا {username1} ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم" if username1 else "لا تَنْسِ ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
            else:
                la_tansa_comma = f"يا {username1}، لا تَنْسَ، " if username1 else "لا تَنْسَ، "
                la_tansa_no_comma = f"يا {username1} لا تَنْسَ، " if username1 else "لا تَنْسَ، "
                la_tansa_direct = f"يا {username1}، لا تَنْسَ " if username1 else "لا تَنْسَ "
                la_tansa_direct_no_comma = f"يا {username1} لا تَنْسَ " if username1 else "لا تَنْسَ "
                default_dhikr = f"لا تَنْسَ يا {username1} ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم" if username1 else "لا تَنْسَ ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
        else:
            ya_name = ""
            la_tansa_comma = ""
            la_tansa_no_comma = ""
            la_tansa_direct = ""
            la_tansa_direct_no_comma = ""
            default_dhikr = "ذِكْر الله، والصلاة على أشرف الخلق: النبي محمد صلى الله عليه وسلم"
        try:
            hijri_date_obj = Gregorian.today().to_hijri()
            current_gregorian_weekday = datetime.datetime.now().weekday()
            if current_gregorian_weekday == 4:
                self.info.setText(f"جمعة مباركة{ya_name}، تشغيل أو قراءة سورة الكهف في هذا اليوم سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 9:
                if 21 <= hijri_date_obj.day <= 29:
                    if not use_name_enabled:
                        self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزق الجميع فضل ليلة القدر، ولا تنسوني من صالح الدعاء، وجزاكم الله خيرا.")
                    elif is_female:
                        self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزقكِ فضل ليلة القدر، ولا تنسيني من صالح دعائكِ، وجزاكِ الله خيراً.")
                    else:
                        if username1:
                            self.info.setText(f"العشر الأواخر من رمضان، الله يرزقك فضل ليلة القدر يا {username1}، لا تنساني من صالح دعاءك، وجزاك الله خيرا.")
                        else:
                            self.info.setText("العشر الأواخر من رمضان، أسأل الله أن يرزق الجميع فضل ليلة القدر، ولا تنسوني من صالح الدعاء، وجزاكم الله خيرا.")
                else:
                    self.info.setText(f"رمضان كريم{ya_name}")
            elif hijri_date_obj.month == 10 and hijri_date_obj.day == 1:
                self.info.setText(f"عيد فطر مبارك{ya_name}")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 10:
                self.info.setText(f"عيد أضحى مبارك{ya_name}")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [11, 12, 13]:
                self.info.setText("أيام التشريق، أيام أكل وشرب وذكر لله")
            elif current_gregorian_weekday == 0:
                self.info.setText(f"{la_tansa_no_comma}صيام يوم الإثنين، سنة عن النبي صلى الله عليه وسلم")
            elif current_gregorian_weekday == 3:
                self.info.setText(f"{la_tansa_no_comma}صيام يوم الخميس، سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 1:
                if not use_name_enabled:
                    self.info.setText("كل عام وأنتم بخير بمناسبة رأس السنة الهجرية الجديدة")
                elif is_female:
                    self.info.setText(f"كل عام وأنتِ بخير{ya_name} بمناسبة رأس السنة الهجرية الجديدة")
                else:
                    self.info.setText(f"كل عام وأنتَ بخير{ya_name} بمناسبة رأس السنة الهجرية الجديدة")
            elif hijri_date_obj.month == 1 and hijri_date_obj.day == 10:
                self.info.setText(f"{la_tansa_no_comma}صيام عاشوراء، مستحب عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 7 and hijri_date_obj.day == 27:
                self.info.setText("ذكرى الإسراء والمعراج")
            elif hijri_date_obj.month == 8 and hijri_date_obj.day == 15:
                if is_female:
                    self.info.setText(f"{la_tansa_comma}ليلة النصف من شعبان، يستحب فيها الدعاء")
                else:
                    self.info.setText(f"{la_tansa_no_comma}ليلة النصف من شعبان، يستحب فيها الدعاء")
            elif hijri_date_obj.month == 8:
                self.info.setText(f"{la_tansa_no_comma}يستحب الصيام في شهر شعبان")
            elif hijri_date_obj.month == 10:
                if is_female:
                    self.info.setText(f"{la_tansa_direct}صيام الست أيام البيض في شهر شوال، وهي سنة عن النبي صلى الله عليه وسلم")
                else:
                    self.info.setText(f"{la_tansa_no_comma}صيام الست أيام البيض في شهر شوال، وهي سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day == 9:
                self.info.setText(f"{la_tansa_direct_no_comma}صيام يوم عرفة، صيام يغفر ذنوب السنة الماضية والسنة القادمة")
            elif hijri_date_obj.month == 12 and hijri_date_obj.day in [1, 2, 3, 4, 5, 6, 7, 8]:
                self.info.setText(f"{la_tansa_comma}صيام العشر الأوائل من ذي الحجة سنة عن النبي صلى الله عليه وسلم")
            elif hijri_date_obj.day in [13, 14, 15]:
                self.info.setText(f"{la_tansa_comma}صيام الأيام القمرية، سنة عن النبي صلى الله عليه وسلم")
            else:
                self.info.setText(default_dhikr)
        except Exception as e:
            print(f"حدث خطأ: {e}")
            self.info.setText(default_dhikr)

    def onToolChanged(self, current, previous):
        self.quranPlayer.mp.pause()
        self.researcher.media_player.pause()

    def adjust_list_widget_width(self, index=None):
        fm = qt1.QFontMetrics(self.list_widget.font())
        current_text = self.list_widget.currentText()
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        self.list_widget.setFixedWidth(text_width + 65)

    def open_error_log_file(self):
        log_path = os.path.join(os.getenv('appdata'), settings_handler.appName, "error.log")
        if not os.path.exists(log_path):
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                print(f"Handled exception: {e}")
        try:
            os.startfile(log_path)
        except Exception as e:
            guiTools.MessageBox.error(self, "خطأ", f"تعذر فتح ملف السجل: {e}")
