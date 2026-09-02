import os
import shutil
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import custom_errors
import guiTools
from .threads import MergeThread, SaveThread

class MotonPlayerMergerSaverMixin:
    def init_merger_saver(self):
        self.ffmpeg_path = os.path.abspath(os.path.join("data", "bin", "ffmpeg.exe"))
        self.merge_thread = None
        self.save_thread = None
        self.is_merging = False
        self.save_mode = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.current_merge_output_path = ""

    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets = [self.text, self.N_bayt, self.P_bayt, self.PPS, self.changeCurrentReciterButton, self.mergeButton, self.saveAllButton]
        for w in widgets:
            if hasattr(self, w.objectName()) or hasattr(self, 'text'):
                w.setEnabled(not is_active)
        if hasattr(self, 'merge_widget'):
            self.merge_widget.setVisible(is_active)
            if is_active:
                self.merge_action_button.setText("إلغاء العملية")
                self.merge_action_button.setStyleSheet("QPushButton#cancelMergeButton {background-color: #8B0000; color: white; border: 2px solid #B22222; padding: 6px 12px; border-radius: 5px; font-weight: bold;} QPushButton#cancelMergeButton:hover {background-color: #A52A2A; border-color: #FF4D4D;}")
                self.merge_progress_bar.setVisible(self.save_mode)
                self.merge_progress_bar.setValue(0)

    def handle_merge_action(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء العملية الحالية؟", "نعم", "لا")
        if reply != 0:
            return
        self.cancellation_requested = True
        if self.is_merging and self.merge_phase == 'merging':
            if hasattr(self, 'merge_thread') and self.merge_thread and self.merge_thread.isRunning():
                self.merge_thread.stop()
        elif self.is_merging and self.merge_phase == 'saving':
            if hasattr(self, 'save_thread') and self.save_thread and self.save_thread.isRunning():
                self.save_thread.cancel()

    def save_current_bayt_audio(self):
        if self.is_merging:
            return
        if self.current_reciter_type == "N":
            src = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, self.matn_slug, f"{self.current_bayt_num}.mp3"))
            if not os.path.exists(src):
                guiTools.speak("ملف الصوت غير متوفر محليا")
                return
            default_name = f"{self.matn_name}_بيت_{self.current_bayt_num}.mp3"
            dest_file, _ = qt.QFileDialog.getSaveFileName(self, "حفظ صوت البيت", default_name, "Audio Files (*.mp3)")
            if dest_file:
                shutil.copy2(src, dest_file)
                guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم حفظ صوت البيت بنجاح")
        else:
            guiTools.speak("هذا القارئ متوفر كملف صوتي كامل للمتن")

    def save_all_verses_audio(self):
        if self.is_merging:
            return
        self.pause_for_action()
        if self.current_reciter_type != "N":
            src = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, f"{self.matn_slug}.mp3"))
            if not os.path.exists(src):
                guiTools.speak("ملف الصوت غير متوفر")
                self.resume_after_action()
                return
            default_name = f"{self.matn_name}.mp3"
            dest_file, _ = qt.QFileDialog.getSaveFileName(self, "حفظ صوت المتن", default_name, "Audio Files (*.mp3)")
            if dest_file:
                shutil.copy2(src, dest_file)
                guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم حفظ الملف الصوتي بنجاح")
            self.resume_after_action()
            return
        file_list = []
        for v in self.all_verses_list:
            b_num = v["global_num"]
            src = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, self.matn_slug, f"{b_num}.mp3"))
            dest_name = f"{b_num:04d}_{self.matn_name}_بيت_{b_num}.mp3"
            if os.path.exists(src):
                file_list.append({"src": src, "dest_name": dest_name})
        if not file_list:
            guiTools.speak("لا توجد ملفات صوتية جاهزة للحفظ")
            self.resume_after_action()
            return
        confirm_message = "جميع الأبيات المحددة جاهزة للحفظ.\nسيتم حفظ الأبيات الآن في المجلد المختار.\n\nهل تريد المتابعة؟"
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        dest_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد حفظ الأبيات")
        if not dest_dir:
            self.resume_after_action()
            return
        self.save_mode = True
        self.is_merging = True
        self.merge_phase = 'saving'
        self.cancellation_requested = False
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري حفظ الأبيات...")
        self.merge_progress_bar.setRange(0, 100)
        self.merge_progress_bar.setValue(0)
        self.merge_progress_bar.show()
        self.save_thread = SaveThread(file_list, dest_dir, self)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.cancelled.connect(lambda: self.on_save_finished(False, "تم إلغاء الحفظ."))
        self.save_thread.start()
        guiTools.speak("جاري حفظ جميع الأبيات...")

    def on_save_finished(self, success, msg):
        self.is_merging = False
        self.merge_phase = 'idle'
        self.set_ui_for_merge(False)
        self.merge_progress_bar.hide()
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الحفظ.")
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", msg)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", msg)
        self.cancellation_requested = False
        self.resume_after_action()

    def merge_all_verses(self):
        if self.is_merging:
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة FFmpeg للدمج.")
            self.resume_after_action()
            return
        if self.current_reciter_type == "Y":
            guiTools.speak("المتن مدمج بالفعل في ملف صوتي واحد")
            self.resume_after_action()
            return
        input_files = []
        for v in self.all_verses_list:
            b_num = v["global_num"]
            src = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, self.matn_slug, f"{b_num}.mp3"))
            if os.path.exists(src):
                input_files.append(src)
        if not input_files:
            guiTools.speak("لا توجد ملفات صوتية للدمج")
            self.resume_after_action()
            return
        confirm_message = "جميع الأبيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\nهل تريد المتابعة؟"
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        default_name = f"{self.matn_name}_كامل.mp3"
        dest_file, _ = qt.QFileDialog.getSaveFileName(self, "دمج وحفظ المتن", default_name, "Audio Files (*.mp3)")
        if not dest_file:
            self.resume_after_action()
            return
        self.save_mode = False
        self.is_merging = True
        self.merge_phase = 'merging'
        self.cancellation_requested = False
        self.current_merge_output_path = dest_file
        self.set_ui_for_merge(True)
        self.merge_progress_bar.hide()
        self.merge_feedback_label.setText("جاري دمج الأبيات في ملف واحد...")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, dest_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()
        guiTools.speak("جاري دمج الأبيات في ملف واحد...")

    def on_merge_finished(self, success, msg):
        self.is_merging = False
        self.merge_phase = 'idle'
        self.set_ui_for_merge(False)
        self.merge_progress_bar.hide()
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try:
                    os.remove(self.current_merge_output_path)
                except Exception:
                    pass
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم دمج وحفظ الأبيات بنجاح")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الدمج", msg)
        self.cancellation_requested = False
        self.resume_after_action()
