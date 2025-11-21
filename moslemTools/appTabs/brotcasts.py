import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from guiTools import speak
import guiTools, os, tempfile, shutil, subprocess, threading, time, uuid
from pathlib import Path
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
except ImportError:
    sd = None
    sf = None
    np = None
global_player = None
global_audio_output = None
global_current_url = None
TMP_DIR = Path(tempfile.gettempdir()) / "radio_recordings_temp"
TMP_DIR.mkdir(exist_ok=True)
class WasapiRecorder(qt2.QObject):
    error = qt2.pyqtSignal(str)
    recording_stopped = qt2.pyqtSignal(str)
    def __init__(self, ffmpeg_path="ffmpeg"):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self._running = False
        self._paused = False
        self._thread = None
        self._stream = None
        self._temp_wav_path = None
        self._sf_handle = None
        self._lock = threading.Lock()
        self.samplerate = None
        self.channels = None
        self.device_id = None
        self._is_ready = False
        if sd is None or sf is None or np is None:
            self.error.emit("مكتبات التسجيل غير مثبتة.")
            return
        try:
            devices = sd.query_devices()
            found_device = False
            target_names = ["stereo mix", "ستيريو", "what u hear"]
            for i, device in enumerate(devices):
                device_name_lower = device['name'].lower()
                if device['max_input_channels'] > 0:
                    if any(t in device_name_lower for t in target_names):
                        self.device_id = i
                        self.channels = device['max_input_channels']
                        self.samplerate = int(device['default_samplerate'])
                        self._is_ready = True
                        found_device = True
                        break
            if not found_device:
                msg = "لم يتم العثور على جهاز 'Stereo Mix' أو 'ستيريو ميكس'.\n"
                msg += "لحل هذه المشكلة وتفعيل التسجيل، يرجى اتباع الخطوات التالية بدقة:\n"
                msg += "1. انتقل إلى لوحة التحكم (Control Panel) في نظام الويندوز.\n"
                msg += "2. اختر أيقونة 'الصوت' (Sound).\n"
                msg += "3. انتقل إلى التبويب المسمى 'تسجيل' (Recording) في الأعلى.\n"
                msg += "4. انقر بزر الماوس الأيمن في أي مساحة فارغة داخل القائمة واختر 'إظهار الأجهزة المعطلة' (Show Disabled Devices).\n"
                msg += "5. سيظهر لك خيار باسم 'Stereo Mix'، انقر عليه بزر الماوس الأيمن واختر 'تمكين' (Enable).\n"
                msg += "6. يفضل النقر عليه مرة أخرى واختيار 'تعيين كجهاز افتراضي' (Set as Default Device).\n"
                msg += "7. بعد ذلك، أعد تشغيل البرنامج وحاول التسجيل مرة أخرى."
                self.error.emit(msg)
                return
        except Exception as e:
            self.error.emit(f"خطأ غير متوقع: {e}")
            self._is_ready = False
    def is_ready(self):
        return self._is_ready
    def _callback(self, indata, frames, time_info, status):
        with self._lock:
            if self._running and not self._paused and self._sf_handle:
                try:
                    self._sf_handle.write(indata.copy())
                except Exception:
                    pass
    def _run_stream(self):
        try:
            self._temp_wav_path = TMP_DIR / f"rec_{uuid.uuid4().hex}.wav"
            self._sf_handle = sf.SoundFile(str(self._temp_wav_path), mode="w", samplerate=self.samplerate, channels=self.channels)
        except Exception as e:
            self.error.emit(f"فشل إنشاء ملف WAV: {e}")
            return
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32', blocksize=2048, callback=self._callback, device=self.device_id, latency='low') as self._stream:
                while self._running:
                    time.sleep(0.05)
        except Exception as e:
            self.error.emit(f"خطأ التسجيل: {e}")
        with self._lock:
            if self._sf_handle:
                self._sf_handle.close()
                self._sf_handle = None
    def start(self):
        if not self._is_ready:
            return
        with self._lock:
            if self._running: return
            self._running = True
            self._paused = False
        self._thread = threading.Thread(target=self._run_stream, daemon=True)
        self._thread.start()
    def pause(self):
        with self._lock:
            self._paused = True
    def resume(self):
        with self._lock:
            self._paused = False
    def stop(self, output_filename=None):
        with self._lock:
            if not self._running: return
            self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        temp_file = self._temp_wav_path
        self._temp_wav_path = None
        if not temp_file or not temp_file.exists():
            self.error.emit("لم يتم العثور على ملف التسجيل.")
            return
        if output_filename is None:
            try: temp_file.unlink(missing_ok=True)
            except: pass
            self.recording_stopped.emit("CLEANUP_ONLY")
            return
        try:
            final_path = Path(output_filename)
            cmd = [self.ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp_file), "-c:a", "libmp3lame", "-b:a", "192k", str(final_path)]
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600, text=True, encoding='utf-8')
            if proc.returncode != 0:
                self.error.emit(f"فشل التحويل: {proc.stderr}")
                return
            self.recording_stopped.emit(str(final_path))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try: temp_file.unlink(missing_ok=True)
            except: pass
