import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from guiTools import speak
import guiTools, os, tempfile, shutil, subprocess, threading, time, uuid, winsound
import ujson as json
from pathlib import Path
from settings import settings_handler, app
from functions import audio_manager
from .recorder import WasapiRecorder, SchedulingDialog
from .stations import (
    ALL_STATIONS,
    quran_brotcast, brotcasts_of_reciters, brotcasts_of_tafseer,
    brotcasts_of_suplications, brotcasts_of_translations, other_brotcasts, set_globals,
    get_global_player, get_global_current_url, get_global_audio_output,
    play_station_by_name, search_stations
)


def format_arabic_duration(total_seconds):
    if total_seconds <= 0:
        return "ثانية واحدة"
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    parts = []
    if h > 0:
        if h == 1:
            parts.append("ساعة واحدة")
        elif h == 2:
            parts.append("ساعتين")
        elif 3 <= h <= 10:
            parts.append(f"{h} ساعات")
        else:
            parts.append(f"{h} ساعة")
    if m > 0:
        if m == 1:
            parts.append("دقيقة واحدة")
        elif m == 2:
            parts.append("دقيقتين")
        elif 3 <= m <= 10:
            parts.append(f"{m} دقائق")
        else:
            parts.append(f"{m} دقيقة")
    if s > 0:
        if s == 1:
            parts.append("ثانية واحدة")
        elif s == 2:
            parts.append("ثانيتين")
        elif 3 <= s <= 10:
            parts.append(f"{s} ثواني")
        else:
            parts.append(f"{s} ثانية")
    if not parts:
        return "ثانية واحدة"
    return " و ".join(parts)


