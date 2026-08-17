from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
import time,os,requests,subprocess,shutil,re,traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, SaveThread

with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)


class PlayerTafseerAndInfoMixin:
    def getCurentAyahTafseer(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
        self.resume_after_action()

    def getCurentAyahIArab(self):
        menu = qt.QMenu("اختر نوع الإعراب", self)
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        simplifiedAction = qt1.QAction("إعراب مبسط", self)
        simplifiedAction.triggered.connect(self.getCurentAyahSimplifiedIArab)
        menu.addAction(simplifiedAction)
        detailedAction = qt1.QAction("إعراب مفصل", self)
        detailedAction.triggered.connect(self.getCurentAyahDetailedIArab)
        menu.addAction(detailedAction)
        menu.exec(self.mapToGlobal(self.cursor().pos()))

    def getCurentAyahSimplifiedIArab(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        guiTools.TextViewer(self,"إعراب مبسط",result).exec()
        self.resume_after_action()

    def getCurentAyahDetailedIArab(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        result=functions.quran_details.get_single_ayah_detailed_irab(surah, Ayah)
        guiTools.TextViewer(self,"إعراب مفصل",result).exec()
        self.resume_after_action()

    def getCurentAyahMeanings(self):
        self.pause_for_action()
        current_text = self.getcurrentAyahText()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_text, self.category, self.type)
        result=functions.quran_details.get_single_ayah_meanings(surah, Ayah, ayah_text=current_text)
        guiTools.TextViewer(self,"معاني كلمات الآية",result).exec()
        self.resume_after_action()

    def getCurentAyahSarf(self):
        self.pause_for_action()
        current_text = self.getcurrentAyahText()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(current_text, self.category, self.type)
        result=functions.quran_details.get_single_ayah_sarf(surah, Ayah, ayah_text=current_text)
        guiTools.TextViewer(self,"صرف كلمات الآية",result).exec()
        self.resume_after_action()

    def getCurrentAyahTanzel(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        result=functions.tanzil.gettanzil(AyahNumber)
        if result: guiTools.TextViewer(self,"اسباب النزول",result).exec()
        else: guiTools.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
        self.resume_after_action()

    def getAyahInfo(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        sajda="الآية تحتوي على سجدة" if juz[3] else ""
        hizb=(juz[2]-1)//4+1
        guiTools.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nتوجد في الجزء {} \nتوجد في الحزب {} \nتوجد في الربع {} \nتوجد في الصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],hizb,juz[2],page,sajda))
        self.resume_after_action()

    def getCurentAyahTranslation(self):
        self.pause_for_action()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        translationViewer(self,AyahNumber,AyahNumber).exec()
        self.resume_after_action()