class SchedulingDialog(qt.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.resize(500, 250)
        self.setWindowTitle("جدولة التسجيل")
        layout = qt.QVBoxLayout(self)
        main_h_layout = qt.QHBoxLayout()
        start_v_layout = qt.QVBoxLayout()
        dur_v_layout = qt.QVBoxLayout()
        self.start_label = qt.QLabel("█ وقت بدء التسجيل █")
        self.start_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.start_label.setStyleSheet("font-weight: bold; color: #0078d7;")
        start_v_layout.addWidget(self.start_label)
        self.start_h_label = qt.QLabel("بدء التسجيل بعد: بالساعات")
        self.start_h_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_h_label)
        self.start_h_spin = qt.QSpinBox()
        self.start_h_spin.setRange(0, 24)
        self.start_h_spin.setAccessibleName("بدء التسجيل بعد بالساعات")
        self.start_h_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_h_spin)
        self.start_m_label = qt.QLabel("بدء التسجيل بعد: بالدقائق")
        self.start_m_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_m_label)
        self.start_m_spin = qt.QSpinBox()
        self.start_m_spin.setRange(0, 59)
        self.start_m_spin.setAccessibleName("بدء التسجيل بعد بالدقائق")
        self.start_m_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_m_spin)
        self.start_s_label = qt.QLabel("بدء التسجيل بعد: بالثواني")
        self.start_s_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_s_label)
        self.start_s_spin = qt.QSpinBox()
        self.start_s_spin.setRange(0, 59)
        self.start_s_spin.setAccessibleName("بدء التسجيل بعد بالثواني")
        self.start_s_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        start_v_layout.addWidget(self.start_s_spin)
        self.dur_label = qt.QLabel("█ مدة التسجيل █")
        self.dur_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.dur_label.setStyleSheet("font-weight: bold; color: #008000;")
        dur_v_layout.addWidget(self.dur_label)
        self.dur_h_label = qt.QLabel("مدة التسجيل: بالساعات")
        self.dur_h_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        dur_v_layout.addWidget(self.dur_h_label)
        self.dur_h_spin = qt.QSpinBox()
        self.dur_h_spin.setRange(0, 24)
        self.dur_h_spin.setAccessibleName("مدة التسجيل بالساعات")
        self.dur_h_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        dur_v_layout.addWidget(self.dur_h_spin)
        self.dur_m_label = qt.QLabel("مدة التسجيل: بالدقائق")
        self.dur_m_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        dur_v_layout.addWidget(self.dur_m_label)
        self.dur_m_spin = qt.QSpinBox()
        self.dur_m_spin.setRange(0, 300)
        self.dur_m_spin.setAccessibleName("مدة التسجيل بالدقائق")
        self.dur_m_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        dur_v_layout.addWidget(self.dur_m_spin)
        self.dur_s_label = qt.QLabel("مدة التسجيل: بالثواني")
        self.dur_s_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        dur_v_layout.addWidget(self.dur_s_label)
        self.dur_s_spin = qt.QSpinBox()
        self.dur_s_spin.setRange(0, 59)
        self.dur_s_spin.setAccessibleName("مدة التسجيل بالثواني")
        dur_v_layout.addWidget(self.dur_s_spin)
        main_h_layout.addLayout(start_v_layout)
        line = qt.QFrame()
        line.setFrameShape(qt.QFrame.Shape.VLine)
        line.setFrameShadow(qt.QFrame.Shadow.Sunken)
        main_h_layout.addWidget(line)
        main_h_layout.addLayout(dur_v_layout)
        layout.addLayout(main_h_layout)
        line2 = qt.QFrame()
        line2.setFrameShape(qt.QFrame.Shape.HLine)
        line2.setFrameShadow(qt.QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        self.warning_label = qt.QLabel("تنبيه: إذا تم إيقاف الإذاعة، سيتم إلغاء جدولة التسجيل.")
        self.warning_label.setStyleSheet("color: #8B0000; font-weight: bold; margin-top: 10px;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.warning_label)
        self.OKBTN = guiTools.QPushButton("موافق")
        self.OKBTN.clicked.connect(self.validate_and_accept)
        self.OKBTN.setStyleSheet("QPushButton { background-color: #008000; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px; }")
        self.cancelBTN = guiTools.QPushButton("إلغاء")
        self.cancelBTN.clicked.connect(self.reject)
        self.cancelBTN.setStyleSheet("QPushButton { background-color: #8B0000; color: white; border-radius: 4px; padding: 8px 20px; font-size: 14px; }")
        buttonsLayout = qt.QHBoxLayout()
        buttonsLayout.addWidget(self.OKBTN)
        buttonsLayout.addWidget(self.cancelBTN)
        wrapper = qt.QHBoxLayout()
        wrapper.addLayout(buttonsLayout)
        wrapper.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(wrapper)
        qt1.QShortcut("Escape", self).activated.connect(self.reject)
    def validate_and_accept(self):
        total_start_time = (self.start_h_spin.value() * 3600) + (self.start_m_spin.value() * 60) + self.start_s_spin.value()
        if total_start_time == 0:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ في الإدخال", "يجب تحديد وقت لبدء التسجيل (ثانية واحدة على الأقل).")
             return
        total_duration = (self.dur_h_spin.value() * 3600) + (self.dur_m_spin.value() * 60) + self.dur_s_spin.value()
        if total_duration == 0:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ في الإدخال", "يجب تحديد مدة للتسجيل (ثانية واحدة على الأقل).")
             return
        self.accept()
    def get_values(self):
        return (self.start_h_spin.value(), self.start_m_spin.value(), self.start_s_spin.value(),
                self.dur_h_spin.value(), self.dur_m_spin.value(), self.dur_s_spin.value())
class other_brotcasts(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_other = qt.QListWidget()
        self.list_of_other.setSpacing(3)
        self.list_of_other.setStyleSheet(style_sheet)
        self.list_of_other.itemActivated.connect(self.play)
        self.list_of_other.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_other.addItem("تَكْبِيرَات العيد")
        self.list_of_other.addItem("الرقية الشرعية")
        self.list_of_other.addItem("إذاعة الصحابة")
        self.list_of_other.addItem("فتاوى إبن باز")
        self.list_of_other.addItem("صور من حياة الصحابة")
        self.list_of_other.addItem("إذاعة عمر عبد الكافي")
        self.list_of_other.addItem("السُنَّة السلفية")
        self.list_of_other.addItem("في ظِلال السيرة النبوية")
        self.list_of_other.addItem("فتاوى ابن العُثيمين")
        self.list_of_other.addItem("العاصمة أونلاين")
        self.list_of_other.addItem("الإحسان")
        self.list_of_other.addItem("الإستقامى")
        self.list_of_other.addItem("الفتح")
        self.list_of_other.addItem("المرأة المسلمة")
        self.list_of_other.addItem("اللغة العربية وعلومها")
        self.list_of_other.addItem("المهارات الحياتية والعلوم التربوية")
        self.list_of_other.addItem("السلوك والآداب والأخلاق ومحاسن الأعمال")
        self.list_of_other.addItem("التوعية الاجتماعية")
        self.list_of_other.addItem("الإذاعة الفقهية")
        self.list_of_other.addItem("الحج")
        self.list_of_other.addItem("رمضان المبارك")
        self.list_of_other.addItem("التراجم والتاريخ والسير")
        self.list_of_other.addItem("الفكر والدعوة والثقافة الإسلامية")
        self.list_of_other.addItem("السيرة النبوية وقصص القرآن والأنبياء والصحابة")
        self.list_of_other.addItem("الحديث وعلومه")
        self.list_of_other.addItem("العقيدة والتوحيد")
        self.list_of_other.addItem("علوم القرآن الكريم")
        self.list_of_other.addItem("راديو كبار العلماء")
        self.list_of_other.addItem("الدكتور سعد الحميد")
        self.list_of_other.addItem("الدكتور خالد الجريسي")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_other)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_other)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_other)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_other.currentItem()
        if not selected_item: return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "تَكْبِيرَات العيد": url_to_play = qt2.QUrl("http://live.mp3quran.net:9728")
        elif station_name == "الرقية الشرعية": url_to_play = qt2.QUrl("http://live.mp3quran.net:9936")
        elif station_name == "إذاعة الصحابة": url_to_play = qt2.QUrl("http://s5.voscast.com:10130/;stream1603343063302/1")
        elif station_name == "فتاوى إبن باز": url_to_play = qt2.QUrl("https://qurango.net/radio/alaikhtiarat_alfiqhayh_bin_baz")
        elif station_name == "صور من حياة الصحابة": url_to_play = qt2.QUrl("http://live.mp3quran.net:8028")
        elif station_name == "إذاعة عمر عبد الكافي": url_to_play = qt2.QUrl("http://node-28.zeno.fm/66geh5zntp8uv?zs=u1rolhJRRS-k08Aw1jvY8Q&rj-tok=AAABgNAugTEAylkfGQGe4UQM-w&rj-ttl=5")
        elif station_name == "السُنَّة السلفية": url_to_play = qt2.QUrl("http://andromeda.shoutca.st:8189/live")
        elif station_name == "في ظِلال السيرة النبوية": url_to_play = qt2.QUrl("https://Qurango.net/radio/fi_zilal_alsiyra")
        elif station_name == "فتاوى ابن العُثيمين": url_to_play = qt2.QUrl("http://live.mp3quran.net:8014")
        elif station_name == "العاصمة أونلاين": url_to_play = qt2.QUrl("https://asima.out.airtime.pro/asima_a")
        elif station_name == "الإحسان": url_to_play = qt2.QUrl("https://cdn.bmstudiopk.com/alehsaan/live/playlist.m3u8")
        elif station_name == "الإستقامى": url_to_play = qt2.QUrl("https://jmc-live.ercdn.net/alistiqama/alistiqama.m3u8")
        elif station_name == "الفتح": url_to_play = qt2.QUrl("https://alfat7-q.com:5443/LiveApp/streams/986613792230697141226562.m3u8")
        elif station_name == "المرأة المسلمة": url_to_play = qt2.QUrl("https://radio.alukah.net/almarah")
        elif station_name == "اللغة العربية وعلومها": url_to_play = qt2.QUrl("https://radio.alukah.net/arabiyyah")
        elif station_name == "المهارات الحياتية والعلوم التربوية": url_to_play = qt2.QUrl("https://radio.alukah.net/maharat")
        elif station_name == "السلوك والآداب والأخلاق ومحاسن الأعمال": url_to_play = qt2.QUrl("https://radio.alukah.net/assuluk")
        elif station_name == "التوعية الاجتماعية": url_to_play = qt2.QUrl("https://radio.alukah.net/attawiyy")
        elif station_name == "الإذاعة الفقهية": url_to_play = qt2.QUrl("https://radio.alukah.net/fiqhiyyah")
        elif station_name == "الحج": url_to_play = qt2.QUrl("https://radio.alukah.net/hajj")
        elif station_name == "رمضان المبارك": url_to_play = qt2.QUrl("https://radio.alukah.net/ramdan")
        elif station_name == "التراجم والتاريخ والسير": url_to_play = qt2.QUrl("https://radio.alukah.net/tarajim")
        elif station_name == "الفكر والدعوة والثقافة الإسلامية": url_to_play = qt2.QUrl("https://radio.alukah.net/alfikr")
        elif station_name == "السيرة النبوية وقصص القرآن والأنبياء والصحابة": url_to_play = qt2.QUrl("https://radio.alukah.net/sirah")
        elif station_name == "الحديث وعلومه": url_to_play = qt2.QUrl("https://radio.alukah.net/hadith")
        elif station_name == "العقيدة والتوحيد": url_to_play = qt2.QUrl("https://radio.alukah.net/aqidah")
        elif station_name == "علوم القرآن الكريم": url_to_play = qt2.QUrl("https://radio.alukah.net/ulumalquran")
        elif station_name == "راديو كبار العلماء": url_to_play = qt2.QUrl("https://radio.alukah.net/ulama")
        elif station_name == "الدكتور سعد الحميد": url_to_play = qt2.QUrl("https://radio.alukah.net/humayid")
        elif station_name == "الدكتور خالد الجريسي": url_to_play = qt2.QUrl("https://radio.alukah.net/aljeraisy")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
