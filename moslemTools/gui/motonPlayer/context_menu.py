import pyperclip
import winsound
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import guiTools
from ..motonViewer.threads import GoToBaytDialog

class MotonPlayerContextMenuMixin:
    def oncontextMenu(self, pos):
        if getattr(self, 'is_merging', False):
            return
        self.was_playing = (self.media.playbackState() == self.media.PlaybackState.PlayingState)
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")

        menu = guiTools.QCustomContextMenu("خيارات البيت", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("خيارات البيت")
        menu.setFocus()

        speed_menu = menu.addMenu("سرعة التشغيل")
        speed_menu.setFont(font)
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            s_act = qt1.QAction(f"{s}x", self)
            s_act.setCheckable(True)
            s_act.setChecked(abs(self.playback_speed - s) < 0.01)
            s_act.triggered.connect(lambda checked, sp=s: self.apply_speed(sp))
            speed_menu.addAction(s_act)

        goto_act = qt1.QAction("الذهاب إلى بيت", self)
        goto_act.setShortcut("ctrl+g")
        goto_act.triggered.connect(self.on_goto_bayt_dialog)
        menu.addAction(goto_act)

        copy_act = qt1.QAction("نسخ البيت", self)
        copy_act.setShortcut("ctrl+c")
        copy_act.triggered.connect(self.copy_current_bayt)
        menu.addAction(copy_act)

        save_act = qt1.QAction("حفظ صوت البيت في الجهاز", self)
        save_act.setShortcut("ctrl+h")
        save_act.triggered.connect(self.save_current_bayt_audio)
        menu.addAction(save_act)

        diacritics_act = qt1.QAction("إظهار التشكيل" if not self.show_diacritics else "إزالة التشكيل", self)
        diacritics_act.setShortcut("ctrl+x")
        diacritics_act.triggered.connect(self.on_toggle_diacritics)
        menu.addAction(diacritics_act)

        menu.aboutToHide.connect(self.resume_playback)
        global_pos = self.text.mapToGlobal(pos) if hasattr(self, "text") else self.cursor().pos()
        menu.exec(global_pos)

    def resume_playback(self):
        if hasattr(self, 'was_playing') and self.was_playing:
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
            self.was_playing = False

    def on_goto_bayt_dialog(self):
        dialog = GoToBaytDialog(self, "الذهاب إلى بيت", "أكتب رقم البيت:", self.current_index + 1, 1, self.total_verses)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            bayt_num, should_play = dialog.get_values()
            self.goto_bayt(bayt_num)
            if should_play:
                self.on_play()

    def copy_current_bayt(self):
        if not (0 <= self.current_index < self.total_verses):
            return
        bayt = self.all_verses_list[self.current_index]
        if bayt:
            sadr = bayt.get("sadr", "")
            ajuz = bayt.get("ajuz", "")
            txt = f"{sadr}\n{ajuz}" if ajuz else sadr
            pyperclip.copy(txt)
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ البيت")
