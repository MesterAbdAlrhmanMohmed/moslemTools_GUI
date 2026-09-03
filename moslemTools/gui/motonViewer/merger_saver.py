import os
import re
import shutil
import pyperclip
import winsound
import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import custom_errors
import guiTools
from .threads import MergeThread, SaveThread

class MotonMergerSaverMixin:
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
        widgets = [self.text, self.changeCurrentReciterButton, self.toggle_search_button, self.numbering_button]
        if hasattr(self, 'previous'):
            widgets.extend([self.previous, self.changeCategory, self.next])
        for w in widgets:
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

    def getCurrentBaytIndex(self):
        b = self.get_bayt_at_cursor()
        if not b:
            return 0
        for idx, v in enumerate(self.displayed_verses):
            if v.get("global_num") == b.get("global_num"):
                return idx
        return 0

    def on_save_bayt_audio(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        bayt_num = bayt["global_num"]
        if self.current_reciter_type == "N":
            src = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", self.current_reciter_slug, self.matn_slug, f"{bayt_num}.mp3"))
            if not os.path.exists(src):
                winsound.Beep(440, 200)
                guiTools.speak("ملف الصوت غير متوفر محليا")
                return
            default_name = f"{self.matn_name}_بيت_{bayt_num}.mp3"
            dest_file, _ = qt.QFileDialog.getSaveFileName(self, "حفظ صوت البيت", default_name, "Audio Files (*.mp3)")
            if dest_file:
                shutil.copy2(src, dest_file)
                guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم حفظ صوت البيت بنجاح")
        else:
            guiTools.speak("هذا القارئ متوفر كملف صوتي كامل للمتن")

    def saveCategoryBayts(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        self.save_verses_range(0, len(self.displayed_verses))

    def saveFromBaytToEnd(self):
        if self.is_merging:
            return
        b = self.get_bayt_at_cursor()
        if not b:
            self.handle_invalid_line_action()
            return
        start_idx = self.getCurrentBaytIndex()
        self.save_verses_range(start_idx, len(self.displayed_verses))

    def saveFromVersToVers(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt or not self.displayed_verses:
            self.handle_invalid_line_action()
            return
        use_matn_num = (self.verse_numbering_mode == "by_matn")
        if use_matn_num:
            min_val = self.displayed_verses[0]["global_num"]
            max_val = self.displayed_verses[-1]["global_num"]
            current_val = bayt["global_num"]
        else:
            min_val = 1
            max_val = len(self.displayed_verses)
            current_val = bayt.get("chapter_bayt_num", self.getCurrentBaytIndex() + 1) if not self.is_full_matn else (self.getCurrentBaytIndex() + 1)

        self.pause_for_action()
        from_bayt, ok = guiTools.QInputDialog.getInt(self, "حفظ من البيت", "الحفظ من:", current_val, min_val, max_val)
        if ok:
            to_bayt, ok2 = guiTools.QInputDialog.getInt(self, "حفظ إلى البيت", "الحفظ إلى:", max_val, from_bayt, max_val)
            if ok2:
                if use_matn_num:
                    verses_to_save = [v for v in self.displayed_verses if from_bayt <= v.get("global_num", 0) <= to_bayt]
                else:
                    if not self.is_full_matn:
                        verses_to_save = [v for v in self.displayed_verses if from_bayt <= v.get("chapter_bayt_num", 0) <= to_bayt]
                    else:
                        verses_to_save = self.displayed_verses[from_bayt - 1: to_bayt]
                self.save_verses_range(verses_to_save, None)
        self.resume_after_action()

    def save_verses_range(self, start_idx, end_idx):
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

        if isinstance(start_idx, list):
            verses_slice = start_idx
        else:
            verses_slice = self.displayed_verses[start_idx:end_idx]
        file_list = []
        for v in verses_slice:
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
        guiTools.speak("جاري حفظ الأبيات...")

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

    def mergeCategoryBayts(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        self.merge_verses_range(0, len(self.displayed_verses))

    def mergeFromBaytToEnd(self):
        if self.is_merging:
            return
        b = self.get_bayt_at_cursor()
        if not b:
            self.handle_invalid_line_action()
            return
        start_idx = self.getCurrentBaytIndex()
        self.merge_verses_range(start_idx, len(self.displayed_verses))

    def mergeBayts(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt or not self.displayed_verses:
            self.handle_invalid_line_action()
            return
        use_matn_num = (self.verse_numbering_mode == "by_matn")
        if use_matn_num:
            min_val = self.displayed_verses[0]["global_num"]
            max_val = self.displayed_verses[-1]["global_num"]
            current_val = bayt["global_num"]
        else:
            min_val = 1
            max_val = len(self.displayed_verses)
            current_val = bayt.get("chapter_bayt_num", self.getCurrentBaytIndex() + 1) if not self.is_full_matn else (self.getCurrentBaytIndex() + 1)

        self.pause_for_action()
        from_bayt, ok = guiTools.QInputDialog.getInt(self, "دمج من البيت", "الدمج من:", current_val, min_val, max_val)
        if ok:
            to_bayt, ok2 = guiTools.QInputDialog.getInt(self, "دمج إلى البيت", "الدمج إلى:", max_val, from_bayt, max_val)
            if ok2:
                if use_matn_num:
                    verses_to_merge = [v for v in self.displayed_verses if from_bayt <= v.get("global_num", 0) <= to_bayt]
                else:
                    if not self.is_full_matn:
                        verses_to_merge = [v for v in self.displayed_verses if from_bayt <= v.get("chapter_bayt_num", 0) <= to_bayt]
                    else:
                        verses_to_merge = self.displayed_verses[from_bayt - 1: to_bayt]
                self.merge_verses_range(verses_to_merge, None)
        self.resume_after_action()

    def merge_verses_range(self, start_idx, end_idx):
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

        if isinstance(start_idx, list):
            verses_slice = start_idx
        else:
            verses_slice = self.displayed_verses[start_idx:end_idx]
        input_files = []
        for v in verses_slice:
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

        clean_chapter = re.sub(r'\s*\([^)]+\)', '', self.chapter_title).strip()
        default_name = f"{self.matn_name}_{clean_chapter}.mp3" if not self.is_full_matn else f"{self.matn_name}_كامل.mp3"
        dest_file, _ = qt.QFileDialog.getSaveFileName(self, "دمج وحفظ المقطع الصوتي", default_name, "Audio Files (*.mp3)")
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

    def copyFromVersToVers(self):
        if self.is_merging:
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        total = len(self.displayed_verses)
        if total == 0:
            return
        current_idx = self.getCurrentBaytIndex()
        self.pause_for_action()
        use_matn_num = (self.verse_numbering_mode == "by_matn")
        if use_matn_num:
            min_val = self.displayed_verses[0]["global_num"]
            max_val = self.displayed_verses[-1]["global_num"]
            current_val = bayt["global_num"]
        else:
            min_val = 1
            max_val = total
            current_val = bayt.get("chapter_bayt_num", current_idx + 1) if not self.is_full_matn else (current_idx + 1)
        from_bayt, ok = guiTools.QInputDialog.getInt(self, "نسخ من البيت", "النسخ من:", current_val, min_val, max_val)
        if ok:
            to_bayt, ok2 = guiTools.QInputDialog.getInt(self, "نسخ إلى البيت", "النسخ إلى:", max_val, from_bayt, max_val)
            if ok2:
                if use_matn_num:
                    verses_slice = [v for v in self.displayed_verses if from_bayt <= v["global_num"] <= to_bayt]
                else:
                    verses_slice = self.displayed_verses[from_bayt - 1:to_bayt]
                lines_to_copy = []
                doc = self.text.document()
                for v in verses_slice:
                    target_global = v.get("global_num")
                    blocks = [line_num for line_num, info in self.line_to_bayt_map.items() if info.get("type") == "verse" and info.get("verse", {}).get("global_num") == target_global]
                    lines = [doc.findBlockByNumber(b_num).text() for b_num in sorted(blocks) if doc.findBlockByNumber(b_num).isValid()]
                    if lines:
                        bayt_text = "\n".join(lines)
                    else:
                        v_num_str = ""
                        if self.verse_numbering_mode == "by_chapter":
                            b_idx = self.displayed_verses.index(v) if v in self.displayed_verses else 0
                            v_num_str = f"{v.get('chapter_bayt_num', b_idx + 1)}. "
                        elif self.verse_numbering_mode == "by_matn":
                            v_num_str = f"{v.get('global_num', 1)}. "
                        sadr = f"{v_num_str}{v.get('sadr', '')}"
                        ajuz = f"    {v.get('ajuz', '')}" if v.get('ajuz') else ""
                        bayt_text = f"{sadr}\n{ajuz}" if ajuz else sadr
                        if self.remove_tashkeel:
                            bayt_text = self._remove_tashkeel_from_text(bayt_text)
                    lines_to_copy.append(bayt_text)
                if lines_to_copy:
                    full_copy = "\n\n".join(lines_to_copy)
                    pyperclip.copy(full_copy)
                    winsound.Beep(1000, 100)
                    guiTools.speak(f"تم نسخ {len(verses_slice)} أبيات بنجاح")
        self.resume_after_action()

