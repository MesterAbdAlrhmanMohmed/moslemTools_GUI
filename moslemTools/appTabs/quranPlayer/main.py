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
from .context_menu import PlayerContextMenuMixin
from .favorites_and_search import PlayerFavoritesAndSearchMixin
from .download_manager import PlayerDownloadManagerMixin
from .batch_and_merge import PlayerBatchAndMergeMixin
from .playback_modes import PlayerPlaybackModesMixin
from .audio_controls import PlayerAudioControlsMixin


class QuranPlayer(PlayerContextMenuMixin, PlayerFavoritesAndSearchMixin, PlayerDownloadManagerMixin, PlayerBatchAndMergeMixin, PlayerPlaybackModesMixin, PlayerAudioControlsMixin, qt.QWidget):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        self.fav_path = os.path.join(os.getenv('appdata'), "moslemTools_GUI", "quran_favorites.json")
        self.fav_manager = FavoritesManager(self.fav_path)
        self.favorites = self.fav_manager.favorites
        self.show_favorites_only = False
        if not os.path.exists(self.ffmpeg_path):
            guiTools.qMessageBox.MessageBox.error(self, "خطأ فادح", "لم يتم العثور على أداة الدمج FFmpeg. خاصية دمج السور لن تعمل.")
        qt1.QShortcut("ctrl+s", self).activated.connect(self.stop_audio_completely)
        qt1.QShortcut("space", self).activated.connect(self.play)
        qt1.QShortcut("alt+right", self).activated.connect(self.skip_forward_5s)
        qt1.QShortcut("alt+left", self).activated.connect(self.skip_backward_5s)
        qt1.QShortcut("alt+up", self).activated.connect(self.skip_forward_10s)
        qt1.QShortcut("alt+down", self).activated.connect(self.skip_backward_10s)
        qt1.QShortcut("ctrl+right", self).activated.connect(self.skip_forward_30s)
        qt1.QShortcut("ctrl+left", self).activated.connect(self.skip_backward_30s)
        qt1.QShortcut("ctrl+up", self).activated.connect(self.skip_forward_1m)
        qt1.QShortcut("ctrl+down", self).activated.connect(self.skip_backward_1m)
        qt1.QShortcut("ctrl+1", self).activated.connect(self.t10)
        qt1.QShortcut("ctrl+2", self).activated.connect(self.t20)
        qt1.QShortcut("ctrl+3", self).activated.connect(self.t30)
        qt1.QShortcut("ctrl+4", self).activated.connect(self.t40)
        qt1.QShortcut("ctrl+5", self).activated.connect(self.t50)
        qt1.QShortcut("ctrl+6", self).activated.connect(self.t60)
        qt1.QShortcut("ctrl+7", self).activated.connect(self.t70)
        qt1.QShortcut("ctrl+8", self).activated.connect(self.t80)
        qt1.QShortcut("ctrl+9", self).activated.connect(self.t90)
        qt1.QShortcut("shift+up", self).activated.connect(self.increase_volume)
        qt1.QShortcut("shift+down", self).activated.connect(self.decrease_volume)
        qt1.QShortcut("shift+right", self).activated.connect(self.increase_speed)
        qt1.QShortcut("shift+left", self).activated.connect(self.decrease_speed)
        qt1.QShortcut("shift+1", self).activated.connect(self.onChangeStartingPosition)
        qt1.QShortcut("shift+2", self).activated.connect(self.onChangeEndingPosition)
        qt1.QShortcut("backspace", self).activated.connect(self.removePosition)
        self.volume_timer = qt2.QTimer(self)
        self.volume_timer.setSingleShot(True)
        self.volume_timer.timeout.connect(self.restore_duration_text)
        self.pending_seek_resume = False
        self.bookmarksPosition = None
        self.isAMustToGoToBookmark = False
        self.startingPosition = None
        self.endingPosition = None
        self.repeatFromPositionToPosition = False
        self._is_seeking_loop = False
        self.merge_list = []
        self.download_batch_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.is_downloading_batch = False
        self.is_downloading_all_app = False
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.successfully_downloaded_in_batch = []
        self.full_batch_cancellation_requested = False
        self.excluded_surahs_in_batch = []
        self.first_merge_selection_index = None
        self.first_download_selection_index = None
        self.batch_download_target = 'app'
        self.download_thread = None
        self.is_loaded = False
        self.reciters_data = {}
        self.setStyleSheet("""
            QPushButton {
                background-color: #0056b3;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #004085;
            }
            QPushButton:pressed {
                background-color: #002752;
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #a0aec0;
            }
        """)
        self.recitersLabel = qt.QLabel("اختيار قارئ")
        self.recitersLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.reciterSearchEdit = qt.QLineEdit()
        self.reciterSearchEdit.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.reciterSearchEdit.setPlaceholderText("ابحث عن قارئ")
        self.reciterSearchEdit.setObjectName("reciterSearch")
        self.reciterSearchEdit.textChanged.connect(self.reciter_onsearch)
        self.recitersListWidget = guiTools.QListWidget()
        self.recitersListWidget.setSpacing(5)
        self.recitersListWidget.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.recitersListWidget.itemSelectionChanged.connect(self.on_reciter_selected)
        self.recitersListWidget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.recitersListWidget.customContextMenuRequested.connect(self.open_reciter_menu)
        self.reciter_fav_info_label = guiTools.QNavigableLabel("لإضافة القارئ إلى قائمة المفضلة أو إزالته، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.reciter_fav_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.reciter_fav_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.view_favorites_btn = guiTools.QPushButton("عرض المفضلة")
        self.view_favorites_btn.clicked.connect(self.toggle_favorites)
        self.surahsLabel = qt.QLabel("السور")
        self.surahsLabel.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahSearchEdit = qt.QLineEdit()
        self.surahSearchEdit .setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.surahSearchEdit.setPlaceholderText("ابحث عن سورة")
        self.surahSearchEdit.setObjectName("surahSearch")
        self.surahSearchEdit.textChanged.connect(self.surah_onsearch)
        self.surahListWidget = guiTools.QListWidget()
        self.surahListWidget.setSpacing(5)
        self.surahListWidget.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.surahListWidget.clicked.connect(self.play_selected_audio)
        self.progressBar = qt.QProgressBar()
        self.progressBar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progressBar.setVisible(False)
        self.progress_text_label = guiTools.QNavigableLabel("")
        self.progress_text_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progress_text_label.setVisible(False)
        self.pause_download_button = guiTools.QPushButton("إيقاف مؤقت")
        self.pause_download_button.setShortcut("ctrl+p")
        self.pause_download_button.setAccessibleDescription("control plus p")
        self.pause_download_button.setVisible(False)
        self.pause_download_button.clicked.connect(self.toggle_download_pause)
        self.pause_download_button.setStyleSheet("QPushButton {background-color: #0056b3;color: white;border: none;padding: 6px 12px;border-radius: 6px;}QPushButton:hover {background-color: #004085;}")
        self.cancel_download_button = guiTools.QPushButton("إلغاء التنزيل")
        self.cancel_download_button.setShortcut("ctrl+c")
        self.cancel_download_button.setAccessibleDescription("control plus c")
        self.cancel_download_button.setVisible(False)
        self.cancel_download_button.clicked.connect(self.cancel_current_download)
        self.cancel_download_button.setStyleSheet("QPushButton {background-color: #c42b1c;color: white;border: none;padding: 6px 12px;border-radius: 6px;}QPushButton:hover {background-color: #b1272c;}")
        self.mp = QMediaPlayer()
        self.apply_speed()
        self.au = QAudioOutput()
        self.au.setDevice(audio_manager.get_audio_device("quran_audio"))
        self.au.setVolume(self.load_volume())
        self.mp.setAudioOutput(self.au)
        self.openBookmarks = guiTools.QPushButton("العلامات المرجعية")
        self.openBookmarks.clicked.connect(self.onBookmarkOpened)
        self.openBookmarks.setShortcut("ctrl+shift+b")
        self.openBookmarks.setAccessibleDescription("control plus shift plus b")
        self.openBookmarks.setMinimumHeight(35)
        self.openBookmarks.setMinimumWidth(120)
        self.openBookmarks.setMaximumWidth(160)
        self.User_guide=guiTools.QPushButton("دليل الاختصارات")
        self.User_guide.setMinimumHeight(35)
        self.User_guide.setMinimumWidth(120)
        self.User_guide.setMaximumWidth(160)
        self.User_guide.setShortcut("ctrl+f1")
        self.User_guide.setAccessibleDescription("control plus f1")
        self.User_guide.clicked.connect(lambda:TextViewer(self,"دليل الاختصارات","ctrl+s: إيقاف\nspace: التشغيل والإيقاف المؤقت\nalt زائد السهم الأيمن: التقديم السريع لمدة 5 ثواني\nalt زائد السهم الأيسر: الترجيع السريع لمدة 5 ثواني\nalt زائد السهم الأعلى: التقديم السريع لمدة 10 ثواني\nalt زائد السهم الأسفل: الترجيع السريع لمدة 10 ثواني\nctrl زائد السهم الأيمن: التقديم السريع لمدة 30 ثانية\nctrl زائد السهم الأيسر: الترجيع السريع لمدة 30 ثانية\nctrl زائد السهم الأعلى: التقديم السريع لمدة دقيقة\nctrl زائد السهم الأسفل: الترجيع  السريع لمدة دقيقة\nctrl زائد رقم: الانتقال إلى موضع محدد من المقطع, مثلا ctrl+10 الانتقال إلى 10% من المقطع\nshift زائد السهم الأعلى: رفع الصوت\nshift زائد السهم الأسفل: خفض الصوت\nshift زائد السهم الأيمن: تسريع الصوت\nshift زائد السهم الأيسر: تبطئة الصوت\nالضغط على زر التطبيقات أو click الأيمن على شريط مدة المقطع يسمح بإضافة علامة مرجعية للموضع الحالي").exec())
        font = qt1.QFont()
        font.setBold(True)

        self.playback_options_btn = guiTools.QPushButton("خيارات التشغيل")
        self.playback_options_btn.setFont(font)
        self.playback_options_btn.setMinimumHeight(35)
        self.playback_options_menu = guiTools.QCustomContextMenu(self)
        self.playback_options_menu.setFont(font)
        self.playback_options_menu.setAccessibleName("خيارات التشغيل")

        self.play_all_to_end = qt1.QAction("تشغيل كل السور من السورة المحددة إلى النهاية", self)
        self.play_all_to_end.setCheckable(True)
        self.play_all_to_end.toggled.connect(self.handle_play_all_toggled)
        self.playback_options_menu.addAction(self.play_all_to_end)

        self.play_all_to_start = qt1.QAction("تشغيل كل السور من السورة المحددة إلى البداية", self)
        self.play_all_to_start.setCheckable(True)
        self.play_all_to_start.toggled.connect(self.handle_play_all_start_toggled)
        self.playback_options_menu.addAction(self.play_all_to_start)

        self.repeat_surah_button = qt1.QAction("تكرار تشغيل السورة المحددة", self)
        self.repeat_surah_button.setCheckable(True)
        self.repeat_surah_button.toggled.connect(self.handle_repeat_toggled)
        self.playback_options_menu.addAction(self.repeat_surah_button)

        self.playback_options_btn.setMenu(self.playback_options_menu)

        self.download_menu_btn = guiTools.QPushButton("تحميل السور")
        self.download_menu_btn.setFont(font)
        self.download_menu_btn.setMinimumHeight(35)
        self.download_menu = guiTools.QCustomContextMenu(self)
        self.download_menu.setFont(font)
        self.download_menu.setAccessibleName("تحميل السور")

        self.dl_all = qt1.QAction("تحميل جميع السور المتاحة لهذا القارئ في الجهاز", self)
        self.dl_all.triggered.connect(self.download_all_soar)
        self.download_menu.addAction(self.dl_all)

        self.dl_all_app = qt1.QAction("تحميل جميع السور المتاحة لهذا القارئ في التطبيق", self)
        self.dl_all_app.triggered.connect(self.download_all_audios_to_app)
        self.download_menu.addAction(self.dl_all_app)

        self.delete = qt.QWidgetAction(self)
        self.delete_btn = guiTools.QPushButton("حذف كل السور للقارئ الحالي من التطبيق")
        self.delete_btn.setFont(font)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c42b1c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #b1272c;
            }
            QPushButton:pressed {
                background-color: #8e1f24;
            }
        """)
        self.delete_btn.clicked.connect(lambda: (self.download_menu.close(), self.delete_surah()))
        self.delete.setDefaultWidget(self.delete_btn)
        self.delete.setVisible(False)
        self.delete.triggered.connect(lambda: (self.download_menu.close(), self.delete_surah()))
        self.download_menu.addAction(self.delete)

        self.download_menu_btn.setMenu(self.download_menu)
        self.download_menu.aboutToShow.connect(self.check_all_surahs_downloaded)

        self.merge_menu_btn = guiTools.QPushButton("دمج السور")
        self.merge_menu_btn.setFont(font)
        self.merge_menu_btn.setMinimumHeight(35)
        self.merge_menu = guiTools.QCustomContextMenu(self)
        self.merge_menu.setFont(font)
        self.merge_menu.setAccessibleName("دمج السور")

        self.merge_all_from_start_button = qt1.QAction("دمج كل السور من البداية إلى النهاية", self)
        self.merge_all_from_start_button.triggered.connect(self.prepare_merge_all_from_start)
        self.merge_menu.addAction(self.merge_all_from_start_button)

        self.merge_all_from_end_button = qt1.QAction("دمج كل السور من النهاية إلى البداية", self)
        self.merge_all_from_end_button.triggered.connect(self.prepare_merge_all_from_end)
        self.merge_menu.addAction(self.merge_all_from_end_button)

        self.merge_menu_btn.setMenu(self.merge_menu)

        self.merge_menu_btn.setEnabled(False)
        self.download_menu_btn.setEnabled(False)

        self.Slider = qt.QSlider(qt2.Qt.Orientation.Horizontal)
        self.Slider.setStyleSheet("QSlider{min-height:30px; margin: 5px 0;} QSlider::groove:horizontal{height:8px;background:#2a2a2a;border-radius:4px;} QSlider::sub-page:horizontal{background:#0056b3;border-radius:4px;} QSlider::add-page:horizontal{background:#2a2a2a;border-radius:4px;} QSlider::handle:horizontal{background:#FFFFFF;width:20px;height:20px;margin:-6px 0;border-radius:10px;}")
        self.Slider.setAccessibleName("التحكم في تقدم السورة")
        self.Slider.setRange(0, 100)
        self.Slider.setTracking(True)
        self.Slider.valueChanged.connect(self.set_position_from_slider)
        self.Slider.sliderReleased.connect(self._check_seek_resume)
        self.Slider.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.Slider.customContextMenuRequested.connect(self.onAddNewBookmark)
        self.mp.durationChanged.connect(self.update_slider)
        self.mp.positionChanged.connect(self.update_slider)
        self.duration = guiTools.QNavigableLabel()
        self.duration.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.duration.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.mp.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.mp.playbackStateChanged.connect(lambda state: self.update_playing_surah_item() if hasattr(self, 'update_playing_surah_item') else None)
        self.info_menu = guiTools.QNavigableLabel("لخيارات السورة، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info_menu.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info_menu.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label = guiTools.QNavigableLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_feedback_label.setVisible(False)
        self.batch_download_feedback_label = guiTools.QNavigableLabel()
        self.batch_download_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.batch_download_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.batch_download_feedback_label.setVisible(False)
        self.merge_action_button = guiTools.QPushButton("بدء دمج السور المحددة")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        self.merge_action_button.setVisible(False)
        self.batch_download_action_button = guiTools.QPushButton("بدء تحميل السور المحددة")
        self.batch_download_action_button.clicked.connect(self.handle_batch_download_action)
        self.batch_download_action_button.setVisible(False)
        recitersLayout = qt.QVBoxLayout()
        recitersLayout.setSpacing(10)
        recitersLayout.addWidget(self.recitersLabel)
        recitersLayout.addWidget(self.reciterSearchEdit)
        recitersLayout.addWidget(self.recitersListWidget)
        recitersLayout.addWidget(self.reciter_fav_info_label)
        recitersLayout.addWidget(self.view_favorites_btn)
        surahsLayout = qt.QVBoxLayout()
        surahsLayout.setSpacing(10)
        surahsLayout.addWidget(self.surahsLabel)
        surahsLayout.addWidget(self.surahSearchEdit)
        surahsLayout.addWidget(self.surahListWidget)
        surahsLayout.addWidget(self.info_menu)
        surahsLayout.addWidget(self.merge_feedback_label)
        surahsLayout.addWidget(self.batch_download_feedback_label)
        merge_action_layout = qt.QVBoxLayout()
        merge_action_layout.setSpacing(8)
        merge_action_layout.addWidget(self.merge_action_button)
        merge_action_layout.addWidget(self.batch_download_action_button)
        surahsLayout.addLayout(merge_action_layout)
        topLayout = qt.QHBoxLayout()
        topLayout.setSpacing(20)
        topLayout.addLayout(recitersLayout)
        topLayout.addLayout(surahsLayout)
        actions_layout = qt.QHBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.addWidget(self.download_menu_btn)
        actions_layout.addWidget(self.merge_menu_btn)
        actions_layout.addWidget(self.playback_options_btn)
        layout = qt.QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        layout.addLayout(topLayout)
        layout.addLayout(actions_layout)
        layout.addWidget(self.Slider)
        progress_cancel_layout = qt.QHBoxLayout()
        progress_cancel_layout.setSpacing(10)
        progress_cancel_layout.addWidget(self.pause_download_button)
        progress_cancel_layout.addWidget(self.progressBar)
        progress_cancel_layout.addWidget(self.progress_text_label)
        progress_cancel_layout.addWidget(self.cancel_download_button)
        layout.addLayout(progress_cancel_layout)
        layout1 = qt.QHBoxLayout()
        layout1.setSpacing(10)
        layout1.addWidget(self.User_guide, 0)
        layout1.addWidget(self.duration, 1)
        layout1.addWidget(self.openBookmarks, 0)
        layout.addLayout(layout1)
        self.setLayout(layout)
        self.surahListWidget.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.surahListWidget.customContextMenuRequested.connect(self.open_context_menu)
        self.cleanup_pending_deletions()
        self.load_data()
        self.is_loaded = True

    def showEvent(self, event):
        if not self.is_loaded:
            self.load_data()
            self.is_loaded = True
        super().showEvent(event)
