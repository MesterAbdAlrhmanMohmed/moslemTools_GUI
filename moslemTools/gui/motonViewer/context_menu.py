import re
import pyperclip
import winsound
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools
from functions import text_actions
import functions.notesManager as notesManager
import functions.bookMarksManager as bookMarksManager

class MotonContextMenuMixin:
    def eventFilter(self, obj, event):
        if getattr(self, 'is_merging', False):
            return True
        if obj == self.text.viewport() and event.type() == qt2.QEvent.Type.MouseButtonPress and event.button() == qt2.Qt.MouseButton.LeftButton:
            cursor = self.text.cursorForPosition(event.position().toPoint())
            self.text.setTextCursor(cursor)
            bayt = self.get_bayt_at_cursor()
            if not bayt:
                self.handle_invalid_line_action()
                return True
            self.on_play()
            return True
        return super().eventFilter(obj, event)

    def oncontextMenu(self):
        if getattr(self, 'is_merging', False):
            return
        bayt = self.get_bayt_at_cursor()
        if not bayt:
            self.handle_invalid_line_action()
            return

        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_bayt = bayt
        self.saved_text = self.text.toPlainText()
        self.context_menu_active = True
        self.pause_for_action()

        menu = guiTools.QCustomContextMenu("الخيارات ", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات ")
        menu.setFocus()

        baytOptions = guiTools.QCustomContextMenu("خيارات البيت الحالي", self)
        baytOptions.setFont(font)

        speed_menu = baytOptions.addMenu("سرعة التشغيل")
        speed_menu.setFont(font)
        current_speed = self.playback_speed
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            action = speed_menu.addAction(f"{s}x")
            action.setCheckable(True)
            action.setChecked(abs(current_speed - s) < 0.01)
            action.triggered.connect(lambda checked, val=s: self.apply_speed(val))

        if self.is_search_view:
            goToBaytAction = qt1.QAction("الذهاب إلى موضع البيت والخروج من وضع البحث", self)
            goToBaytAction.setShortcut("ctrl+g")
            goToBaytAction.triggered.connect(self.goToBaytAndExitSearch)
            baytOptions.addAction(goToBaytAction)
        else:
            goToBaytAction = qt1.QAction("الذهاب إلى بيت", self)
            goToBaytAction.setShortcut("ctrl+g")
            goToBaytAction.triggered.connect(self.goToBayt)
            baytOptions.addAction(goToBaytAction)

        playCurrentBaytAction = qt1.QAction("تشغيل البيت", self)
        playCurrentBaytAction.triggered.connect(self.on_play)
        baytOptions.addAction(playCurrentBaytAction)

        copy_bayt = qt1.QAction("نسخ البيت", self)
        copy_bayt.triggered.connect(lambda: self.copy_bayt(bayt))
        baytOptions.addAction(copy_bayt)

        if not self.is_search_view:
            saveCurrentBaytAction = qt1.QAction("حفظ صوت البيت في الجهاز", self)
            saveCurrentBaytAction.setShortcut("ctrl+h")
            saveCurrentBaytAction.triggered.connect(self.on_save_bayt_audio)
            baytOptions.addAction(saveCurrentBaytAction)

        target_global = bayt["global_num"]
        blocks = [line_num for line_num, info in self.line_to_bayt_map.items() if info.get("type") == "verse" and info.get("verse", {}).get("global_num") == target_global]
        current_combined = " ".join(self.text.document().findBlockByNumber(b_num).text() for b_num in blocks if self.text.document().findBlockByNumber(b_num).isValid())
        current_has_tashkeel = bool(re.search(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', current_combined))
        if current_has_tashkeel:
            bayt_tashkeel_text = "إزالة التشكيل من البيت"
        else:
            bayt_tashkeel_text = "إظهار التشكيل للبيت"

        removeTashkeelBaytAction = qt1.QAction(bayt_tashkeel_text, self)
        removeTashkeelBaytAction.setShortcut("ctrl+x")
        removeTashkeelBaytAction.triggered.connect(lambda: self.removeTashkeelForBayt(cursor_pos=self.saved_cursor_position))
        baytOptions.addAction(removeTashkeelBaytAction)

        state, name = bookMarksManager.getMotonBookmarkName(self.matn_name, bayt["global_num"])
        if state:
            bm_action = qt1.QAction("حذف العلامة المرجعية للبيت: CTRL+B", self)
            bm_action.setShortcut("ctrl+b")
            bm_action.triggered.connect(self.onAddOrRemoveBookmark)
            baytOptions.addAction(bm_action)
        else:
            bm_action = qt1.QAction("إضافة علامة مرجعية للبيت", self)
            bm_action.setShortcut("ctrl+b")
            bm_action.triggered.connect(self.onAddOrRemoveBookmark)
            baytOptions.addAction(bm_action)

        pos_data = {
            "matn_name": self.matn_name,
            "chapter_title": bayt.get("chapter_title", ""),
            "bayt_number": bayt["global_num"],
            "bayt_text": f"{bayt['sadr']} - {bayt['ajuz']}"
        }
        note_exists = notesManager.getNotesForPosition("moton", pos_data)
        if note_exists:
            view_note_action = qt1.QAction("عرض ملاحظة البيت", self)
            view_note_action.setShortcut("ctrl+o")
            view_note_action.triggered.connect(self.onViewNote)
            baytOptions.addAction(view_note_action)

            edit_note_action = qt1.QAction("تعديل ملاحظة البيت", self)
            edit_note_action.triggered.connect(self.onAddOrRemoveNote)
            baytOptions.addAction(edit_note_action)
        else:
            add_note_action = qt1.QAction("إضافة ملاحظة للبيت", self)
            add_note_action.setShortcut("ctrl+n")
            add_note_action.triggered.connect(self.onAddOrRemoveNote)
            baytOptions.addAction(add_note_action)

        menu.addMenu(baytOptions)

        if self.is_search_view:
            category_menu_title = "خيارات نتائج البحث"
            copy_action_text = "نسخ نتائج البحث"
            save_action_text = "حفظ النتائج كملف نصي"
            print_action_text = "طباعة النتائج"
            play_to_end_text = "التشغيل من البيت المحدد إلى نهاية نتائج البحث"
            merge_all_text = "دمج نتائج البحث في ملف واحد"
            merge_to_end_text = "الدمج من البيت المحدد إلى نهاية نتائج البحث"
            save_all_text = "حفظ نتائج البحث في الجهاز"
            save_to_end_text = "الحفظ من البيت المحدد إلى نهاية نتائج البحث"
        elif self.is_full_matn:
            category_menu_title = "خيارات المتن"
            copy_action_text = "نسخ المتن"
            save_action_text = "حفظ المتن كملف نصي"
            print_action_text = "طباعة المتن"
            play_to_end_text = "التشغيل من البيت المحدد إلى نهاية المتن"
            merge_all_text = "دمج أبيات المتن في ملف واحد"
            merge_to_end_text = "الدمج من البيت المحدد إلى نهاية المتن"
            save_all_text = "حفظ أبيات المتن في الجهاز"
            save_to_end_text = "الحفظ من البيت المحدد إلى نهاية المتن"
        else:
            category_menu_title = "خيارات الباب"
            copy_action_text = "نسخ الباب"
            save_action_text = "حفظ الباب كملف نصي"
            print_action_text = "طباعة الباب"
            play_to_end_text = "التشغيل من البيت المحدد إلى نهاية الباب"
            merge_all_text = "دمج أبيات الباب في ملف واحد"
            merge_to_end_text = "الدمج من البيت المحدد إلى نهاية الباب"
            save_all_text = "حفظ أبيات الباب في الجهاز"
            save_to_end_text = "الحفظ من البيت المحدد إلى نهاية الباب"

        surahOption = guiTools.QCustomContextMenu(category_menu_title, self)
        surahOption.setFont(font)

        copySurahAction = qt1.QAction(copy_action_text, self)
        copySurahAction.setShortcut("ctrl+a")
        surahOption.addAction(copySurahAction)
        copySurahAction.triggered.connect(lambda: text_actions.copy_all_text(self, self.text))

        saveSurahAction = qt1.QAction(save_action_text, self)
        saveSurahAction.setShortcut("ctrl+s")
        surahOption.addAction(saveSurahAction)
        saveSurahAction.triggered.connect(lambda: text_actions.save_text_file(self, self.text, f"{self.matn_name}.txt"))

        printSurah = qt1.QAction(print_action_text, self)
        printSurah.setShortcut("ctrl+p")
        surahOption.addAction(printSurah)
        printSurah.triggered.connect(lambda: text_actions.print_text_content(self, self.text))

        if self.is_search_view:
            playSurahToEnd = qt1.QAction(play_to_end_text, self)
            playSurahToEnd.setShortcut("ctrl+shift+p")
            surahOption.addAction(playSurahToEnd)
            playSurahToEnd.triggered.connect(self.playFromBaytToEnd)
        else:
            play_menu = surahOption.addMenu("التشغيل")
            play_menu.setFont(font)
            playSurahToEnd = qt1.QAction(play_to_end_text, self)
            playSurahToEnd.setShortcut("ctrl+shift+p")
            play_menu.addAction(playSurahToEnd)
            playSurahToEnd.triggered.connect(self.playFromBaytToEnd)

            playFromVersToVersAction = qt1.QAction("التشغيل من بيت إلى بيت", self)
            playFromVersToVersAction.setShortcut("ctrl+alt+p")
            play_menu.addAction(playFromVersToVersAction)
            playFromVersToVersAction.triggered.connect(self.playFromVersToVers)

            merge_menu = surahOption.addMenu("الدمج")
            merge_menu.setFont(font)
            mergeAllAction = qt1.QAction(merge_all_text, self)
            mergeAllAction.setShortcut("ctrl+shift+d")
            merge_menu.addAction(mergeAllAction)
            mergeAllAction.triggered.connect(self.mergeCategoryBayts)

            mergeFromBaytToEndAction = qt1.QAction(merge_to_end_text, self)
            mergeFromBaytToEndAction.setShortcut("shift+alt+d")
            merge_menu.addAction(mergeFromBaytToEndAction)
            mergeFromBaytToEndAction.triggered.connect(self.mergeFromBaytToEnd)

            mergeRangeAction = qt1.QAction("الدمج من بيت إلى بيت", self)
            mergeRangeAction.setShortcut("ctrl+alt+d")
            merge_menu.addAction(mergeRangeAction)
            mergeRangeAction.triggered.connect(self.mergeBayts)

            save_menu = surahOption.addMenu("الحفظ")
            save_menu.setFont(font)
            saveAudioCategoryAction = qt1.QAction(save_all_text, self)
            saveAudioCategoryAction.setShortcut("ctrl+shift+h")
            save_menu.addAction(saveAudioCategoryAction)
            saveAudioCategoryAction.triggered.connect(self.saveCategoryBayts)

            saveAudioFromBaytToEndAction = qt1.QAction(save_to_end_text, self)
            saveAudioFromBaytToEndAction.setShortcut("shift+alt+h")
            save_menu.addAction(saveAudioFromBaytToEndAction)
            saveAudioFromBaytToEndAction.triggered.connect(self.saveFromBaytToEnd)

            saveAudioRangeAction = qt1.QAction("حفظ من بيت إلى بيت في الجهاز", self)
            saveAudioRangeAction.setShortcut("ctrl+alt+h")
            save_menu.addAction(saveAudioRangeAction)
            saveAudioRangeAction.triggered.connect(self.saveFromVersToVers)

            copyFromVersToVersAction = qt1.QAction("نسخ من بيت إلى بيت", self)
            copyFromVersToVersAction.setShortcut("ctrl+alt+c")
            surahOption.addAction(copyFromVersToVersAction)
            copyFromVersToVersAction.triggered.connect(self.copyFromVersToVers)

            if self.is_full_matn:
                tashkeel_text = "إظهار التشكيل للمتن" if self.remove_tashkeel else "إزالة التشكيل من المتن"
            else:
                tashkeel_text = "إظهار التشكيل للباب" if self.remove_tashkeel else "إزالة التشكيل من الباب"
            removeTashkeelCategoryAction = qt1.QAction(tashkeel_text, self)
            removeTashkeelCategoryAction.setShortcut("ctrl+shift+x")
            surahOption.addAction(removeTashkeelCategoryAction)
            removeTashkeelCategoryAction.triggered.connect(self.toggleTashkeelView)

            if not self.is_full_matn:
                goToCategoryAction = qt1.QAction("الذهاب إلى باب", self)
                goToCategoryAction.setShortcut("ctrl+alt+g")
                goToCategoryAction.triggered.connect(self.onChangeCategory)
                surahOption.addAction(goToCategoryAction)

        menu.addMenu(surahOption)
        menu.aboutToHide.connect(lambda: self.__setattr__('context_menu_active', False))
        menu.aboutToHide.connect(self.resume_after_action)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def copy_bayt(self, bayt):
        sadr = bayt.get("sadr", "")
        ajuz = bayt.get("ajuz", "")
        txt = f"{sadr}\n{ajuz}" if ajuz else sadr
        pyperclip.copy(txt)
        winsound.Beep(1000, 100)
        guiTools.speak("تم نسخ البيت")
