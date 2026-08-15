from guiTools import note_dialog
import functions.notesManager as notesManager
from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
from ..quranPlayer import QuranPlayer
import time, winsound, pyperclip, os, re, requests, subprocess, shutil, traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, SajdaGoToDialog, AsbabAlnozoleGoToDialog, SajdaFinderThread, AsbabAlnozoleFinderThread, SearchModeDialog, GoToCategoryDialog

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class MergerSaverMixin:
    def handle_merge_action(self):
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
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء عملية العملية الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()

    def mergeAyahs(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        total_ayahs = len(self.original_quran_text.split("\n"))
        start_ayah, ok1 = guiTools.QInputDialog.getInt(self, "تحديد بداية الدمج", "الدمج من", self.getCurrentAyah() + 1, 1, total_ayahs)
        if not ok1:
            self.resume_after_action()
            return
        end_ayah, ok2 = guiTools.QInputDialog.getInt(self, "تحديد نهاية الدمج", "الدمج إلى", total_ayahs, start_ayah, total_ayahs)
        if not ok2:
            self.resume_after_action()
            return
        self.save_mode = False
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لدمجها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        start_index = start_ayah - 1
        end_index = end_ayah
        self.pre_merge_thread = PreMergeCheckThread(start_index, end_index, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def mergeCategoryAyahs(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        total_ayahs = len(self.original_quran_text.split("\n"))
        self.save_mode = False
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لدمجها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(0, total_ayahs, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def saveCurrentAyah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        if current_ayah_index < 0:
            self.resume_after_action()
            return
        total_ayahs = len(self.original_quran_text.split("\n"))
        self.save_mode = True
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآية تمهيداً لحفظها...")
        self.merge_action_button.setText("إلغاء")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(current_ayah_index, current_ayah_index+1, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished_for_save)
        self.pre_merge_thread.error.connect(lambda msg: self.on_save_finished(False, msg))
        self.pre_merge_thread.start()

    def saveFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        total_ayahs = len(self.original_quran_text.split("\n"))
        start_ayah, ok1 = guiTools.QInputDialog.getInt(self, "حفظ من آية إلى آية", "الحفظ من", self.getCurrentAyah() + 1, 1, total_ayahs)
        if not ok1:
            self.resume_after_action()
            return
        end_ayah, ok2 = guiTools.QInputDialog.getInt(self, "حفظ من آية إلى آية", "الحفظ إلى", total_ayahs, start_ayah, total_ayahs)
        if not ok2:
            self.resume_after_action()
            return
        self.save_mode = True
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لحفظها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(start_ayah-1, end_ayah, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished_for_save)
        self.pre_merge_thread.error.connect(lambda msg: self.on_save_finished(False, msg))
        self.pre_merge_thread.start()

    def saveCategoryAyahs(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        total_ayahs = len(self.original_quran_text.split("\n"))
        self.save_mode = True
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لحفظها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(0, total_ayahs, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished_for_save)
        self.pre_merge_thread.error.connect(lambda msg: self.on_save_finished(False, msg))
        self.pre_merge_thread.start()

    def mergeFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        current_ayah_index = self.getCurrentAyah()
        if current_ayah_index < 0:
            self.resume_after_action()
            return
        total_ayahs = len(self.original_quran_text.split("\n"))
        self.save_mode = False
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لدمجها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(current_ayah_index, total_ayahs, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished)
        self.pre_merge_thread.error.connect(lambda msg: self.on_merge_finished(False, msg))
        self.pre_merge_thread.start()

    def saveFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        if current_ayah_index < 0:
            self.resume_after_action()
            return
        total_ayahs = len(self.original_quran_text.split("\n"))
        self.save_mode = True
        self.set_ui_for_merge(True)
        self.merge_feedback_label.setText("جاري التحقق من الآيات تمهيداً لحفظها...")
        self.merge_action_button.setText("إلغاء العملية")
        self.merge_action_button.show()
        self.merge_phase = 'preparing'
        self.cancellation_requested = False
        self.pre_merge_thread = PreMergeCheckThread(current_ayah_index, total_ayahs, self.original_quran_text, self.category, self.type, self.currentReciter, reciters)
        self.pre_merge_thread.finished.connect(self.on_pre_merge_check_finished_for_save)
        self.pre_merge_thread.error.connect(lambda msg: self.on_save_finished(False, msg))
        self.pre_merge_thread.start()

    def on_pre_merge_check_finished(self, merge_list, ayahs_to_download):
        if self.cancellation_requested: return
        self.merge_list = merge_list
        num_files_to_download = len(ayahs_to_download)
        total_ayahs = len(merge_list)
        if total_ayahs == 1:
            if num_files_to_download > 0:
                confirm_message = ("تنبيه: تتطلب العملية تحميل الآية أولاً لأنها غير موجودة.\n\nسيتم البدء بتحميل الآية، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، ستبدأ العملية، وفيها يمكنك الإلغاء فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("الآية المحددة جاهزة.\nستبدأ العملية الآن وسيتم تعطيل الواجهة. يمكنك إلغاء العملية ولكن لا يمكنك إغلاق البرنامج حتى الانتهاء.\n\nهل تريد المتابعة؟")
        else:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()

    def on_pre_merge_check_finished_for_save(self, merge_list, ayahs_to_download):
        if self.cancellation_requested: return
        self.merge_list = merge_list
        num_files_to_download = len(ayahs_to_download)
        total_ayahs = len(merge_list)
        if total_ayahs == 1:
            if num_files_to_download > 0:
                confirm_message = ("تنبيه: يتطلب حفظ الآية تحميلها أولاً لأنها غير موجودة بالقرص.\n\nسيتم البدء بتحميل الآية، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ الآية في المجلد المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("الآية المحددة جاهزة للحفظ.\nسيتم حفظ الآية الآن في المجلد المختار.\n\nهل تريد المتابعة؟")
        else:
            if num_files_to_download > 0:
                confirm_message = (f"تنبيه: يتطلب حفظ الآيات تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ الآيات في المجلد المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
            else:
                confirm_message = ("جميع الآيات المحددة جاهزة للحفظ.\nسيتم حفظ الآيات الآن في المجلد المختار.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return
        output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآيات")
        if not output_dir:
            self.set_ui_for_merge(False)
            self.resume_after_action()
            return
        self.current_merge_output_path = output_dir
        self.merge_phase = 'saving'
        self.merge_action_button.hide()
        msg_save = "جاري حفظ الآية..." if total_ayahs == 1 else "جاري حفظ الآيات..."
        self.merge_feedback_label.setText(msg_save)
        self.merge_progress_bar.show()
        self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.save_thread = SaveThread(self.merge_list, output_dir, numbering=len(self.merge_list)>1)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.start()

    def on_save_finished(self, success, message):
        self.is_merging = False
        self.merge_phase = 'idle'
        if success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", message)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        self.set_ui_for_merge(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.resume_after_action()
        self.save_mode = False

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
            self.is_merging = True
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
                download_path = os.path.join(output_dir, next_item_to_download['filename'])
            else:
                output_dir = os.path.dirname(self.current_merge_output_path)
                safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.current_download_url = next_item_to_download['url']
            self.download_thread = DownloadThread(self.current_download_url, download_path)
            self.download_thread.progress.connect(self.update_download_progress)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.network_error.connect(self.on_download_network_error)
            self.resume_download_button.setVisible(False)
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            self.resume_download_button.setVisible(False)
            if not self.save_mode:
                self.finalize_and_execute_merge()
            else:
                self.on_merge_finished(True, "تم حفظ الآيات بنجاح.")

    def on_download_network_error(self, msg):
        self.resume_download_button.setVisible(True)
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def resume_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            self.download_thread.resume()
            self.resume_download_button.setVisible(False)
            if self.save_mode:
                pass
            else:
                self.finalize_and_execute_merge()

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
        self.is_merging = True
        self.merge_phase = 'merging'
        msg_merge = "جاري تحضير الآية..." if len(self.merge_list) == 1 else f"جاري دمج {len(self.merge_list)} آيات..."
        self.merge_feedback_label.setText(msg_merge)
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
            if self.save_mode:
                msg = "تم حفظ الآية بنجاح." if len(self.merge_list) == 1 else "تم حفظ الآيات بنجاح."
            else:
                msg = "تمت العملية بنجاح." if len(self.merge_list) == 1 else "تم دمج الآيات بنجاح."
            guiTools.qMessageBox.MessageBox.view(self, title, msg)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
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

    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets_to_disable = [self.text, self.search_widget, self.next, self.previous, self.changeCategory, self.changeCurrentReciterButton, self.toggle_search_button]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير للعملية...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