class protcasts(qt.QWidget):
    def __init__(self):
        super().__init__()
        global_player = QMediaPlayer()
        global_audio_output = QAudioOutput()
        global_audio_output.setDevice(audio_manager.get_audio_device("broadcasts"))
        global_player.setAudioOutput(global_audio_output)
        loaded_volume = self.load_volume()
        global_audio_output.setVolume(loaded_volume)
        global_current_url = None
        set_globals(global_player, global_audio_output, global_current_url)

        self.fav_file_path = os.path.join(os.getenv('appdata'), app.appName, "broadcasts_favorites.json")
        self.favorites = []
        self.show_favorites_only = False
        self.load_favorites()

        self.convert_thread_worker = None
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية التسجيل لن تعمل.")
        self.recorder = WasapiRecorder(ffmpeg_path=self.ffmpeg_path)
        self.volume_timer = qt2.QTimer(self)
        self.volume_timer.setSingleShot(True)
        self.volume_timer.timeout.connect(self.restore_aud_text)
        self.countdown_timer = qt2.QTimer(self)
        self.countdown_timer.timeout.connect(self.updateCountdown)
        self.duration_timer = qt2.QTimer(self)
        self.remaining_seconds_to_start = 0
        self.remaining_duration_seconds = 0
        self.scheduled_file_path = ""
        self.is_scheduled_recording = False
        self.pause_countdown_on_recording_pause = False
        self.temp_wav_to_convert = None

        self.brotcasts_tab = guiTools.QCustomTabWidget()
        quran_tab = quran_brotcast(global_audio_output, self)
        reciters_tab = brotcasts_of_reciters(global_audio_output, self)
        tafseer_tab = brotcasts_of_tafseer(global_audio_output, self)
        adhkar_tab = brotcasts_of_suplications(global_audio_output, self)
        translations_tab = brotcasts_of_translations(global_audio_output, self)
        other_tab = other_brotcasts(global_audio_output, self)

        self.brotcasts_tab.addTab(quran_tab, f"إذاعات القرآن الكريم ({len(quran_tab.all_stations)})")
        self.brotcasts_tab.addTab(reciters_tab, f"إذاعات القراء ({len(reciters_tab.all_stations)})")
        self.brotcasts_tab.addTab(tafseer_tab, f"إذاعات التفاسير ({len(tafseer_tab.all_stations)})")
        self.brotcasts_tab.addTab(adhkar_tab, f"إذاعات الأذكار والأدعية ({len(adhkar_tab.all_stations)})")
        self.brotcasts_tab.addTab(translations_tab, f"إذاعات ترجمات القرآن الكريم ({len(translations_tab.all_stations)})")
        self.brotcasts_tab.addTab(other_tab, f"إذاعات إسلامية أخرى ({len(other_tab.all_stations)})")
        if settings_handler.get("g", "theme") == "light":
            self.brotcasts_tab.setStyleSheet("""QTabWidget::pane { border: 1px solid #ccc; border-radius: 6px; background-color: #f5f5f5; } QTabBar::tab { background: #e0e0e0; color: #1e1e1e; padding: 10px 20px; border: 1px solid #ccc; border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; min-width: 100px; font-weight: bold; } QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } QTabBar::tab:hover { background: #d0d0d0; }""")
        else:
            self.brotcasts_tab.setStyleSheet("""QTabWidget::pane { border: 1px solid #444; border-radius: 6px; background-color: #1e1e1e; } QTabBar::tab { background: #2b2b2b; color: white; padding: 10px 20px; border: 1px solid #444; border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; min-width: 100px; font-weight: bold; } QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } QTabBar::tab:hover { background: #3a3a3a; }""")

        view_mode_v_layout = qt.QVBoxLayout()
        view_mode_v_layout.setContentsMargins(5, 0, 5, 0)
        self.view_mode_label = qt.QLabel("طريقة عرض العناصر")
        self.view_mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.view_mode_combo = qt.QComboBox()
        self.view_mode_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.view_mode_combo.setAccessibleName("طريقة عرض العناصر")
        self.view_mode_combo.addItems(["عمودي", "شبكي"])
        grid_enabled = settings_handler.get("broadcasts", "grid_view") == "True"
        self.view_mode_combo.setCurrentIndex(1 if grid_enabled else 0)
        self.view_mode_combo.currentIndexChanged.connect(self.on_view_mode_changed)
        view_mode_v_layout.addWidget(self.view_mode_label)
        view_mode_v_layout.addWidget(self.view_mode_combo)
        view_mode_container = qt.QWidget()
        view_mode_container.setLayout(view_mode_v_layout)
        self.brotcasts_tab.setCornerWidget(view_mode_container, qt2.Qt.Corner.TopRightCorner)

        bold_font = qt1.QFont()
        bold_font.setBold(True)
        self.fav_search_label = qt.QLabel("البحث عن إذاعة في المفضلة")
        self.fav_search_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.fav_search_label.setFont(bold_font)
        self.fav_search_bar = qt.QLineEdit()
        self.fav_search_bar.setFont(bold_font)
        self.fav_search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.fav_search_bar.setPlaceholderText("البحث عن إذاعة في المفضلة")
        self.fav_search_bar.setAccessibleName("البحث عن إذاعة في المفضلة")
        self.fav_search_bar.textChanged.connect(self.on_fav_search)

        self.fav_list_widget = qt.QListWidget()
        self.fav_list_widget.setSpacing(3)
        self.fav_list_widget.setStyleSheet("QListWidget::item { font-weight: bold; font-size: 12pt; }")
        self.fav_list_widget.itemActivated.connect(self.play_fav_station)
        self.fav_list_widget.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.fav_list_widget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.fav_list_widget.customContextMenuRequested.connect(self.on_fav_context_menu)

        self.volume_up_shortcut_fav = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.fav_list_widget)
        self.volume_up_shortcut_fav.activated.connect(self.increase_volume_fav)
        self.volume_down_shortcut_fav = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.fav_list_widget)
        self.volume_down_shortcut_fav.activated.connect(self.decrease_volume_fav)

        self.fav_info_label = guiTools.QNavigableLabel("لمزيد من خيارات الإذاعة، نستخدم زر التطبيقات أو click الأيمن على إذاعة من الإذاعات")
        self.fav_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.fav_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        initial_vol_percent = int(round(loaded_volume * 100))
        self.aud = guiTools.QNavigableLabel()
        self.original_aud_text = f"لرفع أو خفض الصوت: اضغط في القائمة ثم استخدم Shift + الأسهم، أعلى وأسفل: نسبة الصوت الحالية {initial_vol_percent}%"
        self.current_status_text = self.original_aud_text
        self.aud.setText(self.original_aud_text)
        self.aud.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.aud.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white; min-height: 48px; padding: 0 20px; font-weight: bold;")
        self.fav_btn.clicked.connect(self.toggle_favorites)

        info_fav_layout = qt.QHBoxLayout()
        info_fav_layout.addWidget(self.aud, 1)
        info_fav_layout.addWidget(self.fav_btn)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.brotcasts_tab)
        layout.addWidget(self.fav_search_label)
        layout.addWidget(self.fav_search_bar)
        layout.addWidget(self.fav_list_widget)
        layout.addSpacing(10)
        layout.addWidget(self.fav_info_label)
        layout.addSpacing(10)
        layout.addLayout(info_fav_layout)
        layout.addSpacing(15)

        self.startBtn = guiTools.QPushButton("بدء التسجيل")
        self.pauseBtn = guiTools.QPushButton("إيقاف مؤقت")
        self.stopBtn = guiTools.QPushButton("إيقاف التسجيل")
        self.scheduleBtn = guiTools.QPushButton("جدولة التسجيل")
        self.startBtn.setAccessibleDescription("control plus r")
        self.pauseBtn.setAccessibleDescription("control plus p")
        self.stopBtn.setAccessibleDescription("control plus s")
        self.scheduleBtn.setAccessibleDescription("control plus g")
        self.startBtn.setStyleSheet("background-color: #008000; color: white; min-height: 40px; font-size: 16px;")
        self.pauseBtn.setStyleSheet("background-color: #0000AA; color: white; min-height: 40px; font-size: 16px;")
        self.stopBtn.setStyleSheet("background-color: #8B0000; color: white; min-height: 40px; font-size: 16px;")
        self.scheduleBtn.setStyleSheet("background-color: #4B0082; color: white; min-height: 40px; font-size: 16px;")
        self.pauseBtn.setVisible(False)
        self.stopBtn.setVisible(False)
        self.startBtn.setVisible(True)
        self.scheduleBtn.setVisible(True)
        record_layout = qt.QHBoxLayout()
        record_layout.addWidget(self.startBtn)
        record_layout.addWidget(self.pauseBtn)
        record_layout.addWidget(self.stopBtn)
        record_layout.addWidget(self.scheduleBtn)
        layout.addLayout(record_layout)
        self.startBtn.clicked.connect(self.startRecording)
        self.pauseBtn.clicked.connect(self.pauseRecording)
        self.stopBtn.clicked.connect(self.stopRecording)
        self.scheduleBtn.clicked.connect(self.scheduleRecording)
        self.recorder.recording_stopped.connect(self.on_recording_stopped)
        self.recorder.error.connect(self.recordingError)
        self.start_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+R"), self)
        self.start_shortcut.activated.connect(lambda: self.startRecording() if self.startBtn.isVisible() and self.startBtn.isEnabled() else None)
        self.pause_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+P"), self)
        self.pause_shortcut.activated.connect(lambda: (self.pauseRecording() if self.pauseBtn.text() == "إيقاف مؤقت" else self.resumeRecording()) if self.pauseBtn.isVisible() and self.pauseBtn.isEnabled() else None)
        self.stop_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+S"), self)
        self.stop_shortcut.activated.connect(lambda: self.stopRecording() if self.stopBtn.isVisible() and self.stopBtn.isEnabled() else None)
        self.schedule_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+G"), self)
        self.schedule_shortcut.activated.connect(lambda: self.scheduleRecording() if self.scheduleBtn.isVisible() and self.scheduleBtn.isEnabled() else None)
        player = get_global_player()
        if player:
            player.playbackStateChanged.connect(self.on_radio_state_changed)

        self.update_favorites_ui_state()
        self.on_view_mode_changed(self.view_mode_combo.currentIndex())

    def load_favorites(self):
        try:
            if os.path.exists(self.fav_file_path):
                with open(self.fav_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.favorites = data.get("favorites", [])
                        self.show_favorites_only = data.get("show_favorites_only", False)
                    else:
                        self.favorites = data
                        self.show_favorites_only = False
            else:
                self.favorites = []
                self.show_favorites_only = False
        except Exception:
            self.favorites = []
            self.show_favorites_only = False

    def save_favorites(self):
        try:
            os.makedirs(os.path.dirname(self.fav_file_path), exist_ok=True)
            with open(self.fav_file_path, "w", encoding="utf-8") as f:
                json.dump({"favorites": self.favorites, "show_favorites_only": self.show_favorites_only}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def update_favorites_list_widget(self):
        self.fav_list_widget.clear()
        query = self.fav_search_bar.text().strip() if hasattr(self, 'fav_search_bar') else ""
        if query:
            filtered = search_stations(query, self.favorites)
            if filtered:
                self.fav_list_widget.addItems(filtered)
            else:
                self.fav_list_widget.addItem("لا توجد نتائج مطابقة للبحث")
        else:
            if self.favorites:
                self.fav_list_widget.addItems(self.favorites)
            else:
                self.fav_list_widget.addItem("لا توجد إذاعات في قائمة المفضلة")
        if hasattr(self, 'view_mode_combo') and self.view_mode_combo.currentIndex() == 1:
            self.update_grid_size_for_widget(self.fav_list_widget)

    def on_fav_search(self):
        self.update_favorites_list_widget()

    def update_favorites_ui_state(self):
        self.update_favorites_list_widget()
        if self.show_favorites_only:
            self.brotcasts_tab.hide()
            self.fav_search_label.show()
            self.fav_search_bar.show()
            self.fav_list_widget.show()
            self.fav_btn.setText("عرض جميع الإذاعات")
        else:
            self.fav_search_label.hide()
            self.fav_search_bar.hide()
            self.fav_list_widget.hide()
            self.brotcasts_tab.show()
            self.fav_btn.setText("فتح قائمة المفضلة")

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        self.save_favorites()
        self.update_favorites_ui_state()

    def update_grid_size_for_widget(self, list_widget):
        if self.view_mode_combo.currentIndex() != 1:
            return
        fm = list_widget.fontMetrics()
        max_w = 0
        for i in range(list_widget.count()):
            txt = list_widget.item(i).text()
            w = fm.horizontalAdvance(txt) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(txt).width()
            if w > max_w:
                max_w = w
        cell_w = max(200, max_w + 60)
        cell_h = max(60, fm.height() * 2 + 20)
        list_widget.setGridSize(qt2.QSize(cell_w, cell_h))

    def get_all_list_widgets(self):
        widgets = []
        for i in range(self.brotcasts_tab.count()):
            tab_widget = self.brotcasts_tab.widget(i)
            if hasattr(tab_widget, 'list_of_quran_brotcasts'):
                widgets.append(tab_widget.list_of_quran_brotcasts)
            elif hasattr(tab_widget, 'list_of_reciters'):
                widgets.append(tab_widget.list_of_reciters)
            elif hasattr(tab_widget, 'list_of_tafseer'):
                widgets.append(tab_widget.list_of_tafseer)
            elif hasattr(tab_widget, 'list_of_adhkar'):
                widgets.append(tab_widget.list_of_adhkar)
            elif hasattr(tab_widget, 'list_of_translations'):
                widgets.append(tab_widget.list_of_translations)
            elif hasattr(tab_widget, 'list_of_other'):
                widgets.append(tab_widget.list_of_other)
        if hasattr(self, 'fav_list_widget'):
            widgets.append(self.fav_list_widget)
        return widgets

    def on_view_mode_changed(self, index):
        is_grid = (index == 1)
        settings_handler.set("broadcasts", "grid_view", "True" if is_grid else "False")
        if is_grid:
            grid_style = """
                QListWidget::item {
                    padding: 10px 18px;
                    margin: 4px;
                    border-radius: 6px;
                }
                QListWidget::item:selected {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
                QListWidget::item:focus {
                    background-color: #0066CC;
                    color: white;
                    border-radius: 6px;
                }
            """
            for lw in self.get_all_list_widgets():
                lw.setStyleSheet(grid_style)
                lw.setViewMode(qt.QListView.ViewMode.IconMode)
                lw.setResizeMode(qt.QListView.ResizeMode.Adjust)
                self.update_grid_size_for_widget(lw)
                lw.setSpacing(6)
        else:
            list_style = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
            for lw in self.get_all_list_widgets():
                lw.setStyleSheet(list_style)
                lw.setViewMode(qt.QListView.ViewMode.ListMode)
                lw.setResizeMode(qt.QListView.ResizeMode.Fixed)
                lw.setGridSize(qt2.QSize())
                lw.setSpacing(3)

    def toggle_station_favorite(self, station_name):
        if station_name in ["لا توجد إذاعات في قائمة المفضلة", "لا توجد نتائج مطابقة للبحث"]:
            return
        if station_name in self.favorites:
            self.favorites.remove(station_name)
            msg = f"تمت إزالة \"{station_name}\" من قائمة المفضلة."
        else:
            self.favorites.append(station_name)
            msg = f"تمت إضافة \"{station_name}\" إلى قائمة المفضلة."
        self.save_favorites()
        self.update_favorites_list_widget()
        guiTools.qMessageBox.MessageBox.view(self, "المفضلة", msg)

    def play_fav_station(self):
        selected_item = self.fav_list_widget.currentItem()
        if selected_item and selected_item.text() not in ["لا توجد إذاعات في قائمة المفضلة", "لا توجد نتائج مطابقة للبحث"]:
            play_station_by_name(selected_item.text())

    def copy_station_url(self, station_name):
        url = ALL_STATIONS.get(station_name) or ALL_STATIONS.get(station_name.strip())
        if url:
            qt.QApplication.clipboard().setText(url)
            try:
                winsound.Beep(1000, 100)
            except Exception:
                pass
            if station_name.startswith("إذاعة"):
                station_text = station_name
            else:
                station_text = f"إذاعة {station_name}"
            speak(f"تم نسخ رابط {station_text}")
        else:
            speak("لم يتم العثور على رابط لهذه الإذاعة")

    def open_station_context_menu(self, list_widget, pos):
        item = list_widget.itemAt(pos)
        if not item:
            item = list_widget.currentItem()
        if not item:
            return
        station_name = item.text()
        if station_name in ["لا توجد إذاعات في قائمة المفضلة", "لا توجد نتائج مطابقة للبحث"]:
            return

        menu = guiTools.QCustomContextMenu(self)
        menu.setAccessibleName("خيارات الإذاعة")
        boldFont = menu.font()
        boldFont.setBold(True)
        menu.setFont(boldFont)

        copy_action = qt1.QAction("نسخ رابط الإذاعة", self)
        copy_action.triggered.connect(lambda: self.copy_station_url(station_name))
        menu.addAction(copy_action)

        if station_name in self.favorites:
            remove_action = qt.QWidgetAction(self)
            btn = guiTools.QPushButton("إزالة من المفضلة")
            btn.setStyleSheet("background-color: #8B0000; color: white;")
            btn.setFont(boldFont)
            def remove_from_fav():
                menu.close()
                self.toggle_station_favorite(station_name)
            btn.clicked.connect(remove_from_fav)
            remove_action.triggered.connect(remove_from_fav)
            remove_action.setDefaultWidget(btn)
            menu.addAction(remove_action)
        else:
            add_action = qt1.QAction("إضافة إلى المفضلة", self)
            add_action.triggered.connect(lambda: self.toggle_station_favorite(station_name))
            menu.addAction(add_action)

        if pos.x() < 0 or pos.y() < 0:
            rect = list_widget.visualItemRect(item)
            global_pos = list_widget.viewport().mapToGlobal(rect.center())
        else:
            global_pos = list_widget.viewport().mapToGlobal(pos)
        menu.exec(global_pos)

    def on_fav_context_menu(self, pos):
        self.open_station_context_menu(self.fav_list_widget, pos)

    def load_volume(self):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "volume.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("broadcastsTab", data.get("broadcasts", 1.0))
        except Exception as e:
            print(f"Handled exception: {e}")
        return 1.0

    def save_volume(self, volume):
        try:
            path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "volume.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Handled exception: {e}")
            data["broadcastsTab"] = round(volume, 2)
            data["broadcasts"] = round(volume, 2)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Handled exception: {e}")

    def update_aud_status_text(self, volume_percent):
        self.original_aud_text = f"لرفع أو خفض الصوت: اضغط في القائمة ثم استخدم Shift + الأسهم، أعلى وأسفل: نسبة الصوت الحالية {volume_percent}%"
        self.current_status_text = self.original_aud_text

    def increase_volume_fav(self):
        output = get_global_audio_output()
        if output:
            current_volume = output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            output.setVolume(new_volume)
            self.save_volume(new_volume)
            volume_percent = int(round(new_volume * 100))
            self.update_aud_status_text(volume_percent)
            speak(f"نسبة الصوت {volume_percent}")
            self.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.volume_timer.start(3000)

    def decrease_volume_fav(self):
        output = get_global_audio_output()
        if output:
            current_volume = output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            output.setVolume(new_volume)
            self.save_volume(new_volume)
            volume_percent = int(round(new_volume * 100))
            self.update_aud_status_text(volume_percent)
            speak(f"نسبة الصوت {volume_percent}")
            self.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.volume_timer.start(3000)

    def on_radio_state_changed(self, state):
        player = get_global_player()
        current_url = get_global_current_url()
        if state == QMediaPlayer.PlaybackState.StoppedState and current_url is not None:
            if self.recorder._running and not self.is_scheduled_recording:
                self.handle_manual_recording_stop_due_to_radio()
            elif self.countdown_timer.isActive() or self.duration_timer.isActive():
                self.handle_scheduled_recording_stop_due_to_radio()

    def handle_manual_recording_stop_due_to_radio(self):
        result = guiTools.QQuestionMessageBox.view(self, "إيقاف التسجيل", "تم إيقاف التسجيل بسبب إيقاف الإذاعة. هل تريد حفظ التسجيل؟", "نعم", "لا")
        if result == 0:
            self.recorder.stop(cleanup_only=False)
        else:
            self.recorder.stop(cleanup_only=True)
            self.resetRecorderState()
            guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الحفظ.")

    def handle_scheduled_recording_stop_due_to_radio(self):
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
        if self.duration_timer.isActive():
            self.duration_timer.stop()
        if self.recorder._running:
            self.recorder.stop(cleanup_only=False)
            self.scheduled_stop_due_to_radio = True
        else:
            guiTools.qMessageBox.MessageBox.view(self, "إيقاف التسجيل المجدول", "تم إيقاف التسجيل المجدول بسبب إيقاف الإذاعة. لم يتم بدء التسجيل بعد.")
            self.resetRecorderState()

    def restore_aud_text(self):
        if not self.convert_thread_worker and not self.countdown_timer.isActive():
            self.aud.setText(self.current_status_text)

    def get_current_station_name(self):
        try:
            if self.show_favorites_only:
                if self.fav_list_widget.currentItem():
                    station_name = self.fav_list_widget.currentItem().text()
                    if station_name != "لا توجد إذاعات في قائمة المفضلة":
                        safe_name = "".join(c for c in station_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                        return safe_name
            else:
                current_tab = self.brotcasts_tab.currentWidget()
                list_widget = None
                if hasattr(current_tab, 'list_of_other'): list_widget = current_tab.list_of_other
                elif hasattr(current_tab, 'list_of_adhkar'): list_widget = current_tab.list_of_adhkar
                elif hasattr(current_tab, 'list_of_tafseer'): list_widget = current_tab.list_of_tafseer
                elif hasattr(current_tab, 'list_of_reciters'): list_widget = current_tab.list_of_reciters
                elif hasattr(current_tab, 'list_of_quran_brotcasts'): list_widget = current_tab.list_of_quran_brotcasts
                if list_widget and list_widget.currentItem():
                    station_name = list_widget.currentItem().text()
                    safe_name = "".join(c for c in station_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                    return safe_name
        except Exception: pass
        return "تسجيل صوت النظام"

    def check_is_playing(self):
        player = get_global_player()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يجب عليك تشغيل الإذاعة أولاً للبدء بالتسجيل.")
            return False
        return True

    def startRecording(self):
        if not self.check_is_playing(): return
        if not self.recorder.is_ready():
             err = self.recorder.last_error if self.recorder.last_error else "خطأ في تهيئة المسجل."
             guiTools.qMessageBox.MessageBox.error(self, "خطأ في تسجيل الصوت", err)
             return
        if self.recorder._running:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", "التسجيل يعمل بالفعل.")
             return
        result = guiTools.QQuestionMessageBox.view(self, "بدء التسجيل", "ملاحظة: سيتم تسجيل صوت الإذاعة فقط، ولن يتم التقاط أي صوت من المايكروفون أو إشعارات النظام والبرامج الأخرى.\n\nهل تريد البدء بالتسجيل الآن؟", "نعم", "لا")
        if result != 0: return
        self.is_scheduled_recording = False
        self.recorder.start()
        self.startBtn.setVisible(False)
        self.scheduleBtn.setVisible(False)
        self.pauseBtn.setVisible(True)
        self.pauseBtn.setEnabled(True)
        self.stopBtn.setVisible(True)
        self.stopBtn.setEnabled(True)
        self.pauseBtn.setFocus()

    def scheduleRecording(self):
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
            self.restore_aud_text()
            guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الجدولة بنجاح.")
            self.resetRecorderState()
            return
        if not self.check_is_playing(): return
        if not self.recorder.is_ready():
             err = self.recorder.last_error if self.recorder.last_error else "خطأ في تهيئة المسجل."
             guiTools.qMessageBox.MessageBox.error(self, "خطأ في تسجيل الصوت", err)
             return
        dlg = SchedulingDialog(self)
        if dlg.exec() == qt.QDialog.DialogCode.Accepted:
            values = dlg.get_values()
            sh, sm, ss, dh, dm, ds = values[:6]
            self.pause_countdown_on_recording_pause = values[6] if len(values) > 6 else False
            self.remaining_seconds_to_start = (sh * 3600) + (sm * 60) + ss
            self.remaining_duration_seconds = (dh * 3600) + (dm * 60) + ds
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "ملاحظة: سيتم تسجيل صوت الإذاعة فقط، ولن يتم التقاط أي صوت من المايكروفون أو إشعارات النظام والبرامج الأخرى.\nإذا تم إيقاف الإذاعة قبل بدء التسجيل أو أثناءه، سيتم إلغاء العملية.")
            filePath, _ = qt.QFileDialog.getSaveFileName(self, "حفظ التسجيل", f"{self.get_current_station_name()}.mp3", "Audio Files (*.mp3);;All Files (*)")
            if filePath:
                self.scheduled_file_path = filePath
                self.is_scheduled_recording = True
                self.startBtn.setVisible(False)
                self.pauseBtn.setVisible(False)
                self.stopBtn.setVisible(False)
                self.scheduleBtn.setText("إيقاف جدولة التسجيل")
                self.scheduleBtn.setVisible(True)
                self.scheduleBtn.setEnabled(True)
                self.scheduleBtn.setFocus()
                self.updateCountdown()
                self.countdown_timer.start(1000)
            else:
                result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل تريد إلغاء الجدولة؟", "نعم", "لا")
                if result == 0:
                    guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الجدولة.")
                else:
                    self.scheduleRecording()

    def updateCountdown(self):
        player = get_global_player()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.handle_scheduled_recording_stop_due_to_radio()
            return
        if self.remaining_seconds_to_start > 0:
            self.remaining_seconds_to_start -= 1
            time_str = format_arabic_duration(self.remaining_seconds_to_start)
            self.aud.setText(f"متبقي على بدء التسجيل: {time_str}")
        else:
            self.countdown_timer.stop()
            if not self.recorder.is_ready():
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر بدء التسجيل المجدول: خطأ في تهيئة مسجل الصوت.")
                self.resetRecorderState()
                return
            self.recorder.start()
            self.startBtn.setVisible(False)
            self.scheduleBtn.setVisible(False)
            self.pauseBtn.setVisible(True)
            self.pauseBtn.setEnabled(True)
            self.stopBtn.setVisible(True)
            self.stopBtn.setEnabled(True)
            self.pauseBtn.setFocus()
            self.duration_timer.timeout.connect(self.updateDuration)
            self.duration_timer.start(1000)

    def updateDuration(self):
        player = get_global_player()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.handle_scheduled_recording_stop_due_to_radio()
            return
        if getattr(self, 'pause_countdown_on_recording_pause', False) and self.recorder._paused:
            return
        if self.remaining_duration_seconds > 0:
            self.remaining_duration_seconds -= 1
            time_str = format_arabic_duration(self.remaining_duration_seconds)
            self.aud.setText(f"متبقي على انتهاء التسجيل: {time_str}")
        else:
            self.duration_timer.stop()
            self.stopRecording()

    def pauseRecording(self):
        self.recorder.pause()
        self.pauseBtn.setText("استئناف")
        self.pauseBtn.setStyleSheet("background-color: #0056b3; color: white; min-height: 40px; font-size: 16px;")
        try: self.pauseBtn.clicked.disconnect()
        except TypeError: pass
        self.pauseBtn.clicked.connect(self.resumeRecording)

    def resumeRecording(self):
        self.recorder.resume()
        self.pauseBtn.setText("إيقاف مؤقت")
        self.pauseBtn.setStyleSheet("background-color: #0000AA; color: white; min-height: 40px; font-size: 16px;")
        try: self.pauseBtn.clicked.disconnect()
        except TypeError: pass
        self.pauseBtn.clicked.connect(self.pauseRecording)

    def stopRecording(self):
        if self.countdown_timer.isActive() or self.duration_timer.isActive():
            result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإيقاف", "هناك جدولة جارية، هل تريد إيقافها وحفظ ما تم تسجيله إن وجد؟", "نعم", "لا")
            if result != 0: return
            self.countdown_timer.stop()
            self.duration_timer.stop()
            if self.recorder._running: self.recorder.stop(cleanup_only=False)
            else: self.resetRecorderState()
            return
        if not self.recorder._running and not self.recorder._paused: return
        self.recorder.stop(cleanup_only=False)

    @qt2.pyqtSlot(str, str)
    def on_recording_stopped(self, status, temp_wav_path):
        if status == "CONVERTED":
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم حفظ التسجيل بنجاح.")
            self.resetRecorderState()
            return
        if status == "STOPPED" and temp_wav_path and os.path.exists(temp_wav_path):
            self.temp_wav_to_convert = temp_wav_path
            if hasattr(self, 'scheduled_stop_due_to_radio'):
                guiTools.qMessageBox.MessageBox.view(self, "إيقاف التسجيل", "تم إيقاف التسجيل بسبب إيقاف الإذاعة.")
            if self.is_scheduled_recording and self.scheduled_file_path:
                self.aud.setText("جاري تحويل التسجيل المجدول إلى MP3، يرجى الانتظار...")
                self.aud.setFocus()
                self.current_status_text = "جاري تحويل التسجيل المجدول إلى MP3، يرجى الانتظار..."
                self.convert_thread_worker = threading.Thread(target=self.recorder.convert_and_cleanup, args=(temp_wav_path, self.scheduled_file_path), daemon=True)
                self.convert_thread_worker.start()
            else:
                self.convert_and_save_prompt()
        else:
            self.resetRecorderState()

    def convert_and_save_prompt(self):
        filePath, _ = qt.QFileDialog.getSaveFileName(self, "حفظ التسجيل", f"{self.get_current_station_name()}.mp3", "Audio Files (*.mp3);;All Files (*)")
        if filePath:
            self.aud.setText("جاري تحويل الملف إلى MP3، يرجى الانتظار...")
            self.aud.setFocus()
            self.current_status_text = "جاري تحويل الملف إلى MP3، يرجى الانتظار..."
            self.convert_thread_worker = threading.Thread(target=self.recorder.convert_and_cleanup, args=(self.temp_wav_to_convert, filePath), daemon=True)
            self.convert_thread_worker.start()
        else:
            result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل تريد إلغاء حفظ الملف؟", "نعم", "لا")
            if result == 0:
                try: Path(self.temp_wav_to_convert).unlink(missing_ok=True)
                except: pass
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الحفظ.")
                self.resetRecorderState()
            else:
                self.convert_and_save_prompt()
        self.temp_wav_to_convert = None

    @qt2.pyqtSlot(str)
    def recordingError(self, error_msg):
        self.restore_aud_text()
        self.recorder.stop(cleanup_only=True)
        msg = error_msg if error_msg else "حدث خطأ غير متوقع أثناء التسجيل."
        guiTools.qMessageBox.MessageBox.error(self, "خطأ في تسجيل الصوت", msg)
        self.resetRecorderState()

    def resetRecorderState(self):
        if hasattr(self, 'scheduled_stop_due_to_radio'):
            del self.scheduled_stop_due_to_radio
        if self.temp_wav_to_convert:
            try: Path(self.temp_wav_to_convert).unlink(missing_ok=True)
            except: pass
            self.temp_wav_to_convert = None
        self.scheduled_file_path = ""
        self.is_scheduled_recording = False
        self.pause_countdown_on_recording_pause = False
        self.convert_thread_worker = None
        self.countdown_timer.stop()
        self.duration_timer.stop()
        try: self.duration_timer.timeout.disconnect()
        except: pass
        self.startBtn.setVisible(True)
        self.startBtn.setEnabled(True)
        self.scheduleBtn.setVisible(True)
        self.scheduleBtn.setEnabled(True)
        self.scheduleBtn.setText("جدولة التسجيل")
        self.pauseBtn.setVisible(False)
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setVisible(False)
        self.stopBtn.setEnabled(False)
        self.pauseBtn.setText("إيقاف مؤقت")
        self.pauseBtn.setStyleSheet("background-color: #0000AA; color: white; min-height: 40px; font-size: 16px;")
        try: self.pauseBtn.clicked.disconnect()
        except TypeError: pass
        self.pauseBtn.clicked.connect(self.pauseRecording)
        self.current_status_text = self.original_aud_text
        self.restore_aud_text()
