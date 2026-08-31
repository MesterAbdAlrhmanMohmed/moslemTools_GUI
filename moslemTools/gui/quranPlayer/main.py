from ..changeReciter import ChangeReciter
from ..translationViewer import translationViewer
from ..tafaseerViewer import TafaseerViewer
import time,os,requests,subprocess,shutil,re,traceback
import ujson as json
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtMultimedia import QAudioOutput,QMediaPlayer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools,settings,functions
from functions import audio_manager
from .threads import DownloadThread, MergeThread, SaveThread

with open("data/json/files/all_reciters.json","r",encoding="utf-8-sig") as file:
    reciters=json.load(file)
from .audio_player import PlayerAudioMixin
from .merger_saver import PlayerMergerSaverMixin
from .tafseer_and_info import PlayerTafseerAndInfoMixin
from .navigation_display import PlayerNavigationDisplayMixin
from .context_menu import PlayerContextMenuMixin


class QuranPlayer(PlayerContextMenuMixin, PlayerNavigationDisplayMixin, PlayerTafseerAndInfoMixin, PlayerMergerSaverMixin, PlayerAudioMixin, qt.QDialog):
    def __init__(self,p,text,index:int,type,category):
        super().__init__(p)
        self.setWindowState(qt2.Qt.WindowState.WindowMaximized)
        self.font_is_bold = settings.settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings.settings_handler.get("font", "size") or 12)
        self.currentReciter=int(settings.settings_handler.get("g","reciter") or 0)
        self.resize(1200,600)
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        self.type=type
        self.times=int(settings.settings_handler.get("quranPlayer","times") or 1)
        self.currentTime=1
        self.category=category
        self.was_playing_before_action = False
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            guiTools.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج الآيات لن تعمل.")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.save_mode = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.media=QMediaPlayer(self)
        self.apply_speed()
        self.audioOutput=QAudioOutput(self)
        self.audioOutput.setDevice(audio_manager.get_audio_device("quran_text"))
        self.media.setAudioOutput(self.audioOutput)
        self.media.mediaStatusChanged.connect(self.on_state)
        self.index=index
        self.quranText=text.split("\n")
        self.show_diacritics = True
        self.original_ayah_text = self.quranText[self.index]
        self.text=guiTools.QReadOnlyTextEdit(viewer_name="quranPlayer")
        option = self.text.document().defaultTextOption()
        option.setAlignment(qt2.Qt.AlignmentFlag.AlignRight)
        option.setTextDirection(qt2.Qt.LayoutDirection.RightToLeft)
        self.text.document().setDefaultTextOption(option)
        self.update_display_text()
        self.text.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.OnContextMenu)
        self.text.setFocus()
        self.media_progress=qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.media_progress.setRange(0,100)
        self.media_progress.valueChanged.connect(self.set_position_from_slider)
        self.media.durationChanged.connect(self.update_slider)
        self.media.positionChanged.connect(self.update_slider)
        self.media_progress.setAccessibleDescription("يمكنك استخدام الاختصار control مع الأرقام من 1 إلى 9 للذهاب إلى نسبة مئوية من المقطع")
        self.media_progress.setStyleSheet("QSlider{min-height:30px;} QSlider::groove:horizontal{height:10px;background:#000000;border-radius:5px;} QSlider::sub-page:horizontal{background:#0066CC;border-radius:5px;} QSlider::add-page:horizontal{background:#000000;border-radius:5px;} QSlider::handle:horizontal{background:#FFFFFF;width:24px;height:24px;margin:-7px 0;border-radius:12px;}")
        self.time_label = guiTools.QNavigableLabel()
        self.time_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.time_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Preferred)
        progress_time_layout = qt.QVBoxLayout()
        progress_time_layout.addWidget(self.media_progress)
        progress_time_layout.addWidget(self.time_label)
        self.font_laybol=qt.QLabel("حجم الخط")
        self.font_laybol.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font = qt.QSpinBox()
        self.show_font.setRange(1, 100)
        self.show_font.setValue(self.font_size)
        self.show_font.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.show_font.setAccessibleName("حجم النص")
        self.show_font.setAccessibleDescription("للتحكم في حجم النص من أي مكان: نستخدم الاختصارات control plus equals للتكبير و control plus dash للتصغير")
        self.show_font.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.show_font.valueChanged.connect(self.font_size_changed)
        self.N_aya=guiTools.QPushButton("الآيا التالية")
        self.N_aya.setAutoDefault(False)
        self.N_aya.setStyleSheet("background-color: #0000AA; color: white;")
        self.N_aya.clicked.connect(self.onNextAyah)
        self.N_aya.setAccessibleDescription("alt زائد السهم الأيمن")
        self.PPS=guiTools.QPushButton("تشغيل")
        self.PPS.setAutoDefault(False)
        self.PPS.setAccessibleDescription("space")
        self.PPS.clicked.connect(self.on_play)
        self.PPS.setStyleSheet("background-color: #0000AA; color: white;")
        self.P_aya=guiTools.QPushButton("الآيا السابقة")
        self.P_aya.setAutoDefault(False)
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
        self.saveAllButton = guiTools.QPushButton("حفظ الآيات")
        self.saveAllButton.setAutoDefault(False)
        self.saveAllButton.setStyleSheet("background-color: #0000AA; color: white;")
        self.saveAllButton.clicked.connect(self.onSaveAllActionTriggered)
        self.saveAllButton.setAccessibleDescription("control plus shift plus H")
        layout=qt.QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addLayout(progress_time_layout)
        self.merge_feedback_label = guiTools.QNavigableLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_action_button = guiTools.QPushButton("إلغاء العملية")
        self.merge_action_button.setObjectName("cancelMergeButton")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.setMinimumHeight(35)
        self.merge_action_button.setMinimumWidth(160)
        self.merge_action_button.setMaximumWidth(210)
        self.merge_action_button.setStyleSheet("QPushButton#cancelMergeButton {background-color: #8B0000; color: white; border: 2px solid #B22222; padding: 6px 12px; border-radius: 5px; font-weight: bold;} QPushButton#cancelMergeButton:hover {background-color: #A52A2A; border-color: #FF4D4D;}")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        self.resume_download_button = guiTools.QPushButton("استئناف")
        self.resume_download_button.setAutoDefault(False)
        self.resume_download_button.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 5px 10px; border-radius: 5px;} QPushButton:hover {background-color: #0000CC;}")
        self.resume_download_button.setVisible(False)
        self.resume_download_button.clicked.connect(self.resume_current_download)
        merge_layout = qt.QHBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.resume_download_button)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        layout.addWidget(self.merge_widget)
        layout.addWidget(self.font_laybol)
        layout.addWidget(self.show_font)
        self.options_info_label = guiTools.QNavigableLabel("لمزيد من خيارات الآية، نستخدم زر التطبيقات أو click الأيمن على الآية")
        self.options_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.options_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.options_info_label)
        layout1=qt.QHBoxLayout()
        layout1.addWidget(self.changeCurrentReciterButton)
        layout1.addWidget(self.P_aya)
        layout1.addWidget(self.PPS)
        layout1.addWidget(self.N_aya)
        layout1.addWidget(self.mergeButton)
        layout1.addWidget(self.saveAllButton)
        layout.addLayout(layout1)
        qt1.QShortcut("space",self).activated.connect(self.on_play)
        qt1.QShortcut("ctrl+g",self).activated.connect(self.gotoayah)
        qt1.QShortcut("alt+right",self).activated.connect(self.onNextAyah)
        qt1.QShortcut("alt+left",self).activated.connect(self.onPreviousAyah)
        qt1.QShortcut("escape",self).activated.connect(self.safeClose)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("shift+up",self).activated.connect(self.volume_up)
        qt1.QShortcut("shift+down",self).activated.connect(self.volume_down)
        qt1.QShortcut("ctrl+r", self).activated.connect(self.getCurrentAyahTanzel)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.getCurentAyahIArab)
        qt1.QShortcut("ctrl+e", self).activated.connect(self.getCurentAyahQiraat)
        qt1.QShortcut("ctrl+u", self).activated.connect(self.getCurentAyahMeanings)
        qt1.QShortcut("ctrl+k", self).activated.connect(self.getCurentAyahSarf)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.getCurentAyahTafseer)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.getCurentAyahTranslation)
        qt1.QShortcut("ctrl+f", self).activated.connect(self.getAyahInfo)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.mergeAyahs)
        qt1.QShortcut("ctrl+shift+h", self).activated.connect(self.onSaveAllActionTriggered)
        qt1.QShortcut("ctrl+h", self).activated.connect(self.onSaveCurrentAyahActionTriggered)
        self.update_font_size()
        qt2.QTimer.singleShot(0, self.on_play)

    def safeClose(self):
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.stop()
            qt2.QTimer.singleShot(100,self.close)
        else: self.close()

    def closeEvent(self, event):
        if self.is_merging:
            if self.merge_phase == 'downloading':
                guiTools.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء مرحلة تحميل الآيات. الرجاء الانتظار.")
                event.ignore()
            elif self.merge_phase == 'saving':
                guiTools.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء مرحلة حفظ الآيات. الرجاء الانتظار.")
                event.ignore()
            elif self.merge_phase == 'merging':
                guiTools.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء مرحلة دمج الآيات. الرجاء الانتظار.")
                event.ignore()
            else: event.ignore()
        else:
            self.media.stop()
            super().closeEvent(event)
