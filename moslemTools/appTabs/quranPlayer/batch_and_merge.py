import guiTools, requests, os, winsound, gui, functions, subprocess, shutil
import ujson as json
from guiTools import TextViewer
from guiTools import speak
from guiTools.QCustomListDialog import QCustomListDialog
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from functions import audio_manager
from .threads import DownloadThread, MergeThread
from .favorites import FavoritesManager


class PlayerBatchAndMergeMixin:
    def handle_merge_action(self):
        if self.is_merging:
            self.confirm_and_cancel_merge()
        else:
            self.prepare_merge()

    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()

    def add_to_merge_list(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        selected_surah_item = self.surahListWidget.currentItem()
        if not selected_reciter_item or not selected_surah_item:
            return
        reciter = selected_reciter_item.text()
        surah = selected_surah_item.text()
        surah_info = {"reciter": reciter, "surah": surah, "url": self.reciters_data[reciter][surah]}
        self.merge_list.append(surah_info)
        self.update_merge_ui()
        self.update_download_batch_ui()

    def remove_from_merge_list(self):
        if not self.merge_list:
            return
        num_items = len(self.merge_list)
        item_names = [f"{i+1}: {item['surah']}" for i, item in enumerate(self.merge_list)]
        selected_item_str, ok = QCustomListDialog.getItem(self, "إزالة سورة", "اختر السورة لإزالتها:", item_names)
        if ok and selected_item_str:
            index_to_remove = int(selected_item_str.split(':')[0]) - 1
            if 0 <= index_to_remove < num_items:
                del self.merge_list[index_to_remove]
                self.update_merge_ui()
                self.update_download_batch_ui()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرقم المدخل خارج النطاق الصحيح.")

    def update_merge_ui(self):
        count = len(self.merge_list)
        is_merging_selected = count > 0
        if count > 0:
            self.merge_feedback_label.setText(f"تم تحديد {self.format_surah_count(count)} للدمج.")
            self.merge_feedback_label.setVisible(True)
        else:
            self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setVisible(count >= 2)
        self.batch_download_action_button.setEnabled(not is_merging_selected)
        self.dl_all_app.setEnabled(not is_merging_selected)
        self.merge_all_from_start_button.setVisible(not is_merging_selected)
        self.merge_all_from_end_button.setVisible(not is_merging_selected)

    def cancel_merge(self):
        self.merge_list.clear()
        self.update_merge_ui()
        self.update_download_batch_ui()

    def set_as_merge_start(self):
        self.cancel_download_batch()
        self.cancel_download_start()
        self.first_merge_selection_index = self.surahListWidget.currentRow()
        speak(f"تم تحديد {self.surahListWidget.currentItem().text()} كبداية للدمج")

    def cancel_merge_start(self):
        self.first_merge_selection_index = None
        speak("تم إلغاء تحديد بداية الدمج")

    def merge_from_start_to_here(self):
        if self.first_merge_selection_index is None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء تحديد بداية الدمج أولاً.")
            return
        end_index = self.surahListWidget.currentRow()
        start_index = self.first_merge_selection_index
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.merge_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        for i in range(start_index, end_index + 1):
            surah_item = self.surahListWidget.item(i)
            if surah_item:
                surah = surah_item.text()
                surah_info = {"reciter": reciter, "surah": surah, "url": self.reciters_data[reciter][surah]}
                self.merge_list.append(surah_info)
        self.first_merge_selection_index = None
        if len(self.merge_list) < 1:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم تحديد أي سور للدمج.")
            return
        speak(f"سيتم دمج {self.format_surah_count(len(self.merge_list))}")
        self.prepare_merge(is_all=True)

    def set_as_download_start(self, target='app'):
        self.cancel_merge()
        self.cancel_merge_start()
        if self.download_batch_list and self.batch_download_target != target:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك تغيير وجهة التحميل أثناء وجود قائمة نشطة لـ {self.batch_download_target}. قم بإلغاء القائمة الحالية أولاً.")
             return
        self.batch_download_target = target
        self.first_download_selection_index = self.surahListWidget.currentRow()
        speak(f"تم تحديد {self.surahListWidget.currentItem().text()} كبداية للتحميل")

    def cancel_download_start(self):
        self.first_download_selection_index = None
        speak("تم إلغاء تحديد بداية التحميل")

    def download_from_start_to_here(self, target='app'):
        if self.first_download_selection_index is None:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء تحديد بداية التحميل أولاً.")
            return
        if self.download_batch_list and self.batch_download_target != target:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك تغيير وجهة التحميل أثناء وجود قائمة نشطة لـ {self.batch_download_target}. قم بإلغاء القائمة الحالية أولاً.")
             return
        self.batch_download_target = target
        end_index = self.surahListWidget.currentRow()
        start_index = self.first_download_selection_index
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.download_batch_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        for i in range(start_index, end_index + 1):
            surah_item = self.surahListWidget.item(i)
            if surah_item:
                surah = surah_item.text()
                if target == 'app':
                    local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
                    if os.path.exists(local_path):
                        continue
                surah_info = {"reciter": reciter, "surah": surah, "url": self.reciters_data[reciter][surah]}
                self.download_batch_list.append(surah_info)
        self.first_download_selection_index = None
        if not self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", "جميع السور في النطاق المحدد محملة بالفعل.")
            return
        self.prepare_batch_download()

    def prepare_merge_all_from_start(self):
        if not self.recitersListWidget.currentItem():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء اختيار قارئ أولاً.")
            return
        self.merge_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        surah_names = list(self.reciters_data[reciter].keys())
        for surah in surah_names:
            url = self.reciters_data[reciter][surah]
            self.merge_list.append({"reciter": reciter, "surah": surah, "url": url})
        self.prepare_merge(is_all=True)

    def prepare_merge_all_from_end(self):
        if not self.recitersListWidget.currentItem():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرجاء اختيار قارئ أولاً.")
            return
        self.merge_list.clear()
        reciter = self.recitersListWidget.currentItem().text()
        surah_names = list(self.reciters_data[reciter].keys())
        surah_names.reverse()
        for surah in surah_names:
            url = self.reciters_data[reciter][surah]
            self.merge_list.append({"reciter": reciter, "surah": surah, "url": url})
        self.prepare_merge(is_all=True)

    def prepare_merge(self, is_all=False):
        if self.check_if_busy(): return
        if len(self.merge_list) < 2 and not is_all:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يجب تحديد سورتين على الأقل للدمج.")
            return
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            return
        urls_to_download = []
        for item in self.merge_list:
            reciter = item["reciter"]
            surah = item["surah"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if not os.path.exists(local_path):
                urls_to_download.append(item["url"])
        num_files_to_download = len(urls_to_download)
        if num_files_to_download > 0:
            confirm_message = (f"تنبيه: يتطلب الدمج تحميل {self.format_surah_count(num_files_to_download)} غير موجودة.\nسيتم الآن تحميل ودمج الملفات المحددة على مرحلتين:\nمرحلة التحميل: سيتم تحميل الملفات تباعًا. في هذه الأثناء، لا يمكنك إلغاء تحميل أي سورة.\nمرحلة الدمج: بعد انتهاء التحميل، لن تتمكن من استخدام الواجهة إلا لإلغاء عملية الدمج بأكملها.\n\nهل تريد المتابعة؟")
        else:
            confirm_message = ("جميع السور المحددة جاهزة للدمج.\nستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة باستثناء زر إلغاء الدمج.\n\nهل تريد المتابعة؟")
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            if is_all:
                self.cancel_merge()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            if is_all:
                self.cancel_merge()
            return
        self.set_ui_for_merge_download(False)
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.process_next_in_merge_queue()

    def process_next_in_merge_queue(self):
        output_dir = os.path.dirname(self.current_merge_output_path)
        next_item_to_download = None
        count_pending_downloads = 0
        for item in self.merge_list:
            reciter = item["reciter"]
            surah = item["surah"]
            url = item["url"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if os.path.exists(local_path):
                continue
            if url in self.completed_merge_downloads:
                continue
            count_pending_downloads += 1
            if next_item_to_download is None:
                next_item_to_download = item
        if next_item_to_download:
            self.progressBar.setVisible(True)
            self.progress_text_label.setVisible(True)
            total_downloads = len([item for item in self.merge_list if not os.path.exists(os.path.join(os.getenv('appdata'), app.appName, 'quran surah reciters', item['reciter'], item['surah'] + '.mp3'))])
            self.update_progress_label(len(self.completed_merge_downloads), total_downloads)
            self.cancel_download_button.setVisible(False)
            url = next_item_to_download['url']
            reciter = next_item_to_download['reciter']
            surah = next_item_to_download['surah']
            safe_surah_name = "".join(c for c in surah if c.isalnum() or c in (' ', '_')).rstrip()
            download_path = os.path.join(output_dir, f"{reciter}_{safe_surah_name}.mp3")
            self.current_download_url = url
            self.merge_feedback_label.setVisible(True)
            self.merge_feedback_label.setText(f"جاري تحميل: {reciter} - {surah}")
            self.pause_download_button.setText("إيقاف مؤقت")
            self.pause_download_button.setVisible(True)
            self.download_thread = DownloadThread(self, url, download_path)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.network_error.connect(self.on_download_network_error)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.progress_text_label.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)
            self.finalize_and_execute_merge()

    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()

    def finalize_and_execute_merge(self):
        self.set_ui_for_merge_download(True)
        files_for_ffmpeg = []
        self.files_to_delete_after_merge.clear()
        output_dir = os.path.dirname(self.current_merge_output_path)
        for item in self.merge_list:
            reciter, surah, url = item["reciter"], item["surah"], item["url"]
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if os.path.exists(local_path):
                files_for_ffmpeg.append(local_path)
            else:
                safe_surah_name = "".join(c for c in surah if c.isalnum() or c in (' ', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"{reciter}_{safe_surah_name}.mp3")
                files_for_ffmpeg.append(temp_path)
                if temp_path not in self.files_to_delete_after_merge:
                    self.files_to_delete_after_merge.append(temp_path)
        if not files_for_ffmpeg:
             guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على أي ملفات للدمج.")
             self.cancel_merge()
             return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)

    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.cancellation_requested = False
        self.set_ui_enabled(False)
        self.merge_feedback_label.setEnabled(True)
        count = len(self.merge_list)
        self.merge_feedback_label.setText(f"جاري دمج {self.format_surah_count(count)}...")
        self.merge_feedback_label.setVisible(True)
        self.merge_action_button.setVisible(True)
        self.merge_action_button.setEnabled(True)
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
        self.merge_thread = MergeThread(self, self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()

    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.set_ui_enabled(True)
        self.merge_feedback_label.setVisible(False)
        self.merge_action_button.setText("بدء دمج السور المحددة")
        self.merge_action_button.setStyleSheet("")
        self.update_merge_ui()
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                os.remove(self.current_merge_output_path)
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف السور الفردية التي تم تحميلها لهذه العملية الملغاة؟", "نعم", "لا")
                if reply == 0:
                    for f_path in self.files_to_delete_after_merge:
                        if os.path.exists(f_path):
                            try: os.remove(f_path)
                            except: pass
        elif success:
            merged_files_names = [f" {item['surah']}" for item in self.merge_list]
            details = "\n".join(merged_files_names)
            success_message = f"تم دمج السور بنجاح:\n{details}"
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", success_message)
            if self.files_to_delete_after_merge:
                reply = guiTools.QQuestionMessageBox.view(self, "تنظيف", "هل تريد حذف السور الفردية التي تم تحميلها للدمج؟", "نعم", "لا")
                if reply == 0:
                    for f_path in self.files_to_delete_after_merge:
                        if os.path.exists(f_path):
                            try: os.remove(f_path)
                            except: pass
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        self.cancellation_requested = False
        self.cancel_merge()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()

    def handle_batch_download_action(self):
        if self.is_downloading_batch:
            self.full_batch_cancellation_requested = True
            self.cancel_current_download()
        else:
            self.prepare_batch_download()

    def add_to_download_batch(self, target='app'):
        selected_reciter_item = self.recitersListWidget.currentItem()
        selected_surah_item = self.surahListWidget.currentItem()
        if not selected_reciter_item or not selected_surah_item:
            return
        reciter = selected_reciter_item.text()
        surah = selected_surah_item.text()
        if self.download_batch_list:
            if self.download_batch_list[0]["reciter"] != reciter:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لا يمكنك إضافة سور من قراء مختلفين في دفعة واحدة. سيتم إلغاء الدفعة السابقة.")
                self.cancel_download_batch()
            elif self.batch_download_target != target:
                 guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"لا يمكنك إضافة سور لـ {target} لأن القائمة الحالية مخصصة لـ {self.batch_download_target}. يرجى إنهاء القائمة الحالية أو إلغاؤها أولاً.")
                 return
        self.batch_download_target = target
        if target == 'app':
            local_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah}.mp3")
            if os.path.exists(local_path):
                guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", f"سورة {surah} تم تحميلها بالفعل.")
                return
        surah_info = {"reciter": reciter, "surah": surah, "url": self.reciters_data[reciter][surah]}
        if surah_info in self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "ملاحظة", "تم إضافة هذه السورة إلى القائمة بالفعل.")
            return
        self.download_batch_list.append(surah_info)
        self.update_download_batch_ui()
        self.update_merge_ui()

    def remove_from_download_batch(self):
        if not self.download_batch_list:
            return
        num_items = len(self.download_batch_list)
        item_names = [f"{i+1}: {item['surah']}" for i, item in enumerate(self.download_batch_list)]
        selected_item_str, ok = QCustomListDialog.getItem(self, "إزالة سورة", "اختر السورة لإزالتها من قائمة التحميل:", item_names)
        if ok and selected_item_str:
            index_to_remove = int(selected_item_str.split(':')[0]) - 1
            if 0 <= index_to_remove < num_items:
                del self.download_batch_list[index_to_remove]
                self.update_download_batch_ui()
                self.update_merge_ui()
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "الرقم المدخل خارج النطاق الصحيح.")

    def format_surah_count(self, count):
        if count == 1:
            return "سورة واحدة"
        elif count == 2:
            return "سورتين"
        elif count >= 3 and count <= 10:
            return f"{count} سور"
        else:
            return f"{count} سورة"

    def update_download_batch_ui(self):
        count = len(self.download_batch_list)
        excluded_count = len(self.excluded_surahs_in_batch)
        if count > 0:
            message = f"تم تحديد {self.format_surah_count(count)} للتحميل ({'تطبيق' if self.batch_download_target == 'app' else 'جهاز'})."
            if excluded_count > 0:
                message += f" وتم استثناء {self.format_surah_count(excluded_count)}."
            self.batch_download_feedback_label.setText(message)
            self.batch_download_feedback_label.setVisible(True)
        else:
            self.batch_download_feedback_label.setVisible(False)
        self.batch_download_action_button.setVisible(count > 0)
        if self.is_downloading_batch:
            self.batch_download_action_button.setText("إلغاء تحميل الدفعة")
            self.batch_download_action_button.setStyleSheet("background-color: #8B0000; color: white;")
        else:
            self.batch_download_action_button.setText("بدء تحميل السور المحددة")
            self.batch_download_action_button.setStyleSheet("")
            self.excluded_surahs_in_batch.clear()
        is_batching = count > 0
        self.merge_action_button.setEnabled(not is_batching)
        self.merge_all_from_start_button.setEnabled(not is_batching)
        self.merge_all_from_end_button.setEnabled(not is_batching)
        self.dl_all_app.setEnabled(not is_batching)

    def cancel_download_batch(self):
        if self.is_downloading_batch:
            return
        self.download_batch_list.clear()
        self.excluded_surahs_in_batch.clear()
        self.batch_download_feedback_label.setVisible(False)
        self.batch_download_action_button.setVisible(False)
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.update_download_batch_ui()
        self.update_merge_ui()

    def prepare_batch_download(self):
        if self.check_if_busy(): return
        if not self.download_batch_list:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لم يتم تحديد أي سور للتحميل.")
            return
        count = len(self.download_batch_list)
        surah_names = "\n".join([item["surah"] for item in self.download_batch_list])
        if count == 1:
            intro_text = "سيتم تحميل سورة واحدة وهي:"
        elif count == 2:
            intro_text = "سيتم تحميل سورتين وهما:"
        else:
            intro_text = f"سيتم تحميل {self.format_surah_count(count)} وهم:"
        confirm_message = (f"{intro_text}\n{surah_names}\n\nيمكنك إلغاء أي سورة أثناء التحميل وسيكمل تحميل الباقي.")
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", confirm_message, "نعم", "لا")
        if response != 0:
            self.cancel_download_batch()
            return
        reciter = self.download_batch_list[0]["reciter"]
        if self.batch_download_target == 'app':
            app_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
            os.makedirs(app_folder, exist_ok=True)
            self.save_folder = app_folder
        else:
            save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ السور")
            if not save_folder:
                self.cancel_download_batch()
                return
            self.save_folder = save_folder
        self.successfully_downloaded_in_batch.clear()
        self.files_to_download = []
        for item in self.download_batch_list:
            self.files_to_download.append( (item["surah"], item["url"]) )
        self.current_file_index = 0
        self.is_downloading_batch = True
        self.set_ui_for_batch_download(False)
        self.merge_action_button.setVisible(False)
        self.merge_all_from_start_button.setVisible(False)
        self.merge_all_from_end_button.setVisible(False)
        self.merge_feedback_label.setVisible(False)
        self.update_download_batch_ui()
        self.cancel_download_button.setVisible(True)
        self.current_download_reciter = reciter
        self.info_menu.setEnabled(False)
        self.duration.setEnabled(False)
        self.download_next_audio_to_app()

    def set_ui_for_batch_download(self, enabled):
        widgets_to_toggle = [
            self.recitersListWidget, self.surahListWidget,
            self.reciterSearchEdit, self.surahSearchEdit,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.play_all_to_start, self.repeat_surah_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_action_button, self.merge_all_from_start_button,
            self.merge_all_from_end_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        if not enabled:
            self.batch_download_action_button.setEnabled(True)

    def set_ui_enabled(self, enabled):
        widgets_to_toggle = [
            self.recitersListWidget, self.surahListWidget,
            self.reciterSearchEdit, self.surahSearchEdit,
            self.reciterSearchLabel, self.surahSearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.play_all_to_start, self.repeat_surah_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_from_start_button, self.merge_all_from_end_button,
            self.recitersLabel, self.surahsLabel,
            self.duration, self.info_menu,
            self.merge_feedback_label,
            self.batch_download_action_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        if not enabled:
            self.merge_action_button.setEnabled(True)

    def set_ui_for_merge_download(self, enabled):
        widgets_to_toggle = [
            self.recitersListWidget, self.surahListWidget,
            self.reciterSearchEdit, self.surahSearchEdit,
            self.reciterSearchLabel, self.surahSearchLabel,
            self.dl_all, self.dl_all_app, self.delete,
            self.play_all_to_end, self.play_all_to_start, self.repeat_surah_button,
            self.Slider, self.openBookmarks, self.User_guide,
            self.merge_all_from_start_button, self.merge_all_from_end_button,
            self.recitersLabel, self.surahsLabel,
            self.duration, self.info_menu,
            self.merge_action_button,
            self.batch_download_action_button
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
        self.progressBar.setVisible(not enabled)
        self.progress_text_label.setVisible(not enabled)
        self.cancel_download_button.setVisible(False)
        self.merge_feedback_label.setEnabled(True)