class brotcasts_of_suplications(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_adhkar = qt.QListWidget()
        self.list_of_adhkar.setSpacing(3)
        self.list_of_adhkar.setStyleSheet(style_sheet)
        self.list_of_adhkar.itemActivated.connect(self.play)
        self.list_of_adhkar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_adhkar.addItem("أذكار الصباح")
        self.list_of_adhkar.addItem("أذكار المساء")
        self.list_of_adhkar.addItem("أدعية وأذكار يومية")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_adhkar)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_adhkar)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_adhkar)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_adhkar.currentItem()
        if not selected_item: return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "أذكار الصباح": url_to_play = qt2.QUrl("https://qurango.net/radio/athkar_sabah")
        elif station_name == "أذكار المساء": url_to_play = qt2.QUrl("https://qurango.net/radio/athkar_masa")
        elif station_name == "أدعية وأذكار يومية": url_to_play = qt2.QUrl("https://radio.alukah.net/adiyyaha")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
class brotcasts_of_tafseer(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_tafseer = qt.QListWidget()
        self.list_of_tafseer.setSpacing(3)
        self.list_of_tafseer.setStyleSheet(style_sheet)
        self.list_of_tafseer.itemActivated.connect(self.play)
        self.list_of_tafseer.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_tafseer.addItem("تفسير النابلسي")
        self.list_of_tafseer.addItem("تفسير الشعراوي")
        self.list_of_tafseer.addItem("الله أكبر لتفسير الشعراوي")
        self.list_of_tafseer.addItem("المختصر في التفسير")
        self.list_of_tafseer.addItem("إذاعة التفسير")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_tafseer)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_tafseer)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_tafseer)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_tafseer.currentItem()
        if not selected_item: return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "تفسير النابلسي": url_to_play = qt2.QUrl("http://206.72.199.179:9992/;stream.mp3")
        elif station_name == "تفسير الشعراوي": url_to_play = qt2.QUrl("http://206.72.199.180:9990/;")
        elif station_name == "الله أكبر لتفسير الشعراوي": url_to_play = qt2.QUrl("http://66.45.232.132:9996/;stream.mp3")
        elif station_name == "المختصر في التفسير": url_to_play = qt2.QUrl("http://live.mp3quran.net:9698")
        elif station_name == "إذاعة التفسير": url_to_play = qt2.QUrl("http://live.mp3quran.net:9718")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
