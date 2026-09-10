import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import guiTools, os, tempfile, shutil, subprocess, threading, time, uuid
from pathlib import Path

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    from ._native import ProcessLoopback
except (ImportError, ValueError):
    try:
        from _native import ProcessLoopback
    except ImportError:
        try:
            import importlib.util
            _native_path = Path(__file__).parent / "_native.cp311-win_amd64.pyd"
            if not _native_path.exists():
                _native_path = Path(__file__).parent / "_native.pyd"
            if _native_path.exists():
                _spec = importlib.util.spec_from_file_location("_native", str(_native_path))
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                ProcessLoopback = _mod.ProcessLoopback
            else:
                ProcessLoopback = None
        except Exception:
            ProcessLoopback = None

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
        self._capture = None
        self._worker_thread = None
        self._temp_wav_path = None
        self._sf_handle = None
        self._lock = threading.Lock()
        self.samplerate = 48000
        self.channels = 2
        self._is_ready = False
        self._stop_requested = False
        self.last_error = ""
        self.init_device()

    def init_device(self):
        if sf is None or ProcessLoopback is None:
            self._is_ready = False
            self.last_error = "المكتبات المطلوبة لتسجيل الصوت غير متوفرة."
            return False

        try:
            test_cap = ProcessLoopback(os.getpid())
            self._is_ready = True
            self.last_error = ""
            return True
        except Exception as e:
            self._is_ready = False
            self.last_error = f"تعذر تهيئة تسجيل الصوت عبر WASAPI: {e}"
            return False

    def is_ready(self):
        if not self._is_ready:
            self.init_device()
        return self._is_ready

    def _record_loop(self):
        while self._running:
            try:
                if not self._capture:
                    break
                data = self._capture.read()
            except Exception:
                break
            if not data:
                time.sleep(0.001)
                continue
            with self._lock:
                if self._running and not self._paused and self._sf_handle:
                    try:
                        self._sf_handle.buffer_write(data, dtype="float32")
                    except Exception:
                        pass

    def start(self):
        if not self.is_ready():
            return
        with self._lock:
            if self._running:
                return
            self._running = True
            self._paused = False
            self._stop_requested = False

        try:
            self._temp_wav_path = TMP_DIR / f"rec_{uuid.uuid4().hex}.wav"
            self._capture = ProcessLoopback(os.getpid())
            fmt = self._capture.get_format()
            self.samplerate = fmt.get("sample_rate", 48000)
            self.channels = fmt.get("channels", 2)
            self._sf_handle = sf.SoundFile(
                str(self._temp_wav_path),
                mode="w",
                samplerate=self.samplerate,
                channels=self.channels,
                subtype="FLOAT",
            )
            self._capture.start()
            self._worker_thread = threading.Thread(target=self._record_loop, daemon=True)
            self._worker_thread.start()
        except Exception as e:
            with self._lock:
                self._running = False
                if self._sf_handle:
                    try:
                        self._sf_handle.close()
                    except Exception:
                        pass
                    self._sf_handle = None
            if self._capture:
                try:
                    self._capture.stop()
                except Exception:
                    pass
                self._capture = None
            self.error.emit(f"حدث خطأ أثناء بدء التسجيل: {e}")

    def pause(self):
        with self._lock:
            self._paused = True

    def resume(self):
        with self._lock:
            self._paused = False

    def stop(self, cleanup_only=False):
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._stop_requested = not cleanup_only

        if self._capture:
            try:
                self._capture.stop()
            except Exception:
                pass
            self._capture = None

        if self._worker_thread:
            try:
                self._worker_thread.join(timeout=1.0)
            except Exception:
                pass
            self._worker_thread = None

        with self._lock:
            if self._sf_handle:
                try:
                    self._sf_handle.close()
                except Exception:
                    pass
                self._sf_handle = None

        if cleanup_only:
            try:
                if self._temp_wav_path and self._temp_wav_path.exists():
                    self._temp_wav_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._temp_wav_path = None
            self.recording_stopped.emit("CLEANUP_ONLY", "")
        else:
            temp_file = self._temp_wav_path
            self._temp_wav_path = None
            self._stop_requested = False
            if not temp_file or not temp_file.exists():
                self.error.emit("لم يتم العثور على ملف التسجيل المؤقت.")
                self.recording_stopped.emit("FAILED", "")
                return
            self.recording_stopped.emit("STOPPED", str(temp_file))

    def convert_and_cleanup(self, temp_file_path, output_filename):
        temp_file = Path(temp_file_path)
        if not temp_file.exists():
            self.error.emit("لم يتم العثور على ملف التسجيل المؤقت.")
            return
        try:
            final_path = Path(output_filename)
            cmd = [
                self.ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(temp_file),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(final_path),
            ]
            proc = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=600,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if proc.returncode != 0:
                self.error.emit(f"فشل التحويل: {proc.stderr}")
                return
            self.recording_stopped.emit("CONVERTED", str(final_path))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass


class SchedulingDialog(qt.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(780, 345)
        self.resize(780, 345)
        self.setWindowTitle("جدولة التسجيل")
        
        main_dialog_layout = qt.QVBoxLayout(self)
        
        scroll_area = qt.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(qt2.Qt.FocusPolicy.NoFocus)
        scroll_area.setFrameShape(qt.QFrame.Shape.NoFrame)
        
        content_widget = qt.QWidget()
        layout = qt.QVBoxLayout(content_widget)
        
        main_h_layout = qt.QHBoxLayout()
        main_h_layout.setSpacing(40)
        start_v_layout = qt.QVBoxLayout()
        start_v_layout.setSpacing(4)
        dur_v_layout = qt.QVBoxLayout()
        dur_v_layout.setSpacing(4)
        
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
        dur_v_layout.addWidget(self.dur_label)
        self.dur_label.setStyleSheet("font-weight: bold; color: #008000;")
        
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
        self.dur_m_spin.setRange(0, 59)
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
        
        layout.addSpacing(10)
        line2 = qt.QFrame()
        line2.setFrameShape(qt.QFrame.Shape.HLine)
        line2.setFrameShadow(qt.QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        
        self.pause_countdown_cb = qt.QCheckBox("إيقاف العد التنازلي للتسجيل مؤقتاً عند إيقاف التسجيل مؤقتاً")
        self.pause_countdown_cb.setAccessibleName("إيقاف العد التنازلي للتسجيل مؤقتاً عند إيقاف التسجيل مؤقتاً")
        self.pause_countdown_cb.setStyleSheet("QCheckBox { margin: 0px; padding: 0px; }")
        self.warning_label = guiTools.QNavigableLabel("تنبيه: إذا تم إيقاف الإذاعة، سيتم إلغاء جدولة التسجيل.")
        self.warning_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setFixedHeight(24)
        options_widget = qt.QWidget()
        options_layout = qt.QVBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)
        options_layout.addWidget(self.pause_countdown_cb, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        options_layout.addWidget(self.warning_label, alignment=qt2.Qt.AlignmentFlag.AlignCenter)
        options_widget.setSizePolicy(qt.QSizePolicy.Policy.Preferred, qt.QSizePolicy.Policy.Fixed)
        layout.addWidget(options_widget)
        
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
        
        scroll_area.setWidget(content_widget)
        main_dialog_layout.addWidget(scroll_area)
        
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
                self.dur_h_spin.value(), self.dur_m_spin.value(), self.dur_s_spin.value(),
                self.pause_countdown_cb.isChecked())

    def should_pause_countdown_on_pause(self):
        return self.pause_countdown_cb.isChecked()