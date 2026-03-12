from .translationViewer import translationViewer
from .tafaseerViewer import TafaseerViewer
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
import guiTools, settings, functions, os, winsound, json, requests, shutil
from functions import audio_manager
with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)
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
        except:
            self.cancelled.emit()
    def cancel(self):
        self.is_cancelled = True
class PreCheckThread(qt2.QThread):
    finished = qt2.pyqtSignal(bool, str, str, str)
    def __init__(self, ayah_text, category, type_index, current_reciter_index, reciters_data):
        super().__init__()
        self.ayah_text = ayah_text
        self.category = category
        self.type_index = type_index
        self.current_reciter_index = current_reciter_index
        self.reciters_data = reciters_data
    def run(self):
        try:
            Ayah, surah, _, _, _ = functions.quranJsonControl.getAyah(self.ayah_text, self.category, self.type_index)
            surah_str = str(surah).zfill(3)
            ayah_str = str(Ayah).zfill(3)
            filename = f"{surah_str}{ayah_str}.mp3"
            reciter_name = list(self.reciters_data.keys())[self.current_reciter_index]
            reciter_url_base = self.reciters_data[reciter_name]
            reciter_folder_name = reciter_url_base.split("/")[-3]
            local_path = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciter_folder_name, filename)
            remote_url = reciter_url_base + filename
            self.finished.emit(True, filename, local_path, remote_url)
        except:
            self.finished.emit(False, "", "", "")
