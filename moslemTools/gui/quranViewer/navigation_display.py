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


class NavigationDisplayMixin:
    def _remove_tashkeel_from_text(self, text):
        return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

    def _toggle_tashkeel(self, checked):
        self.remove_tashkeel = checked
        self._update_display_text()

    def _show_numbering_options(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.saved_cursor_position = self.text.textCursor().position()
        self.saved_ayah_index = self.getCurrentAyah()
        self.saved_text = self.text.toPlainText()
        self.pause_for_action()
        menu = qt.QMenu(self)
        action_group = qt1.QActionGroup(self)
        action_group.setExclusive(True)
        by_surah_action = qt1.QAction("إظهار الأرقام بحسب السورة", self, checkable=True)
        by_surah_action.setChecked(self.verse_numbering_mode == "by_surah")
        by_surah_action.triggered.connect(lambda: self._set_numbering_mode("by_surah"))
        cumulative_action = qt1.QAction("إظهار الأرقام بحسب الفئة", self, checkable=True)
        cumulative_action.setChecked(self.verse_numbering_mode == "cumulative")
        cumulative_action.triggered.connect(lambda: self._set_numbering_mode("cumulative"))
        quran_wide_action = qt1.QAction("إظهار الأرقام بحسب القرآن كاملا", self, checkable=True)
        quran_wide_action.setChecked(self.verse_numbering_mode == "quran_wide")
        quran_wide_action.triggered.connect(lambda: self._set_numbering_mode("quran_wide"))
        none_action = qt1.QAction("إخفاء أرقام الآيات", self, checkable=True)
        none_action.setChecked(self.verse_numbering_mode == "none")
        none_action.triggered.connect(lambda: self._set_numbering_mode("none"))
        action_group.addAction(by_surah_action)
        action_group.addAction(cumulative_action)
        action_group.addAction(quran_wide_action)
        action_group.addAction(none_action)
        menu.addAction(by_surah_action)
        menu.addAction(cumulative_action)
        menu.addAction(quran_wide_action)
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
        if self.verse_numbering_mode in self.text_cache:
            formatted_text = self.text_cache[self.verse_numbering_mode]
        else:
            lines = self.original_quran_text.split('\n')
            new_lines = []
            if not lines or not self.original_quran_text.strip():
                formatted_text = self.original_quran_text
            elif self.verse_numbering_mode == "none":
                for line in lines:
                    new_lines.append(re.sub(r' \(\d+\)$', '', line))
                formatted_text = "\n".join(new_lines)
            elif self.verse_numbering_mode == "cumulative":
                start_cumulative_num = -1
                try:
                    first_line = ""
                    for line in lines:
                        if line.strip():
                            first_line = line
                            break
                    if first_line:
                        base_text = re.sub(r'\s*\(\d+\)$', '', first_line)
                        _, _, _, _, start_cumulative_num = functions.quranJsonControl.getAyah(base_text, self.category, self.type)
                except Exception as e:
                    print(f"Error getting starting cumulative number: {e}")
                    start_cumulative_num = -1
                if start_cumulative_num != -1:
                    current_cumulative_num = start_cumulative_num
                    for line in lines:
                        if not line.strip():
                            new_lines.append(line)
                            continue
                        base_text = re.sub(r'\s*\(\d+\)$', '', line)
                        new_lines.append(f"{base_text} ({current_cumulative_num})")
                        current_cumulative_num += 1
                    formatted_text = "\n".join(new_lines)
                else:
                    formatted_text = self.original_quran_text
            elif self.verse_numbering_mode == "quran_wide":
                for line in lines:
                    if not line.strip():
                        new_lines.append(line)
                        continue
                    try:
                        _, _, _, _, ayah_number_in_quran = functions.quranJsonControl.getAyah(line, self.category, self.type)
                        base_text = re.sub(r'\s*\(\d+\)$', '', line)
                        new_lines.append(f"{base_text} ({ayah_number_in_quran})")
                    except Exception as e:
                        print(f"Could not get Quran-wide number for line: '{line}'. Error: {e}")
                        new_lines.append(line)
                formatted_text = "\n".join(new_lines)
            else:
                formatted_text = self.original_quran_text
            self.text_cache[self.verse_numbering_mode] = formatted_text
        self.quranText = formatted_text
        display_text = formatted_text
        if self.remove_tashkeel:
            display_text = self._remove_tashkeel_from_text(formatted_text)
        self._set_text_with_delay(display_text)

    def format_category_name(self, category_type, category_value):
        if category_type == 0:
            return f"{category_value}"
        elif category_type == 1:
            return f"الصفحة {category_value}"
        elif category_type == 2:
            return f"الجزء {category_value}"
        elif category_type == 3:
            return f"الربع {category_value}"
        elif category_type == 4:
            return f"الحزب {category_value}"
        return category_value

    def pause_for_action(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False

    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()

    def _set_text_with_delay(self, full_text):
        self.saved_text = full_text
        lines = full_text.split('\n')
        initial_text_chunk = '\n'.join(lines[:40])
        self.text.setText(initial_text_chunk)
        self.update_font_size()
        if len(lines) > 40:
            qt2.QTimer.singleShot(500, self._display_full_content)

    def _display_full_content(self):
        if not hasattr(self, 'context_menu_active') or not self.context_menu_active:
            self.text.setText(self.saved_text)
            self.update_font_size()

    def removeTashkeelForAyah(self, cursor_pos=None):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        target_cursor = qt1.QTextCursor(self.text.document())
        pos_in_block = 0
        if cursor_pos is not None:
            target_cursor.setPosition(cursor_pos)
        else:
            target_cursor = self.text.textCursor()
        temp_cursor = qt1.QTextCursor(target_cursor)
        temp_cursor.movePosition(qt1.QTextCursor.MoveOperation.StartOfBlock)
        block_num = temp_cursor.blockNumber()
        ayah_index = 0
        if self.is_search_view and self.text.toPlainText().startswith("عدد نتائج البحث"):
            ayah_index = block_num - 2
        else:
            ayah_index = block_num
        if ayah_index < 0:
            self._handle_invalid_search_line_action()
            self.resume_after_action()
            return
        block = target_cursor.block()
        if not block.isValid():
            self.resume_after_action()
            return
        line_text = block.text()
        if not line_text.strip():
            self.resume_after_action()
            return
        no_tashkeel_text = self._remove_tashkeel_from_text(line_text)
        lines = self.original_quran_text.split('\n')
        if ayah_index < 0 or ayah_index >= len(lines):
             self.resume_after_action()
             return
        original_line_with_formatting = lines[ayah_index]
        if line_text == no_tashkeel_text:
            new_text = original_line_with_formatting
            guiTools.speak("تم إظهار التشكيل للآية")
        else:
            new_text = no_tashkeel_text
            guiTools.speak("تم إزالة التشكيل من الآية")
        pos_in_block = target_cursor.positionInBlock()
        target_cursor.movePosition(qt1.QTextCursor.MoveOperation.StartOfBlock)
        target_cursor.movePosition(qt1.QTextCursor.MoveOperation.EndOfBlock, qt1.QTextCursor.MoveMode.KeepAnchor)
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        char_format = qt1.QTextCharFormat()
        char_format.setFont(font)
        target_cursor.insertText(new_text, char_format)
        target_cursor.movePosition(qt1.QTextCursor.MoveOperation.StartOfBlock)
        target_cursor.movePosition(qt1.QTextCursor.MoveOperation.Right, n=pos_in_block)
        self.text.setTextCursor(target_cursor)
        self.resume_after_action()

    def toggleTashkeelView(self):
        if self.is_search_view:
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح في وضع البحث")
            return
        new_state = not self.remove_tashkeel
        self._toggle_tashkeel(new_state)
        if new_state:
            guiTools.speak("تم إزالة التشكيل من الفئة")
        else:
            guiTools.speak("تم إظهار التشكيل للفئة")

    def copyAya(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        a = self.text.textCursor().block().text()
        if a:
            pyperclip.copy(a)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ الآية المحددة بنجاح")

    def _go_to_specific_ayah(self, ayah_index):
        cursor = self.text.textCursor()
        cursor.movePosition(qt1.QTextCursor.MoveOperation.Start)
        for _ in range(ayah_index):
            cursor.movePosition(qt1.QTextCursor.MoveOperation.Down)
        self.text.setTextCursor(cursor)
        self.text.setFocus()

    def goToAyahAndExitSearch(self):
        if not self.is_search_view:
            return
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        selected_verse_text = self.text.textCursor().block().text()
        try:
            original_lines = self.original_quran_text.split('\n')
            target_ayah_index = original_lines.index(selected_verse_text)
        except ValueError:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على الآية المحددة في النص الأصلي.")
            return
        self.clear_search_results()
        qt2.QTimer.singleShot(100, lambda: self._go_to_specific_ayah(target_ayah_index))

    def goToAyah(self):
        if self.is_search_view:
            self.goToAyahAndExitSearch()
            return
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        ayah,OK=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية ",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if OK:
            self._go_to_specific_ayah(ayah - 1)
        self.resume_after_action()

    def getCurrentAyah(self):
        if self.is_search_view and self.text.toPlainText().startswith("عدد نتائج البحث"):
            return self.text.textCursor().blockNumber() - 2
        return self.text.textCursor().blockNumber()

    def on_set(self, ayah_index=None):
        if ayah_index is None:
            ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(ayah_index)
        if not current_line:
            return None
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"

    def getCurrentReciter(self):
        index=self.currentReciter
        name=list(reciters.keys())[index]
        return name

    def getcurrentAyahText(self):
        line = self.getCurrentAyah()
        return self._get_line_text_for_action(line) or ""

    def print_text(self):
        functions.text_actions.print_text_content(self, self.text)

    def save_text_as_txt(self):
        functions.text_actions.save_text_file(self, self.text)

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))

    def update_font_size(self):
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)

    def copy_text(self):
        try:
            text=self.text.toPlainText()
            pyperclip.copy(text)
            winsound.Beep(1000,100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه حدث خطأ", str(error))

    def _get_line_text_for_action(self, ayah_index):
        if ayah_index < 0:
            return None
        text_source = self.quranText if self.is_search_view else self.original_quran_text
        lines = text_source.split('\n')
        if ayah_index < len(lines):
            return lines[ayah_index]
        return None

    def _update_view_for_new_content(self, new_text):
        self.quranText = new_text
        self.original_quran_text = new_text
        self.text_cache = {"by_surah": self.original_quran_text}
        self._update_display_text()

    def update_nav_buttons_text(self):
        cat_singular = {0: "السورة", 1: "الصفحة", 2: "الجزء", 3: "الربع", 4: "الحزب"}
        name = cat_singular.get(self.type, "الفئة")
        next_suffix = "التالي" if self.type in [2, 3, 4] else "التالية"
        prev_suffix = "السابق" if self.type in [2, 3, 4] else "السابقة"
        self.next.setText(f"{name} {next_suffix}")
        self.previous.setText(f"{name} {prev_suffix}")

    def onNext(self):
        self.pause_for_action()
        if self.CurrentIndex==len(self.typeResult)-1:
            self.CurrentIndex=0
        else:
            self.CurrentIndex+=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.category = indexs
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        self.update_nav_buttons_text()
        winsound.PlaySound("data/sounds/next_page.wav",1)
        guiTools.speak(str(formatted_name))
        self.info.setText(formatted_name)
        self.resume_after_action()

    def onPreviouse(self):
        self.pause_for_action()
        if self.CurrentIndex==0:
            self.CurrentIndex=len(self.typeResult)-1
        else:
            self.CurrentIndex-=1
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.category = indexs
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        self.update_nav_buttons_text()
        winsound.PlaySound("data/sounds/previous_page.wav",1)
        guiTools.speak(str(formatted_name))
        self.info.setText(formatted_name)
        self.resume_after_action()

    def goToCategory(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        dialog_title = ""
        dialog_label = ""
        category_name = ""
        if self.type == 0:
            category_name = "سورة"
        elif self.type == 1:
            category_name = "صفحة"
        elif self.type == 2:
            category_name = "جزء"
        elif self.type == 3:
            category_name = "ربع"
        elif self.type == 4:
            category_name = "حزب"
        dialog_title = f"الذهاب إلى {category_name}"
        dialog_label = f"اختر {category_name}"
        category,OK=GoToCategoryDialog.getItem(self,dialog_title,dialog_label,list(self.typeResult.keys()), self.CurrentIndex)
        if OK:
            self.CurrentIndex=list(self.typeResult.keys()).index(category)
            indexs=list(self.typeResult.keys())[self.CurrentIndex]
            formatted_name = self.format_category_name(self.type, indexs)
            self.category = indexs
            self.info.setText(formatted_name)
            new_text = self.typeResult[indexs][1]
            self._update_view_for_new_content(new_text)
            self.update_nav_buttons_text()
        self.resume_after_action()

    def onChangeCategory(self):
        self.pause_for_action()
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        menu=qt.QMenu("اختر فئة",self)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        selectedCategory=qt1.QAction(categories[self.type],self)
        menu.addAction(selectedCategory)
        selectedCategory.setCheckable(True)
        selectedCategory.setChecked(True)
        selectedCategory.triggered.connect(self.ONChangeCategoryRequested)
        menu.setDefaultAction(selectedCategory)
        categories.pop(self.type)
        for category in categories:
            action=qt1.QAction(category,self)
            menu.addAction(action)
            action.triggered.connect(self.ONChangeCategoryRequested)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
        self.resume_after_action()

    def ONChangeCategoryRequested(self):
        self.pause_for_action()
        categories=["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"]
        index=categories.index(self.sender().text())
        self.type=index
        if index==0:
            result=functions.quranJsonControl.getSurahs()
        elif index==1:
            result=functions.quranJsonControl.getPage()
        elif index==2:
            result=functions.quranJsonControl.getJuz()
        elif index==3:
            result=functions.quranJsonControl.getHezb()
        elif index==4:
            result=functions.quranJsonControl.getHizb()
        self.typeResult=result
        self.CurrentIndex=0
        indexs=list(self.typeResult.keys())[self.CurrentIndex]
        formatted_name = self.format_category_name(self.type, indexs)
        self.info.setText(formatted_name)
        new_text = self.typeResult[indexs][1]
        self._update_view_for_new_content(new_text)
        self.update_nav_buttons_text()
        self.resume_after_action()

    def onChangeRecitersContextMenuRequested(self):
        self.pause_for_action()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.resume_after_action()

    def _set_initial_ayah_position(self):
        cerser = self.text.textCursor()
        cerser.movePosition(cerser.MoveOperation.Start)
        for i in range(self.initial_ayah_index):
            cerser.movePosition(cerser.MoveOperation.Down)
        self.text.setTextCursor(cerser)

    def copy_current_selection(self):
        functions.text_actions.copy_current_selection(self, self.text, fallback_func=self.copyAya)

    def copyFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        allVerses = self.text.toPlainText().split("\n")
        total_ayahs = len(allVerses)
        FromVers, ok = guiTools.QInputDialog.getInt(self, "نسخ من الآية", "النسخ من", self.getCurrentAyah() + 1, 1, total_ayahs)
        if ok:
            toVers, ok = guiTools.QInputDialog.getInt(self, "نسخ إلى الآية", "النسخ إلى", total_ayahs, FromVers, total_ayahs)
            if ok:
                start_index = FromVers - 1
                end_index = toVers
                verses_to_copy = allVerses[start_index:end_index]
                if verses_to_copy:
                    text_to_copy = "\n".join(verses_to_copy)
                    pyperclip.copy(text_to_copy)
                    winsound.Beep(1000, 100)
                    guiTools.speak(f"تم نسخ {len(verses_to_copy)} آيات بنجاح")
                else:
                    guiTools.speak("لم يتم تحديد آيات للنسخ")
        self.resume_after_action()

    def format_category_name(self, category_type, category_value):
        if category_type == 0:
            return f"{category_value}"
        elif category_type == 1:
            return f"الصفحة {category_value}"
        elif category_type == 2:
            return f"الجزء {category_value}"
        elif category_type == 3:
            return f"الربع {category_value}"
        elif category_type == 4:
            return f"الحزب {category_value}"
        return category_value
