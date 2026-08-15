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


class PlayerNavigationDisplayMixin:
    def _remove_diacritics(self, text):
        return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

    def update_display_text(self):
        text_to_display = self.original_ayah_text
        if not self.show_diacritics:
            text_to_display = self._remove_diacritics(text_to_display)
        self.text.setText(text_to_display)
        self.update_font_size()

    def on_toggle_diacritics(self):
        self.show_diacritics = not self.show_diacritics
        if hasattr(self, 'toggleDiacriticsAction'):
            self.toggleDiacriticsAction.setChecked(not self.show_diacritics)
        self.update_display_text()

    def pause_for_action(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False

    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()

    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))

    def increase_font_size(self):
        functions.text_actions.increase_font_size(self.show_font)

    def decrease_font_size(self):
        functions.text_actions.decrease_font_size(self.show_font)

    def update_font_size(self):
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)

    def on_set(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText(), self.category, self.type)
        if int(surah)<10: surah="00" + surah
        elif int(surah)<100: surah="0" + surah
        else: surah=str(surah)
        if Ayah<10: Ayah="00" + str(Ayah)
        elif Ayah<100: Ayah="0" + str(Ayah)
        else: Ayah=str(Ayah)
        return surah+Ayah+".mp3"

    def gotoayah(self):
        self.pause_for_action()
        number,ok=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية",self.index+1,1,len(self.quranText))
        if ok:
            self.currentTime=1
            self.index=number-1
            self.original_ayah_text = self.quranText[self.index]
            self.update_display_text()
            self.media.stop()
            self.on_play()
        else: self.resume_after_action()

    def onNextAyah(self):
        self.currentTime=1
        if self.index+1==len(self.quranText): self.index=0
        else: self.index+=1
        self.original_ayah_text = self.quranText[self.index]
        self.update_display_text()
        self.media.stop()
        self.on_play()

    def onPreviousAyah(self):
        self.currentTime=1
        if self.index==0: self.index=len(self.quranText)-1
        else: self.index-=1
        self.original_ayah_text = self.quranText[self.index]
        self.update_display_text()
        self.media.stop()
        self.on_play()

    def getcurrentAyahText(self):
        return self.original_ayah_text

    def getCurrentReciter(self):
        return list(reciters.keys())[self.currentReciter]

    def onChangeRecitersContextMenuRequested(self):
        self.pause_for_action()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        if dlg.exec()==dlg.DialogCode.Accepted: self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.resume_after_action()
