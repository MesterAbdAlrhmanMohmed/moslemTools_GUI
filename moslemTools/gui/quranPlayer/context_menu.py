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


class PlayerContextMenuMixin:
    def OnContextMenu(self):
        self.was_playing = self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")
        menu=qt.QMenu("خيارات الآية",self)
        menu.setAccessibleName("خيارات الآية")
        boldFont = menu.font()
        boldFont.setBold(True)
        speed_menu = menu.addMenu("سرعة التشغيل")
        speed_menu.setFont(boldFont)
        current_speed = self.load_speed()
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            action = speed_menu.addAction(f"{s}x")
            action.setCheckable(True)
            action.setChecked(abs(current_speed - s) < 0.01)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
        GoToAya=qt1.QAction("الذهاب إلى آية",self)
        GoToAya.setShortcut("ctrl+g")
        menu.addAction(GoToAya)
        GoToAya.triggered.connect(self.gotoayah)
        aya_info=qt1.QAction("معلومات الآية",self)
        aya_info.setShortcut("ctrl+f")
        menu.addAction(aya_info)
        aya_info.triggered.connect(self.getAyahInfo)
        aya_trans=qt1.QAction("ترجمة الآية",self)
        aya_trans.setShortcut("ctrl+l")
        menu.addAction(aya_trans)
        aya_trans.triggered.connect(self.getCurentAyahTranslation)
        aya_tafsseer=qt1.QAction("تفسير الآية",self)
        aya_tafsseer.setShortcut("ctrl+t")
        menu.addAction(aya_tafsseer)
        aya_tafsseer.triggered.connect(self.getCurentAyahTafseer)
        iarabMenu = menu.addMenu("إعراب الآية: Ctrl+I")
        iarabMenu.setFont(boldFont)
        simplified_iarab = qt1.QAction("إعراب مبسط", self)
        simplified_iarab.triggered.connect(self.getCurentAyahSimplifiedIArab)
        iarabMenu.addAction(simplified_iarab)
        detailed_iarab = qt1.QAction("إعراب مفصل", self)
        detailed_iarab.triggered.connect(self.getCurentAyahDetailedIArab)
        iarabMenu.addAction(detailed_iarab)
        aya_meanings = qt1.QAction("معاني كلمات الآية", self)
        aya_meanings.setShortcut("ctrl+u")
        menu.addAction(aya_meanings)
        aya_meanings.triggered.connect(self.getCurentAyahMeanings)
        aya_sarf = qt1.QAction("صرف كلمات الآية", self)
        aya_sarf.setShortcut("ctrl+k")
        menu.addAction(aya_sarf)
        aya_sarf.triggered.connect(self.getCurentAyahSarf)
        aya_tanzeel=qt1.QAction("أسباب نزول الآية",self)
        aya_tanzeel.setShortcut("ctrl+r")
        menu.addAction(aya_tanzeel)
        aya_tanzeel.triggered.connect(self.getCurrentAyahTanzel)
        menu.addSeparator()
        saveCurrentAyahAction = qt1.QAction("حفظ الآية الحالية", self)
        saveCurrentAyahAction.setShortcut("ctrl+h")
        saveCurrentAyahAction.triggered.connect(self.onSaveCurrentAyahActionTriggered)
        menu.addAction(saveCurrentAyahAction)
        self.toggleDiacriticsAction = qt1.QAction("إخفاء التشكيل", self)
        self.toggleDiacriticsAction.setCheckable(True)
        self.toggleDiacriticsAction.setChecked(not self.show_diacritics)
        self.toggleDiacriticsAction.triggered.connect(self.on_toggle_diacritics)
        menu.addAction(self.toggleDiacriticsAction)
        menu.setFocus()
        menu.aboutToHide.connect(self.resume_playback)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
