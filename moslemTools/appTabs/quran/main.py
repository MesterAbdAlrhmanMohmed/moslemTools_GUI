import gui.translationViewer
import gui, guiTools, functions, re, os, requests, subprocess, shutil, traceback
import ujson as json
from settings.app import appName
from settings import settings_handler
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from .threads import DownloadThread, MergeThread, PreMergeCheckThread, SaveThread, QuranLoader

with open("data/json/files/all_reciters.json", "r", encoding="utf-8-sig") as file:
    reciters = json.load(file)
from .context_menu import QuranTabContextMenuMixin
from .navigation_search import QuranTabNavSearchMixin
from .actions_handler import QuranTabActionsMixin
from .merger_saver import QuranTabMergerSaverMixin


class Quran(QuranTabContextMenuMixin, QuranTabNavSearchMixin, QuranTabActionsMixin, QuranTabMergerSaverMixin, qt.QWidget):
    def __init__(self):
        super().__init__()
        qt1.QShortcut("ctrl+p",self).activated.connect(self.onListenActionTriggert)
        qt1.QShortcut("ctrl+t",self).activated.connect(self.onTafseerActionTriggered)
        qt1.QShortcut("ctrl+l",self).activated.connect(self.onTranslationActionTriggered)
        qt1.QShortcut("ctrl+i",self).activated.connect(self.onIarabActionTriggered)
        qt1.QShortcut("ctrl+u",self).activated.connect(self.onMeaningsActionTriggered)
        qt1.QShortcut("ctrl+k",self).activated.connect(self.onSarfActionTriggered)
        qt1.QShortcut("ctrl+f",self).activated.connect(self.onCategoryInfoTriggered)
        qt1.QShortcut("ctrl+alt+d", self).activated.connect(self.onMergeActionTriggered)
        qt1.QShortcut("ctrl+h", self).activated.connect(self.onSaveActionTriggered)
        qt1.QShortcut("ctrl+1", self).activated.connect(lambda: guiTools.FromToSurahWidget(self, 0).exec())
        qt1.QShortcut("ctrl+2", self).activated.connect(lambda: guiTools.FromToSurahWidget(self, 1).exec())
        qt1.QShortcut("ctrl+3", self).activated.connect(lambda: guiTools.FromToSurahWidget(self, 2).exec())
        qt1.QShortcut("ctrl+4", self).activated.connect(lambda: guiTools.FromToSurahWidget(self, 3).exec())
        qt1.QShortcut("ctrl+5", self).activated.connect(lambda: guiTools.FromToSurahWidget(self, 4).exec())
        self.infoData = []
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.is_saving = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        current_theme = settings_handler.get("g", "theme") or "dark"
        if current_theme == "light":
            self.setStyleSheet("QWidget{color:#1e1e1e;}QLineEdit{background-color:#ffffff;color:#1e1e1e;border:1px solid #cccccc;border-radius:5px;padding:5px;}QComboBox,QLabel{border:1px solid #cccccc;border-radius:5px;padding:5px;color:#1e1e1e;}QLineEdit:focus{border:1px solid #0078d7;}QComboBox QAbstractItemView::item:selected{background-color:blue;color:white;}QPushButton{background-color:#0056b3;color:white;border:none;border-radius:5px;padding:5px;}QPushButton:hover{background-color:#003d80;}QPushButton#customButton{background-color:#008000;color:white;border:none;padding:16px 18px;border-radius:6px;}QPushButton#customButton:hover{background-color:#006600;}QPushButton#cancelMergeButton{background-color:#8B0000;color:white;border:2px solid #B22222;border-radius:5px;padding:6px 12px;font-weight:bold;}QPushButton#cancelMergeButton:hover{background-color:#A52A2A;border-color:#FF4D4D;}QListWidget{background-color:#ffffff;color:#1e1e1e;border:1px solid #cccccc;border-radius:5px;padding:5px;}QListWidget::item{padding:6px 10px;margin:3px;border-radius:5px;color:#1e1e1e;}QListWidget::item:hover{background-color:#e5e5e5;color:#1e1e1e;}QListWidget::item:selected{background-color:red;color:#ffffff;}QMenu{background-color:#ffffff;color:#1e1e1e;}QMenu::item:selected{background-color:#0078d7;color:#ffffff;}")
        else:
            self.setStyleSheet("QWidget{color:#f0f0f0;}QLineEdit{background-color:#3e3e3e;border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QComboBox,QLabel{border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QLineEdit:focus{border:1px solid #0078d7;}QComboBox QAbstractItemView::item:selected{background-color:blue;color:white;}QPushButton{background-color:#0056b3;color:white;border:none;border-radius:5px;padding:5px;}QPushButton:hover{background-color:#003d80;}QPushButton#customButton{background-color:#008000;color:white;border:none;padding:16px 18px;border-radius:6px;}QPushButton#customButton:hover{background-color:#006600;}QPushButton#cancelMergeButton{background-color:#8B0000;color:white;border:2px solid #B22222;border-radius:5px;padding:6px 12px;font-weight:bold;}QPushButton#cancelMergeButton:hover{background-color:#A52A2A;border-color:#FF4D4D;}QListWidget{background-color:#000000;border:1px solid #5a5a5a;border-radius:5px;padding:5px;}QListWidget::item{padding:6px 10px;margin:3px;border-radius:5px;color:#f0f0f0;}QListWidget::item:hover{background-color:#333333;color:#f0f0f0;}QListWidget::item:selected{background-color:red;color:#ffffff;}QMenu{background-color:#3e3e3e;color:#f0f0f0;}QMenu::item:selected{background-color:#0078d7;}")
        browse_layout = qt.QHBoxLayout()
        browse_layout.setContentsMargins(15, 0, 15, 0)

        left_layout = qt.QVBoxLayout()
        self.by = qt.QLabel("التصفح ب")
        self.by.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.by)
        self.type = qt.QComboBox()
        self.type.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.type.setMinimumWidth(100)
        self.type.setMaximumWidth(150)
        self.type.setAccessibleName("التصفح ب")
        self.type.addItems(["سور", "صفحات", "أجزاء", "أرباع", "أحزاب"])
        self.type.currentIndexChanged.connect(self.onTypeChanged)
        left_layout.addWidget(self.type)

        browse_layout.addStretch(1)
        browse_layout.addLayout(left_layout)
        browse_layout.addStretch(2)

        self.custom = guiTools.QPushButton("التصفح المخصص")
        self.custom.setMinimumHeight(52)
        self.custom.setMinimumWidth(160)
        self.custom.setMaximumWidth(180)
        self.custom.setObjectName("customButton")
        self.custom.setShortcut("ctrl+c")
        self.custom.setAccessibleDescription("control plus c")
        self.custom.clicked.connect(self.onCostumBTNClicked)
        browse_layout.addWidget(self.custom, 0, qt2.Qt.AlignmentFlag.AlignCenter)

        browse_layout.addStretch(1)

        font = qt1.QFont()
        font.setBold(True)
        self.show_surah_number_cb = qt.QCheckBox("عرض رقم السورة")
        self.show_surah_number_cb.setFont(font)
        show_surah_num_enabled = settings_handler.get("quran", "show_surah_number") != "False"
        self.show_surah_number_cb.setChecked(show_surah_num_enabled)
        self.show_surah_number_cb.stateChanged.connect(self.on_surah_number_toggled)
        browse_layout.addWidget(self.show_surah_number_cb, 0, qt2.Qt.AlignmentFlag.AlignCenter)

        browse_layout.addStretch(2)

        right_layout = qt.QVBoxLayout()
        self.view_mode_label = qt.QLabel("طريقة عرض العناصر")
        self.view_mode_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.view_mode_label)
        self.view_mode_combo = qt.QComboBox()
        self.view_mode_combo.setSizeAdjustPolicy(qt.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.view_mode_combo.setMinimumWidth(100)
        self.view_mode_combo.setMaximumWidth(150)
        self.view_mode_combo.setAccessibleName("طريقة عرض العناصر")
        self.view_mode_combo.addItems(["عمودي", "شبكي"])
        grid_enabled = settings_handler.get("quran", "grid_view") == "True"
        self.view_mode_combo.setCurrentIndex(1 if grid_enabled else 0)
        self.view_mode_combo.currentIndexChanged.connect(self.on_view_mode_changed)
        right_layout.addWidget(self.view_mode_combo)

        browse_layout.addLayout(right_layout)
        browse_layout.addStretch(1)
        layout.addLayout(browse_layout)
        self.serch = qt.QLabel("البحث عن محتوى فئة")
        self.serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.serch)
        self.search_bar = qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن محتوى فئة")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.info = guiTools.QListWidget()
        self.info.setSpacing(3)
        self.info.setFont(font)
        self.info.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.info.customContextMenuRequested.connect(self.onContextMenu)
        self.info.itemActivated.connect(self.onItemTriggered)
        self.on_view_mode_changed(self.view_mode_combo.currentIndex())
        layout.addWidget(self.info)
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
        guide_layout = qt.QHBoxLayout()
        self.info_of_quran= guiTools.QPushButton("معلومات عن المصحف")
        self.info_of_quran.setShortcut("ctrl+shift+q")
        self.info_of_quran.setAccessibleDescription("control plus shift plus Q")
        self.info_of_quran.setMinimumHeight(35)
        self.info_of_quran.setMinimumWidth(160)
        self.info_of_quran.setMaximumWidth(210)
        self.info_of_quran.clicked.connect(lambda: guiTools.TextViewer(self, "معلومات عن المصحف", ("معلومات عامة عن مصحف المدينة النبوية برواية حفص عن عاصم:\nعدد السور: 114 سورة (86 مكية و28 مدنية، بحسب التقسيم المشهور).\nعدد الآيات: 6236 آية، وفق العدد الكوفي المعتمد في مصحف المدينة برواية حفص عن عاصم.\nعدد الأجزاء: 30 جزءًا.\nعدد الأحزاب: 60 حزبًا.\nعدد الأرباع: 240 ربعًا (4 أرباع في كل حزب، و8 أرباع في كل جزء).\nعدد سجدات التلاوة: 15 سجدة.\nعدد الصفحات: 604 صفحة في مصحف المدينة النبوية الشهير (المصحف العادي).\n\nملاحظات:\nعدد الكلمات: نحو 77430 كلمة، بحسب طريقة العد المستخدمة.\nعدد الحروف: يُذكر في بعض كتب الإحصاء 323671 حرفًا، مع وجود اختلاف في أعداد الحروف بحسب منهج العد.\nعدد الركوعات: 558 ركوعًا، وهو العدد المتداول في المصاحف المعاصرة، مع وجود تقسيمات أخرى للركوع.\n\nتنبيه:\nقد تختلف بعض الإحصاءات القرآنية، مثل عدد الكلمات والحروف وتصنيف بعض السور مكيًا ومدنيًا، باختلاف منهج العد أو التصنيف.")).exec())
        self.info1 = guiTools.QNavigableLabel()
        self.info1.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info1.setText("لخيارات العنصر المحدد، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.info1.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        guide_layout.addWidget(self.info1, 1)
        guide_layout.addWidget(self.info_of_quran, 0)
        layout.addLayout(guide_layout)
        self.loader_thread = None
