import os
import re
import winsound
import ujson as json
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import PyQt6.QtWidgets as qt
import guiTools
import settings
from settings import settings_handler
from .threads import GoToBaytDialog, GoToCategoryDialog

class MotonNavigationDisplayMixin:
    def init_navigation_display(self):
        self.verse_numbering_mode = settings_handler.get("motonViewer", "verse_numbering_mode") or "by_chapter"
        self.remove_tashkeel = settings_handler.get("motonViewer", "remove_tashkeel") == "True"
        self.font_size = int(settings_handler.get("font", "motonViewer_size") or settings_handler.get("font", "size") or 18)
        self.font_is_bold = settings_handler.get("font", "bold") == "True"
        self.saved_text = ""
        self.line_to_bayt_map = {}
        self.displayed_verses = []
        self.was_playing_before_action = False
        self.context_menu_active = False

    def _remove_tashkeel_from_text(self, text):
        return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

    def _toggle_tashkeel(self, checked):
        self.remove_tashkeel = checked
        settings_handler.set("motonViewer", "remove_tashkeel", str(checked))
        self._update_display_text()

    def toggleTashkeelView(self):
        if hasattr(self, 'is_search_view') and self.is_search_view:
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        new_state = not self.remove_tashkeel
        self._toggle_tashkeel(new_state)
        if self.is_full_matn:
            msg = "تم إزالة التشكيل من المتن" if new_state else "تم إظهار التشكيل للمتن"
        else:
            msg = "تم إزالة التشكيل من الباب" if new_state else "تم إظهار التشكيل للباب"
        guiTools.speak(msg)

    def removeTashkeelForBayt(self, cursor_pos=None):
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return
        self.pause_for_action()
        target_global = bayt["global_num"]
        blocks = []
        for line_num, info in self.line_to_bayt_map.items():
            if info.get("type") == "verse" and info.get("verse", {}).get("global_num") == target_global:
                blocks.append((line_num, info.get("line_part", 1)))
        if not blocks:
            self.resume_after_action()
            return

        chap_idx = self.getCurrentBaytIndex()
        v_num_str = ""
        if self.verse_numbering_mode == "by_chapter":
            v_num_str = f"{bayt.get('raw_num', chap_idx + 1)}. "
        elif self.verse_numbering_mode == "by_matn":
            v_num_str = f"{bayt['global_num']}. "

        orig_part1 = f"{v_num_str}{bayt['sadr']}"
        orig_part2 = bayt['ajuz'] if bayt.get('ajuz') else ""
        orig_combined = orig_part1 + " " + orig_part2
        orig_has_tashkeel = bool(re.search(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', orig_combined))

        doc = self.text.document()
        current_combined = " ".join(doc.findBlockByNumber(line_num).text() for line_num, _ in blocks if doc.findBlockByNumber(line_num).isValid())
        current_has_tashkeel = bool(re.search(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', current_combined))

        if not hasattr(self, 'tashkeel_removed_bayts'):
            self.tashkeel_removed_bayts = set()

        if orig_has_tashkeel:
            if current_has_tashkeel:
                part1_text = self._remove_tashkeel_from_text(orig_part1)
                part2_text = self._remove_tashkeel_from_text(orig_part2)
                speak_msg = "تم إزالة التشكيل من البيت"
                self.tashkeel_removed_bayts.add(target_global)
            else:
                part1_text = orig_part1
                part2_text = orig_part2
                speak_msg = "تم إظهار التشكيل للبيت"
                self.tashkeel_removed_bayts.discard(target_global)
        else:
            if target_global in self.tashkeel_removed_bayts:
                part1_text = orig_part1
                part2_text = orig_part2
                speak_msg = "تم إظهار التشكيل للبيت"
                self.tashkeel_removed_bayts.discard(target_global)
            else:
                part1_text = self._remove_tashkeel_from_text(orig_part1)
                part2_text = self._remove_tashkeel_from_text(orig_part2)
                speak_msg = "تم إزالة التشكيل من البيت"
                self.tashkeel_removed_bayts.add(target_global)

        cursor = self.text.textCursor()
        saved_pos = cursor_pos if cursor_pos is not None else cursor.position()

        for line_num, part in blocks:
            block = doc.findBlockByNumber(line_num)
            if block.isValid():
                new_text = part1_text if part == 1 else part2_text
                c = qt1.QTextCursor(block)
                c.movePosition(qt1.QTextCursor.MoveOperation.StartOfBlock)
                c.movePosition(qt1.QTextCursor.MoveOperation.EndOfBlock, qt1.QTextCursor.MoveMode.KeepAnchor)
                font = qt1.QFont()
                font.setPointSize(self.font_size)
                font.setBold(self.font_is_bold)
                fmt = qt1.QTextCharFormat()
                fmt.setFont(font)
                c.insertText(new_text, fmt)

        restore_cursor = self.text.textCursor()
        restore_cursor.setPosition(min(saved_pos, doc.characterCount() - 1))
        self.text.setTextCursor(restore_cursor)
        guiTools.speak(speak_msg)
        self.resume_after_action()

    def _show_numbering_options(self):
        if hasattr(self, 'is_search_view') and self.is_search_view:
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_bayt = self.get_bayt_at_cursor()
        self.pause_for_action()
        menu = guiTools.QCustomContextMenu(self)
        font = menu.font()
        font.setBold(True)
        menu.setFont(font)
        action_group = qt1.QActionGroup(self)
        action_group.setExclusive(True)

        by_chap_action = qt1.QAction("إظهار الأرقام بحسب الباب", self, checkable=True)
        by_chap_action.setChecked(self.verse_numbering_mode == "by_chapter")
        by_chap_action.triggered.connect(lambda: self._set_numbering_mode("by_chapter"))

        by_matn_action = qt1.QAction("إظهار الأرقام بحسب المتن كاملا", self, checkable=True)
        by_matn_action.setChecked(self.verse_numbering_mode == "by_matn")
        by_matn_action.triggered.connect(lambda: self._set_numbering_mode("by_matn"))

        none_action = qt1.QAction("إخفاء أرقام الأبيات", self, checkable=True)
        none_action.setChecked(self.verse_numbering_mode == "none")
        none_action.triggered.connect(lambda: self._set_numbering_mode("none"))

        action_group.addAction(by_chap_action)
        action_group.addAction(by_matn_action)
        action_group.addAction(none_action)

        menu.addAction(by_chap_action)
        menu.addAction(by_matn_action)
        menu.addAction(none_action)
        menu.addSeparator()

        self.remove_tashkeel_action = qt1.QAction("إزالة التشكيل", self, checkable=True)
        self.remove_tashkeel_action.setChecked(self.remove_tashkeel)
        self.remove_tashkeel_action.triggered.connect(self._toggle_tashkeel)
        menu.addAction(self.remove_tashkeel_action)

        menu.aboutToHide.connect(self.resume_after_action)
        menu.exec(qt1.QCursor.pos())

    def _set_numbering_mode(self, mode):
        if self.verse_numbering_mode == mode:
            return
        self.verse_numbering_mode = mode
        self._update_display_text()

    def _update_display_text(self):
        self.prepare_formatted_text()
        display_text = self.formatted_text
        if self.remove_tashkeel:
            display_text = self._remove_tashkeel_from_text(display_text)
        self._set_text_with_delay(display_text)

    def prepare_formatted_text(self):
        self.line_to_bayt_map.clear()
        self.displayed_verses = []
        lines_out = []

        if self.is_full_matn:
            for s_idx, sec in enumerate(self.parsed_sections):
                chap_counter = 0
                for v in sec["verses"]:
                    chap_counter += 1
                    self.displayed_verses.append(v)
                    v_num_str = ""
                    if self.verse_numbering_mode == "by_chapter":
                        v_num_str = f"{v.get('chapter_bayt_num', chap_counter)}. "
                    elif self.verse_numbering_mode == "by_matn":
                        v_num_str = f"{v['global_num']}. "
                    line1 = f"{v_num_str}{v['sadr']}"
                    line2 = v['ajuz'] if v['ajuz'] else ""
                    self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 1}
                    lines_out.append(line1)
                    if line2:
                        self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 2}
                        lines_out.append(line2)
                    self.line_to_bayt_map[len(lines_out)] = {"type": "empty"}
                    lines_out.append("")
        else:
            sec = self.parsed_sections[self.chapter_index] if 0 <= self.chapter_index < len(self.parsed_sections) else {"title": "", "verses": []}
            chap_counter = 0
            for v in sec["verses"]:
                chap_counter += 1
                self.displayed_verses.append(v)
                v_num_str = ""
                if self.verse_numbering_mode == "by_chapter":
                    v_num_str = f"{v.get('chapter_bayt_num', chap_counter)}. "
                elif self.verse_numbering_mode == "by_matn":
                    v_num_str = f"{v['global_num']}. "
                line1 = f"{v_num_str}{v['sadr']}"
                line2 = v['ajuz'] if v['ajuz'] else ""
                self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 1}
                lines_out.append(line1)
                if line2:
                    self.line_to_bayt_map[len(lines_out)] = {"type": "verse", "verse": v, "line_part": 2}
                    lines_out.append(line2)
                self.line_to_bayt_map[len(lines_out)] = {"type": "empty"}
                lines_out.append("")

        if lines_out and lines_out[-1] == "":
            lines_out.pop()
        self.formatted_text = "\n".join(lines_out)

    def _set_text_with_delay(self, full_text):
        self.saved_text = full_text
        self.text.setText(full_text)
        self.update_font_size()

    def _display_full_content(self):
        pass

    def pause_for_action(self):
        if self.media.playbackState() == self.media.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False

    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()
            self.was_playing_before_action = False

    def get_bayt_at_cursor(self):
        cursor = self.text.textCursor()
        block_num = cursor.blockNumber()
        info = self.line_to_bayt_map.get(block_num)
        if info and info.get("type") == "verse":
            return info.get("verse")
        return None

    def handle_invalid_line_action(self):
        winsound.Beep(440, 200)
        guiTools.speak("يرجى التحديد على بيت أولا")

    def highlight_playing_bayt(self, global_bayt_num):
        for line_num, info in self.line_to_bayt_map.items():
            if info.get("type") == "verse" and info.get("verse", {}).get("global_num") == global_bayt_num:
                cursor = self.text.textCursor()
                doc = self.text.document()
                block = doc.findBlockByNumber(line_num)
                if block.isValid():
                    cursor.setPosition(block.position())
                    self.text.setTextCursor(cursor)
                    self.text.ensureCursorVisible()
                break

    def _go_to_specific_bayt(self, target_global_or_idx):
        target_v = None
        for v in self.displayed_verses:
            if v.get("global_num") == target_global_or_idx:
                target_v = v
                break
        if not target_v and 1 <= target_global_or_idx <= len(self.displayed_verses):
            target_v = self.displayed_verses[target_global_or_idx - 1]

        if target_v:
            target_global = target_v.get("global_num")
            for line_num, info in self.line_to_bayt_map.items():
                if info.get("type") == "verse" and info.get("verse", {}).get("global_num") == target_global:
                    cursor = self.text.textCursor()
                    doc = self.text.document()
                    block = doc.findBlockByNumber(line_num)
                    if block.isValid():
                        cursor.setPosition(block.position())
                        self.text.setTextCursor(cursor)
                        self.text.ensureCursorVisible()
                        self.text.setFocus()
                        display_num = target_v.get("chapter_bayt_num") if (self.verse_numbering_mode == "by_chapter" and not self.is_full_matn) else target_global
                        guiTools.speak(f"البيت رقم {display_num}")
                    return
        winsound.Beep(440, 200)

    def goToBayt(self):
        if hasattr(self, 'is_search_view') and self.is_search_view:
            self.goToBaytAndExitSearch()
            return
        b = self.get_bayt_at_cursor()
        if not b or not self.displayed_verses:
            self.handle_invalid_line_action()
            return
        use_matn_num = (self.verse_numbering_mode == "by_matn")
        if use_matn_num:
            min_val = self.displayed_verses[0]["global_num"]
            max_val = self.displayed_verses[-1]["global_num"]
            current_val = b["global_num"]
        else:
            min_val = 1
            max_val = len(self.displayed_verses)
            current_val = b.get("chapter_bayt_num", self.getCurrentBaytIndex() + 1) if not self.is_full_matn else (self.getCurrentBaytIndex() + 1)

        self.pause_for_action()
        dialog = GoToBaytDialog(self, "الذهاب إلى بيت", "أكتب رقم البيت:", current_val, min_val, max_val)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            bayt_num, should_play = dialog.get_values()
            target_v = None
            if use_matn_num:
                for v in self.displayed_verses:
                    if v.get("global_num") == bayt_num:
                        target_v = v
                        break
            else:
                if not self.is_full_matn:
                    for v in self.displayed_verses:
                        if v.get("chapter_bayt_num") == bayt_num:
                            target_v = v
                            break
                if not target_v and 1 <= bayt_num <= len(self.displayed_verses):
                    target_v = self.displayed_verses[bayt_num - 1]

            if target_v:
                self._go_to_specific_bayt(target_v["global_num"])
                if should_play:
                    self.media.stop()
                    self.play_bayt(target_v["global_num"])
            else:
                self.resume_after_action()
        else:
            self.resume_after_action()

    def play_next_sound(self):
        next_wav = os.path.join("data", "sounds", "next_page.wav")
        if os.path.exists(next_wav):
            winsound.PlaySound(next_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(1200, 50)

    def play_previous_sound(self):
        prev_wav = os.path.join("data", "sounds", "previous_page.wav")
        if os.path.exists(prev_wav):
            winsound.PlaySound(prev_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(1000, 50)

    def onNext(self):
        if getattr(self, 'is_search_view', False):
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        if self.is_full_matn:
            guiTools.speak("أنت في وضع عرض المتن كاملا")
            return
        if not self.parsed_sections:
            return
        if self.chapter_index < len(self.parsed_sections) - 1:
            self.chapter_index += 1
        else:
            self.chapter_index = 0
        self.chapter_title = self.parsed_sections[self.chapter_index]["title"]
        self.info.setText(self.format_title_text())
        self.play_next_sound()
        self._update_display_text()
        guiTools.speak(self.chapter_title)

    def onPreviouse(self):
        if getattr(self, 'is_search_view', False):
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        if self.is_full_matn:
            guiTools.speak("أنت في وضع عرض المتن كاملا")
            return
        if not self.parsed_sections:
            return
        if self.chapter_index > 0:
            self.chapter_index -= 1
        else:
            self.chapter_index = len(self.parsed_sections) - 1
        self.chapter_title = self.parsed_sections[self.chapter_index]["title"]
        self.info.setText(self.format_title_text())
        self.play_previous_sound()
        self._update_display_text()
        guiTools.speak(self.chapter_title)

    def onChangeCategory(self):
        if getattr(self, 'is_search_view', False):
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        if self.is_full_matn:
            guiTools.speak("أنت في وضع عرض المتن كاملا")
            return
        self.pause_for_action()
        chapters = [s["title"] for s in self.parsed_sections if s["title"]]
        if not chapters:
            self.resume_after_action()
            return
        chapter, OK = GoToCategoryDialog.getItem(self, "الذهاب إلى باب", "اختر باب", chapters, self.chapter_index)
        if OK and chapter in chapters:
            self.select_chapter(chapters.index(chapter))
        self.resume_after_action()

    def select_chapter(self, index):
        self.chapter_index = index
        self.chapter_title = self.parsed_sections[self.chapter_index]["title"]
        self.info.setText(self.format_title_text())
        self.play_next_sound()
        self._update_display_text()
        guiTools.speak(self.chapter_title)

    def font_size_changed(self, size):
        self.font_size = size
        self.update_font_size()
        settings_handler.set("font", "motonViewer_size", str(size))

    def update_font_size(self):
        font = self.text.font()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setFont(font)
        if hasattr(self, 'show_font'):
            self.show_font.blockSignals(True)
            self.show_font.setValue(self.font_size)
            self.show_font.blockSignals(False)

    def increase_font_size(self):
        if self.font_size < 100:
            self.font_size += 2
            self.font_size_changed(self.font_size)
            guiTools.speak(f"حجم الخط {self.font_size}")

    def decrease_font_size(self):
        if self.font_size > 8:
            self.font_size -= 2
            self.font_size_changed(self.font_size)
            guiTools.speak(f"حجم الخط {self.font_size}")
