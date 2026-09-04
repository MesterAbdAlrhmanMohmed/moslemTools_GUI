import os
import re
import shutil
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import custom_errors
import guiTools
from .threads import MergeThread, SaveThread, PreMergeCheckThread, DownloadThread
from functions.moton_data import get_moton_bayt_audio_path, get_moton_continuous_audio_path, get_moton_appdata_dir

class MotonPlayerMergerSaverMixin:
    def init_merger_saver(self):
        self.ffmpeg_path = os.path.abspath(os.path.join("data", "bin", "ffmpeg.exe"))
        self.merge_thread = None
        self.save_thread = None
        self.download_thread = None
        self.pre_merge_thread = None
        self.is_merging = False
        self.save_mode = False
        self.single_save_mode = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.current_merge_output_path = ""
        self.current_download_url = None
        self.merge_list = []
        self.completed_merge_downloads = set()
        self.files_to_delete_after_merge = []

    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets = [self.text, self.N_bayt, self.P_bayt, self.PPS, self.changeCurrentReciterButton, self.mergeButton, self.saveAllButton]
        for w in widgets:
            if hasattr(self, w.objectName()) or hasattr(self, 'text'):
                w.setEnabled(not is_active)
        if hasattr(self, 'merge_widget'):
            self.merge_widget.setVisible(is_active)
            if is_active:
                self.merge_feedback_label.setText("جاري التحضير للعملية...")
                self.merge_action_button.setText("إلغاء العملية")
                self.merge_action_button.setStyleSheet("QPushButton#cancelMergeButton {background-color: #8B0000; color: white; border: 2px solid #B22222; padding: 6px 12px; border-radius: 5px; font-weight: bold;} QPushButton#cancelMergeButton:hover {background-color: #A52A2A; border-color: #FF4D4D;}")
                self.merge_progress_bar.hide()
                self.merge_progress_bar.setValue(0)
                if hasattr(self, 'resume_download_button'):
                    self.resume_download_button.setVisible(False)

    def handle_merge_action(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء العملية الحالية؟", "نعم", "لا")
        if reply != 0:
            return
        self.cancellation_requested = True
        if self.is_merging and self.merge_phase == 'merging':
            if hasattr(self, 'merge_thread') and self.merge_thread and self.merge_thread.isRunning():
                self.merge_thread.stop()
        elif self.is_merging and self.merge_phase == 'downloading':
            if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.isRunning():
                self.download_thread.cancel()
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
        elif self.is_merging and self.merge_phase == 'preparing':
            if hasattr(self, 'pre_merge_thread') and self.pre_merge_thread and self.pre_merge_thread.isRunning():
                self.pre_merge_thread.terminate()
            self.on_merge_finished(False, "تم إلغاء عملية التحضير من قبل المستخدم.")
        elif self.is_merging and self.merge_phase == 'saving':
            if hasattr(self, 'save_thread') and self.save_thread and self.save_thread.isRunning():
                self.save_thread.cancel()

    def start_check_flow(self, verses_slice, is_save):
        if self.is_merging:
            return
        self.pause_for_action()
        if not is_save:
            if not os.path.exists(self.ffmpeg_path):
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة FFmpeg للدمج.")
                self.resume_after_action()
                return
            if self.current_reciter_type != "N":
                guiTools.speak("المتن مدمج بالفعل في ملف صوتي واحد")
                self.resume_after_action()
                return
        if not verses_slice:
            self.resume_after_action()
            return

        self.save_mode = is_save
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الأبيات تمهيداً لحفظها..." if is_save else "جاري التحقق من الأبيات تمهيداً لدمجها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False

        self.pre_merge_thread = PreMergeCheckThread(
            verses_slice,
            self.current_reciter_slug,
            self.matn_slug,
            self.matn_name,
            self.current_reciter_type
        )
        if is_save:
            self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished_for_save)
            self.pre_merge_thread.error.connect(lambda msg: self.on_save_finished(False, msg))
        else:
            self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
            self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def on_pre_merge_check_finished(self, merge_list, verses_to_download):
        if self.cancellation_requested:
            return
        self.merge_list = merge_list
        num_files_to_download = len(verses_to_download)
        total_verses = len(merge_list)
        if total_verses == 1:
            if num_files_to_download > 0:
                confirm_message = ("تنبيه: تتطلب العملية تحميل البيت أولاً لأنه غير موجود.\n\nسيتم البدء بتحميل البيت، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، ستبدأ العملية، وفيها يمكنك الإلغاء فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("البيت المحدد جاهز.\nستبدأ العملية الآن وسيتم تعطيل الواجهة. يمكنك إلغاء العملية ولكن لا يمكنك إغلاق البرنامج حتى الانتهاء.\n\nهل تريد المتابعة؟")
        else:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} أبيات غير موجودة.\n\nسيتم البدء بتحميل الأبيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الأبيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return

        default_name = f"{self.matn_name}_كامل.mp3"
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", default_name, "Audio Files (*.mp3)")
        if not output_filename:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return
        self.current_merge_output_path = output_filename
        self.single_save_mode = False
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()

    def on_pre_merge_check_finished_for_save(self, merge_list, verses_to_download):
        if self.cancellation_requested:
            return
        self.merge_list = merge_list
        num_files_to_download = len(verses_to_download)
        total_verses = len(merge_list)
        if self.current_reciter_type != "N":
            if num_files_to_download > 0:
                confirm_message = ("تنبيه: يتطلب حفظ المتن تحميل الملف الصوتي أولاً لأنه غير موجود بالقرص.\n\nسيتم البدء بتحميل الملف الصوتي، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ الملف في المكان المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("الملف الصوتي للمتن جاهز للحفظ.\nسيتم حفظ الملف الآن في المكان المختار.\n\nهل تريد المتابعة؟")
        elif total_verses == 1:
            if num_files_to_download > 0:
                confirm_message = ("تنبيه: يتطلب حفظ البيت تحميله أولاً لأنه غير موجود بالقرص.\n\nسيتم البدء بتحميل البيت، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ البيت في المكان المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("البيت المحدد جاهز للحفظ.\nسيتم حفظ البيت الآن في المكان المختار.\n\nهل تريد المتابعة؟")
        else:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب حفظ الأبيات تحميل {num_files_to_download} أبيات غير موجودة.\n\nسيتم البدء بتحميل الأبيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ الأبيات في المجلد المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الأبيات المحددة جاهزة للحفظ.\nسيتم حفظ الأبيات الآن في المجلد المختار.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return

        if total_verses == 1:
            bayt_num = merge_list[0].get("global_num", "")
            if self.current_reciter_type != "N":
                default_name = f"{self.matn_name}.mp3"
                dialog_title = "حفظ صوت المتن"
            else:
                default_name = f"{self.matn_name}_بيت_{bayt_num}.mp3"
                dialog_title = "حفظ صوت البيت"
            output_file, _ = qt.QFileDialog.getSaveFileName(self, dialog_title, default_name, "Audio Files (*.mp3)")
            if not output_file:
                self.set_ui_for_merge(False)
                self.resume_after_action()
                return
            self.current_merge_output_path = output_file
            self.single_save_mode = True
        else:
            output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الأبيات")
            if not output_dir:
                self.set_ui_for_merge(False)
                self.resume_after_action()
                return
            self.current_merge_output_path = output_dir
            self.single_save_mode = False

        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()

    def process_next_in_merge_queue(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
            return

        next_item = next((item for item in self.merge_list if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads), None)
        if next_item:
            self.is_merging = True
            self.merge_phase = 'downloading'
            self.merge_action_button.hide()
            total = len(self.merge_list)
            done = len(self.completed_merge_downloads)
            if total > 1:
                overall = int((done / total) * 100)
                self.merge_progress_bar.setValue(min(100, overall))
                if done > 0:
                    self.merge_feedback_label.setText(f"جاري تحميل الأبيات: تم تحميل {done} من {total} ({overall}%)...")
                else:
                    self.merge_feedback_label.setText("جاري تحميل الأبيات المطلوبة...")
            else:
                self.merge_progress_bar.setValue(0)
                msg_dl = "جاري تحميل الملف الصوتي..." if self.current_reciter_type != "N" else "جاري تحميل البيت المطلوب..."
                self.merge_feedback_label.setText(msg_dl)
            self.merge_progress_bar.show()
            self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)

            download_path = next_item["local_path"]
            if download_path not in self.files_to_delete_after_merge:
                self.files_to_delete_after_merge.append(download_path)

            self.current_download_url = next_item["url"]
            self.download_thread = DownloadThread(self.current_download_url, download_path)
            self.download_thread.progress.connect(self.update_download_progress)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.network_error.connect(self.on_download_network_error)
            if hasattr(self, 'resume_download_button'):
                self.resume_download_button.setVisible(False)
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            if hasattr(self, 'resume_download_button'):
                self.resume_download_button.setVisible(False)
            if self.save_mode:
                self.start_save_thread()
            else:
                self.finalize_and_execute_merge()

    def update_download_progress(self, file_percent):
        total = len(self.merge_list)
        if total > 1:
            done = len(self.completed_merge_downloads)
            overall = int(((done + (file_percent / 100.0)) / total) * 100)
            self.merge_progress_bar.setValue(min(100, overall))
            self.merge_feedback_label.setText(f"جاري تحميل الأبيات: تم تحميل {done} من {total} ({overall}%)...")
        else:
            self.merge_progress_bar.setValue(file_percent)
            msg_p = f"جاري تحميل الملف الصوتي ({file_percent}%)..." if self.current_reciter_type != "N" else f"جاري تحميل البيت المطلوب ({file_percent}%)..."
            self.merge_feedback_label.setText(msg_p)

    def on_single_merge_download_finished(self):
        if hasattr(self, 'current_download_url') and self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()

    def on_download_network_error(self, msg):
        if hasattr(self, 'resume_download_button'):
            self.resume_download_button.setVisible(True)
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def resume_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            self.download_thread.resume()
            if hasattr(self, 'resume_download_button'):
                self.resume_download_button.setVisible(False)

    def start_save_thread(self):
        if self.cancellation_requested:
            self.on_save_finished(False, "تم إلغاء العملية قبل بدء الحفظ.")
            return
        if getattr(self, 'single_save_mode', False) or len(self.merge_list) == 1:
            item = self.merge_list[0]
            src = item["local_path"]
            dest = self.current_merge_output_path
            try:
                os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
                shutil.copy2(src, dest)
                msg = "تم حفظ الملف الصوتي بنجاح." if self.current_reciter_type != "N" else "تم حفظ صوت البيت بنجاح."
                self.on_save_finished(True, msg)
            except Exception as e:
                self.on_save_finished(False, f"فشل حفظ الملف: {str(e)}")
            return

        self.merge_phase = 'saving'
        self.merge_action_button.hide()
        self.merge_feedback_label.setText("جاري حفظ الأبيات...")
        self.merge_progress_bar.setValue(0)
        self.merge_progress_bar.show()
        self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.save_thread = SaveThread(self.merge_list, self.current_merge_output_path, self)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.cancelled.connect(lambda: self.on_save_finished(False, "تم إلغاء الحفظ."))
        self.save_thread.start()

    def finalize_and_execute_merge(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية قبل بدء الدمج.")
            return
        self.merge_action_button.show()
        files_for_ffmpeg = []
        for item in self.merge_list:
            if os.path.exists(item["local_path"]):
                files_for_ffmpeg.append(item["local_path"])
            else:
                self.on_merge_finished(False, f"خطأ: الملف الصوتي للبيت لم يتم العثور عليه: {item.get('filename', '')}")
                return
        if len(files_for_ffmpeg) != len(self.merge_list):
            self.on_merge_finished(False, "لم يتم العثور على جميع الملفات المطلوبة للدمج.")
            return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)

    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.merge_phase = 'merging'
        msg_merge = "جاري تحضير البيت..." if len(self.merge_list) == 1 else f"جاري دمج {len(self.merge_list)} أبيات..."
        self.merge_feedback_label.setText(msg_merge)
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()

    def on_merge_finished(self, success, msg):
        self.is_merging = False
        self.merge_phase = 'idle'
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try: os.remove(self.current_merge_output_path)
                except: pass
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم دمج وحفظ الأبيات بنجاح.")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الدمج", msg)

        if not self.save_mode and self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
            if reply == 0:
                for f_path in self.files_to_delete_after_merge:
                    if os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass

        self.set_ui_for_merge(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.resume_after_action()
        self.save_mode = False
        self.single_save_mode = False

    def on_save_finished(self, success, msg):
        self.is_merging = False
        self.merge_phase = 'idle'
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الحفظ.")
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", msg)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", msg)

        self.set_ui_for_merge(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.resume_after_action()
        self.save_mode = False
        self.single_save_mode = False

    def save_current_bayt_audio(self):
        if self.is_merging:
            return
        if not (0 <= self.current_index < len(self.all_verses_list)):
            return
        bayt = self.all_verses_list[self.current_index]
        self.start_check_flow([bayt], is_save=True)

    def save_all_verses_audio(self):
        if self.is_merging:
            return
        self.start_check_flow(self.all_verses_list, is_save=True)

    def merge_all_verses(self):
        if self.is_merging:
            return
        self.start_check_flow(self.all_verses_list, is_save=False)
