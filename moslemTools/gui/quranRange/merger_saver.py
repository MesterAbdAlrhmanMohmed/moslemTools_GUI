import os
import shutil
import functions
import guiTools
import ujson as json
import PyQt6.QtWidgets as qt
from settings import settings_handler
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class QuranRangeMergerSaverMixin:
    def _get_current_reciter_name(self):
        return list(reciters.keys())[self.currentReciter]

    def _create_ayah_filename(self, ayah_text):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            return f"{surah_str}{ayah_str}.mp3"
        except:
            return None

    def handle_merge_action(self):
        if self.is_merging and self.merge_phase == 'saving':
            guiTools.qMessageBox.MessageBox.warning(self, "غير مسموح", "لا يمكن إلغاء عملية الحفظ.")
            return
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء العملية الحالية؟", "نعم", "لا")
        if reply != 0:
            return
        if self.is_merging and self.merge_phase == 'merging':
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
        elif self.is_merging and self.merge_phase == 'preparing':
            self.cancellation_requested = True
            if hasattr(self, 'pre_merge_thread') and self.pre_merge_thread.isRunning():
                self.pre_merge_thread.terminate()
            self.on_merge_finished(False, "تم إلغاء عملية التحضير من قبل المستخدم.")

    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء",
            "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()

    def onMergeActionTriggered(self):
        if self.is_merging: return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return
        all_ayahs_text = self._get_selected_ayahs()
        if not all_ayahs_text:
            guiTools.qMessageBox.MessageBox.error(self, "تحذير", "لا توجد آيات في النطاق المحدد للدمج.")
            return
        self.save_mode = False
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات المطلوبة...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        self.pre_merge_thread = PreMergeCheckThread(all_ayahs_text, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def onSaveActionTriggered(self):
        if self.is_merging: return
        all_ayahs_text = self._get_selected_ayahs()
        if not all_ayahs_text:
            guiTools.qMessageBox.MessageBox.error(self, "تحذير", "لا توجد آيات في النطاق المحدد للحفظ.")
            return
        self.save_mode = True
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات المطلوبة...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        self.pre_merge_thread = PreMergeCheckThread(all_ayahs_text, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def on_pre_merge_check_finished(self, merge_list, ayahs_to_download, reciter_name, reciter_local_path_base):
        if self.cancellation_requested: return
        self.merge_list = merge_list
        num_files_to_download = len(ayahs_to_download)
        if self.save_mode:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب حفظ الآيات تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق النافذة**.\nبعد انتهاء التحميل، سيتم حفظ الآيات في المجلد المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الآيات المحددة جاهزة للحفظ.\nسيتم حفظ الآيات الآن في المجلد المختار.\n\nهل تريد المتابعة؟")
            reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
            if reply != 0:
                self.set_ui_for_merge(False)
                return
            output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآيات")
            if not output_dir:
                self.set_ui_for_merge(False)
                return
            self.current_merge_output_path = output_dir
            self.files_to_delete_after_merge.clear()
            self.completed_merge_downloads.clear()
            self.process_next_in_merge_queue()
        else:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق النافذة**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق النافذة حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
            reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
            if reply != 0:
                self.set_ui_for_merge(False)
                return
            output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
            if not output_filename:
                self.set_ui_for_merge(False)
                return
            self.current_merge_output_path = output_filename
            self.files_to_delete_after_merge.clear()
            self.completed_merge_downloads.clear()
            self.process_next_in_merge_queue()

    def update_download_progress(self, file_percent):
        total = len(self.merge_list)
        if total > 1:
            done = len(self.completed_merge_downloads)
            overall = int(((done + (file_percent / 100.0)) / total) * 100)
            self.merge_progress_bar.setValue(min(100, overall))
            self.merge_feedback_label.setText(f"جاري تحميل الآيات: تم تحميل {done} من {total} ({overall}%)...")
        else:
            self.merge_progress_bar.setValue(file_percent)
            self.merge_feedback_label.setText(f"جاري تحميل الآية المطلوبة ({file_percent}%)...")

    def process_next_in_merge_queue(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
            return
        next_item_to_download = next((item for item in self.merge_list if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads), None)
        if next_item_to_download:
            self.merge_phase = 'downloading'
            self.merge_action_button.hide()
            total = len(self.merge_list)
            done = len(self.completed_merge_downloads)
            if total > 1:
                overall = int((done / total) * 100)
                self.merge_progress_bar.setValue(min(100, overall))
                if done > 0:
                    self.merge_feedback_label.setText(f"جاري تحميل الآيات: تم تحميل {done} من {total} ({overall}%)...")
                else:
                    self.merge_feedback_label.setText("جاري تحميل الآيات المطلوبة...")
            else:
                self.merge_progress_bar.setValue(0)
                self.merge_feedback_label.setText("جاري تحميل الآية المطلوبة...")
            self.merge_progress_bar.show()
            if self.save_mode:
                output_dir = self.current_merge_output_path
                idx = self.merge_list.index(next_item_to_download) + 1
                prefix = f"{idx:04d}_" if len(self.merge_list) > 1 else ""
                download_path = os.path.join(output_dir, prefix + next_item_to_download['filename'])
            else:
                output_dir = os.path.dirname(self.current_merge_output_path)
                safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.current_download_url = next_item_to_download['url']
            self.download_thread = DownloadThread(self.current_download_url, download_path)
            self.download_thread.progress.connect(self.update_download_progress)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            if self.save_mode:
                self.start_save_thread()
            else:
                self.finalize_and_execute_merge()

    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()

    def start_save_thread(self):
        self.merge_phase = 'saving'
        self.merge_action_button.hide()
        msg_save = "جاري حفظ الآية..." if len(self.merge_list) == 1 else "جاري حفظ الآيات..."
        self.merge_feedback_label.setText(msg_save)
        self.merge_progress_bar.show()
        self.save_thread = SaveThread(self.merge_list, self.current_merge_output_path)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.cancelled.connect(lambda: self.on_merge_finished(False, "تم إلغاء الحفظ."))
        self.save_thread.start()

    def on_save_finished(self, success, message):
        self.on_merge_finished(success, message)

    def finalize_and_execute_merge(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية قبل بدء الدمج.")
            return
        self.merge_action_button.show()
        files_for_ffmpeg = []
        self.files_to_delete_after_merge.clear()
        output_dir = os.path.dirname(self.current_merge_output_path)
        for item in self.merge_list:
            if os.path.exists(item["local_path"]):
                files_for_ffmpeg.append(item["local_path"])
            else:
                safe_filename = "".join(c for c in item['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"temp_{safe_filename}")
                if os.path.exists(temp_path):
                    files_for_ffmpeg.append(temp_path)
                    if temp_path not in self.files_to_delete_after_merge:
                        self.files_to_delete_after_merge.append(temp_path)
                else:
                    self.on_merge_finished(False, f"خطأ: الملف المؤقت للآية لم يتم العثور عليه: {item['filename']}")
                    return
        if len(files_for_ffmpeg) != len(self.merge_list):
            self.on_merge_finished(False, "لم يتم العثور على جميع الملفات المطلوبة للدمج.")
            return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)

    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.merge_phase = 'merging'
        self.merge_feedback_label.setText(f"جاري دمج {len(self.merge_list)} آيات...")
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()

    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.merge_phase = 'idle'
        if self.cancellation_requested:
            title = "تم الإلغاء"
            msg = "تم إلغاء عملية الحفظ." if self.save_mode else "تم إلغاء عملية الدمج."
            guiTools.qMessageBox.MessageBox.view(self, title, msg)
            if not self.save_mode and hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try: os.remove(self.current_merge_output_path)
                except: pass
        elif success:
            title = "نجاح"
            msg = "تم حفظ الآيات بنجاح." if self.save_mode else "تم دمج الآيات بنجاح."
            guiTools.qMessageBox.MessageBox.view(self, title, msg)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف",
                "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
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
        self.save_mode = False

    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        self.controls_widget.setEnabled(not is_active)
        if is_active:
            self.setFixedHeight(self.merge_ui_height)
            self.merge_widget.setVisible(True)
            self.merge_feedback_label.setText("جاري التحضير للعملية...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
        else:
            self.merge_widget.setVisible(False)
            self.setFixedHeight(self.original_height)