class QuranPlayer(qt.QDialog):
    def __init__(self,p,text:str,index:int,type:int,category):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.type=type
        self.category=category
        self.verses=text.split("\n")
        self.index=index
        self.currentReciter=int(settings.settings_handler.get("g","reciter"))
        self.font_size = int(settings.settings_handler.get("font", "size"))
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.is_saving = False
        self.media=QMediaPlayer(self)
        self.audioOutput=QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("quran_player"))
        self.media.setAudioOutput(self.audioOutput)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.setWindowTitle("المشغل")
        layout=qt.QVBoxLayout(self)
        self.text=guiTools.QReadOnlyTextEdit()
        self.text.setText(self.verses[self.index])
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.update_font_size()
        self.progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.progress.setRange(0,100)
        self.progress.valueChanged.connect(self.set_position_from_slider)
        self.progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.time_label = qt.QLabel()
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        progress_layout = qt.QHBoxLayout()
        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(self.time_label)
        self.save_feedback_label = qt.QLabel()
        self.save_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.save_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.save_progress_bar = qt.QProgressBar()
        self.save_action_button = guiTools.QPushButton("إلغاء العملية")
        self.save_action_button.setAutoDefault(False)
        self.save_action_button.clicked.connect(self.cancel_save)
        self.save_widget = qt.QWidget()
        save_layout_ui = qt.QHBoxLayout(self.save_widget)
        save_layout_ui.addWidget(self.save_feedback_label)
        save_layout_ui.addWidget(self.save_progress_bar)
        save_layout_ui.addWidget(self.save_action_button)
        self.save_widget.setVisible(False)
        self.info=qt.QLabel()
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.update_info()
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleDescription("حجم النص")
        self.show_font.valueChanged.connect(self.font_size_changed)
        layout.addWidget(self.text)
        layout.addLayout(progress_layout)
        layout.addWidget(self.save_widget)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        layout.addWidget(self.info)
        self.play_button=guiTools.QPushButton("تشغيل/إيقاف مؤقت")
        self.play_button.setAutoDefault(False)
        self.play_button.clicked.connect(self.on_play)
        self.play_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.next_button=guiTools.QPushButton("الآية التالية")
        self.next_button.setAutoDefault(False)
        self.next_button.clicked.connect(self.on_next)
        self.next_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.previous_button=guiTools.QPushButton("الآية السابقة")
        self.previous_button.setAutoDefault(False)
        self.previous_button.clicked.connect(self.on_previous)
        self.previous_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.save_button = guiTools.QPushButton("حفظ الآية الحالية في الجهاز")
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self.onSaveCurrentAyah)
        self.save_button.setStyleSheet("background-color: #0000AA; color: white;")
        buttons_layout=qt.QHBoxLayout()
        buttons_layout.addWidget(self.previous_button)
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addWidget(self.save_button)
        layout.addLayout(buttons_layout)
        self.play_shortcut = qt1.QShortcut(qt1.QKeySequence("Space"), self)
        self.play_shortcut.activated.connect(self.on_play)
        self.next_shortcut = qt1.QShortcut(qt1.QKeySequence("Alt+Right"), self)
        self.next_shortcut.activated.connect(self.on_next)
        self.prev_shortcut = qt1.QShortcut(qt1.QKeySequence("Alt+Left"), self)
        self.prev_shortcut.activated.connect(self.on_previous)
        self.save_shortcut = qt1.QShortcut(qt1.QKeySequence("Ctrl+H"), self)
        self.save_shortcut.activated.connect(self.onSaveCurrentAyah)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+0", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+g", self).activated.connect(self.onGoToAyah)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.onAyahInfo)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.onAyahTranslation)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.onAyahTafseer)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.onAyahIArab)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.onAyahTanzeel)
        self.on_set()
    def t10(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.1))
    def t20(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.2))
    def t30(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.3))
    def t40(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.4))
    def t50(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.5))
    def t60(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.6))
    def t70(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.7))
    def t80(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.8))
    def t90(self):
        if self.media.duration() == 0:
            guiTools.speak("لا يوجد مقطع مشغل حالياً")
            return
        total_duration = self.media.duration()
        self.media.setPosition(int(total_duration * 0.9))
    def update_info(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            self.info.setText(f"سورة {juz[1]} الآية {Ayah} الصفحة {page}")
        except:
            self.info.setText("")
    def on_set(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            if int(surah)<10:
                surah="00"+surah
            elif int(surah)<100:
                surah="0"+surah
            else:
                surah=str(surah)
            if Ayah<10:
                Ayah="00"+str(Ayah)
            elif Ayah<100:
                Ayah="0"+str(Ayah)
            else:
                Ayah=str(Ayah)
            fileName=surah+Ayah+".mp3"
            reciterKey=list(reciters.keys())[self.currentReciter]
            reciterFolder = reciters[reciterKey].split("/")[-3]
            localFilePath = os.path.join(os.getenv('appdata'), settings.app.appName, "reciters", reciterFolder, fileName)
            if os.path.exists(localFilePath):
                path = qt2.QUrl.fromLocalFile(localFilePath)
            else:
                path = qt2.QUrl(reciters[reciterKey] + fileName)
            self.media.setSource(path)
            self.media.play()
        except:
            pass
    def on_state(self,state):
        if state==QMediaPlayer.MediaStatus.EndOfMedia:
            if self.index<len(self.verses)-1:
                self.index+=1
                self.text.setText(self.verses[self.index])
                self.update_font_size()
                self.update_info()
                self.on_set()
            else:
                self.media.stop()
    def on_play(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.pause()
        else:
            self.media.play()
    def on_next(self):
        if self.index<len(self.verses)-1:
            self.index+=1
            self.text.setText(self.verses[self.index])
            self.update_font_size()
            self.update_info()
            self.on_set()
        else:
            guiTools.speak("نهاية الآيات")
    def on_previous(self):
        if self.index>0:
            self.index-=1
            self.text.setText(self.verses[self.index])
            self.update_font_size()
            self.update_info()
            self.on_set()
        else:
            guiTools.speak("بداية الآيات")
    def set_position_from_slider(self, value):
        duration = self.media.duration()
        new_position = int((value / 100) * duration)
        self.media.setPosition(new_position)
        guiTools.speak(f"{value}%")
    def update_slider(self):
        try:
            self.progress.blockSignals(True)
            position = self.media.position()
            duration = self.media.duration()
            if duration > 0:
                progress_value = int((position / duration) * 100)
                self.progress.setValue(progress_value)
                self.update_time_label(position, duration)
            self.progress.blockSignals(False)
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
    def OnContextMenu(self):
        menu=qt.QMenu(self)
        GoToAya=qt1.QAction("الذهاب إلى آية",self)
        GoToAya.setShortcut("ctrl+g")
        menu.addAction(GoToAya)
        GoToAya.triggered.connect(self.onGoToAyah)
        aya_info=qt1.QAction("معلومات الآية",self)
        aya_info.setShortcut("ctrl+f")
        menu.addAction(aya_info)
        aya_info.triggered.connect(self.onAyahInfo)
        aya_trans=qt1.QAction("ترجمة الآية",self)
        aya_trans.setShortcut("ctrl+l")
        menu.addAction(aya_trans)
        aya_trans.triggered.connect(self.onAyahTranslation)
        aya_tafsseer=qt1.QAction("تفسير الآية",self)
        aya_tafsseer.setShortcut("ctrl+t")
        menu.addAction(aya_tafsseer)
        aya_tafsseer.triggered.connect(self.onAyahTafseer)
        aya_arab=qt1.QAction("إعراب الآية",self)
        aya_arab.setShortcut("ctrl+i")
        menu.addAction(aya_arab)
        aya_arab.triggered.connect(self.onAyahIArab)
        aya_tanzeel=qt1.QAction("أسباب النزول",self)
        aya_tanzeel.setShortcut("ctrl+r")
        menu.addAction(aya_tanzeel)
        aya_tanzeel.triggered.connect(self.onAyahTanzeel)
        saveCurrentAyahAction = qt1.QAction("حفظ الآية الحالية في الجهاز", self)
        saveCurrentAyahAction.setShortcut("ctrl+h")
        menu.addAction(saveCurrentAyahAction)
        saveCurrentAyahAction.triggered.connect(self.onSaveCurrentAyah)
        Previous_aya=qt1.QAction("الآية السابقة",self)
        Previous_aya.setShortcut("alt+left")
        menu.addAction(Previous_aya)
        Previous_aya.triggered.connect(self.on_previous)
        next_aya=qt1.QAction("الآية التالية",self)
        next_aya.setShortcut("alt+right")
        menu.addAction(next_aya)
        next_aya.triggered.connect(self.on_next)
        fontMenu = qt.QMenu("حجم الخط", self)
        incressFontAction = qt1.QAction("تكبير الخط", self)
        incressFontAction.setShortcut("ctrl+=")
        fontMenu.addAction(incressFontAction)
        incressFontAction.triggered.connect(self.increase_font_size)
        decreaseFontSizeAction = qt1.QAction("تصغير الخط", self)
        decreaseFontSizeAction.setShortcut("ctrl+-")
        fontMenu.addAction(decreaseFontSizeAction)
        decreaseFontSizeAction.triggered.connect(self.decrease_font_size)
        menu.addMenu(fontMenu)
        menu.exec(qt1.QCursor.pos())
    def onGoToAyah(self):
        ayah,ok=guiTools.QInputDialog.getInt(self,"الذهاب إلى آية","أكتب رقم الآية",self.index+1,1,len(self.verses))
        if ok:
            self.index=ayah-1
            self.text.setText(self.verses[self.index])
            self.update_font_size()
            self.update_info()
            self.on_set()
    def onAyahInfo(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            sajda=""
            if juz[3]:
                sajda="الآية تحتوي على سجدة"
            guiTools.qMessageBox.MessageBox.view(self,"معلومة","رقم الآية {} \nرقم السورة {} {} \nرقم الآية في المصحف {} \nالجزء {} \nالربع {} \nالصفحة {} \n{}".format(str(Ayah),surah,juz[1],AyahNumber,juz[0],juz[2],page,sajda))
        except:
            pass
    def onAyahTranslation(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            self.media.pause()
            translationViewer(self,AyahNumber,AyahNumber).exec()
            self.media.play()
        except:
            pass
    def onAyahTafseer(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            self.media.pause()
            TafaseerViewer(self,AyahNumber,AyahNumber).exec()
            self.media.play()
        except:
            pass
    def onAyahIArab(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            result=functions.iarab.getIarab(AyahNumber,AyahNumber)
            self.media.pause()
            guiTools.TextViewer(self,"إعراب",result).exec()
            self.media.play()
        except:
            pass
    def onAyahTanzeel(self):
        try:
            Ayah,surah,juz,page,AyahNumber=functions.quranJsonControl.getAyah(self.verses[self.index], self.category, self.type)
            result=functions.tanzil.gettanzil(AyahNumber)
            if result:
                self.media.pause()
                guiTools.TextViewer(self,"أسباب النزول",result).exec()
                self.media.play()
            else:
                guiTools.qMessageBox.MessageBox.view(self,"تنبيه","لا توجد أسباب نزول متاحة لهذه الآية")
        except:
            pass
    def onSaveCurrentAyah(self):
        if self.is_saving: return
        self.media.pause()
        self.is_saving = True
        self.set_ui_for_save(True)
        self.save_feedback_label.setText("جاري التحقق من الآية...")
        self.pre_check_thread = PreCheckThread(self.verses[self.index], self.category, self.type, self.currentReciter, reciters)
        self.pre_check_thread.finished.connect(self.on_pre_check_finished)
        self.pre_check_thread.start()
    def on_pre_check_finished(self, success, filename, local_path, remote_url):
        if not success:
            self.finalize_save_process(False, "حدث خطأ أثناء التحضير للحفظ.")
            return
        self.current_filename = filename
        self.current_local_path = local_path
        self.current_remote_url = remote_url
        if os.path.exists(local_path):
            self.start_copy_process()
        else:
            confirm_msg = "الآية المطلوبة غير موجودة في جهازك، هل تريد تحميلها ثم حفظها؟\n\nتنبيه: خلال التحميل لن تتمكن من إغلاق البرنامج."
            reply = guiTools.QQuestionMessageBox.view(self, "تأكيد التحميل", confirm_msg, "نعم", "لا")
            if reply == 0:
                self.start_download_process()
            else:
                self.finalize_save_process(False, "تم إلغاء العملية.")
    def start_download_process(self):
        self.save_feedback_label.setText("جاري تحميل الآية...")
        self.save_progress_bar.show()
        self.save_action_button.hide()
        output_dir = os.path.join(os.getenv('appdata'), settings.app.appName, "temp_downloads")
        os.makedirs(output_dir, exist_ok=True)
        self.temp_download_path = os.path.join(output_dir, self.current_filename)
        self.download_thread = DownloadThread(self.current_remote_url, self.temp_download_path)
        self.download_thread.progress.connect(self.save_progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.cancelled.connect(lambda: self.finalize_save_process(False, "فشل التحميل."))
        self.download_thread.start()
    def on_download_finished(self):
        self.save_progress_bar.hide()
        self.current_local_path = self.temp_download_path
        self.start_copy_process()
    def start_copy_process(self):
        dest_dir = qt.QFileDialog.getExistingDirectory(self, "اختر مجلد لحفظ الآية")
        if not dest_dir:
            self.finalize_save_process(False, "تم إلغاء اختيار المجلد.")
            return
        try:
            dest_path = os.path.join(dest_dir, self.current_filename)
            shutil.copy2(self.current_local_path, dest_path)
            self.finalize_save_process(True, "تم حفظ الآية بنجاح.")
        except Exception as e:
            self.finalize_save_process(False, f"فشل حفظ الملف: {str(e)}")
    def finalize_save_process(self, success, message):
        self.is_saving = False
        self.set_ui_for_save(False)
        if success:
            guiTools.qMessageBox.MessageBox.view(self, "نجاح", message)
        else:
            if "إلغاء" not in message:
                guiTools.qMessageBox.MessageBox.error(self, "خطأ", message)
        self.media.play()
    def cancel_save(self):
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel()
        self.finalize_save_process(False, "تم إلغاء العملية.")
    def set_ui_for_save(self, active):
        self.save_widget.setVisible(active)
        self.play_button.setEnabled(not active)
        self.next_button.setEnabled(not active)
        self.previous_button.setEnabled(not active)
        self.save_button.setEnabled(not active)
        if active:
            self.save_progress_bar.hide()
            self.save_progress_bar.setValue(0)
            self.save_action_button.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
    def increase_font_size(self):
        if self.show_font.value() < 100:
            self.show_font.setValue(self.show_font.value() + 1)
    def decrease_font_size(self):
        if self.show_font.value() > 1:
            self.show_font.setValue(self.show_font.value() - 1)
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(value))
    def update_font_size(self):
        cursor=self.text.textCursor()
        self.text.selectAll()
        font=qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.text.setCurrentFont(font)
        self.text.setTextCursor(cursor)
