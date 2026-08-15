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


class PlayerDownloadManagerMixin:
    def delete_surah(self, surah_name=None):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter = selected_reciter_item.text()
        reciter_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
        try:
            if surah_name:
                surah_path = os.path.join(reciter_folder, f"{surah_name}.mp3")
                if os.path.exists(surah_path):
                    confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف السورة المحددة؟", "نعم", "لا")
                    if confirm == 0:
                        self.stop_audio_completely()
                        try:
                            os.remove(surah_path)
                            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف السورة بنجاح.")
                        except PermissionError:
                            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف السورة. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
            else:
                if os.path.exists(reciter_folder):
                    confirm = guiTools.QQuestionMessageBox.view(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف جميع السور؟", "نعم", "لا")
                    if confirm == 0:
                        self.stop_audio_completely()
                        for file in os.listdir(reciter_folder):
                            if file.endswith(".mp3"):
                                try:
                                    os.remove(os.path.join(reciter_folder, file))
                                except PermissionError:
                                    guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر حذف بعض الملفات. قد تكون قيد الاستخدام, يرجى إعادة تشغيل البرنامج")
                        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم حذف جميع السور بنجاح.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ غير متوقع", str(e))
        self.check_all_surahs_downloaded()

    def check_all_surahs_downloaded(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item:
            reciter = selected_reciter_item.text()
            reciter_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
            if os.path.exists(reciter_folder):
                all_files = os.listdir(reciter_folder)
                all_surahs = self.reciters_data.get(reciter, {}).keys()
                downloaded_surahs = {os.path.splitext(file)[0] for file in all_files if file.endswith(".mp3")}
                if downloaded_surahs >= set(all_surahs):
                    self.delete.setVisible(True)
                    self.dl_all_app.setVisible(False)
                else:
                    self.delete.setVisible(False)
                    self.dl_all_app.setVisible(True)
            else:
                self.delete.setVisible(False)
                self.dl_all_app.setVisible(True)

    def check_current_surah_downloaded(self):
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter = selected_reciter_item.text()
        selected_item = self.surahListWidget.currentItem()
        if not selected_item:
            return
        surah_name = selected_item.text()
        surah_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah_name}.mp3")
        if os.path.exists(surah_path):
            action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("حذف السورة المحددة من التطبيق")
            btn.setStyleSheet("background-color: #8B0000; color: white;")
            btn.clicked.connect(lambda: self.delete_surah(surah_name))
            action.setDefaultWidget(btn)
            return action
        return None

    def download_selected_audio_to_app(self):
        if self.check_if_busy(): return
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                url = self.reciters_data[reciter][selected_item.text()]
                audio_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                os.makedirs(audio_folder, exist_ok=True)
                filepath = os.path.join(audio_folder, f"{selected_item.text()}.mp3")
                if self.is_audio_downloaded(filepath):
                    guiTools.qMessageBox.MessageBox.view(self, "تنبيه", f"سورة {selected_item.text()} تم تحميلها بالفعل.")
                    return
                self.set_ui_enabled(False)
                self.progressBar.setVisible(True)
                self.progress_text_label.setText("جاري تحميل سورة واحدة...")
                self.progress_text_label.setVisible(True)
                self.pause_download_button.setText("إيقاف مؤقت")
                self.pause_download_button.setVisible(True)
                self.cancel_download_button.setVisible(True)
                self.current_download_filename = selected_item.text()
                self.current_download_reciter = reciter
                self.download_thread = DownloadThread(self, url, filepath)
                self.download_thread.progress.connect(self.progressBar.setValue)
                self.download_thread.finished.connect(self.download_audio_complete)
                self.download_thread.cancelled.connect(self.on_download_cancelled)
                self.download_thread.network_error.connect(self.on_download_network_error)
                self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء تحميل المقطع: " + str(e))
            self.set_ui_enabled(True)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)

    def download_all_audios_to_app(self):
        if self.check_if_busy(): return
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            self.files_to_download = [
                (file_name, url)
                for file_name, url in self.reciters_data.get(reciter, {}).items()
                if not self.is_audio_downloaded(
                    os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{file_name}.mp3")
                )
            ]
            self.current_file_index = 0
            if not self.files_to_download:
                guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "جميع السور محملة بالفعل")
                return
            response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", "هل تريد تحميل جميع السور المتاحة لهذا القارئ؟", "نعم", "لا")
            if response == 0:
                self.is_downloading_all_app = True
                self.successfully_downloaded_in_batch.clear()
                self.excluded_surahs_in_batch.clear()
                app_folder = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter)
                os.makedirs(app_folder, exist_ok=True)
                self.save_folder = app_folder
                self.set_ui_for_batch_download(False)
                self.cancel_download_button.setVisible(True)
                self.current_download_reciter = reciter
                self.info_menu.setEnabled(False)
                self.duration.setEnabled(False)
                self.download_next_audio_to_app()
            else:
                return
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "حدث خطأ أثناء بدء التحميل: " + str(e))
            if hasattr(self, 'is_downloading_all_app'):
                self.is_downloading_all_app = False
            self.set_ui_for_batch_download(True)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)

    def is_audio_downloaded(self, filepath):
        return os.path.exists(filepath)

    def on_single_batch_download_finished(self):
        if hasattr(self, 'current_download_filename'):
            self.successfully_downloaded_in_batch.append(self.current_download_filename)
        self.download_next_audio_to_app()

    def download_next_audio_to_app(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            if self.is_audio_downloaded(filepath):
                self.current_file_index += 1
                self.download_next_audio_to_app()
                return
            self.update_progress_label(self.current_file_index, len(self.files_to_download))
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.progress_text_label.setVisible(True)
            self.pause_download_button.setText("إيقاف مؤقت")
            self.pause_download_button.setVisible(True)
            self.cancel_download_button.setVisible(True)
            self.current_download_filename = file_name
            self.download_thread = DownloadThread(self, url, filepath)
            self.download_thread.progress.connect(self.progressBar.setValue)
            self.download_thread.finished.connect(self.on_single_batch_download_finished)
            self.download_thread.network_error.connect(self.on_download_network_error)
            if hasattr(self, 'is_downloading_all_app') and self.is_downloading_all_app:
                self.download_thread.cancelled.connect(self.on_download_cancelled_all_app)
            else:
                self.download_thread.cancelled.connect(self.on_download_cancelled_batch_internal)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.progress_text_label.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)
            self.info_menu.setEnabled(True)
            self.duration.setEnabled(True)
            message_parts = []
            if self.successfully_downloaded_in_batch:
                downloaded_list = "\n".join([name for name in self.successfully_downloaded_in_batch])
                message_parts.append(f"تم تحميل السور التالية بنجاح:\n{downloaded_list}")
            if self.excluded_surahs_in_batch:
                excluded_list = "\n".join([name for name in self.excluded_surahs_in_batch])
                message_parts.append(f"\nتم إلغاء أو استثناء تحميل السور التالية:\n{excluded_list}")
            if not message_parts:
                success_message = "اكتملت عملية التحميل (لم يتم تحميل ملفات جديدة)."
            else:
                success_message = "\n".join(message_parts)
            guiTools.qMessageBox.MessageBox.view(self, "تم الانتهاء من التحميل", success_message)
            self.successfully_downloaded_in_batch.clear()
            self.excluded_surahs_in_batch.clear()
            if self.is_downloading_batch:
                self.is_downloading_batch = False
                self.set_ui_for_batch_download(True)
                self.cancel_download_batch()
            else:
                self.set_ui_for_batch_download(True)
            if hasattr(self, 'is_downloading_all_app'):
                self.is_downloading_all_app = False
            self.update_merge_ui()

    def on_download_cancelled_all_app(self):
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.info_menu.setEnabled(True)
        self.duration.setEnabled(True)
        self.set_ui_for_batch_download(True)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'current_download_reciter'):
            self.mark_for_deletion(self.current_download_filename, self.current_download_reciter, app_internal=True)
            del self.current_download_filename
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل باقي السور، وتم الاحتفاظ بما تم تحميله بنجاح.")
        self.is_downloading_all_app = False
        self.current_file_index = len(self.files_to_download)
        self.update_merge_ui()

    def download_audio_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.set_ui_enabled(True)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل السورة بنجاح.")
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename
        if hasattr(self, 'current_download_reciter'):
            del self.current_download_reciter

    def download_all_soar(self):
        if self.check_if_busy(): return
        selected_reciter_item = self.recitersListWidget.currentItem()
        if not selected_reciter_item:
            return
        reciter_name = selected_reciter_item.text()
        self.files_to_download = list(self.reciters_data.get(reciter_name, {}).items())
        self.current_file_index = 0
        save_folder = qt.QFileDialog.getExistingDirectory(self, "اختيار مجلد لحفظ السور")
        if not save_folder:
            return
        response = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", "هل أنت متأكد من تحميل جميع السور؟", "نعم", "لا")
        if response == 0:
            self.save_folder = save_folder
            self.set_ui_enabled(False)
            self.progressBar.setVisible(True)
            self.progress_text_label.setVisible(True)
            self.cancel_download_button.setVisible(True)
            self.download_next_sora()
        else:
            return

    def download_next_sora(self):
        if self.current_file_index < len(self.files_to_download):
            file_name, url = self.files_to_download[self.current_file_index]
            filepath = os.path.join(self.save_folder, f"{file_name}.mp3")
            self.update_progress_label(self.current_file_index, len(self.files_to_download))
            self.current_file_index += 1
            self.progressBar.setVisible(True)
            self.progress_text_label.setVisible(True)
            self.pause_download_button.setText("إيقاف مؤقت")
            self.pause_download_button.setVisible(True)
            self.cancel_download_button.setVisible(True)
            self.current_download_filename = file_name
            self.download_thread = DownloadThread(self, url, filepath)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.cancelled.connect(self.on_download_cancelled_batch_external)
            self.download_thread.network_error.connect(self.on_download_network_error)
            self.download_thread.start()
        else:
            self.progressBar.setVisible(False)
            self.progress_text_label.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)
            self.set_ui_enabled(True)
            guiTools.qMessageBox.MessageBox.view(self, "تم التحميل", "تم تحميل جميع السور.")

    def update_progress(self, progress_percent):
        self.progressBar.setValue(progress_percent)

    def download_finished(self):
        self.progressBar.setValue(100)
        self.download_next_sora()

    def download_complete(self):
        self.progressBar.setValue(100)
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.set_ui_enabled(True)
        guiTools.qMessageBox.MessageBox.view(self, "تم", "تم تحميل السورة")
        if hasattr(self, 'current_download_filename'):
            del self.current_download_filename

    def toggle_download_pause(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            if self.download_thread.is_paused:
                self.pause_download_button.setText("إيقاف مؤقت")
                self.download_thread.resume()
            else:
                self.pause_download_button.setText("استئناف")
                self.download_thread.pause()

    def on_download_network_error(self, msg):
        self.pause_download_button.setText("استئناف")
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def cancel_current_download(self):
        if hasattr(self, 'is_downloading_all_app') and self.is_downloading_all_app:
            reply = guiTools.QQuestionMessageBox.view(self, "إلغاء التحميل", "هل أنت متأكد أنك تريد إلغاء تحميل باقي السور بالكامل؟", "نعم", "لا")
            if reply == 0:
                if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                    self.download_thread.cancel()
            return
        is_batch_download = self.is_downloading_batch or (hasattr(self, 'files_to_download') and self.current_file_index < len(self.files_to_download) and hasattr(self, 'current_download_reciter'))
        if is_batch_download and not self.full_batch_cancellation_requested:
            current_surah_name = self.current_download_filename
            remaining_files = len(self.files_to_download) - self.current_file_index
            reply = guiTools.QQuestionMessageBox.view(self, "إلغاء سورة", f"هل تريد إلغاء تحميل السورة الحالية ({current_surah_name}) ومتابعة تحميل باقي السور ({self.format_surah_count(remaining_files)})؟\n\nاضغط 'نعم' للإلغاء، 'لا' للمتابعة دون إلغاء هذه السورة.", "نعم", "لا")
            if reply == 0:
                if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                    self.download_thread.cancel()
            else:
                pass
        else:
            if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                self.download_thread.cancel()

    def on_download_cancelled(self):
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'current_download_reciter'):
            self.mark_for_deletion(self.current_download_filename, self.current_download_reciter, app_internal=True)
            del self.current_download_filename
            del self.current_download_reciter
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل السورة.")

    def on_download_cancelled_batch_internal(self):
        if self.full_batch_cancellation_requested:
            self.full_batch_cancellation_requested=False
            self.current_file_index=len(self.files_to_download)
            self.progressBar.setVisible(False)
            self.progress_text_label.setVisible(False)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)
            self.info_menu.setEnabled(True)
            self.duration.setEnabled(True)
            files_to_delete=list(self.successfully_downloaded_in_batch)
            if hasattr(self, 'current_download_filename') and self.current_download_filename not in files_to_delete:
                files_to_delete.append(self.current_download_filename)
            if files_to_delete and hasattr(self,'current_download_reciter'):
                reciter=self.current_download_reciter
                for file_name in files_to_delete:
                    self.mark_for_deletion(file_name,reciter,app_internal=(self.batch_download_target == 'app'))
                guiTools.qMessageBox.MessageBox.view(self,"إلغاء التحميل",f"تم إلغاء تحميل الدفعة وحذف {self.format_surah_count(len(files_to_delete))} ملفات.")
            else:
                guiTools.qMessageBox.MessageBox.view(self,"إلغاء التحميل","تم إلغاء تحميل الدفعة.")
            self.successfully_downloaded_in_batch.clear()
            self.excluded_surahs_in_batch.clear()
            if hasattr(self,'current_download_filename'): del self.current_download_filename
            if hasattr(self,'current_download_reciter'): del self.current_download_reciter
            if self.is_downloading_batch:
                self.is_downloading_batch=False
                self.set_ui_for_batch_download(True)
                self.cancel_download_batch()
            else:
                self.set_ui_for_batch_download(True)
            self.update_merge_ui()
        else:
            self.progressBar.setVisible(False)
            self.progress_text_label.setVisible(False)
            self.cancel_download_button.setVisible(True)
            current_surah_name=self.current_download_filename
            self.mark_for_deletion(self.current_download_filename,self.current_download_reciter,app_internal=(self.batch_download_target == 'app'))
            self.excluded_surahs_in_batch.append(current_surah_name)
            self.update_download_batch_ui()
            del self.current_download_filename
            guiTools.qMessageBox.MessageBox.view(self,"تخطي السورة",f"تم إلغاء تحميل {current_surah_name} وسيتم متابعة الباقي.")
            self.download_next_audio_to_app()

    def on_download_cancelled_batch_external(self):
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename
        self.current_file_index = len(self.files_to_download)
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل جميع السور، لكن سيتم حذف آخر سورة كان يتم تحميلها")

    def mark_for_deletion(self, file_name, reciter, app_internal=False):
        if app_internal:
            filepath=os.path.join(os.getenv('appdata'),app.appName,"quran surah reciters",reciter,f"{file_name}.mp3")
        else:
            filepath=os.path.join(self.save_folder,f"{file_name}.mp3")
        if not os.path.exists(filepath):
            return
        delete_me=filepath+".delete_me"
        if os.path.exists(delete_me):
            try: os.remove(delete_me)
            except: pass
        try:
            os.rename(filepath,delete_me)
        except:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ",f"تعذر وضع علامة للحذف على الملف: {file_name}.mp3. قد تحتاج إلى حذفه يدوياً بعد إغلاق التطبيق.")

    def download_selected_audio(self):
        if self.check_if_busy(): return
        try:
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            selected_item = self.surahListWidget.currentItem()
            if selected_item:
                url = self.reciters_data[reciter][selected_item.text()]
                filepath, _ = qt.QFileDialog.getSaveFileName(self, "save surah", "", "Audio Files (*.mp3)")
                if filepath:
                    self.set_ui_enabled(False)
                    self.progressBar.setVisible(True)
                    self.progress_text_label.setText("جاري تحميل سورة واحدة...")
                    self.progress_text_label.setVisible(True)
                    self.pause_download_button.setText("إيقاف مؤقت")
                    self.pause_download_button.setVisible(True)
                    self.cancel_download_button.setVisible(True)
                    self.save_folder = os.path.dirname(filepath)
                    self.current_download_filename = os.path.splitext(os.path.basename(filepath))[0]
                    self.download_thread = DownloadThread(self, url, filepath)
                    self.download_thread.progress.connect(self.progressBar.setValue)
                    self.download_thread.finished.connect(self.download_complete)
                    self.download_thread.cancelled.connect(self.on_download_cancelled_external_single)
                    self.download_thread.network_error.connect(self.on_download_network_error)
                    self.download_thread.start()
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "حدث خطأ ما: " + str(e))
            self.set_ui_enabled(True)
            self.cancel_download_button.setVisible(False)
            self.pause_download_button.setVisible(False)

    def on_download_cancelled_external_single(self):
        self.progressBar.setVisible(False)
        self.progress_text_label.setVisible(False)
        self.cancel_download_button.setVisible(False)
        self.pause_download_button.setVisible(False)
        self.set_ui_enabled(True)
        if hasattr(self, 'current_download_filename') and hasattr(self, 'save_folder'):
            filepath = os.path.join(self.save_folder, f"{self.current_download_filename}.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر حذف الملف الذي تم إلغاء تنزيله: {self.current_download_filename}.mp3\nالرجاء حذفه يدوياً. {e}")
            del self.current_download_filename
            del self.save_folder
        guiTools.qMessageBox.MessageBox.view(self, "إلغاء التحميل", "تم إلغاء تحميل السورة.")

    def cleanup_pending_deletions(self):
        quran_reciters_dir = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters")
        if os.path.exists(quran_reciters_dir):
            for root, _, files in os.walk(quran_reciters_dir):
                for file in files:
                    if file.endswith(".delete_me"):
                        filepath = os.path.join(root, file)
                        try:
                            os.remove(filepath)
                            print(f"Cleaned up deleted file: {filepath}")
                        except Exception as e:
                            print(f"Could not delete {filepath} on startup: {e}")
