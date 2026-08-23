import gui.translationViewer
import gui, guiTools, functions, re, os, requests, subprocess, shutil, traceback
import ujson as json
from settings.app import appName
from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, QuranLoader

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)


class QuranTabActionsMixin:
    def onCategoryInfoTriggered(self):
        if not self.info.currentItem():
            return
        category_index = self.type.currentIndex()
        item_text = self.info.currentItem().text()
        try:
            with open("data/json/quran.json", "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", f"تعذر تحميل بيانات القرآن: {e}")
            return
        medinan_surahs = [2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110]
        cat_singular = {0: "سورة", 1: "صفحة", 2: "جزء", 3: "ربع", 4: "حزب"}
        title = f"معلومات {cat_singular.get(category_index, '')} {item_text}"
        info_text = ""
        if category_index == 0:
            try:
                s_num = self.infoData.index(item_text) + 1
                surah = data.get(str(s_num))
                if surah:
                    s_type = "مدنية" if s_num in medinan_surahs else "مكية"
                    ayahs = surah['ayahs']
                    pages = [a['page'] for a in ayahs]
                    juzs = [a['juz'] for a in ayahs]
                    rubs = [a['hizbQuarter'] for a in ayahs]
                    info_text = (f"رقم السورة: {s_num}.\n"
                                 f"نوع السورة: {s_type}.\n"
                                 f"عدد الآيات: {surah['numberOfAyahs']}.\n"
                                 f"رقم أول آية بترتيب المصحف: {ayahs[0]['number']}.\n"
                                 f"رقم آخر آية بترتيب المصحف: {ayahs[-1]['number']}.\n"
                                 f"تبدأ في الصفحة: {min(pages)}.\n"
                                 f"تنتهي في الصفحة: {max(pages)}.\n"
                                 f"تبدأ في الحزب: {(min(rubs)-1)//4+1}.\n"
                                 f"تنتهي في الحزب: {(max(rubs)-1)//4+1}.\n"
                                 f"تبدأ في الجزء: {min(juzs)}.\n"
                                 f"تنتهي في الجزء: {max(juzs)}.\n"
                                 f"تبدأ في الربع: {min(rubs)}.\n"
                                 f"تنتهي في الربع: {max(rubs)}.")
            except: pass
        elif category_index == 1:
            p_num = int(item_text)
            matches = []
            for s_v in data.values():
                for a in s_v['ayahs']:
                    if a['page'] == p_num: matches.append((s_v['name'], a))
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
            matches = []
            for s_v in data.values():
                for a in s_v['ayahs']:
                    if a['juz'] == j_num: matches.append((s_v['name'], a))
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages, rubs = [m[1]['page'] for m in matches], [m[1]['hizbQuarter'] for m in matches]
                info_text = (f"رقم الجزء: {j_num}.\n"
                             f"يبدأ الجزء {j_num} من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي الجزء في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"يبدأ في الربع {min(rubs)} وينتهي في الربع {max(rubs)}.\n"
                             f"يبدأ في الحزب {(min(rubs)-1)//4+1} وينتهي في الحزب {(max(rubs)-1)//4+1}.\n"
                             f"عدد السور في الجزء: {len(surah_names)}.\n"
                             f"عدد الآيات في الجزء: {len(matches)}.\n"
                             f"السور في الجزء: {', '.join(surah_names)}.")
        elif category_index == 3:
            r_num = int(item_text)
            matches = []
            for s_v in data.values():
                for a in s_v['ayahs']:
                    if a['hizbQuarter'] == r_num: matches.append((s_v['name'], a))
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages = [m[1]['page'] for m in matches]
                hizb, juz = (r_num-1)//4+1, (r_num-1)//8+1
                q_in_j, q_in_h = (r_num-1)%8, (r_num-1)%4
                ord_f = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن"]
                ord_h = ["الأول", "الثاني", "الثالث", "الرابع"]
                hizb_j_names = ["الأول", "الثاني"]
                info_text = (f"رقم الربع: {r_num}.\n"
                             f"يبدأ الربع {r_num} من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي الربع في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"موضع الربع في الجزء: الربع {ord_f[q_in_j]} في الحزب {hizb_j_names[(hizb-1)%2]} في الجزء {juz}.\n"
                             f"موضع الربع في المصحف: الربع {ord_h[q_in_h]} من الحزب {hizb} في الجزء {juz}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"عدد السور في الربع: {len(surah_names)}.\n"
                             f"عدد الآيات في الربع: {len(matches)}.\n"
                             f"السور في الربع: {', '.join(surah_names)}.")
        elif category_index == 4:
            h_num = int(item_text)
            matches = []
            for s_v in data.values():
                for a in s_v['ayahs']:
                    if (a['hizbQuarter']-1)//4+1 == h_num: matches.append((s_v['name'], a))
            if matches:
                surah_names = list(dict.fromkeys(m[0] for m in matches))
                pages, rubs = [m[1]['page'] for m in matches], [m[1]['hizbQuarter'] for m in matches]
                juz, h_in_j_names = (h_num-1)//2+1, ["الأول", "الثاني"]
                info_text = (f"رقم الحزب: {h_num}.\n"
                             f"يبدأ الحزب {h_num} من الآية {matches[0][1]['numberInSurah']} في سورة {matches[0][0]}.\n"
                             f"ينتهي الحزب في الآية {matches[-1][1]['numberInSurah']} من سورة {matches[-1][0]}.\n"
                             f"موضع الحزب في الجزء: الحزب {h_in_j_names[(h_num-1)%2]} من الجزء {juz}.\n"
                             f"يبدأ من الصفحة {min(pages)} وينتهي في الصفحة {max(pages)}.\n"
                             f"يبدأ في الربع {min(rubs)} وينتهي في الربع {max(rubs)}.\n"
                             f"عدد السور في الحزب: {len(surah_names)}.\n"
                             f"عدد الآيات في الحزب: {len(matches)}.\n"
                             f"السور في الحزب: {', '.join(surah_names)}.")
        if info_text:
            guiTools.qMessageBox.MessageBox.view(self, title, info_text)

    def onListenActionTriggert(self):
        if not self.info.currentItem():
            return
        result = self.getResult()
        gui.QuranPlayer(self, result, 0, self.type.currentIndex(), self.info.currentItem().text()).exec()

    def onTafseerActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.TafaseerViewer(self, AyahNumber1, AyahNumber2).exec()

    def onTranslationActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        gui.translationViewer(self, AyahNumber1, AyahNumber2).exec()

    def onIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        menu = guiTools.QCustomContextMenu("اختر نوع الإعراب", self)
        simplified_action = qt1.QAction("إعراب مبسط", self)
        simplified_action.triggered.connect(self.onSimplifiedIarabActionTriggered)
        menu.addAction(simplified_action)
        detailed_action = qt1.QAction("إعراب مفصل", self)
        detailed_action.triggered.connect(self.onDetailedIarabActionTriggered)
        menu.addAction(detailed_action)
        menu.exec(qt1.QCursor.pos())

    def onSimplifiedIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0], category, type)
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1], category, type)
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self, "إعراب مبسط", result).exec()

    def onDetailedIarabActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        result = functions.quran_details.get_range_detailed_irab(ayahList, category, type)
        guiTools.TextViewer(self, "إعراب مفصل", result).exec()

    def onMeaningsActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        result = functions.quran_details.get_range_meanings(ayahList, category, type)
        guiTools.TextViewer(self, "معاني كلمات الآيات", result).exec()

    def onSarfActionTriggered(self):
        if not self.info.currentItem():
            return
        ayahList = self.getResult().split("\n")
        category = self.info.currentItem().text()
        type = self.type.currentIndex()
        result = functions.quran_details.get_range_sarf(ayahList, category, type)
        guiTools.TextViewer(self, "صرف كلمات الآيات", result).exec()

    def onCostumBTNClicked(self):
        categories=["من سورة إلى سورة", "من صفحة إلى صفحة", "من جزء إلى جزء", "من ربع إلى ربع", "من حزب إلى حزب"]
        menu=guiTools.QCustomContextMenu("اختر فئة",self)
        font=qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        menu.setAccessibleName("اختر فئة")
        menu.setFocus()
        for i, category in enumerate(categories):
            action=qt1.QAction(category,self)
            action.setShortcut(f"ctrl+{i+1}")
            menu.addAction(action)
            action.triggered.connect(self.onCostumBTNRequested)
        menu.exec(qt1.QCursor.pos())
        menu.setFont(font)

    def onCostumBTNRequested(self):
        categories=["من سورة إلى سورة", "من صفحة إلى صفحة", "من جزء إلى جزء", "من ربع إلى ربع", "من حزب إلى حزب"]
        index=categories.index(self.sender().text())
        guiTools.FromToSurahWidget(self,index).exec()

    def _get_current_reciter_name(self):
        return list(reciters.keys())[self.currentReciter]
