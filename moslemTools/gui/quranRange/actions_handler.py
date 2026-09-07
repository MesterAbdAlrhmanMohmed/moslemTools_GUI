import functions
import gui
import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class QuranRangeActionsMixin:
    def onOpen(self):
        result = self._get_selected_ayahs()
        label = self.get_range_label()
        gui.QuranViewer(self.p, "\n".join(result), 5, label, enableNextPreviouseButtons=False, enableBookmarks=False).exec()

    def onGo(self):
        menu = guiTools.QCustomContextMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setAccessibleName("خيارات")
        menu.setFont(font)
        readAction = qt1.QAction("قراءة", self)
        readAction.setShortcut("ctrl+o")
        readAction.triggered.connect(self.onOpen)
        menu.addAction(readAction)
        menu.setDefaultAction(readAction)
        listenAction = qt1.QAction("تشغيل", self)
        listenAction.setShortcut("ctrl+p")
        listenAction.triggered.connect(self.onListenActionTriggert)
        menu.addAction(listenAction)
        tafseerAction = qt1.QAction("تفسير", self)
        tafseerAction.setShortcut("ctrl+t")
        tafseerAction.triggered.connect(self.onTafseerActionTriggered)
        menu.addAction(tafseerAction)
        translationAction = qt1.QAction("ترجمة", self)
        translationAction.setShortcut("ctrl+l")
        translationAction.triggered.connect(self.onTranslationActionTriggered)
        menu.addAction(translationAction)
        iarab_menu = menu.addMenu("إعراب: Ctrl+I")
        iarab_menu.setFont(font)
        simplifiedAction = qt1.QAction("إعراب مبسط", self)
        simplifiedAction.triggered.connect(self.onSimplifiedIarabActionTriggered)
        iarab_menu.addAction(simplifiedAction)
        detailedAction = qt1.QAction("إعراب مفصل", self)
        detailedAction.triggered.connect(self.onDetailedIarabActionTriggered)
        iarab_menu.addAction(detailedAction)
        analyticalAction = qt1.QAction("إعراب تحليلي", self)
        analyticalAction.triggered.connect(self.onAnalyticalIarabActionTriggered)
        iarab_menu.addAction(analyticalAction)
        qiraatAction = qt1.QAction("قراءات الآيات", self)
        qiraatAction.setShortcut("ctrl+e")
        qiraatAction.triggered.connect(self.onQiraatActionTriggered)
        menu.addAction(qiraatAction)
        meaningsAction = qt1.QAction("معاني كلمات الآيات", self)
        meaningsAction.setShortcut("ctrl+u")
        meaningsAction.triggered.connect(self.onMeaningsActionTriggered)
        menu.addAction(meaningsAction)
        sarfAction = qt1.QAction("صرف كلمات الآيات", self)
        sarfAction.setShortcut("ctrl+k")
        sarfAction.triggered.connect(self.onSarfActionTriggered)
        menu.addAction(sarfAction)
        menu.addSeparator()
        mergeAction = qt1.QAction("دمج الآيات", self)
        mergeAction.setShortcut("ctrl+d")
        mergeAction.triggered.connect(self.onMergeActionTriggered)
        menu.addAction(mergeAction)
        saveAction = qt1.QAction("حفظ الآيات", self)
        saveAction.setShortcut("ctrl+h")
        saveAction.triggered.connect(self.onSaveActionTriggered)
        menu.addAction(saveAction)
        menu.exec(qt1.QCursor.pos())

    def onListenActionTriggert(self):
        result = self._get_selected_ayahs()
        label = self.get_range_label()
        gui.QuranPlayer(self.p, "\n".join(result), 0, 5, label).exec()

    def onTafseerActionTriggered(self):
        result = self._get_selected_ayahs()
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض التفسير.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.TafaseerViewer(self.p, AyahNumber1, AyahNumber2).exec()

    def onTranslationActionTriggered(self):
        result = self._get_selected_ayahs()
        if not result:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الترجمة.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(result[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(result[-1])
        gui.translationViewer(self.p, AyahNumber1, AyahNumber2).exec()

    def onIarabActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب.")
            return
        menu = guiTools.QCustomContextMenu("اختر نوع الإعراب", self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)
        simplified_action = qt1.QAction("إعراب مبسط", self)
        simplified_action.triggered.connect(self.onSimplifiedIarabActionTriggered)
        menu.addAction(simplified_action)
        detailed_action = qt1.QAction("إعراب مفصل", self)
        detailed_action.triggered.connect(self.onDetailedIarabActionTriggered)
        menu.addAction(detailed_action)
        analytical_action = qt1.QAction("إعراب تحليلي", self)
        analytical_action.triggered.connect(self.onAnalyticalIarabActionTriggered)
        menu.addAction(analytical_action)
        menu.exec(qt1.QCursor.pos())

    def onSimplifiedIarabActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب.")
            return
        Ayah, surah, juz, page, AyahNumber1 = functions.quranJsonControl.getAyah(ayahList[0])
        Ayah, surah, juz, page, AyahNumber2 = functions.quranJsonControl.getAyah(ayahList[-1])
        result = functions.iarab.getIarab(AyahNumber1, AyahNumber2)
        guiTools.TextViewer(self.p, "إعراب مبسط", result).exec()

    def onDetailedIarabActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب المفصل.")
            return
        result = functions.quran_details.get_range_detailed_irab(ayahList)
        guiTools.TextViewer(self.p, "إعراب مفصل", result).exec()

    def onAnalyticalIarabActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض الإعراب التحليلي.")
            return
        result = functions.quran_details.get_range_analytical_irab(ayahList)
        guiTools.TextViewer(self.p, "إعراب تحليلي", result).exec()

    def onQiraatActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض القراءات.")
            return
        result = functions.quran_details.get_range_qiraat(ayahList)
        guiTools.TextViewer(self.p, "قراءات الآيات", result).exec()

    def onMeaningsActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض معاني الكلمات.")
            return
        result = functions.quran_details.get_range_meanings(ayahList)
        guiTools.TextViewer(self.p, "معاني كلمات الآيات", result).exec()

    def onSarfActionTriggered(self):
        ayahList = self._get_selected_ayahs()
        if not ayahList:
            guiTools.qMessageBox.MessageBox.warning(self, "تحذير", "لا توجد آيات في النطاق المحدد لعرض صرف الكلمات.")
            return
        result = functions.quran_details.get_range_sarf(ayahList)
        guiTools.TextViewer(self.p, "صرف كلمات الآيات", result).exec()
