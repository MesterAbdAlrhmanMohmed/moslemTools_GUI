import gui.translationViewer
import gui, guiTools, functions, re, os, requests, subprocess, shutil, traceback
import ujson as json
from settings.app import appName
from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, QuranLoader

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class QuranTabMergerSaverMixin:
    def _create_ayah_filename(self, ayah_text):
        category = self.info.currentItem().text()
        type_index = self.type.currentIndex()
        Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(ayah_text, category, type_index)
        surah_str = str(surah).zfill(3)
        ayah_str = str(Ayah).zfill(3)
        return f"{surah_str}{ayah_str}.mp3"

    def handle_merge_action(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء العملية الحالية؟", "نعم", "لا")
        if reply != 0:
            return
        if getattr(self, 'is_merging', False) and self.merge_phase == 'merging':
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
        elif getattr(self, 'is_merging', False) and self.merge_phase == 'preparing':
            self.cancellation_requested = True
            if hasattr(self, 'pre_merge_thread') and self.pre_merge_thread.isRunning():
                self.pre_merge_thread.terminate()
            self.on_merge_finished(False, "تم إلغاء عملية التحضير من قبل المستخدم.")
        elif getattr(self, 'is_saving', False) and self.merge_phase == 'preparing_save':
            self.cancellation_requested = True
            if hasattr(self, 'pre_save_thread') and self.pre_save_thread.isRunning():
                self.pre_save_thread.terminate()
            self.on_save_finished(False, "تم إلغاء عملية التحضير من قبل المستخدم.")

    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء العملية الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()

    def onMergeActionTriggered(self):
        if not self.info.currentItem():
            return
        if getattr(self, 'is_merging', False) or getattr(self, 'is_saving', False):
            return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        all_ayahs_text = self.getResult().split("\n")
        self.merge_list.clear()
        self.set_ui_for_operation(True)
        self.is_merging = True
        self.merge_feedback_label.setText("جاري التحقق من الآيات المطلوبة...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(all_ayahs_text, self.currentReciter, reciters, self.info.currentItem().text(), self.type.currentIndex())
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def on_pre_merge_check_finished(self, merge_list, ayahs_to_download, reciter_name, reciter_local_path_base):
        if self.cancellation_requested: return
        self.merge_list = merge_list
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
        else:
            confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن. يمكنك إلغاء عملية الدمج ولكن لا يمكنك التفاعل مع الواجهة حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_operation(False)
            self.is_merging = False
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.set_ui_for_operation(False)
            self.is_merging = False
            return
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
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
        output_dir = os.path.dirname(self.current_merge_output_path)
        next_item_to_download = None
        for item in self.merge_list:
            if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads:
                next_item_to_download = item
                break
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
            url = next_item_to_download['url']
            safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
            download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.current_download_url = url
            self.download_thread = DownloadThread(url, download_path)
            self.download_thread.progress.connect(self.update_download_progress)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.network_error.connect(self.on_download_network_error)
            self.resume_download_button.setVisible(False)
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            self.resume_download_button.setVisible(False)
            self.finalize_and_execute_merge()

    def on_download_network_error(self, msg):
        self.resume_download_button.setVisible(True)
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def resume_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            self.download_thread.resume()
            self.resume_download_button.setVisible(False)

    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()

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
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try: os.remove(self.current_merge_output_path)
                except: pass
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم دمج الآيات بنجاح.")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
            if reply == 0:
                for f_path in self.files_to_delete_after_merge:
                    if os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass
        self.set_ui_for_operation(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()

    def onSaveActionTriggered(self):
        if not self.info.currentItem(): return
        if getattr(self, 'is_merging', False) or getattr(self, 'is_saving', False): return
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        all_ayahs_text = self.getResult().split("\n")
        self.set_ui_for_operation(True)
        self.is_saving = True
        self.merge_phase = 'preparing_save'
        self.cancellation_requested = False
        self.pre_save_thread = PreMergeCheckThread(all_ayahs_text, self.currentReciter, reciters, self.info.currentItem().text(), self.type.currentIndex())
        self.pre_save_thread.finished.connect(self.on_pre_save_check_finished)
        self.pre_save_thread.error.connect(lambda msg: self.on_save_prepare_error(msg))
        self.pre_save_thread.start()

    def on_save_prepare_error(self, msg):
        self.set_ui_for_operation(False)
        self.is_saving = False
        self.merge_phase = 'idle'
        guiTools.qMessageBox.MessageBox.error(self, "خطأ", msg)

    def on_pre_save_check_finished(self, merge_list, ayahs_to_download, reciter_name, reciter_local_path_base):
        if self.cancellation_requested:
            self.set_ui_for_operation(False)
            self.is_saving = False
            self.merge_phase = 'idle'
            return
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = f"تنبيه: يتطلب الحفظ تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بالتحميل المباشر للمجلد المختار.\nخلال هذه المرحلة لن تتمكن من إلغاء العملية.\n\nهل أنت متأكد أنك تريد المتابعة؟"
        else:
            confirm_message = "جميع الآيات المحددة جاهزة للحفظ.\nستبدأ عملية الحفظ الآن.\n\nهل تريد المتابعة؟"
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_operation(False)
            self.is_saving = False
            self.merge_phase = 'idle'
            return
        target_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآيات")
        if not target_dir:
            self.set_ui_for_operation(False)
            self.is_saving = False
            self.merge_phase = 'idle'
            return
        self.merge_action_button.hide()
        self.merge_progress_bar.setMaximum(100)
        self.merge_progress_bar.setValue(0)
        self.merge_progress_bar.show()
        self.save_thread = SaveThread(merge_list, target_dir)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.status.connect(self.merge_feedback_label.setText)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.start()

    def on_save_finished(self, success, message):
        self.is_saving = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        if success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", message)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        self.set_ui_for_operation(False)

    def set_ui_for_operation(self, is_active):
        widgets_to_disable = [self.by, self.type, self.custom, self.serch, self.search_bar, self.info, self.info_of_quran, self.info1]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير للعملية...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setMaximum(100)
            self.merge_progress_bar.setValue(0)
