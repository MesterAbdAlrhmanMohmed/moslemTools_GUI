from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
import time,os,requests,subprocess,shutil,re,traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, SaveThread

with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)


class PlayerMergerSaverMixin:
    def handle_merge_action(self):
        if self.is_merging and self.merge_phase == 'merging':
            self.confirm_and_cancel_merge()
        elif self.is_merging and self.merge_phase == 'downloading' and not self.save_mode:
            self.cancellation_requested = True
            if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                self.download_thread.cancel()
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
        elif self.is_merging and self.merge_phase == 'saving':
            guiTools.MessageBox.error(self, "غير مسموح", "لا يمكن إلغاء عملية الحفظ.")

    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء","هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()

    def _on_set_for_merge(self, index):
        ayah_text = self.quranText[index]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(ayah_text, self.category, self.type)
        if int(surah)<10: surah="00" + surah
        elif int(surah)<100: surah="0" + surah
        else: surah=str(surah)
        if Ayah<10: Ayah="00" + str(Ayah)
        elif Ayah<100: Ayah="0" + str(Ayah)
        else: Ayah=str(Ayah)
        return surah+Ayah+".mp3"

    def mergeAyahs(self):
        if self.is_merging:
            return
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        self.save_mode = False
        self.merge_list.clear()
        reciter_url_base = reciters[self.getCurrentReciter()]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
        ayahs_to_download = []
        for i in range(len(self.quranText)):
            ayah_filename = self._on_set_for_merge(i)
            if not ayah_filename: continue
            local_path = os.path.join(reciter_local_path_base, ayah_filename)
            ayah_info = {"index": i, "filename": ayah_filename,"url": reciter_url_base + ayah_filename,"local_path": local_path}
            self.merge_list.append(ayah_info)
            if not os.path.exists(local_path): ayahs_to_download.append(ayah_info)
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\nهل أنت متأكد أنك تريد المتابعة؟")
        else:
            confirm_message = ("جميع الآيات المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.resume_after_action()
            return
        self.set_ui_for_merge(True)
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()

    def onSaveAllActionTriggered(self):
        if self.is_merging:
            return
        self.pause_for_action()
        self.save_mode = True
        self.merge_list.clear()
        reciter_url_base = reciters[self.getCurrentReciter()]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
        ayahs_to_download = []
        for i in range(len(self.quranText)):
            ayah_filename = self._on_set_for_merge(i)
            if not ayah_filename: continue
            local_path = os.path.join(reciter_local_path_base, ayah_filename)
            ayah_info = {"index": i, "filename": ayah_filename,"url": reciter_url_base + ayah_filename,"local_path": local_path}
            self.merge_list.append(ayah_info)
            if not os.path.exists(local_path): ayahs_to_download.append(ayah_info)
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب حفظ الآيات تحميل {num_files_to_download} آية غير موجودة.\n\nسيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\nبعد انتهاء التحميل، سيتم حفظ الآيات في المجلد المختار.\n\nهل أنت متأكد أنك تريد المتابعة؟")
        else:
            confirm_message = ("جميع الآيات المحددة جاهزة للحفظ.\nسيتم حفظ الآيات الآن في المجلد المختار.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآيات")
        if not output_dir:
            self.resume_after_action()
            return
        self.set_ui_for_merge(True)
        self.current_merge_output_path = output_dir
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()

    def onSaveCurrentAyahActionTriggered(self):
        if self.is_merging:
            return
        self.pause_for_action()
        self.save_mode = True
        self.merge_list.clear()
        reciter_url_base = reciters[self.getCurrentReciter()]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
        ayah_filename = self._on_set_for_merge(self.index)
        if not ayah_filename:
            guiTools.MessageBox.error(self, "خطأ", "فشل في تحديد اسم ملف الآية.")
            self.resume_after_action()
            return
        local_path = os.path.join(reciter_local_path_base, ayah_filename)
        ayah_info = {"index": self.index, "filename": ayah_filename,"url": reciter_url_base + ayah_filename,"local_path": local_path}
        self.merge_list.append(ayah_info)
        num_files_to_download = 0 if os.path.exists(local_path) else 1
        if num_files_to_download > 0:
            confirm_message = ("تنبيه: الآية غير موجودة محلياً وسيتم تحميلها الآن.\n\nهل تريد المتابعة؟")
        else:
            confirm_message = ("الآية موجودة محلياً وجاهزة للحفظ.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآية")
        if not output_dir:
            self.resume_after_action()
            return
        self.set_ui_for_merge(True)
        self.current_merge_output_path = output_dir
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
        output_dir = os.path.dirname(self.current_merge_output_path) if not self.save_mode else self.current_merge_output_path
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
            if self.save_mode:
                self.start_save_thread()
            else:
                self.finalize_and_execute_merge()

    def on_download_network_error(self, msg):
        self.resume_download_button.setVisible(True)
        guiTools.MessageBox.error(self, "انقطاع الاتصال", msg)

    def resume_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            self.download_thread.resume()
            self.resume_download_button.setVisible(False)

    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()

    def start_save_thread(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية قبل بدء الحفظ.")
            return
        self.merge_phase = 'saving'
        self.merge_action_button.hide()
        msg_save = "جاري حفظ الآية..." if len(self.merge_list) == 1 else "جاري حفظ الآيات..."
        self.merge_feedback_label.setText(msg_save)
        self.merge_progress_bar.show()
        output_dir = self.current_merge_output_path
        for item in self.merge_list:
            if os.path.exists(item["local_path"]):
                item["local_path"] = item["local_path"]
            else:
                safe_filename = "".join(c for c in item['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"temp_{safe_filename}")
                if os.path.exists(temp_path):
                    item["local_path"] = temp_path
                else:
                    self.on_merge_finished(False, f"خطأ: الملف المؤقت للآية لم يتم العثور عليه: {item['filename']}")
                    return
        self.save_thread = SaveThread(self.merge_list, output_dir)
        self.save_thread.progress.connect(self.merge_progress_bar.setValue)
        self.save_thread.finished.connect(self.on_merge_finished)
        self.save_thread.cancelled.connect(lambda: self.on_merge_finished(False, "تم إلغاء الحفظ."))
        self.save_thread.start()

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
                    if temp_path not in self.files_to_delete_after_merge: self.files_to_delete_after_merge.append(temp_path)
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
            if self.save_mode:
                guiTools.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الحفظ.")
            else:
                guiTools.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
                if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                    try: os.remove(self.current_merge_output_path)
                    except: pass
        elif success:
            if self.save_mode:
                guiTools.MessageBox.view(self, "نجاح", "تم حفظ الآيات بنجاح.")
            else:
                guiTools.MessageBox.view(self, "نجاح", "تم دمج الآيات بنجاح.")
        else:
            guiTools.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف","هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
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
        self.resume_after_action()

    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets_to_disable = [self.text, self.N_aya, self.P_aya, self.PPS, self.changeCurrentReciterButton, self.mergeButton, self.saveAllButton]
        for widget in widgets_to_disable: widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير لعملية الدمج...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
        else: self.merge_action_button.setStyleSheet("")
