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


class QuranTabContextMenuMixin:
    def onContextMenu(self):
        category_name = {0: "السورة", 1: "الصفحة", 2: "الجزء", 3: "الربع", 4: "الحزب"}.get(self.type.currentIndex(), "الفئة")
        menu = guiTools.QCustomContextMenu(f"خيارات {category_name}", self)
        menu.setAccessibleName(f"خيارات {category_name}")
        menu.setFocus()
        listenAction = qt1.QAction("تشغيل", self)
        listenAction.setShortcut("ctrl+p")
        menu.addAction(listenAction)
        listenAction.triggered.connect(self.onListenActionTriggert)
        menu.setDefaultAction(listenAction)
        tafseerAction = qt1.QAction("تفسير", self)
        tafseerAction.setShortcut("ctrl+t")
        menu.addAction(tafseerAction)
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        translationAction = qt1.QAction("ترجمة", self)
        translationAction.setShortcut("ctrl+l")
        menu.addAction(translationAction)
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        iarab_menu = menu.addMenu("إعراب: Ctrl+I")
        simplifiedAction = qt1.QAction("إعراب مبسط", self)
        simplifiedAction.triggered.connect(self.onSimplifiedIarabActionTriggered)
        iarab_menu.addAction(simplifiedAction)
        detailedAction = qt1.QAction("إعراب مفصل", self)
        detailedAction.triggered.connect(self.onDetailedIarabActionTriggered)
        iarab_menu.addAction(detailedAction)
        meaningsAction = qt1.QAction("معاني كلمات الآيات", self)
        meaningsAction.setShortcut("ctrl+u")
        menu.addAction(meaningsAction)
        meaningsAction.triggered.connect(self.onMeaningsActionTriggered)
        sarfAction = qt1.QAction("صرف كلمات الآيات", self)
        sarfAction.setShortcut("ctrl+k")
        menu.addAction(sarfAction)
        sarfAction.triggered.connect(self.onSarfActionTriggered)
        current_item = self.info.currentItem()
        if current_item:
            category_idx = self.type.currentIndex()
            if category_idx == 0:
                clean_name = re.sub(r'^\d+[\s\.\-]*', '', current_item.text())
                info_action_text = f"معلومات سورة: {clean_name}"
            else:
                cat_map = {1: "الصفحة", 2: "الجزء", 3: "الربع", 4: "الحزب"}
                info_action_text = f"معلومات {cat_map.get(category_idx, '')}"
            infoAction = qt1.QAction(info_action_text, self)
            infoAction.setShortcut("ctrl+f")
            infoAction.triggered.connect(self.onCategoryInfoTriggered)
            menu.addAction(infoAction)
        menu.addSeparator()
        mergeAction = qt1.QAction("دمج الآيات", self)
        mergeAction.setShortcut("ctrl+alt+d")
        menu.addAction(mergeAction)
        mergeAction.triggered.connect(self.onMergeActionTriggered)
        saveAction = qt1.QAction("حفظ الآيات", self)
        saveAction.setShortcut("ctrl+h")
        menu.addAction(saveAction)
        saveAction.triggered.connect(self.onSaveActionTriggered)
        menu.exec(qt1.QCursor.pos())
