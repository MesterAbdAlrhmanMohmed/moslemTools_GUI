from guiTools import note_dialog
import functions.notesManager as notesManager
from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
from ..quranPlayer import QuranPlayer
import time, winsound, pyperclip, os, re, requests, subprocess, shutil, traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QTimer
import guiTools, settings, functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, SajdaGoToDialog, AsbabAlnozoleGoToDialog, SajdaFinderThread, AsbabAlnozoleFinderThread, SearchModeDialog, GoToCategoryDialog

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class ContextMenuMixin:
    def eventFilter(self, obj, event):
        if obj == self.text.viewport() and event.type() == qt2.QEvent.Type.MouseButtonPress and event.button() == qt2.Qt.MouseButton.LeftButton:
            cursor = self.text.cursorForPosition(event.position().toPoint())
            self.text.setTextCursor(cursor)
            self.on_play()
            return True
        return super().eventFilter(obj, event)

    def oncontextMenu(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_ayah_index = self.getCurrentAyah()
        self.saved_text = self.text.toPlainText()
        temp_cursor = self.text.textCursor()
        current_line_text = temp_cursor.block().text()
        no_tashkeel_text = self._remove_tashkeel_from_text(current_line_text)
        if current_line_text == no_tashkeel_text:
            ayah_tashkeel_text = "إظهار التشكيل للآية"
        else:
            ayah_tashkeel_text = "إزالة التشكيل من الآية"
        self.context_menu_active = True
        self.pause_for_action()
        menu = qt.QMenu("الخيارات ", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("الخيارات ")
        menu.setFocus()
        ayahOptions = qt.QMenu("خيارات الآية الحالية", self)
        ayahOptions.setFont(font)
        speed_menu = ayahOptions.addMenu("سرعة التشغيل")
        speed_menu.setFont(font)
        current_speed = self.load_speed()
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            action = speed_menu.addAction(f"{s}x")
            action.setCheckable(True)
            action.setChecked(abs(current_speed - s) < 0.01)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
        if self.is_search_view:
            goToAyahAction = qt1.QAction("الذهاب إلى موضع الآية والخروج من وضع البحث", self)
            goToAyahAction.setShortcut("ctrl+g")
            ayahOptions.addAction(goToAyahAction)
            goToAyahAction.triggered.connect(self.goToAyahAndExitSearch)
        else:
            goToAyah = qt1.QAction("الذهاب إلى آية", self)
            goToAyah.setShortcut("ctrl+g")
            ayahOptions.addAction(goToAyah)
            goToAyah.triggered.connect(self.goToAyah)
        playCurrentAyahAction = qt1.QAction("تشغيل الآية", self)
        playCurrentAyahAction.setShortcut("space")
        ayahOptions.addAction(playCurrentAyahAction)
        playCurrentAyahAction.triggered.connect(self.on_play)
        tafaserCurrentAyahAction = qt1.QAction("تفسير الآية", self)
        tafaserCurrentAyahAction.setShortcut("ctrl+t")
        ayahOptions.addAction(tafaserCurrentAyahAction)
        tafaserCurrentAyahAction.triggered.connect(self.getCurentAyahTafseer)
        iarabCurrentMenu = ayahOptions.addMenu("إعراب الآية: Ctrl+I")
        iarabCurrentMenu.setFont(font)
        simplifiedCurrentAction = qt1.QAction("إعراب مبسط", self)
        simplifiedCurrentAction.triggered.connect(self.getCurentAyahSimplifiedIArab)
        iarabCurrentMenu.addAction(simplifiedCurrentAction)
        detailedCurrentAction = qt1.QAction("إعراب مفصل", self)
        detailedCurrentAction.triggered.connect(self.getCurentAyahDetailedIArab)
        iarabCurrentMenu.addAction(detailedCurrentAction)
        meaningsCurrentAction = qt1.QAction("معاني كلمات الآية", self)
        meaningsCurrentAction.setShortcut("ctrl+u")
        ayahOptions.addAction(meaningsCurrentAction)
        meaningsCurrentAction.triggered.connect(self.getCurentAyahMeanings)
        sarfCurrentAction = qt1.QAction("صرف كلمات الآية", self)
        sarfCurrentAction.setShortcut("ctrl+k")
        ayahOptions.addAction(sarfCurrentAction)
        sarfCurrentAction.triggered.connect(self.getCurentAyahSarf)
        tanzelCurrentAyahAction = qt1.QAction("أسباب نزول الآية", self)
        tanzelCurrentAyahAction.setShortcut("ctrl+r")
        ayahOptions.addAction(tanzelCurrentAyahAction)
        tanzelCurrentAyahAction.triggered.connect(self.getCurrentAyahTanzel)
        translationCurrentAyahAction = qt1.QAction("ترجمة الآية", self)
        translationCurrentAyahAction.setShortcut("ctrl+l")
        ayahOptions.addAction(translationCurrentAyahAction)
        translationCurrentAyahAction.triggered.connect(self.getCurentAyahTranslation)
        ayahInfo = qt1.QAction("معلومات الآية", self)
        ayahInfo.setShortcut("ctrl+f")
        ayahOptions.addAction(ayahInfo)
        ayahInfo.triggered.connect(self.getAyahInfo)
        copy_aya = qt1.QAction("نسخ الآية", self)
        ayahOptions.addAction(copy_aya)
        copy_aya.triggered.connect(self.copyAya)
        if not self.is_search_view:
            saveCurrentAyahAction = qt1.QAction("حفظ الآية في الجهاز", self)
            saveCurrentAyahAction.setShortcut("ctrl+h")
            ayahOptions.addAction(saveCurrentAyahAction)
            saveCurrentAyahAction.triggered.connect(self.saveCurrentAyah)
        removeTashkeelAyahAction = qt1.QAction(ayah_tashkeel_text, self)
        removeTashkeelAyahAction.setShortcut("ctrl+x")
        ayahOptions.addAction(removeTashkeelAyahAction)
        removeTashkeelAyahAction.triggered.connect(lambda: self.removeTashkeelForAyah(cursor_pos=self.saved_cursor_position))
        if self.enableBookmarks:
            state, self.nameOfBookmark = functions.bookMarksManager.getQuranBookmarkName(self.type, self.category, self.saved_ayah_index, isPlayer=False)
            if state:
                removeBookmarkAction = qt.QWidgetAction(self)
                delete_button = qt.QPushButton("حذف العلامة المرجعية للآية: CTRL+B")
                delete_button.setDefault(True)
                delete_button.setShortcut("ctrl+b")
                delete_button.setStyleSheet("background-color: #8B0000; color: white;")
                delete_button.clicked.connect(self.onRemoveBookmark)
                removeBookmarkAction.setDefaultWidget(delete_button)
                ayahOptions.addAction(removeBookmarkAction)
            else:
                addNewBookMark = qt1.QAction("إضافة علامة مرجعية للآية", self)
                addNewBookMark.setShortcut("ctrl+b")
                ayahOptions.addAction(addNewBookMark)
                addNewBookMark.triggered.connect(self.onAddBookMark)
            ayah_position = {"ayah_text": self.original_quran_text.split("\n")[self.saved_ayah_index], "ayah_number": self.saved_ayah_index, "surah": self.category}
            note_exists = notesManager.getNotesForPosition("quran", ayah_position)
            if note_exists:
                note_action = qt1.QAction("عرض ملاحظة الآية", self)
                note_action.setShortcut("ctrl+o")
                note_action.triggered.connect(lambda: self.onNoteAction(ayah_position))
                ayahOptions.addAction(note_action)
                delete_note_action = qt.QWidgetAction(self)
                delete_button = qt.QPushButton("حذف ملاحظة الآية: CTRL+SHIFT+N")
                delete_button.setDefault(True)
                delete_button.setShortcut("ctrl+shift+n")
                delete_button.setStyleSheet("background-color: #8B0000; color: white;")
                delete_button.clicked.connect(lambda: self.onDeleteNote(ayah_position))
                delete_note_action.setDefaultWidget(delete_button)
                ayahOptions.addAction(delete_note_action)
            else:
                note_action = qt1.QAction("إضافة ملاحظة للآية", self)
                note_action.setShortcut("ctrl+n")
                note_action.triggered.connect(lambda: self.onAddNote(ayah_position))
                ayahOptions.addAction(note_action)
        menu.addMenu(ayahOptions)
        category_menu_title = ""
        cat_target_label = ""
        go_to_action_text = ""
        copy_action_text = ""
        save_action_text = ""
        print_action_text = ""
        info_action_text = ""
        play_to_end_text = ""
        tafseer_action_text = ""
        iarab_action_text = ""
        translation_action_text = ""
        tashkeel_action_text = ""
        save_audio_category_text = ""
        merge_audio_category_text = ""
        save_audio_to_end_text = ""
        merge_audio_to_end_text = ""
        tafseer_to_end_text = ""
        translation_to_end_text = ""
        iarab_to_end_text = ""
        if self.is_search_view:
            category_menu_title = "خيارات نتائج البحث"
            cat_target_label = "نتائج البحث"
            copy_action_text = "نسخ نتائج البحث"
            save_action_text = "حفظ النتائج كملف نصي"
            print_action_text = "طباعة النتائج"
            play_to_end_text = "التشغيل من الآية المحددة إلى نهاية نتائج البحث"
        elif self.type == 5:
            category_menu_title = "خيارات العرض المخصص"
            cat_target_label = "العرض المخصص"
            copy_action_text = "نسخ الآيات"
            save_action_text = "حفظ الآيات كملف نصي"
            print_action_text = "طباعة الآيات"
            play_to_end_text = "التشغيل من الآية المحددة إلى نهاية العرض المخصص"
            save_audio_category_text = "حفظ جميع الآيات في الجهاز"
            merge_audio_category_text = "دمج جميع الآيات في ملف واحد"
            save_audio_to_end_text = "الحفظ من الآية المحددة إلى نهاية العرض المخصص"
            merge_audio_to_end_text = "الدمج من الآية المحددة إلى نهاية العرض المخصص"
            tafseer_to_end_text = "التفسير من الآية المحددة إلى نهاية العرض المخصص"
            translation_to_end_text = "الترجمة من الآية المحددة إلى نهاية العرض المخصص"
            iarab_to_end_text = "الإعراب من الآية المحددة إلى نهاية العرض المخصص"
        else:
            cat_map_al = {0: "السورة", 1: "الصفحة", 2: "الجزء", 3: "الربع", 4: "الحزب"}
            cat_map_no_al = {0: "سورة", 1: "صفحة", 2: "جزء", 3: "ربع", 4: "حزب"}
            category_name_al = cat_map_al.get(self.type, "الفئة")
            category_name_no_al = cat_map_no_al.get(self.type, "فئة")
            if self.type == 0:
                surah_name_clean = re.sub(r'^\d+[\s\.\-]*', '', str(self.category))
                cat_target_label = f"سورة {surah_name_clean}"
                info_action_text = f"معلومات سورة: {surah_name_clean}"
                category_menu_title = f"خيارات سورة {surah_name_clean}"
                tafseer_action_text = f"تفسير سورة {surah_name_clean}"
                iarab_action_text = f"إعراب سورة {surah_name_clean}"
                translation_action_text = f"ترجمة سورة {surah_name_clean}"
            else:
                cat_name_dyn = "صفحة" if self.type == 1 else category_name_al
                cat_target_label = f"{cat_name_dyn} {self.category}"
                info_action_text = f"معلومات {category_name_al}: {self.category}"
                category_menu_title = f"خيارات {category_name_al}"
                tafseer_action_text = f"تفسير {category_name_al}"
                iarab_action_text = f"إعراب {category_name_al}"
                translation_action_text = f"ترجمة {category_name_al}"
            go_to_action_text = f"الذهاب إلى {category_name_no_al}"
            copy_action_text = f"نسخ {category_name_al}"
            save_action_text = f"حفظ {category_name_al} كملف نصي"
            print_action_text = f"طباعة {category_name_al}"
            play_to_end_text = f"التشغيل من الآية المحددة إلى نهاية {cat_target_label}"
            tafseer_to_end_text = f"التفسير من الآية المحددة إلى نهاية {cat_target_label}"
            translation_to_end_text = f"الترجمة من الآية المحددة إلى نهاية {cat_target_label}"
            iarab_to_end_text = f"الإعراب من الآية المحددة إلى نهاية {cat_target_label}"
            save_audio_category_text = f"حفظ آيات {cat_target_label} في الجهاز"
            merge_audio_category_text = f"دمج آيات {cat_target_label} في ملف واحد"
            save_audio_to_end_text = f"الحفظ من الآية المحددة إلى نهاية {cat_target_label}"
            merge_audio_to_end_text = f"الدمج من الآية المحددة إلى نهاية {cat_target_label}"
            if self.remove_tashkeel:
                tashkeel_action_text = f"إظهار التشكيل ل{category_name_al}"
            else:
                tashkeel_action_text = f"إزالة التشكيل من {category_name_al}"
        surahOption = qt.QMenu(category_menu_title, self)
        surahOption.setFont(font)
        copySurahAction = qt1.QAction(copy_action_text, self)
        copySurahAction.setShortcut("ctrl+a")
        surahOption.addAction(copySurahAction)
        copySurahAction.triggered.connect(self.copy_text)
        saveSurahAction = qt1.QAction(save_action_text, self)
        saveSurahAction.setShortcut("ctrl+s")
        surahOption.addAction(saveSurahAction)
        saveSurahAction.triggered.connect(self.save_text_as_txt)
        printSurah = qt1.QAction(print_action_text, self)
        printSurah.setShortcut("ctrl+p")
        surahOption.addAction(printSurah)
        printSurah.triggered.connect(self.print_text)
        if info_action_text:
            categoryInfoAction = qt1.QAction(info_action_text, self)
            categoryInfoAction.setShortcut("ctrl+shift+f")
            surahOption.addAction(categoryInfoAction)
            categoryInfoAction.triggered.connect(self.onSurahInfo)
        try:
            current_line = self._get_line_text_for_action(self.saved_ayah_index)
            _, _, juz_info, _, _ = functions.quranJsonControl.getAyah(current_line, self.category, self.type)
            surah_name = juz_info[1]
        except Exception:
            surah_name = None
        if surah_name and (self.type != 0 or self.is_search_view or self.type == 5):
            currentSurahInfoAction = qt1.QAction(f"معلومات سورة: {surah_name}", self)
            currentSurahInfoAction.setShortcut("ctrl+alt+f")
            currentSurahInfoAction.triggered.connect(self.show_current_surah_info)
            surahOption.addAction(currentSurahInfoAction)
        play_menu = surahOption.addMenu("التشغيل")
        play_menu.setFont(font)
        playSurahToEnd = qt1.QAction(play_to_end_text, self)
        playSurahToEnd.setShortcut("ctrl+shift+p")
        play_menu.addAction(playSurahToEnd)
        playSurahToEnd.triggered.connect(self.onPlayToEnd)
        if not self.is_search_view:
            playFromVersToVersAction = qt1.QAction("التشغيل من آية إلى آية", self)
            playFromVersToVersAction.setShortcut("ctrl+alt+p")
            play_menu.addAction(playFromVersToVersAction)
            playFromVersToVersAction.triggered.connect(self.playFromVersToVers)
            tafseer_menu = surahOption.addMenu("التفسير")
            tafseer_menu.setFont(font)
            if self.type != 5:
                tafaseerSurahAction = qt1.QAction(tafseer_action_text, self)
                tafaseerSurahAction.setShortcut("ctrl+shift+t")
                tafseer_menu.addAction(tafaseerSurahAction)
                tafaseerSurahAction.triggered.connect(self.getTafaseerForSurah)
            if tafseer_to_end_text:
                tafseerFromAyahToEndAction = qt1.QAction(tafseer_to_end_text, self)
                tafseerFromAyahToEndAction.setShortcut("shift+alt+t")
                tafseer_menu.addAction(tafseerFromAyahToEndAction)
                tafseerFromAyahToEndAction.triggered.connect(self.getTafaseerFromAyahToEnd)
            tafseerFromVersToVersAction = qt1.QAction("التفسير من آية إلى آية", self)
            tafseerFromVersToVersAction.setShortcut("ctrl+alt+t")
            tafseer_menu.addAction(tafseerFromVersToVersAction)
            tafseerFromVersToVersAction.triggered.connect(self.TafseerFromVersToVers)
            translation_menu = surahOption.addMenu("الترجمة")
            translation_menu.setFont(font)
            if self.type != 5:
                translationSurahAction = qt1.QAction(translation_action_text, self)
                translationSurahAction.setShortcut("ctrl+shift+l")
                translation_menu.addAction(translationSurahAction)
                translationSurahAction.triggered.connect(self.getTranslationForSurah)
            if translation_to_end_text:
                translationFromAyahToEndAction = qt1.QAction(translation_to_end_text, self)
                translationFromAyahToEndAction.setShortcut("shift+alt+l")
                translation_menu.addAction(translationFromAyahToEndAction)
                translationFromAyahToEndAction.triggered.connect(self.getTranslationFromAyahToEnd)
            translateFromVersToVersAction = qt1.QAction("الترجمة من آية إلى آية", self)
            translateFromVersToVersAction.setShortcut("ctrl+alt+l")
            translation_menu.addAction(translateFromVersToVersAction)
            translateFromVersToVersAction.triggered.connect(self.translateFromVersToVers)
            iarab_menu = surahOption.addMenu("الإعراب")
            iarab_menu.setFont(font)
            simplified_iarab_menu = iarab_menu.addMenu("إعراب مبسط")
            simplified_iarab_menu.setFont(font)
            if self.type != 5:
                IArabSurah = qt1.QAction(iarab_action_text, self)
                IArabSurah.setShortcut("ctrl+shift+i")
                simplified_iarab_menu.addAction(IArabSurah)
                IArabSurah.triggered.connect(self.getIArabForSurah)
            if iarab_to_end_text:
                iarabFromAyahToEndAction = qt1.QAction(iarab_to_end_text, self)
                iarabFromAyahToEndAction.setShortcut("shift+alt+i")
                simplified_iarab_menu.addAction(iarabFromAyahToEndAction)
                iarabFromAyahToEndAction.triggered.connect(self.getIArabFromAyahToEnd)
            IArabFromVersToVersAction = qt1.QAction("الإعراب المبسط من آية إلى آية", self)
            simplified_iarab_menu.addAction(IArabFromVersToVersAction)
            IArabFromVersToVersAction.triggered.connect(self.SimplifiedIArabFromVersToVers)
            detailed_iarab_menu = iarab_menu.addMenu("إعراب مفصل")
            detailed_iarab_menu.setFont(font)
            if self.type != 5:
                DetailedIArabSurah = qt1.QAction(f"إعراب مفصل لـ {cat_target_label}", self)
                DetailedIArabSurah.setShortcut("ctrl+shift+alt+i")
                detailed_iarab_menu.addAction(DetailedIArabSurah)
                DetailedIArabSurah.triggered.connect(self.getDetailedIArabForSurah)
            if iarab_to_end_text:
                detailedIArabFromAyahToEndAction = qt1.QAction(f"الإعراب المفصل من الآية المحددة إلى نهاية {cat_target_label}", self)
                detailedIArabFromAyahToEndAction.setShortcut("shift+alt+e")
                detailed_iarab_menu.addAction(detailedIArabFromAyahToEndAction)
                detailedIArabFromAyahToEndAction.triggered.connect(self.getDetailedIArabFromAyahToEnd)
            DetailedIArabFromVersToVersAction = qt1.QAction("الإعراب المفصل من آية إلى آية", self)
            DetailedIArabFromVersToVersAction.setShortcut("ctrl+alt+e")
            detailed_iarab_menu.addAction(DetailedIArabFromVersToVersAction)
            DetailedIArabFromVersToVersAction.triggered.connect(self.DetailedIArabFromVersToVers)
            meanings_menu = surahOption.addMenu("معاني كلمات الآيات")
            meanings_menu.setFont(font)
            if self.type != 5:
                meaningsSurahAction = qt1.QAction(f"معاني كلمات آيات {cat_target_label}", self)
                meaningsSurahAction.setShortcut("ctrl+shift+u")
                meanings_menu.addAction(meaningsSurahAction)
                meaningsSurahAction.triggered.connect(self.getMeaningsForSurah)
            meaningsFromAyahToEndAction = qt1.QAction(f"معاني الكلمات من الآية المحددة إلى نهاية {cat_target_label}", self)
            meaningsFromAyahToEndAction.setShortcut("shift+alt+u")
            meanings_menu.addAction(meaningsFromAyahToEndAction)
            meaningsFromAyahToEndAction.triggered.connect(self.getMeaningsFromAyahToEnd)
            meaningsFromVersToVersAction = qt1.QAction("معاني الكلمات من آية إلى آية", self)
            meaningsFromVersToVersAction.setShortcut("ctrl+alt+u")
            meanings_menu.addAction(meaningsFromVersToVersAction)
            meaningsFromVersToVersAction.triggered.connect(self.MeaningsFromVersToVers)
            sarf_menu = surahOption.addMenu("صرف كلمات الآيات")
            sarf_menu.setFont(font)
            if self.type != 5:
                sarfSurahAction = qt1.QAction(f"صرف كلمات آيات {cat_target_label}", self)
                sarfSurahAction.setShortcut("ctrl+shift+k")
                sarf_menu.addAction(sarfSurahAction)
                sarfSurahAction.triggered.connect(self.getSarfForSurah)
            sarfFromAyahToEndAction = qt1.QAction(f"صرف الكلمات من الآية المحددة إلى نهاية {cat_target_label}", self)
            sarfFromAyahToEndAction.setShortcut("shift+alt+k")
            sarf_menu.addAction(sarfFromAyahToEndAction)
            sarfFromAyahToEndAction.triggered.connect(self.getSarfFromAyahToEnd)
            sarfFromVersToVersAction = qt1.QAction("صرف الكلمات من آية إلى آية", self)
            sarfFromVersToVersAction.setShortcut("ctrl+shift+alt+k")
            sarf_menu.addAction(sarfFromVersToVersAction)
            sarfFromVersToVersAction.triggered.connect(self.SarfFromVersToVers)
            merge_menu = surahOption.addMenu("الدمج")
            merge_menu.setFont(font)
            if merge_audio_category_text:
                mergeAllAction = qt1.QAction(merge_audio_category_text, self)
                mergeAllAction.setShortcut("ctrl+shift+d")
                merge_menu.addAction(mergeAllAction)
                mergeAllAction.triggered.connect(self.mergeCategoryAyahs)
            if merge_audio_to_end_text:
                mergeFromAyahToEndAction = qt1.QAction(merge_audio_to_end_text, self)
                mergeFromAyahToEndAction.setShortcut("shift+alt+d")
                merge_menu.addAction(mergeFromAyahToEndAction)
                mergeFromAyahToEndAction.triggered.connect(self.mergeFromAyahToEnd)
            mergeRangeAction = qt1.QAction("الدمج من آية إلى آية", self)
            mergeRangeAction.setShortcut("ctrl+alt+d")
            merge_menu.addAction(mergeRangeAction)
            mergeRangeAction.triggered.connect(self.mergeAyahs)
            save_menu = surahOption.addMenu("الحفظ")
            save_menu.setFont(font)
            if save_audio_category_text:
                saveAudioCategoryAction = qt1.QAction(save_audio_category_text, self)
                saveAudioCategoryAction.setShortcut("ctrl+shift+h")
                save_menu.addAction(saveAudioCategoryAction)
                saveAudioCategoryAction.triggered.connect(self.saveCategoryAyahs)
            if save_audio_to_end_text:
                saveAudioFromAyahToEndAction = qt1.QAction(save_audio_to_end_text, self)
                saveAudioFromAyahToEndAction.setShortcut("shift+alt+h")
                save_menu.addAction(saveAudioFromAyahToEndAction)
                saveAudioFromAyahToEndAction.triggered.connect(self.saveFromAyahToEnd)
            saveAudioRangeAction = qt1.QAction("حفظ من آية إلى آية في الجهاز", self)
            saveAudioRangeAction.setShortcut("ctrl+alt+h")
            save_menu.addAction(saveAudioRangeAction)
            saveAudioRangeAction.triggered.connect(self.saveFromVersToVers)
            copyFromVersToVersAction = qt1.QAction("نسخ من آية إلى آية", self)
            copyFromVersToVersAction.setShortcut("ctrl+alt+c")
            surahOption.addAction(copyFromVersToVersAction)
            copyFromVersToVersAction.triggered.connect(self.copyFromVersToVers)
            if tashkeel_action_text:
                removeTashkeelCategoryAction = qt1.QAction(tashkeel_action_text, self)
                removeTashkeelCategoryAction.setShortcut("ctrl+shift+x")
                surahOption.addAction(removeTashkeelCategoryAction)
                removeTashkeelCategoryAction.triggered.connect(self.toggleTashkeelView)
            if self.type == 5:
                sajda_action_text = "عرض جميع الآيات التي تحتوي على سجدة في العرض المخصص"
            else:
                sajda_action_text = f"عرض جميع الآيات التي تحتوي على سجدة في {category_name_no_al} {self.category}"
            showSajdaAction = qt1.QAction(sajda_action_text, self)
            showSajdaAction.setShortcut("ctrl+alt+j")
            surahOption.addAction(showSajdaAction)
            showSajdaAction.triggered.connect(self.showSajdaVerses)
            if self.type == 5:
                asbab_action_text = "عرض جميع الآيات التي تحتوي على أسباب نزول في العرض المخصص"
            else:
                asbab_action_text = f"عرض جميع الآيات التي تحتوي على أسباب نزول في {category_name_no_al} {self.category}"
            showAsbabAction = qt1.QAction(asbab_action_text, self)
            showAsbabAction.setShortcut("ctrl+alt+r")
            surahOption.addAction(showAsbabAction)
            showAsbabAction.triggered.connect(self.showAsbabAlnozoleVerses)
            if self.enableNextPreviouseButtons and go_to_action_text:
                goToCategoryAction = qt1.QAction(go_to_action_text, self)
                goToCategoryAction.setShortcut("ctrl+shift+g")
                goToCategoryAction.triggered.connect(self.goToCategory)
                surahOption.addAction(goToCategoryAction)
        menu.addMenu(surahOption)
        menu.aboutToHide.connect(lambda: self.__setattr__('context_menu_active', False))
        menu.aboutToHide.connect(self.resume_after_action)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
