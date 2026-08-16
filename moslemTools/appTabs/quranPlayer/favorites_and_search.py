import guiTools, requests, os, winsound, gui, functions, subprocess, shutil
import ujson as json
from guiTools import TextViewer
from guiTools import speak
from guiTools.QCustomListDialog import QCustomListDialog
from settings import *
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from functions import audio_manager
from .threads import DownloadThread, MergeThread
from .favorites import FavoritesManager


class PlayerFavoritesAndSearchMixin:
    def update_progress_label(self, current, total):
        if total == 1:
            self.progress_text_label.setText("جاري تحميل سورة واحدة...")
            return
        if current == 0:
            current_text = "0 سورة"
        else:
            current_text = self.format_surah_count(current)
        total_text = self.format_surah_count(total)
        self.progress_text_label.setText(f"تم تحميل {current_text} من أصل {total_text}")

    def load_data(self):
        self.reciters_data = self.load_reciters()
        self.recitersList = list(self.reciters_data.keys())
        self.recitersList.sort()
        self.load_favorites_from_disk()
        self.update_favorites_ui_state()
        self.reciter_onsearch()
        if self.recitersListWidget.count() > 0:
            self.recitersListWidget.setCurrentRow(0)
            self.on_reciter_selected()

    def load_favorites_from_disk(self):
        if os.path.exists(self.fav_path):
            try:
                with open(self.fav_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.favorites = data.get("favorites", [])
                    self.show_favorites_only = data.get("show_favorites_only", False)
            except: pass

    def save_favorites_to_disk(self):
        os.makedirs(os.path.dirname(self.fav_path), exist_ok=True)
        with open(self.fav_path, 'w', encoding='utf-8') as f:
            json.dump({"favorites": self.favorites, "show_favorites_only": self.show_favorites_only}, f, ensure_ascii=False)

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        self.save_favorites_to_disk()
        self.update_favorites_ui_state()
        self.reciter_onsearch()

    def update_favorites_ui_state(self):
        if self.show_favorites_only:
            self.view_favorites_btn.setText("عرض كل القراء")
            self.reciterSearchLabel.setText("ابحث عن القارئ المفضل")
            self.reciterSearchEdit.setAccessibleName("ابحث عن القارئ المفضل")
        else:
            self.view_favorites_btn.setText("عرض المفضلة")
            self.reciterSearchLabel.setText("ابحث عن قارئ")
            self.reciterSearchEdit.setAccessibleName("ابحث عن قارئ")

    def open_reciter_menu(self, pos):
        item = self.recitersListWidget.itemAt(pos) or self.recitersListWidget.currentItem()
        if not item: return
        name = item.text()
        if name == "لا يوجد قراء في قائمة المفضلة": return
        if name in self.favorites:
            self.manage_favorites(name, "remove")
        else:
            self.manage_favorites(name, "add")

    def manage_favorites(self, name, op):
        if op == "add" and name not in self.favorites:
            self.favorites.append(name)
            guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم إضافة {name} إلى المفضلة")
        elif op == "remove" and name in self.favorites:
            self.favorites.remove(name)
            guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم إزالة {name} من المفضلة")
        self.save_favorites_to_disk()
        if self.show_favorites_only: self.reciter_onsearch()

    def check_media_loaded(self):
        if self.mp.duration() <= 0:
            speak("لا توجد سورة مُشَغَّلَة حالياً")
            return False
        return True

    def check_if_busy(self):
        if hasattr(self, 'download_thread') and self.download_thread is not None and self.download_thread.isRunning():
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "هناك عملية تحميل جارية بالفعل. الرجاء الانتظار حتى تنتهي أو قم بإلغائها.")
            return True
        if hasattr(self, 'merge_thread') and self.merge_thread is not None and self.merge_thread.isRunning():
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "هناك عملية دمج جارية بالفعل. الرجاء الانتظار.")
            return True
        return False

    def update_button_style(self, button, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
        else:
            button.setStyleSheet("")

    def search(self, search_text, data):
        return [item for item in data if search_text in item.lower()]

    def reciter_onsearch(self):
        search_text = self.reciterSearchEdit.text().lower()
        self.recitersListWidget.clear()
        source = self.favorites if self.show_favorites_only else self.recitersList
        result = self.search(search_text, source)
        if self.show_favorites_only and not result:
            self.recitersListWidget.addItem("لا يوجد قراء في قائمة المفضلة")
        else:
            self.recitersListWidget.addItems(result)

    def surah_onsearch(self):
        search_text = self.surahSearchEdit.text().lower()
        self.surahListWidget.clear()
        selected_reciter_item = self.recitersListWidget.currentItem()
        if selected_reciter_item:
            reciter = selected_reciter_item.text()
            surah_list = list(self.reciters_data[reciter].keys())
        else:
            surah_list = []
        result = self.search(search_text, surah_list)
        self.surahListWidget.addItems(result)

    def load_reciters(self):
        file_path = "data/json/reciters.json"
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