class brotcasts_of_reciters(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_reciters = qt.QListWidget()
        self.list_of_reciters.setSpacing(3)
        self.list_of_reciters.setStyleSheet(style_sheet)
        self.list_of_reciters.itemActivated.connect(self.play)
        self.list_of_reciters.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_reciters.addItem("إذاعة القُراء")
        self.list_of_reciters.addItem("القارء أبو بكر الشاطري")
        self.list_of_reciters.addItem("القارئ إدريس أبكر")
        self.list_of_reciters.addItem("القارئ سعود الشريم")
        self.list_of_reciters.addItem("القارئ صلاح البدير")
        self.list_of_reciters.addItem("القارئ عبد الباسط عبد الصمد")
        self.list_of_reciters.addItem("القارئ عبد الرحمن السديس")
        self.list_of_reciters.addItem("القارئ ماهر المعيقلي")
        self.list_of_reciters.addItem("القارئ محمود خليل الحُصَري")
        self.list_of_reciters.addItem("القارئ محمود خليل الحُصَري القرآن بالتحقيق")
        self.list_of_reciters.addItem("القارئ محمود علي البنا القرآن بالتحقيق")
        self.list_of_reciters.addItem("مشاري راشد")
        self.list_of_reciters.addItem("القارئ مصطفى رعد العزاوي")
        self.list_of_reciters.addItem("القارئ مصطفى اللاهونِي")
        self.list_of_reciters.addItem("القارئ يحيى حوا")
        self.list_of_reciters.addItem("القارئ يوسف بن نوح")
        self.list_of_reciters.addItem("القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع")
        self.list_of_reciters.addItem("القارئ طارق دعوب- رواية قالون عن نافع")
        self.list_of_reciters.addItem("القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع")
        self.list_of_reciters.addItem("القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني")
        self.list_of_reciters.addItem("القارئ  محمد عبد الحكيم قِراءة ابن كثير")
        self.list_of_reciters.addItem("القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر")
        self.list_of_reciters.addItem("القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ عبد الرشيد صوفي- رواية خلف عن حمزة")
        self.list_of_reciters.addItem("القارئ محمود الشيمي- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي")
        self.list_of_reciters.addItem("القارئ ياسر المزروعي قِراءة يعقوب")
        self.list_of_reciters.addItem("القارئ الشيخ العيون الكوشي - ورش عن نافع")
        self.list_of_reciters.addItem("القارِء الشيخ سعد الغامدي")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_reciters)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_reciters)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_reciters)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_reciters.currentItem()
        if not selected_item: return
        reciter_name = selected_item.text()
        url_to_play = None
        if reciter_name == "إذاعة القُراء": url_to_play = qt2.QUrl("http://live.mp3quran.net:8006")
        elif reciter_name == "القارء أبو بكر الشاطري": url_to_play = qt2.QUrl("http://live.mp3quran.net:9966")
        elif reciter_name == "القارئ إدريس أبكر": url_to_play = qt2.QUrl("http://live.mp3quran.net:9968")
        elif reciter_name == "القارئ سعود الشريم": url_to_play = qt2.QUrl("http://live.mp3quran.net:9986")
        elif reciter_name == "القارئ صلاح البدير": url_to_play = qt2.QUrl("https://qurango.net/radio/salah_albudair")
        elif reciter_name == "القارئ عبد الباسط عبد الصمد": url_to_play = qt2.QUrl("http://live.mp3quran.net:9980")
        elif reciter_name == "القارئ عبد الرحمن السديس": url_to_play = qt2.QUrl("http://live.mp3quran.net:9988")
        elif reciter_name == "القارئ ماهر المعيقلي": url_to_play = qt2.QUrl("http://live.mp3quran.net:9996")
        elif reciter_name == "القارئ محمود خليل الحُصَري": url_to_play = qt2.QUrl("http://live.mp3quran.net:9958/;")
        elif reciter_name == "القارئ محمود خليل الحُصَري القرآن بالتحقيق": url_to_play = qt2.QUrl("https://Qurango.net/radio/mahmoud_khalil_alhussary_mojawwad")
        elif reciter_name == "القارئ محمود علي البنا القرآن بالتحقيق": url_to_play = qt2.QUrl("https://qurango.net/radio/mahmoud_ali__albanna_mojawwad")
        elif reciter_name == "مشاري راشد": url_to_play = qt2.QUrl("http://live.mp3quran.net:9982")
        elif reciter_name == "القارئ مصطفى رعد العزاوي": url_to_play = qt2.QUrl("https://Qurango.net/radio/mustafa_raad_alazawy")
        elif reciter_name == "القارئ مصطفى اللاهونِي": url_to_play = qt2.QUrl("http://live.mp3quran.net:9798")
        elif reciter_name == "القارئ يحيى حوا": url_to_play = qt2.QUrl("https://Qurango.net/radio/yahya_hawwa")
        elif reciter_name == "القارئ يوسف بن نوح": url_to_play = qt2.QUrl("https://Qurango.net/radio/yousef_bin_noah_ahmad")
        elif reciter_name == "القارئ أحمد خضر الطرابلسي- رواية قالون عن نافع": url_to_play = qt2.QUrl("https://Qurango.net/radio/ahmad_khader_altarabulsi")
        elif reciter_name == "القارئ طارق دعوب- رواية قالون عن نافع": url_to_play = qt2.QUrl("https://qurango.net/radio/tareq_abdulgani_daawob")
        elif reciter_name == "القارئ عبد الباسط عبد الصمد- رواية ورش عن نافع": url_to_play = qt2.QUrl("http://live.mp3quran.net:9956")
        elif reciter_name == "القارئ محمد عبد الكريم رواية ورش عن نافع من طريق أبي بكر الأصبهاني": url_to_play = qt2.QUrl("https://qurango.net/radio/mohammad_abdullkarem_alasbahani")
        elif reciter_name == "القارئ  محمد عبد الحكيم قِراءة ابن كثير": url_to_play = qt2.QUrl("https://Qurango.net/radio/mohammad_alabdullah_albizi")
        elif reciter_name == "القارئ الفاتح محمد الزُبَيْري- رواية الدُوري عن أبي عمرو": url_to_play = qt2.QUrl("https://Qurango.net/radio/alfateh_alzubair")
        elif reciter_name == "القارئ مفتاح السلطني- رواية الدُوري عن أبي عمرو": url_to_play = qt2.QUrl("https://Qurango.net/radio/muftah_alsaltany_aldori_an_abi_amr")
        elif reciter_name == "القارئ مفتاح السلطني- رواية ابن ذكوان عن ابن عامر": url_to_play = qt2.QUrl("https://qurango.net/radio/muftah_alsaltany_ibn_thakwan_an_ibn_amr")
        elif reciter_name == "القارئ محمد عبد الحكيم سعيد- رواية الدُوري عن الكِسائي": url_to_play = qt2.QUrl("https://Qurango.net/radio/mohammad_alabdullah_aldorai")
        elif reciter_name == "القارئ عبد الرشيد صوفي- رواية خلف عن حمزة": url_to_play = qt2.QUrl("https://Qurango.net/radio/abdulrasheed_soufi_khalaf")
        elif reciter_name == "القارئ محمود الشيمي- رواية الدُوري عن الكِسائي": url_to_play = qt2.QUrl("https://Qurango.net/radio/mahmood_alsheimy")
        elif reciter_name == "القارئ مفتاح السلطني- رواية الدُوري عن الكِسائي": url_to_play = qt2.QUrl("https://Qurango.net/radio/muftah_alsaltany_aldorai")
        elif reciter_name == "القارئ ياسر المزروعي قِراءة يعقوب": url_to_play = qt2.QUrl("https://Qurango.net/radio/yasser_almazroyee")
        elif reciter_name == "القارئ الشيخ العيون الكوشي - ورش عن نافع": url_to_play = qt2.QUrl("http://live.mp3quran.net:9912/;")
        elif reciter_name == "القارِء الشيخ سعد الغامدي": url_to_play = qt2.QUrl("https://qurango.net/radio/saad_alghamdi")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
