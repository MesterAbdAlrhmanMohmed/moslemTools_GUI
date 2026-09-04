import os
import re
import winsound
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import PyQt6.QtWidgets as qt
import guiTools
from settings import settings_handler

class MotonPlayerNavigationDisplayMixin:
    def remove_diacritics(self, text):
        return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

    def update_display_text(self):
        if not (0 <= self.current_index < self.total_verses):
            return
        bayt = self.all_verses_list[self.current_index]
        if isinstance(bayt, dict):
            self.current_bayt_num = bayt.get("global_num", self.current_index + 1)
            sadr = bayt.get("sadr", "")
            ajuz = bayt.get("ajuz", "")
        else:
            self.current_bayt_num = self.current_index + 1
            sadr = str(bayt)
            ajuz = ""

        if not self.show_diacritics:
            sadr = self.remove_diacritics(sadr)
            if ajuz:
                ajuz = self.remove_diacritics(ajuz)

        mode = getattr(self, "verse_numbering_mode", None) or settings_handler.get("motonViewer", "verse_numbering_mode") or "by_chapter"
        v_num_str = ""
        if mode == "by_chapter":
            num = (bayt.get("chapter_bayt_num") or bayt.get("raw_num") or (self.current_index + 1)) if isinstance(bayt, dict) else (self.current_index + 1)
            v_num_str = f"{num}. "
        elif mode == "by_matn":
            num = (bayt.get("global_num") or (self.current_index + 1)) if isinstance(bayt, dict) else (self.current_index + 1)
            v_num_str = f"{num}. "
        elif mode == "none":
            v_num_str = ""

        line1 = f"{v_num_str}{sadr}"
        if ajuz:
            display_str = f"{line1}\n{ajuz}"
        else:
            display_str = line1
        self.text.setPlainText(display_str)

    def _set_numbering_mode(self, mode):
        self.verse_numbering_mode = mode
        self.update_display_text()
        guiTools.speak("تم تغيير طريقة عرض الأرقام")

    def onNextBayt(self):
        if getattr(self, "is_closing", False) or self.total_verses == 0:
            return
        self.currentTime = 1
        self.is_user_paused = False
        self.saved_pause_position = 0
        if self.current_index + 1 == self.total_verses:
            self.current_index = 0
        else:
            self.current_index += 1
        self.update_display_text()
        self.media.stop()
        self.on_play()

    def onPreviousBayt(self):
        if getattr(self, "is_closing", False) or self.total_verses == 0:
            return
        self.currentTime = 1
        self.is_user_paused = False
        self.saved_pause_position = 0
        if self.current_index == 0:
            self.current_index = self.total_verses - 1
        else:
            self.current_index -= 1
        self.update_display_text()
        self.media.stop()
        self.on_play()

    def goto_bayt(self, target_num):
        if 1 <= target_num <= self.total_verses:
            self.currentTime = 1
            self.is_user_paused = False
            self.saved_pause_position = 0
            self.current_index = target_num - 1
            self.update_display_text()
            self.media.stop()
            self.on_play()
        else:
            guiTools.speak(f"الرقم غير صالح، يجب أن يكون بين 1 و {self.total_verses}")

    def on_toggle_diacritics(self):
        self.show_diacritics = not self.show_diacritics
        settings_handler.set("motonPlayer", "show_diacritics", str(self.show_diacritics))
        self.update_display_text()
        guiTools.speak("تم إظهار التشكيل" if self.show_diacritics else "تم إزالة التشكيل")

    def font_size_changed(self, size):
        self.font_size = size
        self.update_font_size()
        settings_handler.set("font", "motonPlayer_size", str(size))

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
