import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from guiTools import speak
import guiTools, os, tempfile, shutil, subprocess, threading, time, uuid
from pathlib import Path
from functions import audio_manager
from .recorder import WasapiRecorder, SchedulingDialog
from .stations import quran_brotcast, brotcasts_of_reciters, brotcasts_of_tafseer, brotcasts_of_suplications, other_brotcasts, set_globals, get_global_player, get_global_current_url


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
        self.aud = qt.QLabel()
        self.original_aud_text = "لرفع أو خفض الصوت: اضغط في القائمة ثم استخدم Shift + الأسهم، أعلى وأسفل"
        self.current_status_text = self.original_aud_text
        self.aud.setText(self.original_aud_text)
        self.aud.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.aud.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.brotcasts_tab.setStyleSheet("""QTabWidget::pane { border: 1px solid #444; border-radius: 6px; background-color: #1e1e1e; } QTabBar::tab { background: #2b2b2b; color: white; padding: 10px 20px; border: 1px solid #444; border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; min-width: 100px; font-weight: bold; } QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } QTabBar::tab:hover { background: #3a3a3a; }""")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.brotcasts_tab)
        layout.addSpacing(15)
        layout.addWidget(self.aud)
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

    def startRecording(self):
        if not self.check_is_playing(): return
        if not self.recorder.is_ready():
             self.recorder.error.emit("خطأ في تهيئة المسجل.")
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
            time_str = self.format_time_arabic(h, m, s)
            msg = f"سيتم بدء التسجيل بعد {time_str}"
            self.aud.setText(msg)
            self.current_status_text = msg
        else:
            self.countdown_timer.stop()
            if not self.recorder.is_ready():
                self.handle_scheduled_recording_stop_due_to_radio()
                self.recorder.error.emit("فشل بدء التسجيل المجدول: المسجل غير جاهز.")
                return
            self.recorder.start()
            self.scheduleBtn.setText("جدولة التسجيل")
            self.scheduleBtn.setEnabled(False)
            self.stopBtn.setEnabled(True)
            self.pauseBtn.setEnabled(True)
            try: self.duration_timer.timeout.disconnect()
            except: pass
            self.duration_timer.timeout.connect(self.updateDurationCountdown)
            self.duration_timer.start(1000)
            self.updateDurationCountdown()

    def updateDurationCountdown(self):
        player = get_global_player()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.handle_scheduled_recording_stop_due_to_radio()
            return
        if self.remaining_duration_seconds > 0:
            self.remaining_duration_seconds -= 1
            h = self.remaining_duration_seconds // 3600
            m = (self.remaining_duration_seconds % 3600) // 60
            s = self.remaining_duration_seconds % 60
            time_str = self.format_time_arabic(h, m, s)
            msg = f"جاري التسجيل... متبقي {time_str} لاكتمال التسجيل"
            self.aud.setText(msg)
            self.current_status_text = msg
        else:
            self.stopRecording(skip_save_dialog=False)

    def format_time_arabic(self, h, m, s):
        parts = []
        if h == 1: parts.append("ساعة واحدة")
        elif h == 2: parts.append("ساعتان")
        elif 3 <= h <= 10: parts.append(f"{h} ساعات")
        elif h > 10: parts.append(f"{h} ساعة")
        if m == 1: parts.append("دقيقة واحدة")
        elif m == 2: parts.append("دقيقتان")
        elif 3 <= m <= 10: parts.append(f"{m} دقائق")
        elif m > 10: parts.append(f"{m} دقيقة")
        if s == 1: parts.append("ثانية واحدة")
        elif s == 2: parts.append("ثانيتان")
        elif 3 <= s <= 10: parts.append(f"{s} ثواني")
        elif s > 10: parts.append(f"{s} ثانية")
        return " و ".join(parts) if parts else "الآن"

    def check_is_playing(self):
        player = get_global_player()
        current_url = get_global_current_url()
        if not player or player.playbackState() != QMediaPlayer.PlaybackState.PlayingState or not current_url:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "يجب تشغيل إذاعة أولاً لبدء التسجيل.")
            return False
        return True

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

    def stopRecording(self, skip_save_dialog=False):
        if not self.recorder._running and not self.countdown_timer.isActive(): return
        self.startBtn.setEnabled(False)
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.scheduleBtn.setEnabled(True)
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
            self.restore_aud_text()
            guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الجدولة.")
            self.resetRecorderState()
            return
        if self.duration_timer.isActive():
            self.duration_timer.stop()
            try: self.duration_timer.timeout.disconnect()
            except: pass
        if not self.recorder._running: return
        if self.is_scheduled_recording and self.scheduled_file_path and skip_save_dialog:
            self.aud.setText("تم إيقاف التسجيل المجدول بنجاح.")
            self.current_status_text = "تم إيقاف التسجيل المجدول بنجاح."
            self.is_scheduled_recording = False
            self.scheduled_file_path = ""
            self.recorder.stop(cleanup_only=True)
            return
        elif self.is_scheduled_recording and self.scheduled_file_path:
            self.aud.setText("تم إيقاف التسجيل. جاري تحويل الملف المجدول...")
            self.current_status_text = "تم إيقاف التسجيل. جاري تحويل الملف المجدول..."
            self.is_scheduled_recording = False
            self.recorder.stop(cleanup_only=False)
            return
        self.aud.setText("جاري إيقاف التسجيل...")
        self.current_status_text = "جاري إيقاف التسجيل..."
        self.recorder.stop(cleanup_only=False)
    @qt2.pyqtSlot(str, str)

    def on_recording_stopped(self, status, path):
        self.restore_aud_text()
        if status == "STOPPED":
            if hasattr(self, 'scheduled_stop_due_to_radio') and self.scheduled_stop_due_to_radio:
                self.scheduled_stop_due_to_radio = False
                if self.scheduled_file_path:
                    self.aud.setText("جاري تحويل الملف إلى MP3، يرجى الانتظار...")
                    self.current_status_text = "جاري تحويل الملف إلى MP3، يرجى الانتظار..."
                    self.convert_thread_worker = threading.Thread(target=self.recorder.convert_and_cleanup, args=(path, self.scheduled_file_path), daemon=True)
                    self.convert_thread_worker.start()
                else:
                    self.temp_wav_to_convert = path
                    self.convert_and_save_prompt()
            else:
                self.temp_wav_to_convert = path
                self.convert_and_save_prompt()
        elif status == "CONVERTED":
            if hasattr(self, 'scheduled_stop_due_to_radio') and self.scheduled_stop_due_to_radio:
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", "تم حفظ الملف بنجاح في المسار المحدد.")
            else:
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", "تم حفظ الملف بنجاح.")
            self.resetRecorderState()
        elif status == "CLEANUP_ONLY":
            self.resetRecorderState()
        elif status == "FAILED":
            self.resetRecorderState()

    def convert_and_save_prompt(self):
        if self.temp_wav_to_convert is None: return
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
        if not self.startBtn.isEnabled() or self.countdown_timer.isActive():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في التسجيل", "يبدو أن جهاز تسجيل صوت الكمبيوتر stereo mix لا يعمل، لتشغيله اتبع الخطوات التالية\n\n1 فتح قائمة Run عن طريق الاختصار Windows + R ثم اكتب هذا الأمر:\nrundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,1\n2 اذهب إلى تبويبة التسجيل Recording واختر منها Stereo Mix ثم اضغط عليه بزر الفأرة الأيمن أو زر التطبيقات واختر Enable ثم اضغط OK.\nلمن واجه أي مشكلة يمكنه التواصل معي على حسابي في تليجرام من قسم (عن المطور) في قائمة المزيد من الخيارات.")
        self.resetRecorderState()

    def resetRecorderState(self):
        if hasattr(self, 'scheduled_stop_due_to_radio'):
            del self.scheduled_stop_due_to_radio
        if self.temp_wav_to_convert:
            try: Path(self.temp_wav_to_convert).unlink(missing_ok=True)
            except: pass
            self.temp_wav_to_convert = None
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
