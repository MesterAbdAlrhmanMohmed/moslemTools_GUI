from .changeReciter import ChangeReciter
from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
import time,os,json,requests,subprocess,shutil
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)
class DownloadThread(qt2.QThread):
    progress = qt2.pyqtSignal(int)
    finished = qt2.pyqtSignal()
    cancelled = qt2.pyqtSignal()
    def __init__(self, url, filepath):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.is_cancelled = False
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            with open(self.filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if self.is_cancelled:
                        self.cancelled.emit()
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percent)
            self.finished.emit()
        except Exception as e:
            print(f"Error during download or file writing: {e}")
            self.cancelled.emit()
    def cancel(self):
        self.is_cancelled = True
class MergeThread(qt2.QThread):
    finished = qt2.pyqtSignal(bool, str)
    def __init__(self, ffmpeg_path, input_files, output_file):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.input_files = input_files
        self.output_file = output_file
        self.process = None
    def run(self):
        list_filepath = os.path.join(os.path.dirname(self.output_file), "mergelist.txt")
        try:
            with open(list_filepath, 'w', encoding='utf-8') as f:
                for file_path in self.input_files:
                    safe_path = file_path.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")
            command = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_filepath,
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                self.output_file
            ]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = self.process.communicate()
            if self.process.returncode == 0:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"فشل الدمج أو تم إلغاؤه.\n{stderr}")
        except Exception as e:
            self.finished.emit(False, f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if os.path.exists(list_filepath):
                os.remove(list_filepath)
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
class QuranPlayer(qt.QDialog):
    def __init__(self,p,text,index:int,type,category):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.currentReciter=int(settings.settings_handler.get("g","reciter"))
        self.resize(1200,600)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.type=type
        self.times=int(settings.settings_handler.get("quranPlayer","times"))
        self.currentTime=1
        self.category=category
        self.was_playing_before_action = False
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج الآيات لن تعمل.")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.media.setAudioOutput(self.audioOutput)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.index=index-1
        self.quranText=text.split("\n")
        self.text=guiTools.QReadOnlyTextEdit()
        self.text.setLineWrapMode(qt.QTextEdit.LineWrapMode.WidgetWidth)
        self.text.setWordWrapMode(qt1.QTextOption.WrapMode.WordWrap)
        option = self.text.document().defaultTextOption()
        option.setAlignment(qt2.Qt.AlignmentFlag.AlignRight)
        option.setTextDirection(qt2.Qt.LayoutDirection.RightToLeft)
        self.text.document().setDefaultTextOption(option)
        self.text.setText(text[index-1])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.text.setFocus()
        self.font_size=12
        font=self.font()
        font.setPointSize(self.font_size)
        self.text.setFont(font)
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.media_progress.setAccessibleName("التحكم في تقدم الآية")
        self.time_label = qt.QLabel()
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        progress_time_layout = qt.QHBoxLayout()
        progress_time_layout.addWidget(self.media_progress, 3)
        progress_time_layout.addWidget(self.time_label)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font=qt.QLabel()
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setText(str(self.font_size))
        self.N_aya=guiTools.QPushButton("الآيا التالية")
        self.N_aya.setAutoDefault(False)
        self.N_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_aya.clicked.connect(self.onNextAyah)
        self.N_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_aya.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=guiTools.QPushButton("تشغيل")
        self.PPS.setAutoDefault(False)
        self.PPS.setAccessibleDescription("space")
        self.PPS.clicked.connect(self.on_play)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya=guiTools.QPushButton("الآيا السابقة")
        self.P_aya.setAutoDefault(False)
        self.P_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya.clicked.connect(self.onPreviousAyah)
        self.P_aya.setAccessibleDescription("alt زائد السهم الأيسر")
        self.changeCurrentReciterButton=guiTools.QPushButton("تغيير القارئ")
        self.changeCurrentReciterButton.setAutoDefault(False)
        self.changeCurrentReciterButton.clicked.connect(self.onChangeRecitersContextMenuRequested)
        self.changeCurrentReciterButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.changeCurrentReciterButton.setShortcut("ctrl+shift+r")
        self.changeCurrentReciterButton.setAccessibleDescription("control plus shift plus R")
        self.mergeButton = guiTools.QPushButton("دمج الآيات")
        self.mergeButton.setAutoDefault(False)
        self.mergeButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.mergeButton.clicked.connect(self.mergeAyahs)
        self.mergeButton.setAccessibleDescription("control plus alt plus d")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addLayout(progress_time_layout)
        self.merge_feedback_label = qt.QLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_action_button = guiTools.QPushButton("إلغاء الدمج")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        merge_layout = qt.QHBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        layout.addWidget(self.merge_widget)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout1=qt.QHBoxLayout()
        layout1.addWidget(self.changeCurrentReciterButton)
        layout1.addWidget(self.P_aya)
        layout1.addWidget(self.PPS)
        layout1.addWidget(self.N_aya)
        layout1.addWidget(self.mergeButton)
        layout.addLayout(layout1)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.gotoayah)
        qt1.QShortcut("alt+right",self).activated.connect(self.onNextAyah)
        qt1.QShortcut("alt+left",self).activated.connect(self.onPreviousAyah)
        qt1.QShortcut("escape",self).activated.connect(self.safeClose)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("shift+up",self).activated.connect(self.volume_up)
        qt1.QShortcut("shift+down",self).activated.connect(self.volume_down)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        qt1.QShortcut("ctrl+1",self).activated.connect(self.set_font_size_dialog)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.mergeAyahs)
        self.on_play()
    def pause_for_action(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.was_playing_before_action = True
            self.media.pause()
        else:
            self.was_playing_before_action = False
    def resume_after_action(self):
        if self.was_playing_before_action:
            self.media.play()
    def handle_merge_action(self):
        if self.is_merging and self.merge_phase == 'merging':
            self.confirm_and_cancel_merge()
    def confirm_and_cancel_merge(self):
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء",
            "هل أنت متأكد أنك تريد إلغاء عملية الدمج الحالية؟", "نعم", "لا")
        if reply == 0:
            self.cancellation_requested = True
            if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                self.merge_thread.stop()
    def _on_set_for_merge(self, index):
        ayah_text = self.quranText[index]
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(ayah_text, self.category, self.type)
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"
    def mergeAyahs(self):
        self.pause_for_action()
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على أداة الدمج FFmpeg.")
            self.resume_after_action()
            return
        self.merge_list.clear()
        reciter_url_base = reciters[self.getCurrentReciter()]
        reciter_folder_name = reciter_url_base.split("/")[-3]
        reciter_local_path_base = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name)
        ayahs_to_download = []
        for i in range(len(self.quranText)):
            ayah_filename = self._on_set_for_merge(i)
            if not ayah_filename: continue
            local_path = os.path.join(reciter_local_path_base, ayah_filename)
            ayah_info = {
                "index": i, "filename": ayah_filename,
                "url": reciter_url_base + ayah_filename,
                "local_path": local_path
            }
            self.merge_list.append(ayah_info)
            if not os.path.exists(local_path):
                ayahs_to_download.append(ayah_info)
        num_files_to_download = len(ayahs_to_download)
        if num_files_to_download > 0:
            confirm_message = (
                f"تنبيه: يتطلب الدمج تحميل {num_files_to_download} آية غير موجودة.\n\n"
                "سيتم البدء بتحميل الآيات، وخلال هذه المرحلة **لن تتمكن من إلغاء العملية أو إغلاق البرنامج**.\n"
                "بعد انتهاء التحميل، ستبدأ مرحلة الدمج، وفيها يمكنك إلغاء عملية الدمج فقط.\n\n"
                "هل أنت متأكد أنك تريد المتابعة؟"
            )
        else:
            confirm_message = (
                "جميع الآيات المحددة جاهزة للدمج.\n"
                "ستبدأ عملية الدمج الآن وسيتم تعطيل الواجهة. يمكنك إلغاء عملية الدمج ولكن لا يمكنك إغلاق البرنامج حتى انتهاء العملية.\n\n"
                "هل تريد المتابعة؟"
            )
        reply = guiTools.QQuestionMessageBox.view(self, "تأكيد بدء الدمج", confirm_message, "نعم", "لا")
        if reply != 0:
            self.resume_after_action()
            return
        output_filename, _ = qt.QFileDialog.getSaveFileName(self, "حفظ الملف المدموج", "", "Audio Files (*.mp3)")
        if not output_filename:
            self.resume_after_action()
            return
        self.set_ui_for_merge(True)
        self.current_merge_output_path = output_filename
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.cancellation_requested = False
        self.process_next_in_merge_queue()
    def process_next_in_merge_queue(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية من قبل المستخدم.")
            return
        output_dir = os.path.dirname(self.current_merge_output_path)
        next_item_to_download = None
        for item in self.merge_list:
            if not os.path.exists(item["local_path"]) and item["url"] not in self.completed_merge_downloads:
                next_item_to_download = item
                break
        if next_item_to_download:
            self.merge_phase = 'downloading'
            self.merge_action_button.hide()
            self.merge_feedback_label.setText("جاري تحميل الآيات المطلوبة...")
            self.merge_progress_bar.show()
            url = next_item_to_download['url']
            safe_filename = "".join(c for c in next_item_to_download['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
            download_path = os.path.join(output_dir, f"temp_{safe_filename}")
            self.current_download_url = url
            self.download_thread = DownloadThread(url, download_path)
            self.download_thread.progress.connect(self.merge_progress_bar.setValue)
            self.download_thread.finished.connect(self.on_single_merge_download_finished)
            self.download_thread.cancelled.connect(lambda: self.on_merge_finished(False, "حدث خطأ أثناء التحميل."))
            self.download_thread.start()
        else:
            self.merge_progress_bar.hide()
            self.finalize_and_execute_merge()
    def on_single_merge_download_finished(self):
        if self.current_download_url:
            self.completed_merge_downloads.add(self.current_download_url)
            self.current_download_url = None
        self.process_next_in_merge_queue()
    def finalize_and_execute_merge(self):
        if self.cancellation_requested:
            self.on_merge_finished(False, "تم إلغاء العملية قبل بدء الدمج.")
            return
        self.merge_action_button.show()
        files_for_ffmpeg = []
        self.files_to_delete_after_merge.clear()
        output_dir = os.path.dirname(self.current_merge_output_path)
        for item in self.merge_list:
            if os.path.exists(item["local_path"]):
                files_for_ffmpeg.append(item["local_path"])
            else:
                safe_filename = "".join(c for c in item['filename'] if c.isalnum() or c in ('.', '_')).rstrip()
                temp_path = os.path.join(output_dir, f"temp_{safe_filename}")
                if os.path.exists(temp_path):
                    files_for_ffmpeg.append(temp_path)
                    if temp_path not in self.files_to_delete_after_merge:
                        self.files_to_delete_after_merge.append(temp_path)
                else:
                    self.on_merge_finished(False, f"خطأ: الملف المؤقت للآية لم يتم العثور عليه: {item['filename']}")
                    return
        if len(files_for_ffmpeg) != len(self.merge_list):
            self.on_merge_finished(False, "لم يتم العثور على جميع الملفات المطلوبة للدمج.")
            return
        self.execute_merge(files_for_ffmpeg, self.current_merge_output_path)
    def execute_merge(self, input_files, output_file):
        self.is_merging = True
        self.merge_phase = 'merging'
        self.merge_feedback_label.setText(f"جاري دمج {len(self.merge_list)} آيات...")
        self.merge_action_button.setText("إلغاء الدمج")
        self.merge_thread = MergeThread(self.ffmpeg_path, input_files, output_file)
        self.merge_thread.finished.connect(self.on_merge_finished)
        self.merge_thread.start()
    def on_merge_finished(self, success, message):
        self.is_merging = False
        self.merge_phase = 'idle'
        if self.cancellation_requested:
            guiTools.qMessageBox.MessageBox.view(self, "تم الإلغاء", "تم إلغاء عملية الدمج.")
            if hasattr(self, 'current_merge_output_path') and os.path.exists(self.current_merge_output_path):
                try: os.remove(self.current_merge_output_path)
                except: pass
        elif success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", "تم دمج الآيات بنجاح.")
        else:
            guiTools.qMessageBox.MessageBox.error(self, "فشل", message)
        if self.files_to_delete_after_merge:
            reply = guiTools.QQuestionMessageBox.view(self, "تنظيف",
                "هل تريد حذف الملفات المؤقتة التي تم تحميلها لهذه العملية؟", "نعم", "لا")
            if reply == 0:
                for f_path in self.files_to_delete_after_merge:
                    if os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass
        self.set_ui_for_merge(False)
        self.cancellation_requested = False
        self.merge_list.clear()
        self.files_to_delete_after_merge.clear()
        self.completed_merge_downloads.clear()
        self.resume_after_action()
    def set_ui_for_merge(self, is_active):
        self.is_merging = is_active
        widgets_to_disable = [self.text, self.N_aya, self.P_aya, self.PPS, self.changeCurrentReciterButton, self.mergeButton]
        for widget in widgets_to_disable:
            widget.setEnabled(not is_active)
        self.merge_widget.setVisible(is_active)
        if is_active:
            self.merge_feedback_label.setText("جاري التحضير لعملية الدمج...")
            self.merge_action_button.setText("إلغاء العملية")
            self.merge_action_button.setStyleSheet("background-color: #8B0000; color: white;")
            self.merge_progress_bar.hide()
            self.merge_progress_bar.setValue(0)
        else:
            self.merge_action_button.setStyleSheet("")
    def OnContextMenu(self):
        self.was_playing = self.media.isPlaying()
        if self.was_playing:
            self.media.pause()
            self.PPS.setText("تشغيل")
        menu=qt.QMenu("الخيارات",self)
        menu.setAccessibleName("الخيارات")
        aya=qt.QMenu("خيارات الآية",self)
        GoToAya=qt1.QAction("الذهاب الى آيا",self)
        GoToAya.setShortcut("ctrl+g")
        aya.addAction(GoToAya)
        aya.setDefaultAction(GoToAya)
        GoToAya.triggered.connect(self.gotoayah)
        aya_info=qt1.QAction("معلومات الآيا الحالية",self)
        aya_info.setShortcut("ctrl+f")
        aya.addAction(aya_info)
        aya_info.triggered.connect(self.getAyahInfo)
        aya_trans=qt1.QAction("ترجمة الآيا الحالية",self)
        aya_trans.setShortcut("ctrl+l")
        aya.addAction(aya_trans)
        aya_trans.triggered.connect(self.getCurentAyahTranslation)
        aya_tafsseer=qt1.QAction("تفسير الآيا الحالية",self)
        aya_tafsseer.setShortcut("ctrl+t")
        aya.addAction(aya_tafsseer)
        aya_tafsseer.triggered.connect(self.getCurentAyahTafseer)
        aya_arab=qt1.QAction("إعراب الآيا الحالية",self)
        aya_arab.setShortcut("ctrl+i")
        aya.addAction(aya_arab)
        aya_arab.triggered.connect(self.getCurentAyahIArab)
        aya_tanzeel=qt1.QAction("أسباب نزول الآيا الحالية",self)
        aya_tanzeel.setShortcut("ctrl+r")
        aya.addAction(aya_tanzeel)
        aya_tanzeel.triggered.connect(self.getCurrentAyahTanzel)
        Previous_aya=qt1.QAction("الآيا السابقة",self)
        Previous_aya.setShortcut("alt+left")
        aya.addAction(Previous_aya)
        Previous_aya.triggered.connect(self.onPreviousAyah)
        next_aya=qt1.QAction("الآيا التالية",self)
        next_aya.setShortcut("alt+right")
        aya.addAction(next_aya)
        next_aya.triggered.connect(self.onNextAyah)
        menu.setFocus()
        fontMenu=qt.QMenu("حجم الخط",self)
        incressFontAction=qt1.QAction("تكبير الخط",self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        fontMenu.setDefaultAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction=qt1.QAction("تصغير الخط",self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        set_font_size=qt1.QAction("تعيين حجم مخصص للنص", self)
        set_font_size.setShortcut("ctrl+1")
        set_font_size.triggered.connect(self.set_font_size_dialog)
        fontMenu.addAction(set_font_size)
        menu.addMenu(aya)
        menu.addMenu(fontMenu)
        menu.aboutToHide.connect(self.resume_playback)
        menu.exec(self.mapToGlobal(self.cursor().pos()))
    def resume_playback(self):
        if hasattr(self, 'was_playing') and self.was_playing and not self.media.isPlaying():
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
    def increase_font_size(self):
        if self.font_size < 50:
            self.font_size += 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
            guiTools.speak(str(self.font_size))
            self.show_font.setText(str(self.font_size))
            self.update_font_size()
    def update_font_size(self):
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=self.text.font()
        font.setPointSize(self.font_size)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
    def on_set(self):
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        if int(surah)<10:
            surah="00" + surah
        elif int(surah)<100:
            surah="0" + surah
        else:
            surah=str(surah)
        if Ayah<10:
            Ayah="00" + str(Ayah)
        elif Ayah<100:
            Ayah="0" + str(Ayah)
        else:
            Ayah=str(Ayah)
        return surah+Ayah+".mp3"
    def on_play(self):
        if not self.media.isPlaying():
            if os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set())):
                path=qt2.QUrl.fromLocalFile(os.path.join(os.getenv('appdata'),settings.app.appName,"reciters",reciters[self.getCurrentReciter()].split("/")[-3],self.on_set()))
            else:
                path=qt2.QUrl(reciters[self.getCurrentReciter()] + self.on_set())
            if not self.media.source()==path:
                self.media.setSource(path)
            self.media.play()
            self.PPS.setText("إيقاف مؤقت")
        else:
            self.media.pause()
            self.PPS.setText("تشغيل")
    def gotoayah(self):
        if self.media.isPlaying():
            self.media.stop()
        number,ok=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية",self.index+1,1,len(self.quranText))
        if ok:
            self.currentTime=1
            self.index=number-1
            self.text.setText(self.quranText[self.index])
            self.update_font_size()
            self.on_play()
    def onNextAyah(self):
        self.currentTime=1
        if self.index+1==len(self.quranText):
            self.index=0
        else:
            self.index+=1
        self.text.setText(self.quranText[self.index])
        self.update_font_size()
        self.media.stop()
        self.on_play()
    def onPreviousAyah(self):
        self.currentTime=1
        if self.index==0:
            self.index=len(self.quranText)-1
        else:
            self.index-=1
        self.text.setText(self.quranText[self.index])
        self.update_font_size()
        self.media.stop()
        self.on_play()
    def getcurrentAyahText(self):
        return self.text.toPlainText()
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            if self.times==self.currentTime:
                if settings.settings_handler.get("quranPlayer","replay")=="False":
                    if not self.index+1==len(self.quranText):
                        qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
                    else:
                        self.PPS.setText("تشغيل")
                        self.index=0
                        self.text.setText(self.quranText[self.index])
                else:
                    qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.onNextAyah)
            else:
                self.currentTime+=1
                qt2.QTimer.singleShot(int(settings.settings_handler.get("quranPlayer","duration"))*1000,qt2.Qt.TimerType.PreciseTimer,self.media.play)
    def getCurrentReciter(self):
        index=self.currentReciter
        name=list(reciters.keys())[index]
        return name
    def getCurentAyahTafseer(self):
        if self.media.isPlaying():
            self.media.stop()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        TafaseerViewer(self,AyahNumber,AyahNumber).exec()
    def safeClose(self):
        if self.media.isPlaying():
            self.media.stop()
            qt2.QTimer.singleShot(100, self.close)
        else:
            self.close()
    def closeEvent(self, event):
        if self.is_merging:
            if self.merge_phase == 'downloading':
                guiTools.qMessageBox.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق البرنامج أثناء مرحلة تحميل الآيات. الرجاء الانتظار.")
                event.ignore()
            elif self.merge_phase == 'merging':
                reply = guiTools.QQuestionMessageBox.view(self, "تأكيد", "عملية الدمج قيد التشغيل. هل تريد إلغاءها والخروج؟", "نعم", "لا")
                if reply == 0:
                    self.cancellation_requested = True
                    if hasattr(self, 'merge_thread') and self.merge_thread.isRunning():
                        self.merge_thread.stop()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            self.media.stop()
            super().closeEvent(event)
    def getCurentAyahIArab(self):
        if self.media.isPlaying():
            self.media.stop()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.iarab.getIarab(AyahNumber,AyahNumber)
        guiTools.TextViewer(self,"إعراب",result).exec()
    def getCurrentAyahTanzel(self):
        if self.media.isPlaying():
            self.media.stop()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        result=functions.tanzil.gettanzil(AyahNumber)
        if result:
            guiTools.TextViewer(self,"اسباب النزول",result).exec()
        else:
            guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
    def getAyahInfo(self):
        if self.media.isPlaying():
            self.media.stop()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        sajda=""
        if juz[3]:
            sajda="الآية تحتوي على سجدة"
        guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nالجزء {} \nالربع {} \nالصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
    def getCurentAyahTranslation(self):
        if self.media.isPlaying():
            self.media.stop()
        Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.getcurrentAyahText())
        translationViewer(self,AyahNumber,AyahNumber).exec()
    def volume_up(self):
        self.audioOutput.setVolume(self.audioOutput.volume()+0.10)
    def volume_down(self):
        self.audioOutput.setVolume(self.audioOutput.volume()-0.10)
    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)
    def update_slider(self):
        try:
            self.media_progress.blockSignals(True)
            position = self.media.position()
            duration = self.media.duration()
            if duration > 0:
                progress_value = int((position / duration) * 100)
                self.media_progress.setValue(progress_value)
                self.update_time_label(position, duration)
            self.media_progress.blockSignals(False)
        except:
            pass
    def update_time_label(self, position, duration):
        position_sec = position // 1000
        duration_sec = duration // 1000
        remaining_sec = duration_sec - position_sec
        position_str = f"{position_sec // 60}:{position_sec % 60:02d}"
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        remaining_str = f"{remaining_sec // 60}:{remaining_sec % 60:02d}"
        self.time_label.setText(f"الوقت المنقضي: {position_str} | الوقت المتبقي: {remaining_str} | مدة الآية: {duration_str}")
    def onChangeRecitersContextMenuRequested(self):
        if self.media.isPlaying():
            self.media.stop()
        RL=list(reciters.keys())
        dlg=ChangeReciter(self,RL,self.currentReciter)
        code=dlg.exec()
        if code==dlg.DialogCode.Accepted:
            self.currentReciter=list(reciters.keys()).index(dlg.recitersListWidget.currentItem().text())
        self.on_play()
    def set_font_size_dialog(self):
        try:
            size, ok = guiTools.QInputDialog.getInt(
                self,
                "تغيير حجم الخط",
                "أدخل حجم الخط (من 1 الى 50):",
                value=self.font_size,
                min=1,
                max=50
            )
            if ok:
                self.font_size = size
                self.show_font.setText(str(self.font_size))
                self.update_font_size()
                guiTools.speak(f"تم تغيير حجم الخط إلى {size}")
        except Exception as error:
            guiTools.qMessageBox.MessageBox.error(self, "حدث خطأ", str(error))