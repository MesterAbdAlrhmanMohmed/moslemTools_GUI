import guiTools, pyperclip, winsound, functions, re, os, settings, requests, shutil
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from gui.quranViewer import QuranViewer
from gui.tafaseerViewer import TafaseerViewer
from gui.translationViewer import translationViewer
from gui.changeReciter import ChangeReciter
from .search_worker import DownloadThread, SearchModeDialog, SearchThread, RemainingThread


class ResearcherActionsMixin:
    def show_tafseer(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        TafaseerViewer(self, ayah_num, ayah_num).exec()
        self.resume_after_action()

    def show_translation(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        translationViewer(self, ayah_num, ayah_num).exec()
        self.resume_after_action()

    def show_iarab(self, metadata):
        menu = qt.QMenu("اختر نوع الإعراب", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        simplified_action = qt1.QAction("إعراب مبسط", self)
        simplified_action.triggered.connect(lambda: self.show_simplified_iarab(metadata))
        menu.addAction(simplified_action)
        detailed_action = qt1.QAction("إعراب مفصل", self)
        detailed_action.triggered.connect(lambda: self.show_detailed_iarab(metadata))
        menu.addAction(detailed_action)
        menu.exec(qt1.QCursor.pos())

    def show_simplified_iarab(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        result = functions.iarab.getIarab(ayah_num, ayah_num)
        guiTools.TextViewer(self, "إعراب مبسط", result).exec()
        self.resume_after_action()

    def show_detailed_iarab(self, metadata):
        self.pause_for_action()
        surah_number = metadata["surah_number"]
        ayah_number_in_surah = metadata["ayah_number_in_surah"]
        result = functions.quran_details.get_single_ayah_detailed_irab(surah_number, ayah_number_in_surah)
        guiTools.TextViewer(self, "إعراب مفصل", result).exec()
        self.resume_after_action()

    def show_meanings(self, metadata):
        self.pause_for_action()
        surah_number = metadata["surah_number"]
        ayah_number_in_surah = metadata["ayah_number_in_surah"]
        line_text = metadata.get("clean_ayah_text")
        if not line_text:
            cursor = self.results.textCursor()
            line_text = re.sub(r'^\d+\s*', '', cursor.block().text())
        result = functions.quran_details.get_single_ayah_meanings(surah_number, ayah_number_in_surah, ayah_text=line_text)
        guiTools.TextViewer(self, "معاني كلمات الآية", result).exec()
        self.resume_after_action()

    def show_sarf(self, metadata):
        self.pause_for_action()
        surah_number = metadata["surah_number"]
        ayah_number_in_surah = metadata["ayah_number_in_surah"]
        line_text = metadata.get("clean_ayah_text")
        if not line_text:
            cursor = self.results.textCursor()
            line_text = re.sub(r'^\d+\s*', '', cursor.block().text())
        result = functions.quran_details.get_single_ayah_sarf(surah_number, ayah_number_in_surah, ayah_text=line_text)
        guiTools.TextViewer(self, "صرف كلمات الآية", result).exec()
        self.resume_after_action()

    def show_tanzil(self, metadata):
        self.pause_for_action()
        ayah_num = metadata["overall_ayah_number"]
        result = functions.tanzil.gettanzil(ayah_num)
        if result:
            guiTools.TextViewer(self, "أسباب النزول", result).exec()
        else:
            guiTools.MessageBox.view(self, "تنبيه", "لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()

    def show_ayah_info(self, metadata):
        self.pause_for_action()
        surah_number = metadata["surah_number"]
        ayah_number_in_surah = metadata["ayah_number_in_surah"]
        ayah_data = self.quran_data[str(surah_number)]['ayahs'][ayah_number_in_surah - 1]
        sajda_text = "الآية تحتوي على سجدة" if ayah_data.get("sajda") else ""
        info_text = f"رقم الآية: {ayah_number_in_surah}\n"
        info_text += f"رقم السورة: {surah_number} ({metadata['surah_name']})\n"
        info_text += f"رقم الآية في المصحف: {ayah_data['number']}\n"
        info_text += f"الجزء: {ayah_data['juz']}\n"
        info_text += f"الربع: {ayah_data['hizbQuarter']}\n"
        info_text += f"الصفحة: {ayah_data['page']}\n{sajda_text}"
        guiTools.MessageBox.view(self, "معلومات الآية", info_text)
        self.resume_after_action()

    def go_to_surah(self, metadata):
        self.pause_for_action()
        surah_name_key = f"{metadata['surah_number']}. {metadata['surah_name']}"
        if surah_name_key not in self.surahsList:
            for k in self.surahsList.keys():
                if k.startswith(f"{metadata['surah_number']}."):
                    surah_name_key = k
                    break
        if surah_name_key in self.surahsList:
            surah_text = self.surahsList[surah_name_key][1]
            ayah_index = metadata["ayah_number_in_surah"] - 1
            QuranViewer(self, text=surah_text, type=5, category=surah_name_key, index=ayah_index, enableNextPreviouseButtons=False, enableBookmarks=False).exec()
        else:
            guiTools.MessageBox.error(self, "خطأ", f"لم يتم العثور على بيانات السورة: {surah_name_key}")
        self.resume_after_action()

    def go_to_hadith(self, metadata):
        self.pause_for_action()
        from gui import hadeeth_viewer
        hadeeth_viewer(self, metadata["file_name"], index=metadata["hadith_index"]).exec()
        self.resume_after_action()

    def on_tafseer_shortcut(self):
        self.on_shortcut_activated(self.show_tafseer)

    def on_translation_shortcut(self):
        self.on_shortcut_activated(self.show_translation)

    def on_iarab_shortcut(self):
        self.on_shortcut_activated(self.show_iarab)

    def on_meanings_shortcut(self):
        self.on_shortcut_activated(self.show_meanings)

    def on_sarf_shortcut(self):
        self.on_shortcut_activated(self.show_sarf)

    def on_tanzil_shortcut(self):
        self.on_shortcut_activated(self.show_tanzil)

    def on_goto_surah_shortcut(self):
        cursor = self.results.textCursor()
        line_number = cursor.blockNumber() + 1
        metadata = self.search_metadata.get(line_number)
        if not metadata:
            if self.serch.currentIndex() == 1:
                guiTools.speak("يرجى تحديد حديث أولاً لتطبيق الإجراء")
            else:
                guiTools.speak("يرجى تحديد آية أولاً لتطبيق الإجراء")
            return
        if isinstance(metadata, dict) and metadata.get("type") == "hadith":
            self.go_to_hadith(metadata)
        else:
            self.go_to_surah(metadata)

    def on_ayah_info_shortcut(self):
        self.on_shortcut_activated(self.show_ayah_info)

    def on_save_shortcut(self):
        self.on_shortcut_activated(self.save_ayah)

    def save_ayah(self, metadata):
        if getattr(self, 'is_saving', False): return
        self.pause_for_action()
        with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
            reciters = json.load(file)
        reciter_url = list(reciters.values())[self.currentReciter]
        reciter_folder = reciter_url.split('/')[-3]
        surah_num_str = str(metadata["surah_number"]).zfill(3)
        ayah_num_str = str(metadata["ayah_number_in_surah"]).zfill(3)
        filename = f"{surah_num_str}{ayah_num_str}.mp3"
        local_path = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder, filename)
        is_local = os.path.exists(local_path)
        if not is_local:
            confirm_message = "تنبيه: الآية غير موجودة محلياً وسيتم تحميلها الآن.\n\nهل تريد المتابعة؟"
        else:
            confirm_message = "الآية موجودة محلياً وجاهزة للحفظ.\n\nهل تريد المتابعة؟"
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الحفظ", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآية")
        if not output_dir:
            self.resume_after_action()
            return
        self.save_mode_data = {"filename": filename, "local_path": local_path, "url": reciter_url + filename, "output_dir": output_dir, "is_local": is_local}
        self.set_ui_for_save(True)
        if is_local:
            self.save_feedback_label.setText("جاري حفظ الآية...")
            dest = os.path.join(output_dir, filename)
            try:
                shutil.copy2(local_path, dest)
                self.on_save_finished(True, "تم حفظ الآية بنجاح.")
            except Exception as e:
                self.on_save_finished(False, f"فشل نسخ الآية: {str(e)}")
        else:
            self.save_feedback_label.setText("جاري تحميل الآية المطلوبة...")
            self.cancellation_requested = False
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_')).rstrip()
            self.temp_download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.download_thread = DownloadThread(self.save_mode_data["url"], self.temp_download_path)
            self.download_thread.progress.connect(self.save_progress_bar.setValue)
            self.download_thread.finished.connect(self.on_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_save_finished(False, "تم إلغاء العملية."))
            self.download_thread.network_error.connect(self.on_download_network_error)
            self.resume_download_button.setVisible(False)
            self.download_thread.start()

    def on_download_network_error(self, msg):
        self.resume_download_button.setVisible(True)
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def resume_current_download(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            self.download_thread.resume()
            self.resume_download_button.setVisible(False)

    def on_download_finished(self):
        if self.cancellation_requested:
            self.on_save_finished(False, "تم إلغاء العملية.")
            return
        dest = os.path.join(self.save_mode_data["output_dir"], self.save_mode_data["filename"])
        try:
            if os.path.exists(self.temp_download_path):
                shutil.move(self.temp_download_path, dest)
                self.on_save_finished(True, "تم حفظ الآية بنجاح.")
            else:
                self.on_save_finished(False, "الملف المؤقت غير موجود.")
        except Exception as e:
            self.on_save_finished(False, f"فشل نقل الآية: {str(e)}")

    def cancel_save(self):
        self.cancellation_requested = True
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel()

    def on_save_finished(self, success, message):
        self.set_ui_for_save(False)
        if self.cancellation_requested:
            guiTools.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الحفظ.")
            if hasattr(self, 'temp_download_path') and os.path.exists(self.temp_download_path):
                try: os.remove(self.temp_download_path)
                except: pass
        elif success:
            guiTools.MessageBox.view(self, "نجاح", message)
        else:
            guiTools.MessageBox.error(self, "فشل", message)
            if hasattr(self, 'temp_download_path') and os.path.exists(self.temp_download_path):
                try: os.remove(self.temp_download_path)
                except: pass
        self.cancellation_requested = False
        self.resume_after_action()

    def set_ui_for_save(self, is_active):
        self.is_saving = is_active
        widgets_to_disable = [self.serch, self.ahadeeth, self.surahs, self.specific_scope_combo, self.serch_input, self.search_mode_button, self.start, self.results, self.clear_results_button]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.save_widget.setVisible(is_active)
        if is_active:
            self.save_progress_bar.setValue(0)

    def copy_line(self):
        try:
            cursor = self.results.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
            else:
                cursor.select(qt1.QTextCursor.SelectionType.BlockUnderCursor)
                pyperclip.copy(cursor.selectedText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))

    def copy_text(self):
        try:
            pyperclip.copy(self.results.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def update_font_size(self):
        cursor = self.results.textCursor()
        self.results.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.results.setCurrentFont(font)
        self.results.setTextCursor(cursor)
        self.adjust_all_combos_width()
