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


class TafseerAndInfoMixin:
    def getCurentAyahTafseer(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getTafaseerForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getTafaseerFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[current_index], self.category, self.type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        TafaseerViewer(self, AyahNumber1, AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def show_current_surah_info(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        if self.type == 0 and not self.is_search_view:
            return
        self.pause_for_action()
        current_line = self._get_line_text_for_action(self.getCurrentAyah())
        if not current_line:
            self.resume_after_action()
            return
        try:
            with open("data/json/quran.json", "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            _, s_num_str, juz_info, _, _ = functions.quranJsonControl.getAyah(current_line, self.category, self.type)
            item_text = juz_info[1]
            s_num = int(s_num_str)
            surah = data.get(str(s_num))
            if surah:
                medinan_surahs = [2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110]
                s_type = "مدنية" if s_num in medinan_surahs else "مكية"
                ayahs = surah['ayahs']
                pages = [a['page'] for a in ayahs]
                juzs = [a['juz'] for a in ayahs]
                rubs = [a['hizbQuarter'] for a in ayahs]
                info_text = (f"رقم السورة: {s_num}.\n"
                             f"اسم السورة: {item_text}.\n"
                             f"نوع السورة: {s_type}.\n"
                             f"عدد الآيات: {surah['numberOfAyahs']}.\n"
                             f"رقم أول آية بترتيب المصحف: {ayahs[0]['number']}.\n"
                             f"رقم آخر آية بترتيب المصحف: {ayahs[-1]['number']}.\n"
                             f"تبدأ في الصفحة: {min(pages)}.\n"
                             f"تنتهي في الصفحة: {max(pages)}.\n"
                             f"تبدأ في الجزء: {min(juzs)}.\n"
                             f"تنتهي في الجزء: {max(juzs)}.\n"
                             f"تبدأ في الحزب: {(min(rubs)-1)//4+1}.\n"
                             f"تنتهي في الحزب: {(max(rubs)-1)//4+1}.\n"
                             f"تبدأ في الربع: {min(rubs)}.\n"
                             f"تنتهي في الربع: {max(rubs)}.")
                guiTools.qMessageBox.MessageBox.view(self, f"معلومات سورة: {item_text}", info_text)
            else:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على معلومات.")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"حدث خطأ أثناء جلب معلومات السورة: {e}")
        self.resume_after_action()

    def onSurahInfo(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        if self.is_search_view or self.type == 5:
            winsound.Beep(440, 200)
            guiTools.speak("هذا الخيار غير متاح لهذا العرض.")
            self.resume_after_action()
            return
        self.pause_for_action()
        category_index = self.type
        item_text = self.category
        try:
            with open("data/json/quran.json", "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر تحميل بيانات القرآن: {e}")
            self.resume_after_action()
            return
        medinan_surahs = [2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110]
        cat_singular = {0: "سورة", 1: "صفحة", 2: "جزء", 3: "ربع", 4: "حزب"}
        title = f"معلومات {cat_singular.get(category_index, '')} {item_text}"
        info_text = ""
        if category_index == 0:
            try:
                all_surahs_dict = functions.quranJsonControl.getSurahs()
                s_num = list(all_surahs_dict.keys()).index(item_text) + 1
                surah = data.get(str(s_num))
                if surah:
                    s_type = "مدنية" if s_num in medinan_surahs else "مكية"
                    ayahs = surah['ayahs']
                    pages = [a['page'] for a in ayahs]
                    juzs = [a['juz'] for a in ayahs]
                    rubs = [a['hizbQuarter'] for a in ayahs]
                    info_text = (f"رقم السورة: {s_num}.\n"
                                 f"اسم السورة: {item_text}.\n"
                                 f"نوع السورة: {s_type}.\n"
                                 f"عدد الآيات: {surah['numberOfAyahs']}.\n"
                                 f"رقم أول آية بترتيب المصحف: {ayahs[0]['number']}.\n"
                                 f"رقم آخر آية بترتيب المصحف: {ayahs[-1]['number']}.\n"
                                 f"تبدأ في الصفحة: {min(pages)}.\n"
                                 f"تنتهي في الصفحة: {max(pages)}.\n"
                                 f"تبدأ في الجزء: {min(juzs)}.\n"
                                 f"تنتهي في الجزء: {max(juzs)}.\n"
                                 f"تبدأ في الحزب: {(min(rubs)-1)//4+1}.\n"
                                 f"تنتهي في الحزب: {(max(rubs)-1)//4+1}.\n"
                                 f"تبدأ في الربع: {min(rubs)}.\n"
                                 f"تنتهي في الربع: {max(rubs)}.")
            except (ValueError, KeyError, IndexError):
                info_text = "لم يتم العثور على معلومات."
        elif category_index == 1:
            p_num = int(item_text)
            matches = [(s_v['name'], a) for s_v in data.values() for a in s_v['ayahs'] if a['page'] == p_num]
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                juz, rub = matches[0][1]['juz'], matches[0][1]['hizbQuarter']
                info_text = (f"رقم الصفحة: {p_num}.\n"
                             f"توجد في الجزء: {juz}.\n"
                             f"توجد في الحزب: {(rub-1)//4+1}.\n"
                             f"توجد في الربع: {rub}.\n"
                             f"تبدأ الصفحة بالآية {matches[0][1]['numberInSurah']} من سورة {matches[0][0]}.\n"
                             f"تنتهي الصفحة بالآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"عدد السور في الصفحة: {len(surah_names)}.\n"
                             f"عدد الآيات في الصفحة: {len(matches)}.\n"
                             f"السور في الصفحة: {', '.join(surah_names)}.")
        elif category_index == 2:
            j_num = int(item_text)
            matches = [(s_v['name'], a) for s_v in data.values() for a in s_v['ayahs'] if a['juz'] == j_num]
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages, rubs = [m[1]['page'] for m in matches], [m[1]['hizbQuarter'] for m in matches]
                info_text = (f"رقم الجزء: {j_num}.\n"
                             f"يبدأ الجزء من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي الجزء في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"يبدأ في الربع {min(rubs)} وينتهي في الربع {max(rubs)}.\n"
                             f"عدد السور في الجزء: {len(surah_names)}.\n"
                             f"عدد الآيات في الجزء: {len(matches)}.")
        elif category_index == 3:
            r_num = int(item_text)
            matches = [(s_v['name'], a) for s_v in data.values() for a in s_v['ayahs'] if a['hizbQuarter'] == r_num]
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages = [m[1]['page'] for m in matches]
                hizb, juz = (r_num-1)//4+1, matches[0][1]['juz']
                info_text = (f"رقم الربع: {r_num}.\n"
                             f"يقع في الجزء: {juz}.\n"
                             f"يقع في الحزب: {hizb}.\n"
                             f"يبدأ من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"عدد السور: {len(surah_names)}.\n"
                             f"عدد الآيات: {len(matches)}.")
        elif category_index == 4:
            h_num = int(item_text)
            matches = [(s_v['name'], a) for s_v in data.values() for a in s_v['ayahs'] if (a['hizbQuarter']-1)//4+1 == h_num]
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages, rubs = [m[1]['page'] for m in matches], [m[1]['hizbQuarter'] for m in matches]
                juz = matches[0][1]['juz']
                info_text = (f"رقم الحزب: {h_num}.\n"
                             f"يقع في الجزء: {juz}.\n"
                             f"يبدأ من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"يحتوي على الأرباع من {min(rubs)} إلى {max(rubs)}.\n"
                             f"عدد السور: {len(surah_names)}.\n"
                             f"عدد الآيات: {len(matches)}.")
        if info_text:
            guiTools.qMessageBox.MessageBox.view(self, title, info_text)
        else:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على معلومات.")
        self.resume_after_action()

    def showSajdaVerses(self):
        if self.is_search_view:
            return
        self.saved_ayah_index = self.getCurrentAyah()
        self.is_counting_sajdas = True
        self.original_info_text = self.info.text()
        self.info.setText("جاري حصر الآيات التي تحتوي على سجدة...")
        self.info.setFocus()
        self.sajda_thread = SajdaFinderThread(self.original_quran_text.split('\n'), self.category, self.type)
        self.sajda_thread.finished.connect(self.onSajdaFinderFinished)
        self.sajda_thread.start()

    def onSajdaFinderFinished(self, sajda_verses):
        self.is_counting_sajdas = False
        self.info.setText(self.original_info_text)
        if not sajda_verses:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا توجد آيات تحتوي على سجدة في هذه الفئة.")
            return
        items = []
        selected_index = -1
        for i, v in enumerate(sajda_verses):
            if self.type == 0:
                item_text = f"الآية {v['numberInSurah']}"
            else:
                item_text = f"سورة {v['surah']} الآية {v['numberInSurah']}"
            items.append(item_text)
            if v['index'] == self.saved_ayah_index:
                selected_index = i
        dialog = SajdaGoToDialog(self, "السجدات", "اختر آية للذهاب إليها", items, selected_index)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            target_index = sajda_verses[dialog.selected_index]['index']
            cursor = self.text.textCursor()
            cursor.movePosition(qt1.QTextCursor.MoveOperation.Start)
            for _ in range(target_index):
                cursor.movePosition(qt1.QTextCursor.MoveOperation.Down)
            self.text.setTextCursor(cursor)
            self.text.setFocus()

    def showAsbabAlnozoleVerses(self):
        if self.is_search_view:
            return
        self.saved_ayah_index = self.getCurrentAyah()
        self.is_counting_asbab_alnozole = True
        self.original_info_text = self.info.text()
        self.info.setText("جاري حصر الآيات التي تحتوي على أسباب نزول...")
        self.info.setFocus()
        self.asbab_thread = AsbabAlnozoleFinderThread(self.original_quran_text.split('\n'), self.category, self.type)
        self.asbab_thread.finished.connect(self.onAsbabAlnozoleFinderFinished)
        self.asbab_thread.start()

    def onAsbabAlnozoleFinderFinished(self, asbab_verses):
        self.is_counting_asbab_alnozole = False
        self.info.setText(self.original_info_text)
        if not asbab_verses:
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "لا توجد آيات تحتوي على أسباب نزول في هذه الفئة.")
            return
        items = []
        selected_index = -1
        for i, v in enumerate(asbab_verses):
            if self.type == 0:
                item_text = f"الآية {v['numberInSurah']}"
            else:
                item_text = f"سورة {v['surah']} الآية {v['numberInSurah']}"
            items.append(item_text)
            if v['index'] == self.saved_ayah_index:
                selected_index = i
        dialog = AsbabAlnozoleGoToDialog(self, "أسباب النزول", "اختر آية للذهاب إليها", items, selected_index)
        if dialog.exec() == qt.QDialog.DialogCode.Accepted:
            target_index = asbab_verses[dialog.selected_index]['index']
            cursor = self.text.textCursor()
            cursor.movePosition(qt1.QTextCursor.MoveOperation.Start)
            for _ in range(target_index):
                cursor.movePosition(qt1.QTextCursor.MoveOperation.Down)
            self.text.setTextCursor(cursor)
            self.text.setFocus()

    def getCurentAyahIArab(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        menu = qt.QMenu("اختر نوع الإعراب", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        simplifiedAction = qt1.QAction("إعراب مبسط", self)
        simplifiedAction.triggered.connect(self.getCurentAyahSimplifiedIArab)
        menu.addAction(simplifiedAction)
        detailedAction = qt1.QAction("إعراب مفصل", self)
        detailedAction.triggered.connect(self.getCurentAyahDetailedIArab)
        menu.addAction(detailedAction)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def getCurentAyahSimplifiedIArab(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب مبسط",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getCurentAyahDetailedIArab(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.quran_details.get_single_ayah_detailed_irab(surah, Ayah)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب مفصل",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getCurentAyahMeanings(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.quran_details.get_single_ayah_meanings(surah, Ayah, ayah_text=current_line)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"معاني كلمات الآية",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getCurentAyahSarf(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.quran_details.get_single_ayah_sarf(surah, Ayah, ayah_text=current_line)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"صرف كلمات الآية",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getIArabForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self,"إعراب مبسط",result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getIArabFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[current_index], self.category, self.type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "إعراب مبسط", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getCurrentAyahTanzel(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            self.text.setUpdatesEnabled(False)
            guiTools.TextViewer(self,"أسباب النزول",result).exec()
            self.text.setUpdatesEnabled(True)
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()

    def getAyahInfo(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nتوجد في الجزء {} \nتوجد في الربع {} \nتوجد في الصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
        self.resume_after_action()

    def getCurentAyahTranslation(self):
        if self._is_invalid_search_line():
            self._handle_invalid_search_line_action()
            return
        self.pause_for_action()
        current_ayah_index = self.getCurrentAyah()
        current_line = self._get_line_text_for_action(current_ayah_index)
        if not current_line:
            self.resume_after_action()
            return
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_line, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber,AyahNumber).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getTranslationForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList=self.original_quran_text.split("\n")
        Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[0], self.category, self.type)
        Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        translationViewer(self,AyahNumber1,AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getTranslationFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[current_index], self.category, self.type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], self.category, self.type)
        self.text.setUpdatesEnabled(False)
        translationViewer(self, AyahNumber1, AyahNumber2).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def TafseerFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","التفسير من",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","التفسير إلى",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                TafaseerViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def translateFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","الترجمة من",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","الترجمة إلى",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                translationViewer(self,AyahNumber1,AyahNumber2).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def IArabFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        menu = qt.QMenu("اختر نوع الإعراب (من آية إلى آية)", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        simplifiedAction = qt1.QAction("إعراب مبسط", self)
        simplifiedAction.triggered.connect(self.SimplifiedIArabFromVersToVers)
        menu.addAction(simplifiedAction)
        detailedAction = qt1.QAction("إعراب مفصل", self)
        detailedAction.triggered.connect(self.DetailedIArabFromVersToVers)
        menu.addAction(detailedAction)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def SimplifiedIArabFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        FromVers,ok=guiTools.QInputDialog.getInt(self,"من الآية","الإعراب المبسط من",self.getCurrentAyah()+1,1,len(self.original_quran_text.split("\n")))
        if ok:
            toVers,ok=guiTools.QInputDialog.getInt(self,"إلى الآية","الإعراب المبسط إلى",len(self.original_quran_text.split("\n")),FromVers,len(self.original_quran_text.split("\n")))
            if ok:
                ayahList=self.original_quran_text.split("\n")
                Ayah,surah,juz,page,AyahNumber1=functions.quranJsonControl.getAyah(ayahList[FromVers-1], self.category, self.type)
                Ayah,surah,juz,page,AyahNumber2=functions.quranJsonControl.getAyah(ayahList[toVers-1], self.category, self.type)
                self.text.setUpdatesEnabled(False)
                result=functions.iarab.getIarab(AyahNumber1,AyahNumber2)
                guiTools.TextViewer(self,"إعراب مبسط",result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getDetailedIArabForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        result = functions.quran_details.get_range_detailed_irab(ayahList, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "إعراب مفصل", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getDetailedIArabFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        target_list = ayahList[current_index:]
        result = functions.quran_details.get_range_detailed_irab(target_list, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "إعراب مفصل", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def DetailedIArabFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        FromVers, ok = guiTools.QInputDialog.getInt(self, "من الآية", "الإعراب المفصل من", self.getCurrentAyah() + 1, 1, len(ayahList))
        if ok:
            toVers, ok = guiTools.QInputDialog.getInt(self, "إلى الآية", "الإعراب المفصل إلى", len(ayahList), FromVers, len(ayahList))
            if ok:
                target_list = ayahList[FromVers - 1:toVers]
                self.text.setUpdatesEnabled(False)
                result = functions.quran_details.get_range_detailed_irab(target_list, self.category, self.type)
                guiTools.TextViewer(self, "إعراب مفصل", result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getMeaningsForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        result = functions.quran_details.get_range_meanings(ayahList, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "معاني كلمات الآيات", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getMeaningsFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        target_list = ayahList[current_index:]
        result = functions.quran_details.get_range_meanings(target_list, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "معاني كلمات الآيات", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def MeaningsFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        FromVers, ok = guiTools.QInputDialog.getInt(self, "من الآية", "معاني الكلمات من", self.getCurrentAyah() + 1, 1, len(ayahList))
        if ok:
            toVers, ok = guiTools.QInputDialog.getInt(self, "إلى الآية", "معاني الكلمات إلى", len(ayahList), FromVers, len(ayahList))
            if ok:
                target_list = ayahList[FromVers - 1:toVers]
                self.text.setUpdatesEnabled(False)
                result = functions.quran_details.get_range_meanings(target_list, self.category, self.type)
                guiTools.TextViewer(self, "معاني كلمات الآيات", result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getSarfForSurah(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        result = functions.quran_details.get_range_sarf(ayahList, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "صرف كلمات الآيات", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def getSarfFromAyahToEnd(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        current_index = self.getCurrentAyah()
        if current_index < 0 or current_index >= len(ayahList):
            current_index = 0
        target_list = ayahList[current_index:]
        result = functions.quran_details.get_range_sarf(target_list, self.category, self.type)
        self.text.setUpdatesEnabled(False)
        guiTools.TextViewer(self, "صرف كلمات الآيات", result).exec()
        self.text.setUpdatesEnabled(True)
        self.resume_after_action()

    def SarfFromVersToVers(self):
        if self.is_search_view:
            self._handle_search_view_restriction()
            return
        self.pause_for_action()
        ayahList = self.original_quran_text.split("\n")
        FromVers, ok = guiTools.QInputDialog.getInt(self, "من الآية", "صرف الكلمات من", self.getCurrentAyah() + 1, 1, len(ayahList))
        if ok:
            toVers, ok = guiTools.QInputDialog.getInt(self, "إلى الآية", "صرف الكلمات إلى", len(ayahList), FromVers, len(ayahList))
            if ok:
                target_list = ayahList[FromVers - 1:toVers]
                self.text.setUpdatesEnabled(False)
                result = functions.quran_details.get_range_sarf(target_list, self.category, self.type)
                guiTools.TextViewer(self, "صرف كلمات الآيات", result).exec()
                self.text.setUpdatesEnabled(True)
        self.resume_after_action()
