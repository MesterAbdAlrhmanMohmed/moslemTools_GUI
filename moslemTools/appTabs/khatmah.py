import os, math, datetime
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools, settings, functions, gui

def format_pages(n):
    if n == 0:
        return "0 صفحة"
    elif n == 1:
        return "صفحة واحدة"
    elif n == 2:
        return "صفحتان"
    elif 3 <= n <= 10:
        return f"{n} صفحات"
    else:
        return f"{n} صفحة"

def format_days(n):
    if n == 0:
        return "0 يوم"
    elif n == 1:
        return "يوم واحد"
    elif n == 2:
        return "يومان"
    elif 3 <= n <= 10:
        return f"{n} أيام"
    else:
        return f"{n} يوماً"

class KhatmahTab(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        self.khatmah_path = os.path.join(os.getenv('appdata'), settings.app.appName, "khatmah.json")
        self.data = self.load_data()
        self.init_ui()

    def load_data(self):
        if not os.path.exists(self.khatmah_path):
            default_data = {
                "has_khatmah": False,
                "target_days": 30,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": 20,
                "completed_pages": 0,
                "is_completed": False
            }
            self.save_data(default_data)
            return default_data
        try:
            with open(self.khatmah_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "has_khatmah" not in data:
                    data["has_khatmah"] = False
                return data
        except Exception:
            default_data = {
                "has_khatmah": False,
                "target_days": 30,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": 20,
                "completed_pages": 0,
                "is_completed": False
            }
            self.save_data(default_data)
            return default_data

    def save_data(self, data=None):
        if data is None:
            data = self.data
        try:
            with open(self.khatmah_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def init_ui(self):
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        font_bold = qt1.QFont()
        font_bold.setBold(True)

        config_group = qt.QGroupBox()
        config_group.setFont(font_bold)
        config_layout = qt.QVBoxLayout(config_group)
        config_layout.setSpacing(8)

        self.days_label = qt.QLabel("أكتب المدة المستهدفة بالأيام (من 1 إلى 365)")
        self.days_label.setFont(font_bold)
        self.days_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.days_spin = qt.QSpinBox()
        self.days_spin.setFont(font_bold)
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(self.data.get("target_days", 30))
        self.days_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.days_spin.setAccessibleName("أكتب المدة المستهدفة بالأيام (من 1 إلى 365)")
        self.days_spin.setMinimumWidth(180)

        self.btn_start = guiTools.QPushButton("بدء ختمة جديدة")
        self.btn_start.setFont(font_bold)
        self.btn_start.setStyleSheet("background-color: #008000; color: white;")
        self.btn_start.setMinimumWidth(180)
        self.btn_start.clicked.connect(self.start_new_khatmah)

        config_layout.addWidget(self.days_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        config_layout.addWidget(self.days_spin, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        config_layout.addWidget(self.btn_start, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(config_group)

        self.status_group = qt.QGroupBox()
        self.status_group.setFont(font_bold)
        status_layout = qt.QVBoxLayout(self.status_group)
        status_layout.setSpacing(10)

        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 604)
        self.progress_bar.setValue(self.data.get("completed_pages", 0))
        self.progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progress_bar.setAccessibleName("نسبة التقدم في الختمة")
        status_layout.addWidget(self.progress_bar)

        self.info_text = guiTools.QReadOnlyTextEdit(viewer_name="khatmahTab")
        self.info_text.setAccessibleName("معلومات الختمة")
        status_layout.addWidget(self.info_text)

        main_layout.addWidget(self.status_group)

        self.actions_widget = qt.QWidget()
        actions_layout = qt.QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_read_today = guiTools.QPushButton("قراءة ورد اليوم")
        self.btn_read_today.setFont(font_bold)
        self.btn_read_today.setStyleSheet("background-color: #0000AA; color: white;")
        self.btn_read_today.setShortcut("ctrl+r")
        self.btn_read_today.setAccessibleDescription("control plus r")
        self.btn_read_today.clicked.connect(self.read_today_ward)

        self.btn_mark_today = guiTools.QPushButton("تسجيل إتمام ورد اليوم")
        self.btn_mark_today.setFont(font_bold)
        self.btn_mark_today.setStyleSheet("background-color: #008000; color: white;")
        self.btn_mark_today.setShortcut("ctrl+t")
        self.btn_mark_today.setAccessibleDescription("control plus t")
        self.btn_mark_today.clicked.connect(self.mark_today_completed)

        self.btn_manual_page = guiTools.QPushButton("تحديث الصفحة يدوياً")
        self.btn_manual_page.setFont(font_bold)
        self.btn_manual_page.setStyleSheet("background-color: #0056b3; color: white;")
        self.btn_manual_page.setShortcut("ctrl+u")
        self.btn_manual_page.setAccessibleDescription("control plus u")
        self.btn_manual_page.clicked.connect(self.update_page_manually)

        self.btn_reset = guiTools.QPushButton("إعادة تعيين الختمة")
        self.btn_reset.setFont(font_bold)
        self.btn_reset.setStyleSheet("background-color: #8E2405; color: white;")
        self.btn_reset.setShortcut("ctrl+delete")
        self.btn_reset.setAccessibleDescription("control plus delete")
        self.btn_reset.clicked.connect(self.reset_khatmah)

        self.btn_stop = guiTools.QPushButton("إيقاف الختمة")
        self.btn_stop.setFont(font_bold)
        self.btn_stop.setStyleSheet("background-color: #8B0000; color: white;")
        self.btn_stop.setShortcut("ctrl+f")
        self.btn_stop.setAccessibleDescription("control plus f")
        self.btn_stop.clicked.connect(self.stop_khatmah)

        actions_layout.addWidget(self.btn_read_today)
        actions_layout.addWidget(self.btn_mark_today)
        actions_layout.addWidget(self.btn_manual_page)
        actions_layout.addWidget(self.btn_reset)
        actions_layout.addWidget(self.btn_stop)

        main_layout.addWidget(self.actions_widget)
        self.update_ui_state()

    def update_ui_state(self):
        has_khatmah = self.data.get("has_khatmah", False)
        self.actions_widget.setVisible(has_khatmah)
        self.progress_bar.setVisible(has_khatmah)
        if not has_khatmah:
            self.progress_bar.setValue(0)
            self.info_text.setText("لا توجد ختمة قائمة حالياً.")
            return

        completed_pages = self.data.get("completed_pages", 0)
        target_days = self.data.get("target_days", 30)
        total_pages = 604
        rem_pages = max(0, total_pages - completed_pages)

        if target_days > 0:
            daily_target = math.ceil(total_pages / target_days)
        else:
            daily_target = 20

        current_page = min(604, completed_pages + 1)
        self.data["current_page"] = current_page
        self.data["daily_pages"] = daily_target
        self.save_data()

        percent = (completed_pages / total_pages) * 100
        self.progress_bar.setValue(completed_pages)

        start_date_str = self.data.get("start_date", datetime.date.today().strftime("%Y-%m-%d"))
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except Exception:
            start_date = datetime.date.today()

        today = datetime.date.today()
        days_passed = max(0, (today - start_date).days)

        if completed_pages >= total_pages:
            rem_days = 0
            expected_date_str = today.strftime("%Y-%m-%d")
        else:
            expected_daily_pace = total_pages / max(1, target_days)
            if days_passed == 0:
                actual_pace = expected_daily_pace
            else:
                actual_pace = completed_pages / days_passed if completed_pages > 0 else expected_daily_pace

            rem_days = math.ceil(rem_pages / expected_daily_pace) if expected_daily_pace > 0 else 0
            days_needed = math.ceil(rem_pages / actual_pace) if actual_pace > 0 else rem_days
            expected_date = today + datetime.timedelta(days=days_needed)
            expected_date_str = expected_date.strftime("%Y-%m-%d")

        if daily_target < 5:
            prayer_str = ""
        else:
            base_per_prayer = daily_target // 5
            rem_after_prayers = daily_target % 5
            base_str = format_pages(base_per_prayer)

            if rem_after_prayers == 0:
                prayer_str = f" ({base_str} بعد كل صلاة)"
            elif rem_after_prayers == 1:
                prayer_str = f" ({base_str} بعد كل صلاة، وتتبقى صفحة واحدة تقرأها في أي وقت من اليوم)"
            elif rem_after_prayers == 2:
                prayer_str = f" ({base_str} بعد كل صلاة، وتتبقى صفحتان تقرأهما في أي وقت من اليوم)"
            else:
                prayer_str = f" ({base_str} بعد كل صلاة، وتتبقى {format_pages(rem_after_prayers)} تقرأها في أي وقت من اليوم)"

        start_page = min(604, completed_pages + 1)
        end_page = min(604, start_page + daily_target - 1)

        if completed_pages >= total_pages:
            khatmah_status = "مكتملة"
            ward_today_str = "ورد اليوم: اكتملت الختمة"
        else:
            expected_days_passed = round(completed_pages * target_days / total_pages)
            diff_days = expected_days_passed - days_passed
            if diff_days == 0:
                khatmah_status = "تسير حسب الخطة"
            elif diff_days > 0:
                if diff_days == 1:
                    khatmah_status = "متقدم عن الخطة بيوم واحد"
                elif diff_days == 2:
                    khatmah_status = "متقدم عن الخطة بيومين"
                elif 3 <= diff_days <= 10:
                    khatmah_status = f"متقدم عن الخطة بـ {diff_days} أيام"
                else:
                    khatmah_status = f"متقدم عن الخطة بـ {diff_days} يوماً"
            else:
                abs_diff = abs(diff_days)
                if abs_diff == 1:
                    khatmah_status = "متأخر بيوم واحد"
                elif abs_diff == 2:
                    khatmah_status = "متأخر بيومين"
                elif 3 <= abs_diff <= 10:
                    khatmah_status = f"متأخر بـ {abs_diff} أيام"
                else:
                    khatmah_status = f"متأخر بـ {abs_diff} يوماً"

            if start_page < end_page:
                ward_today_str = f"ورد اليوم: من صفحة {start_page} إلى صفحة {end_page}"
            else:
                ward_today_str = f"ورد اليوم: صفحة {start_page}"

        info_str = (
            f"حالة الختمة: {khatmah_status}\n"
            f"{ward_today_str}\n"
            f"الورد اليومي المطلوب: {format_pages(daily_target)} تقريباً{prayer_str}\n"
            f"الصفحات المكتملة: {format_pages(completed_pages)} من {format_pages(604)} ({percent:.1f}%)\n"
            f"الصفحات المتبقية: {format_pages(rem_pages)}\n"
            f"عدد الأيام المنقضية: {format_days(days_passed)}\n"
            f"الأيام المتبقية: {format_days(rem_days)}\n"
            f"المدة المستهدفة: {format_days(target_days)}\n"
            f"تاريخ بدء الختمة: {start_date_str}\n"
            f"تاريخ الانتهاء المتوقع: {expected_date_str}"
        )

        if completed_pages >= total_pages:
            info_str += "\n\nمبارك! لقد أتممت ختم القرآن الكريم كاملاً!"

        self.info_text.setText(info_str)

    def start_new_khatmah(self):
        target_days = self.days_spin.value()
        if self.data.get("has_khatmah", False):
            msg = f"هل تريد بدء ختمة جديدة لمدة {format_days(target_days)} وإعادة ضبط التقدم؟"
        else:
            msg = f"هل تريد بدء ختمة جديدة لمدة {format_days(target_days)}؟"
        confirm = guiTools.QQuestionMessageBox.view(
            self,
            "تأكيد بدء ختمة جديدة",
            msg,
            "نعم",
            "لا"
        )
        if confirm == 0:
            self.data = {
                "has_khatmah": True,
                "target_days": target_days,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": math.ceil(604 / target_days),
                "completed_pages": 0,
                "is_completed": False
            }
            self.save_data()
            self.update_ui_state()
            guiTools.MessageBox.view(self, "تم", "تم بدء الختمة الجديدة بنجاح.")

    def read_today_ward(self):
        completed_pages = self.data.get("completed_pages", 0)
        if completed_pages >= 604:
            guiTools.MessageBox.view(self, "تنبيه", "لقد أكملت الختمة بالفعل.")
            return
        start_page = completed_pages + 1
        daily_pages = self.data.get("daily_pages", 20)
        end_page = min(604, start_page + daily_pages - 1)

        pages_dict = functions.quranJsonControl.getPage()
        content_list = []
        for p_num in range(start_page, end_page + 1):
            p_str = str(p_num)
            if p_str in pages_dict:
                content_list.append(f"صفحة {p_str}\n" + pages_dict[p_str][1])

        full_text = "\n\n".join(content_list)
        label_title = f"ورد اليوم (من صفحة {start_page} إلى صفحة {end_page})"
        viewer = gui.QuranViewer(self, full_text, 5, label_title, enableNextPreviouseButtons=False, enableBookmarks=False)
        viewer.exec()

    def mark_today_completed(self):
        completed_pages = self.data.get("completed_pages", 0)
        if completed_pages >= 604:
            guiTools.MessageBox.view(self, "تنبيه", "الختمة مكتملة بالفعل.")
            return
        daily_pages = self.data.get("daily_pages", 20)
        new_completed = min(604, completed_pages + daily_pages)
        self.data["completed_pages"] = new_completed
        if new_completed >= 604:
            self.data["is_completed"] = True
        self.save_data()
        self.update_ui_state()
        guiTools.MessageBox.view(self, "تم", f"تم تسجيل إتمام الورد. وصل تقدمك إلى الصفحة {new_completed}.")

    def update_page_manually(self):
        curr = self.data.get("completed_pages", 0)
        val, ok = guiTools.QInputDialog.getInt(self, "تحديث الصفحة الحالية", "أدخل رقم آخر صفحة أنجزت قراءتها (0-604):", curr, 0, 604)
        if ok:
            self.data["completed_pages"] = val
            if val >= 604:
                self.data["is_completed"] = True
            self.save_data()
            self.update_ui_state()
            guiTools.MessageBox.view(self, "تم", "تم تحديث التقدم يدوياً بنجاح.")

    def reset_khatmah(self):
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد من إعادة تعيين الختمة الحالية بجميع بياناتها؟", "نعم", "لا")
        if confirm == 0:
            target_days = self.data.get("target_days", 30)
            self.data = {
                "has_khatmah": True,
                "target_days": target_days,
                "start_date": datetime.date.today().strftime("%Y-%m-%d"),
                "current_page": 1,
                "total_pages": 604,
                "daily_pages": math.ceil(604 / target_days) if target_days > 0 else 20,
                "completed_pages": 0,
                "is_completed": False
            }
            self.save_data()
            self.update_ui_state()
            guiTools.MessageBox.view(self, "تم", "تم إعادة تعيين الختمة.")

    def stop_khatmah(self):
        confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الإيقاف", "هل أنت متأكد من إيقاف الختمة الحالية؟", "نعم", "لا")
        if confirm == 0:
            self.data["has_khatmah"] = False
            self.save_data()
            self.update_ui_state()
            guiTools.MessageBox.view(self, "تم", "تم إيقاف الختمة.")
