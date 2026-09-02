import re
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import PyQt6.QtWidgets as qt
import guiTools
from settings import settings_handler
from .threads import SearchModeDialog

class MotonSearchHandlerMixin:
    def init_search_handler(self):
        self.is_search_view = False
        self.ignore_tashkeel = settings_handler.get("moton_search", "ignore_tashkeel") != "False"
        self.ignore_hamza = settings_handler.get("moton_search", "ignore_hamza") != "False"
        self.ignore_symbols = settings_handler.get("moton_search", "ignore_symbols") != "False"
        self.search_results_verses = []

    def show_search_mode_dialog(self):
        self.pause_for_action()
        dialog = SearchModeDialog(self, self.ignore_tashkeel, self.ignore_hamza, self.ignore_symbols)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            settings_values = dialog.get_settings()
            self.ignore_tashkeel = settings_values["ignore_tashkeel"]
            self.ignore_hamza = settings_values["ignore_hamza"]
            self.ignore_symbols = settings_values["ignore_symbols"]
            guiTools.speak("تم تطبيق إعدادات البحث بنجاح")
        else:
            guiTools.speak("تم إلغاء التغييرات")
        self.resume_after_action()

    def get_search_button_text(self):
        return "البحث في المتن" if self.is_full_matn else "البحث في الباب"

    def toggle_search_bar(self):
        if self.search_widget.isVisible():
            self.search_widget.hide()
            self.toggle_search_button.setText(self.get_search_button_text())
            guiTools.speak("تم إخفاء شريط البحث")
            self.text.setFocus()
        else:
            self.search_widget.show()
            self.toggle_search_button.setText("إخفاء شريط البحث")
            self.search_input.setFocus()
            self.search_input.selectAll()

    def normalize_arabic(self, text):
        if not text:
            return ""
        def remove_tashkeel(t):
            t = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', t)
            t = re.sub(r'\u0640', '', t)
            return t
        def normalize_hamza(t):
            t = re.sub(r'[أإآٱ]', 'ا', t)
            t = re.sub(r'[\u0624\u0626]', 'ي', t)
            t = re.sub(r'ى', 'ي', t)
            t = re.sub(r'ة', 'ه', t)
            return t
        def normalize_symbols(t):
            t = re.sub(r'[^\w\s\u0600-\u06FF]', '', t)
            t = re.sub(r'[.,!?;:\"\'«»\(\)\[\]\{\}\-_/\\\*]', '', t)
            return t
        res = text
        if self.ignore_tashkeel:
            res = remove_tashkeel(res)
        if self.ignore_hamza:
            res = normalize_hamza(res)
        if self.ignore_symbols:
            res = normalize_symbols(res)
        res = re.sub(r'\s+', ' ', res).strip()
        return res

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يرجى كتابة محتوى للبحث")
            return
        normalized_query = self.normalize_arabic(query)
        self.search_results_verses = []

        sources = self.parsed_sections if self.is_full_matn else [self.parsed_sections[self.chapter_index] if 0 <= self.chapter_index < len(self.parsed_sections) else {"title": "", "verses": []}]
        for sec in sources:
            for v in sec.get("verses", []):
                sadr = v.get("sadr", "")
                ajuz = v.get("ajuz", "")
                combined = f"{sadr} {ajuz}"
                sadr_norm = self.normalize_arabic(sadr)
                ajuz_norm = self.normalize_arabic(ajuz)
                combined_norm = self.normalize_arabic(combined)
                if normalized_query in sadr_norm or normalized_query in ajuz_norm or normalized_query in combined_norm:
                    self.search_results_verses.append(v)

        count = len(self.search_results_verses)
        if count == 0:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لم يتم العثور على نتائج")
            return

        self.is_search_view = True
        self.clear_results_button.show()
        self.line_to_bayt_map.clear()
        self.displayed_verses = list(self.search_results_verses)
        lines_out = []

        header = f"عدد نتائج البحث ({count}):"
        self.line_to_bayt_map[len(lines_out)] = {"type": "header"}
        lines_out.append(header)
        self.line_to_bayt_map[len(lines_out)] = {"type": "empty"}
        lines_out.append("")

        for v in self.search_results_verses:
            line1 = f"{v['global_num']}. {v['sadr']}"
            line2 = f"    {v['ajuz']}" if v.get('ajuz') else ""
            self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 1}
            lines_out.append(line1)
            if line2:
                self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 2}
                lines_out.append(line2)
            self.line_to_bayt_map[len(lines_out)] = {"type": "empty"}
            lines_out.append("")

        if lines_out and lines_out[-1] == "":
            lines_out.pop()

        search_text = "\n".join(lines_out)
        self._set_text_with_delay(search_text)
        guiTools.speak(f"عدد نتائج البحث {count}")

    def clear_search_results(self):
        self.is_search_view = False
        self.clear_results_button.hide()
        self.search_input.clear()
        self._update_display_text()
        guiTools.speak("تمت العودة إلى العرض الأصلي")
        self.text.setFocus()

    def goToBaytAndExitSearch(self):
        if not self.is_search_view:
            return
        b = self.get_bayt_at_cursor()
        if not b:
            self.handle_invalid_line_action()
            return
        target_num = b["global_num"]
        self.clear_search_results()
        qt2.QTimer.singleShot(100, lambda: self._go_to_specific_bayt(target_num))
