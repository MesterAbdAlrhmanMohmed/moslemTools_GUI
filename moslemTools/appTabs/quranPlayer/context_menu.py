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


class PlayerContextMenuMixin:
    def open_context_menu(self, position):
        menu = qt.QMenu(self)
        menu.setAccessibleName("خيارات السورة")
        boldFont=menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)
        speed_menu = menu.addMenu("سرعة التشغيل")
        speed_menu.setFont(boldFont)
        current_speed = self.load_speed()
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        for s in speeds:
            action = speed_menu.addAction(f"{s}x")
            action.setCheckable(True)
            action.setChecked(abs(current_speed - s) < 0.01)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
        is_merging_active = self.merge_list or self.first_merge_selection_index is not None
        is_batch_download_active = bool(self.download_batch_list) or self.first_download_selection_index is not None
        if not is_batch_download_active:
            merge_menu = menu.addMenu("دمج السور")
            if self.first_merge_selection_index is None:
                if not self.merge_list:
                    start_merge_action = qt1.QAction("بدء الدمج من هذه السورة", self)
                    start_merge_action.triggered.connect(self.add_to_merge_list)
                    merge_menu.addAction(start_merge_action)
                else:
                    add_next_action = qt1.QAction(f"إضافة السورة رقم {len(self.merge_list) + 1}", self)
                    add_next_action.triggered.connect(self.add_to_merge_list)
                    merge_menu.addAction(add_next_action)
                    undo_action = qt1.QAction("التراجع عن تحديد سورة", self)
                    undo_action.triggered.connect(self.remove_from_merge_list)
                    merge_menu.addAction(undo_action)
                    cancel_merge_action = qt.QWidgetAction(self)
                    btn_cm = guiTools.QPushButton("إلغاء عملية الدمج الحالية")
                    btn_cm.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                    btn_cm.clicked.connect(self.cancel_merge)
                    btn_cm.clicked.connect(menu.close)
                    cancel_merge_action.setDefaultWidget(btn_cm)
                    merge_menu.addAction(cancel_merge_action)
            merge_menu.addSeparator()
            if not self.merge_list:
                if self.first_merge_selection_index is None:
                    set_start_action = qt1.QAction("تحديد كبداية للدمج", self)
                    set_start_action.triggered.connect(self.set_as_merge_start)
                    merge_menu.addAction(set_start_action)
                else:
                    current_index = self.surahListWidget.currentRow()
                    start_item_text = self.surahListWidget.item(self.first_merge_selection_index).text()
                    merge_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                    if current_index != self.first_merge_selection_index:
                        merge_range_action = qt1.QAction("الدمج من البداية المحددة إلى هنا", self)
                        merge_range_action.triggered.connect(self.merge_from_start_to_here)
                        merge_menu.addAction(merge_range_action)
                    cancel_start_action = qt.QWidgetAction(self)
                    btn_csm = guiTools.QPushButton("إلغاء تحديد بداية الدمج")
                    btn_csm.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                    btn_csm.clicked.connect(self.cancel_merge_start)
                    btn_csm.clicked.connect(menu.close)
                    cancel_start_action.setDefaultWidget(btn_csm)
                    merge_menu.addAction(cancel_start_action)
            menu.addSeparator()
        if not is_merging_active:
            if not is_batch_download_active or self.batch_download_target == 'app':
                batch_download_app_menu = menu.addMenu("تحميل مخصص في التطبيق")
                if self.first_download_selection_index is None:
                    if not self.download_batch_list:
                        start_batch_dl_action = qt1.QAction("بدء التحميل المخصص من هذه السورة", self)
                        start_batch_dl_action.triggered.connect(lambda: self.add_to_download_batch('app'))
                        batch_download_app_menu.addAction(start_batch_dl_action)
                    else:
                        add_next_dl_action = qt1.QAction(f"إضافة السورة رقم {len(self.download_batch_list) + 1} للتحميل", self)
                        add_next_dl_action.triggered.connect(lambda: self.add_to_download_batch('app'))
                        batch_download_app_menu.addAction(add_next_dl_action)
                        remove_dl_action = qt1.QAction("إزالة سورة من قائمة التحميل", self)
                        remove_dl_action.triggered.connect(self.remove_from_download_batch)
                        batch_download_app_menu.addAction(remove_dl_action)
                        cancel_batch_dl_action = qt.QWidgetAction(self)
                        btn_c_app = guiTools.QPushButton("إلغاء التحميل المخصص")
                        btn_c_app.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                        btn_c_app.clicked.connect(self.cancel_download_batch)
                        btn_c_app.clicked.connect(menu.close)
                        cancel_batch_dl_action.setDefaultWidget(btn_c_app)
                        batch_download_app_menu.addAction(cancel_batch_dl_action)
                batch_download_app_menu.addSeparator()
                if not self.download_batch_list:
                    if self.first_download_selection_index is None:
                        set_start_dl_action = qt1.QAction("تحديد كبداية للتحميل", self)
                        set_start_dl_action.triggered.connect(lambda: self.set_as_download_start('app'))
                        batch_download_app_menu.addAction(set_start_dl_action)
                    else:
                        current_index = self.surahListWidget.currentRow()
                        if self.batch_download_target == 'app':
                            start_item_text = self.surahListWidget.item(self.first_download_selection_index).text()
                            batch_download_app_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                            if current_index != self.first_download_selection_index:
                                download_range_action = qt1.QAction("التحميل من البداية المحددة إلى هنا", self)
                                download_range_action.triggered.connect(lambda: self.download_from_start_to_here('app'))
                                batch_download_app_menu.addAction(download_range_action)
                            cancel_start_dl_action = qt.QWidgetAction(self)
                            btn_cs_app = guiTools.QPushButton("إلغاء تحديد بداية التحميل")
                            btn_cs_app.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                            btn_cs_app.clicked.connect(self.cancel_download_start)
                            btn_cs_app.clicked.connect(menu.close)
                            cancel_start_dl_action.setDefaultWidget(btn_cs_app)
                            batch_download_app_menu.addAction(cancel_start_dl_action)
            if not is_batch_download_active or self.batch_download_target == 'device':
                batch_download_device_menu = menu.addMenu("تحميل مخصص في الجهاز")
                if self.first_download_selection_index is None:
                    if not self.download_batch_list:
                        start_batch_dl_action = qt1.QAction("بدء التحميل المخصص من هذه السورة", self)
                        start_batch_dl_action.triggered.connect(lambda: self.add_to_download_batch('device'))
                        batch_download_device_menu.addAction(start_batch_dl_action)
                    else:
                        add_next_dl_action = qt1.QAction(f"إضافة السورة رقم {len(self.download_batch_list) + 1} للتحميل", self)
                        add_next_dl_action.triggered.connect(lambda: self.add_to_download_batch('device'))
                        batch_download_device_menu.addAction(add_next_dl_action)
                        remove_dl_action = qt1.QAction("إزالة سورة من قائمة التحميل", self)
                        remove_dl_action.triggered.connect(self.remove_from_download_batch)
                        batch_download_device_menu.addAction(remove_dl_action)
                        cancel_batch_dl_action = qt.QWidgetAction(self)
                        btn_c_dev = guiTools.QPushButton("إلغاء التحميل المخصص")
                        btn_c_dev.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                        btn_c_dev.clicked.connect(self.cancel_download_batch)
                        btn_c_dev.clicked.connect(menu.close)
                        cancel_batch_dl_action.setDefaultWidget(btn_c_dev)
                        batch_download_device_menu.addAction(cancel_batch_dl_action)
                batch_download_device_menu.addSeparator()
                if not self.download_batch_list:
                    if self.first_download_selection_index is None:
                        set_start_dl_action = qt1.QAction("تحديد كبداية للتحميل", self)
                        set_start_dl_action.triggered.connect(lambda: self.set_as_download_start('device'))
                        batch_download_device_menu.addAction(set_start_dl_action)
                    else:
                        current_index = self.surahListWidget.currentRow()
                        if self.batch_download_target == 'device':
                            start_item_text = self.surahListWidget.item(self.first_download_selection_index).text()
                            batch_download_device_menu.addAction(f"البداية المحددة: {start_item_text}").setEnabled(False)
                            if current_index != self.first_download_selection_index:
                                download_range_action = qt1.QAction("التحميل من البداية المحددة إلى هنا", self)
                                download_range_action.triggered.connect(lambda: self.download_from_start_to_here('device'))
                                batch_download_device_menu.addAction(download_range_action)
                            cancel_start_dl_action = qt.QWidgetAction(self)
                            btn_cs_dev = guiTools.QPushButton("إلغاء تحديد بداية التحميل")
                            btn_cs_dev.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
                            btn_cs_dev.clicked.connect(self.cancel_download_start)
                            btn_cs_dev.clicked.connect(menu.close)
                            cancel_start_dl_action.setDefaultWidget(btn_cs_dev)
                            batch_download_device_menu.addAction(cancel_start_dl_action)
            menu.addSeparator()
        if self.mp.duration() > 0:
            repeateFromPositionTopositionMenue = menu.addMenu("التكرار من موضع إلى موضع")
            setStartingPositionAction = qt1.QAction("تحديد موضع البداية", self)
            setStartingPositionAction.setShortcut("shift+1")
            setStartingPositionAction.triggered.connect(self.onChangeStartingPosition)
            repeateFromPositionTopositionMenue.addAction(setStartingPositionAction)
            repeateFromPositionTopositionMenue.setDefaultAction(setStartingPositionAction)
            setEndingPositionAction = qt1.QAction("تحديد موضع النهاية", self)
            setEndingPositionAction.setShortcut("shift+2")
            setEndingPositionAction.triggered.connect(self.onChangeEndingPosition)
            repeateFromPositionTopositionMenue.addAction(setEndingPositionAction)
            if self.startingPosition is not None or self.endingPosition is not None or self.repeatFromPositionToPosition:
                resetAndStopRepeatingAction = qt1.QAction("حذف الموضع المحدد وإيقاف التكرار", self)
                resetAndStopRepeatingAction.setShortcut("backspace")
                resetAndStopRepeatingAction.triggered.connect(self.removePosition)
                repeateFromPositionTopositionMenue.addAction(resetAndStopRepeatingAction)
            repeateFromPositionTopositionMenue.setFont(boldFont)
        play_action = qt1.QAction("تشغيل السورة المحددة", self)
        play_action.triggered.connect(self.play_selected_audio)
        menu.addAction(play_action)
        selected_item = self.surahListWidget.currentItem()
        if selected_item:
            surah_name = selected_item.text()
            selected_reciter_item = self.recitersListWidget.currentItem()
            if not selected_reciter_item:
                return
            reciter = selected_reciter_item.text()
            surah_path = os.path.join(os.getenv('appdata'), app.appName, "quran surah reciters", reciter, f"{surah_name}.mp3")
            if not os.path.exists(surah_path):
                download_app_action = qt1.QAction("تحميل السورة المحددة في التطبيق", self)
                download_app_action.triggered.connect(self.download_selected_audio_to_app)
                menu.addAction(download_app_action)
            download_device_action = qt1.QAction("تحميل السورة المحددة في الجهاز", self)
            download_device_action.triggered.connect(self.download_selected_audio)
            menu.addAction(download_device_action)
        delete_option = self.check_current_surah_downloaded()
        if delete_option:
            menu.addAction(delete_option)
        addNewBookmarkAction = qt1.QAction("إضافة علامة مرجعية", self)
        menu.addAction(addNewBookmarkAction)
        addNewBookmarkAction.triggered.connect(self.onAddNewBookmark)
        menu.exec(self.surahListWidget.viewport().mapToGlobal(position))