class quran_brotcast(qt.QWidget):
    def __init__(self, audio_output_instance, parent_widget):
        super().__init__()
        self.audio_output = audio_output_instance
        self.parent_widget = parent_widget
        style_sheet = "QListWidget::item { font-weight: bold; font-size: 12pt; }"
        self.list_of_quran_brotcasts = qt.QListWidget()
        self.list_of_quran_brotcasts.setSpacing(3)
        self.list_of_quran_brotcasts.setStyleSheet(style_sheet)
        self.list_of_quran_brotcasts.itemActivated.connect(self.play)
        self.list_of_quran_brotcasts.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من نابلِس")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من القاهرة")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من السعودية")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من تونس")
        self.list_of_quran_brotcasts.addItem("إذاعة دُبَيْ للقرآن الكريم")
        self.list_of_quran_brotcasts.addItem("تلاوات خاشعة")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من أستراليا")
        self.list_of_quran_brotcasts.addItem("إذاعة طيبة للقرآن الكريم من السودان")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من مصر")
        self.list_of_quran_brotcasts.addItem("إذاعة القرآن الكريم من فَلَسطين")
        self.list_of_quran_brotcasts.addItem("إذاعة تراتيل")
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.list_of_quran_brotcasts)
        self.volume_up_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Up"), self.list_of_quran_brotcasts)
        self.volume_up_shortcut.activated.connect(self.increase_volume)
        self.volume_down_shortcut = qt1.QShortcut(qt1.QKeySequence("Shift+Down"), self.list_of_quran_brotcasts)
        self.volume_down_shortcut.activated.connect(self.decrease_volume)
    def play(self):
        global global_current_url, global_player
        selected_item = self.list_of_quran_brotcasts.currentItem()
        if not selected_item: return
        station_name = selected_item.text()
        url_to_play = None
        if station_name == "إذاعة القرآن الكريم من نابلِس": url_to_play = qt2.QUrl("http://www.quran-radio.org:8002/;stream.mp3")
        elif station_name == "إذاعة القرآن الكريم من القاهرة": url_to_play = qt2.QUrl("http://n0e.radiojar.com/8s5u5tpdtwzuv?rj-ttl=5&rj-tok=AAABeel-l8gApvlPoJcG2WWz8A")
        elif station_name == "إذاعة القرآن الكريم من السعودية": url_to_play = qt2.QUrl("https://stream.radiojar.com/4wqre23fytzuv")
        elif station_name == "إذاعة القرآن الكريم من تونس": url_to_play = qt2.QUrl("http://5.135.194.225:8000/live")
        elif station_name == "إذاعة دُبَيْ للقرآن الكريم": url_to_play = qt2.QUrl("http://uk5.internet-radio.com:8079/stream")
        elif station_name == "تلاوات خاشعة": url_to_play = qt2.QUrl("http://live.mp3quran.net:9992")
        elif station_name == "إذاعة القرآن الكريم من أستراليا": url_to_play = qt2.QUrl("http://listen.qkradio.com.au:8382/listen.mp3")
        elif station_name == "إذاعة طيبة للقرآن الكريم من السودان": url_to_play = qt2.QUrl("http://live.mp3quran.net:9960")
        elif station_name == "إذاعة القرآن الكريم من مصر": url_to_play = qt2.QUrl("http://66.45.232.131:9994/;stream")
        elif station_name == "إذاعة القرآن الكريم من فَلَسطين": url_to_play = qt2.QUrl("http://streamer.mada.ps:8029/quranfm")
        elif station_name == "إذاعة تراتيل": url_to_play = qt2.QUrl("http://live.mp3quran.net:8030")
        if url_to_play:
            if global_player.isPlaying() and global_current_url == url_to_play:
                global_player.stop()
                global_current_url = None
            else:
                global_player.stop()
                global_player.setSource(url_to_play)
                global_player.play()
                global_current_url = url_to_play
    def increase_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = min(1.0, current_volume + 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
    def decrease_volume(self):
        if self.audio_output:
            current_volume = self.audio_output.volume()
            new_volume = max(0.0, current_volume - 0.1)
            self.audio_output.setVolume(new_volume)
            volume_percent = int(new_volume * 100)
            speak(f"نسبة الصوت {volume_percent}")
            self.parent_widget.aud.setText(f"نسبة الصوت: {volume_percent}%")
            self.parent_widget.volume_timer.start(1000)
class protcasts(qt.QWidget):
    def __init__(self):
        super().__init__()
        global global_player, global_audio_output, global_current_url
        global_player = QMediaPlayer()
        global_audio_output = QAudioOutput()
        global_player.setAudioOutput(global_audio_output)
        global_audio_output.setVolume(1.0)
        global_current_url = None
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
        self.startBtn.setAccessibleDescription("بدء التسجيل (Control + R)")
        self.pauseBtn.setAccessibleDescription("إيقاف مؤقت/استئناف التسجيل (Control + P)")
        self.stopBtn.setAccessibleDescription("إيقاف التسجيل (Control + S)")
        self.scheduleBtn.setAccessibleDescription("جدولة التسجيل (Control + G)")
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
             self.recorder.error.emit(self.recorder.error.string) if hasattr(self.recorder.error, 'string') else self.recorder.error.emit("خطأ في تهيئة المسجل.")
             return
        if self.recorder._running:
             guiTools.qMessageBox.MessageBox.error(self, "خطأ", "التسجيل يعمل بالفعل.")
             return
        guiTools.qMessageBox.MessageBox.view(self, "تنبيه هام", "سيتم تسجيل جميع الأصوات الصادرة من النظام (الكمبيوتر) فقط، ولن يتم تسجيل أي صوت خارجي (الميكروفون).")
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
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الجدولة.")
    def updateCountdown(self):
        if not global_player or global_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.stopRecording()
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
                self.stopRecording()
                self.recorder.error.emit("فشل بدء التسجيل المجدول: المسجل غير جاهز.")
                return
            self.recorder.start()
            self.scheduleBtn.setText("جدولة التسجيل")
            self.scheduleBtn.setEnabled(False)
            self.stopBtn.setEnabled(True)
            self.pauseBtn.setEnabled(True)
            self.duration_timer.timeout.disconnect() if self.duration_timer.isActive() else None
            try: self.duration_timer.timeout.disconnect()
            except: pass
            self.duration_timer.timeout.connect(self.updateDurationCountdown)
            self.duration_timer.start(1000)
            self.updateDurationCountdown()
    def updateDurationCountdown(self):
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
            self.stopRecording()
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
        if not global_player or global_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState or not global_current_url:
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
    def stopRecording(self):
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
        if self.is_scheduled_recording and self.scheduled_file_path:
            self.aud.setText("جاري حفظ التسجيل المجدول...")
            self.current_status_text = "جاري حفظ التسجيل المجدول..."
            self.convert_thread_worker = threading.Thread(target=self.recorder.stop, args=(self.scheduled_file_path,), daemon=True)
            self.convert_thread_worker.start()
            self.is_scheduled_recording = False
            self.scheduled_file_path = ""
        else:
            filePath, _ = qt.QFileDialog.getSaveFileName(self, "حفظ التسجيل", f"{self.get_current_station_name()}.mp3", "Audio Files (*.mp3);;All Files (*)")
            if filePath:
                self.aud.setText("جاري تحويل الملف إلى MP3، يرجى الانتظار...")
                self.aud.setFocus()
                self.current_status_text = "جاري تحويل الملف إلى MP3، يرجى الانتظار..."
                self.convert_thread_worker = threading.Thread(target=self.recorder.stop, args=(filePath,), daemon=True)
                self.convert_thread_worker.start()
            else:
                guiTools.qMessageBox.MessageBox.view(self, "إلغاء", "تم إلغاء الحفظ. سيتم حذف الملف المؤقت.")
                self.convert_thread_worker = threading.Thread(target=self.recorder.stop, args=(None,), daemon=True)
                self.convert_thread_worker.start()
    @qt2.pyqtSlot(str)
    def on_recording_stopped(self, final_path):
        self.restore_aud_text()
        if final_path != "CLEANUP_ONLY":
            guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", "تم حفظ الملف بنجاح.")
        self.resetRecorderState()
    @qt2.pyqtSlot(str)
    def recordingError(self, error_msg):
        self.restore_aud_text()
        if not self.startBtn.isEnabled() or self.countdown_timer.isActive():
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في التسجيل", "يبدو أن جهاز تسجيل صوت الكمبيوتر stereo mix لا يعمل، لتشغيله اتبع الخطوات التالية\n\n1 فتح قائمة Run عن طريق الاختصار Windows + R ثم اكتب هذا الأمر:\nrundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,1\n2 اذهب إلى تبويبة التسجيل Recording واختر منها Stereo Mix ثم اضغط عليه بزر الفأرة الأيمن أو زر التطبيقات واختر Enable ثم اضغط OK.\nلمن واجه أي مشكلة يمكنه التواصل معي على حسابي في تليجرام من قسم (عن المطور) في قائمة المزيد من الخيارات.")
        self.resetRecorderState()
    def resetRecorderState(self):
        if self.recorder._running: self.recorder.stop(None)
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