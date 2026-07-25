import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
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

TMP_DIR = Path(tempfile.gettempdir()) / "radio_recordings_temp"
TMP_DIR.mkdir(exist_ok=True)

class WasapiRecorder(qt2.QObject):
    error = qt2.pyqtSignal(str)
    recording_stopped = qt2.pyqtSignal(str, str)
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
        self._stop_requested = False
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
        if self._stop_requested:
            temp_file = self._temp_wav_path
            self._temp_wav_path = None
            self._stop_requested = False
            if not temp_file or not temp_file.exists():
                self.error.emit("لم يتم العثور على ملف التسجيل.")
                self.recording_stopped.emit("FAILED", "")
                return
            self.recording_stopped.emit("STOPPED", str(temp_file))
    def start(self):
        if not self._is_ready:
            return
        with self._lock:
            if self._running: return
            self._running = True
            self._paused = False
            self._stop_requested = False
        self._thread = threading.Thread(target=self._run_stream, daemon=True)
        self._thread.start()
    def pause(self):
        with self._lock:
            self._paused = True
    def resume(self):
        with self._lock:
            self._paused = False
    def stop(self, cleanup_only=False):
        with self._lock:
            if not self._running: return
            self._running = False
            self._stop_requested = not cleanup_only
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        if cleanup_only:
            try:
                if self._temp_wav_path and self._temp_wav_path.exists():
                    self._temp_wav_path.unlink(missing_ok=True)
            except:
                pass
            self.recording_stopped.emit("CLEANUP_ONLY", "")
    def convert_and_cleanup(self, temp_file_path, output_filename):
        temp_file = Path(temp_file_path)
        if not temp_file.exists():
            self.error.emit("لم يتم العثور على ملف التسجيل المؤقت للتحويل.")
            return
        try:
            final_path = Path(output_filename)
            cmd = [self.ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp_file), "-c:a", "libmp3lame", "-b:a", "192k", str(final_path)]
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600, text=True, encoding='utf-8')
            if proc.returncode != 0:
                self.error.emit(f"فشل التحويل: {proc.stderr}")
                return
            self.recording_stopped.emit("CONVERTED", str(final_path))
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
        self.dur_s_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
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
