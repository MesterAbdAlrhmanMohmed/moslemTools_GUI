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


class QuranTabNavSearchMixin:
    def showEvent(self, event):
        super().showEvent(event)
        if self.info.count() == 0:
            self.info.clear()
            self.info.addItem("جاري تحميل البيانات...")
            if self.loader_thread is None:
                self.loader_thread = QuranLoader()
                self.loader_thread.data_loaded.connect(self.on_data_loaded)
                self.loader_thread.finished.connect(self.loader_thread.deleteLater)
                self.loader_thread.finished.connect(lambda: setattr(self, 'loader_thread', None))
                self.loader_thread.start()

    def on_data_loaded(self):
        self.info.clear()
        self.onTypeChanged(self.type.currentIndex())

    def search(self, pattern, text_list):
        tashkeel_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        normalized_pattern = tashkeel_pattern.sub('', pattern)
        matches = [text for text in text_list if normalized_pattern in tashkeel_pattern.sub('', text)]
        return matches

    def onsearch(self):
        search_text = self.search_bar.text().lower()
        self.info.clear()
        result = self.search(search_text, self.infoData)
        self.info.addItems(result)

    def onItemTriggered(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
            selected_item_text = self.info.currentItem().text()
            matched_key = None
            for key in result.keys():
                if key == selected_item_text or re.sub(r'^\d+[\s\.\-]*', '', key) == re.sub(r'^\d+[\s\.\-]*', '', selected_item_text):
                    matched_key = key
                    break
            if matched_key:
                correct_index = list(result.keys()).index(matched_key)
                gui.QuranViewer(self, result[matched_key][1], index, selected_item_text, enableNextPreviouseButtons=True, typeResult=result, CurrentIndex=correct_index).exec()
            return
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        selected_item_text = self.info.currentItem().text()
        try:
            correct_index = list(result.keys()).index(selected_item_text)
        except ValueError:
            correct_index = self.info.currentRow()
        gui.QuranViewer(self, result[selected_item_text][1], index, selected_item_text, enableNextPreviouseButtons=True, typeResult=result, CurrentIndex=correct_index).exec()

    def on_surah_number_toggled(self, state=None):
        is_checked = self.show_surah_number_cb.isChecked()
        settings_handler.set("quran", "show_surah_number", "True" if is_checked else "False")
        self.onTypeChanged(self.type.currentIndex())

    def onTypeChanged(self, index: int):
        self.info.clear()
        self.infoData = []
        if index == 0:
            self.show_surah_number_cb.setVisible(True)
            surah_keys = list(functions.quranJsonControl.getSurahs().keys())
            if not self.show_surah_number_cb.isChecked():
                self.infoData = [re.sub(r'^\d+[\s\.\-]*', '', key) for key in surah_keys]
            else:
                self.infoData = surah_keys
            self.search_bar.setPlaceholderText("البحث عن سورة")
            self.search_bar.setAccessibleName("البحث عن سورة")
            self.info1.setText("لخيارات السورة المحددة، نستخدم مفتاح التطبيقات أو click الأيمن")
        else:
            self.show_surah_number_cb.setVisible(False)
            if index == 1:
                for i in range(1, 605):
                    self.infoData.append(str(i))
                self.search_bar.setPlaceholderText("البحث عن صفحة")
                self.search_bar.setAccessibleName("البحث عن صفحة")
                self.info1.setText("لخيارات الصفحة المحددة، نستخدم مفتاح التطبيقات أو click الأيمن")
            elif index == 2:
                for i in range(1, 31):
                    self.infoData.append(str(i))
                self.search_bar.setPlaceholderText("البحث عن جزء")
                self.search_bar.setAccessibleName("البحث عن جزء")
                self.info1.setText("لخيارات الجزء المحدد، نستخدم مفتاح التطبيقات أو click الأيمن")
            elif index == 3:
                for i in range(1, 241):
                    self.infoData.append(str(i))
                self.search_bar.setPlaceholderText("البحث عن ربع")
                self.search_bar.setAccessibleName("البحث عن ربع")
                self.info1.setText("لخيارات الربع المحدد، نستخدم مفتاح التطبيقات أو click الأيمن")
            elif index == 4:
                for i in range(1, 61):
                    self.infoData.append(str(i))
                self.search_bar.setPlaceholderText("البحث عن حزب")
                self.search_bar.setAccessibleName("البحث عن حزب")
                self.info1.setText("لخيارات الحزب المحدد، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info.addItems(self.infoData)

    def on_view_mode_changed(self, index):
        is_grid = (index == 1)
        settings_handler.set("quran", "grid_view", "True" if is_grid else "False")
        if is_grid:
            self.info.setViewMode(qt.QListView.ViewMode.IconMode)
            self.info.setResizeMode(qt.QListView.ResizeMode.Adjust)
            fm = self.info.fontMetrics()
            cell_w = max(150, fm.horizontalAdvance("114. سورة النَّاس") + 35)
            cell_h = max(48, fm.height() * 2 + 14)
            self.info.setGridSize(qt2.QSize(cell_w, cell_h))
            self.info.setSpacing(6)
        else:
            self.info.setViewMode(qt.QListView.ViewMode.ListMode)
            self.info.setResizeMode(qt.QListView.ResizeMode.Fixed)
            self.info.setGridSize(qt2.QSize())
            self.info.setSpacing(3)

    def getResult(self):
        index = self.type.currentIndex()
        if index == 0:
            result = functions.quranJsonControl.getSurahs()
            item_text = self.info.currentItem().text()
            for key in result.keys():
                if key == item_text or re.sub(r'^\d+[\s\.\-]*', '', key) == re.sub(r'^\d+[\s\.\-]*', '', item_text):
                    return result[key][1]
        elif index == 1:
            result = functions.quranJsonControl.getPage()
        elif index == 2:
            result = functions.quranJsonControl.getJuz()
        elif index == 3:
            result = functions.quranJsonControl.getHezb()
        elif index == 4:
            result = functions.quranJsonControl.getHizb()
        return result[self.info.currentItem().text()][1]
