import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from guiTools import speak
import guiTools, os, tempfile, shutil, subprocess, threading, time, uuid
import ujson as json
from pathlib import Path
from settings import app
from functions import audio_manager
from .recorder import WasapiRecorder, SchedulingDialog
from .stations import (
    quran_brotcast, brotcasts_of_reciters, brotcasts_of_tafseer,
    brotcasts_of_suplications, other_brotcasts, set_globals,
    get_global_player, get_global_current_url, get_global_audio_output,
    play_station_by_name
)


class protcasts(qt.QWidget):
    def __init__(self):
        super().__init__()
        global_player = QMediaPlayer()
        global_audio_output = QAudioOutput()
        global_audio_output.setDevice(audio_manager.get_audio_device("broadcasts"))
        global_player.setAudioOutput(global_audio_output)
        global_audio_output.setVolume(1.0)
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
        self.temp_wav_to_convert = None

        self.brotcasts_tab = qt.QTabWidget()
        self.brotcasts_tab.addTab(quran_brotcast(global_audio_output, self), "إذاعات القرآن الكريم")
        self.brotcasts_tab.addTab(brotcasts_of_reciters(global_audio_output, self), "إذاعات القراء")
        self.brotcasts_tab.addTab(brotcasts_of_tafseer(global_audio_output, self), "إذاعات التفاسير")
        self.brotcasts_tab.addTab(brotcasts_of_suplications(global_audio_output, self), "إذاعات الأذكار والأدعية")
        self.brotcasts_tab.addTab(other_brotcasts(global_audio_output, self), "إذاعات إسلامية أخرى")
        self.brotcasts_tab.setStyleSheet("""QTabWidget::pane { border: 1px solid #444; border-radius: 6px; background-color: #1e1e1e; } QTabBar::tab { background: #2b2b2b; color: white; padding: 10px 20px; border: 1px solid #444; border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; min-width: 100px; font-weight: bold; } QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } QTabBar::tab:hover { background: #3a3a3a; }""")

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

        self.fav_info_label = qt.QLabel("يمكنكم إضافة إذاعة إلى قائمة المفضلة أو إزالتها بالضغط على click الأيمن أو زر التطبيقات على الإذاعة المحددة")
        self.fav_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.fav_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.aud = qt.QLabel()
        self.original_aud_text = "لرفع أو خفض الصوت: اضغط في القائمة ثم استخدم Shift + الأسهم، أعلى وأسفل"
        self.current_status_text = self.original_aud_text
        self.aud.setText(self.original_aud_text)
        self.aud.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.aud.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white;")
        self.fav_btn.clicked.connect(self.toggle_favorites)

        info_fav_layout = qt.QHBoxLayout()
        info_fav_layout.addWidget(self.aud, 1)
        info_fav_layout.addWidget(self.fav_btn)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.brotcasts_tab)
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
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
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
        self.start_shortcut.activated.connect(lambda: self.startRecording() if self.startBtn.isEnabled() else None)
        self.pause_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+P"), self)
        self.pause_shortcut.activated.connect(lambda: (self.pauseRecording() if self.pauseBtn.text() == "إيقاف مؤقت" else self.resumeRecording()) if self.pauseBtn.isEnabled() else None)
        self.stop_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+S"), self)
        self.stop_shortcut.activated.connect(lambda: self.stopRecording() if self.stopBtn.isEnabled() else None)
        self.schedule_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+G"), self)
        self.schedule_shortcut.activated.connect(lambda: self.scheduleRecording() if self.scheduleBtn.isEnabled() else None)
        player = get_global_player()
        if player:
            player.playbackStateChanged.connect(self.on_radio_state_changed)

        self.update_favorites_ui_state()

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
        if self.favorites:
            self.fav_list_widget.addItems(self.favorites)
        else:
            self.fav_list_widget.addItem("لا توجد إذاعات في قائمة المفضلة")

    def update_favorites_ui_state(self):
        self.update_favorites_list_widget()
        if self.show_favorites_only:
            self.brotcasts_tab.hide()
            self.fav_list_widget.show()
            self.fav_btn.setText("عرض جميع الإذاعات")
        else:
            self.fav_list_widget.hide()
            self.brotcasts_tab.show()
            self.fav_btn.setText("فتح قائمة المفضلة")

    def toggle_favorites(self):
        self.show_favorites_only = not self.show_favorites_only
        self.save_favorites()
        self.update_favorites_ui_state()

    def toggle_station_favorite(self, station_name):
        if station_name == "لا توجد إذاعات في قائمة المفضلة":
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
        if selected_item and selected_item.text() != "لا توجد إذاعات في قائمة المفضلة":
            play_station_by_name(selected_item.text())

    def on_fav_context_menu(self, pos):
        item = self.fav_list_widget.itemAt(pos)
        if not item:
            item = self.fav_list_widget.currentItem()
        if item and item.text() != "لا توجد إذاعات في قائمة المفضلة":
            self.toggle_station_favorite(item.text())

    def increase_volume_fav(self):
        output = get_global_audio_output()
        if output:
            current_volume = output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.volume_timer.start(1000)

    def decrease_volume_fav(self):
        output = get_global_audio_output()
        if output:
            current_volume = output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.volume_timer.start(1000)

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
             guiTools.qMessageBox.MessageBox.error(self, "عفوا يبدو أن مايكروفون Stereo Mix ليس هو الجهاز الافتراضي", err)
             return
        if self.recorder._running:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", "التسجيل يعمل بالفعل.")
             return
        result = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء التسجيل", "تنبيه هام: سيتم تسجيل جميع الأصوات الصادرة من النظام (الكمبيوتر) فقط، ولن يتم تسجيل أي صوت خارجي (الميكروفون).\n\nهل تريد البدء بالتسجيل الآن؟", "نعم", "لا")
        if result != 0: return
        self.is_scheduled_recording = False
        self.recorder.start()
        self.startBtn.setEnabled(False)
        self.scheduleBtn.setEnabled(False)
        self.pauseBtn.setEnabled(True)
        self.stopBtn.setEnabled(True)

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
             guiTools.qMessageBox.MessageBox.error(self, "عفوا يبدو أن مايكروفون Stereo Mix ليس هو الجهاز الافتراضي", err)
             return
        dlg = SchedulingDialog(self)
        if dlg.exec() == qt.QDialog.DialogCode.Accepted:
            sh, sm, ss, dh, dm, ds = dlg.get_values()
            self.remaining_seconds_to_start = (sh * 3600) + (sm * 60) + ss
            self.remaining_duration_seconds = (dh * 3600) + (dm * 60) + ds
            guiTools.qMessageBox.MessageBox.view(self, "تنبيه", "سيتم تسجيل جميع الأصوات الصادرة من النظام (الكمبيوتر) فقط، ولن يتم تسجيل أي صوت خارجي (الميكروفون).\nإذا تم إيقاف الإذاعة قبل بدء التسجيل أو أثناءه، سيتم إلغاء العملية.")
            filePath, _ = qt.QFileDialog.getSaveFileName(self, "حفظ التسجيل", f"{self.get_current_station_name()}.mp3", "Audio Files (*.mp3);;All Files (*)")
            if filePath:
                self.scheduled_file_path = filePath
                self.is_scheduled_recording = True
                self.startBtn.setEnabled(False)
                self.scheduleBtn.setText("إيقاف جدولة التسجيل")
                self.scheduleBtn.setEnabled(True)
                self.pauseBtn.setEnabled(False)
                self.stopBtn.setEnabled(False)
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
            h = self.remaining_seconds_to_start // 3600
            m = (self.remaining_seconds_to_start % 3600) // 60
            s = self.remaining_seconds_to_start % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            self.aud.setText(f"متبقي على بدء التسجيل: {time_str}")
            self.aud.setFocus()
        else:
            self.countdown_timer.stop()
            if not self.recorder.is_ready():
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر بدء التسجيل المجدول: الجهاز الافتراضي ليس Stereo Mix.")
                self.resetRecorderState()
                return
            self.recorder.start()
            self.pauseBtn.setEnabled(True)
            self.stopBtn.setEnabled(True)
            self.duration_timer.timeout.connect(self.updateDuration)
            self.duration_timer.start(1000)

    def updateDuration(self):
        player = get_global_player()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.handle_scheduled_recording_stop_due_to_radio()
            return
        if self.remaining_duration_seconds > 0:
            self.remaining_duration_seconds -= 1
            h = self.remaining_duration_seconds // 3600
            m = (self.remaining_duration_seconds % 3600) // 60
            s = self.remaining_duration_seconds % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            self.aud.setText(f"متبقي على إيقاف التسجيل: {time_str}")
            self.aud.setFocus()
        else:
            self.duration_timer.stop()
            self.stopRecording()

    def pauseRecording(self):
        self.recorder.pause()
        self.pauseBtn.setText("استئناف")
        self.pauseBtn.setStyleSheet("background-color: #FF8C00; color: white; min-height: 40px; font-size: 16px;")
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

    @qt2.pyqtSlot(str)
    def on_recording_stopped(self, temp_wav_path):
        if temp_wav_path and os.path.exists(temp_wav_path):
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
        guiTools.qMessageBox.MessageBox.error(self, "عفوا يبدو أن مايكروفون Stereo Mix ليس هو الجهاز الافتراضي", msg)
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
        self.convert_thread_worker = None
        self.countdown_timer.stop()
        self.duration_timer.stop()
        try: self.duration_timer.timeout.disconnect()
        except: pass
        self.startBtn.setEnabled(True)
        self.scheduleBtn.setEnabled(True)
        self.scheduleBtn.setText("جدولة التسجيل")
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.pauseBtn.setText("إيقاف مؤقت")
        self.pauseBtn.setStyleSheet("background-color: #0000AA; color: white; min-height: 40px; font-size: 16px;")
        try: self.pauseBtn.clicked.disconnect()
        except TypeError: pass
        self.pauseBtn.clicked.connect(self.pauseRecording)
        self.current_status_text = self.original_aud_text
        self.restore_aud_text()
