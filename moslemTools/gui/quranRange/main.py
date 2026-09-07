import os
import functions
import guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from settings import settings_handler
from .actions_handler import QuranRangeActionsMixin
from .merger_saver import QuranRangeMergerSaverMixin


class QuranRange(QuranRangeActionsMixin, QuranRangeMergerSaverMixin, qt.QDialog):
    def __init__(self, p, index: int):
        super().__init__()
        self.p = p
        self.index = index
        self.original_height = 300
        self.merge_ui_height = 450
        self.resize(300, self.original_height)
        self.ffmpeg_path = os.path.join("data", "bin", "ffmpeg.exe")
        self.merge_list = []
        self.files_to_delete_after_merge = []
        self.is_merging = False
        self.save_mode = False
        self.merge_phase = 'idle'
        self.cancellation_requested = False
        self.completed_merge_downloads = set()
        self.current_download_url = None
        self.currentReciter = int(settings_handler.get("g", "reciter"))
        font = qt1.QFont()
        font.setBold(True)
        self.setFont(font)
        item_name = ""
        if index == 0:
            self.surahs = functions.quranJsonControl.getSurahs()
            self.setWindowTitle("تحديد سور القرآن الكريم")
            item_name = "السورة"
        elif index == 1:
            self.surahs = functions.quranJsonControl.getPage()
            self.setWindowTitle("تحديد صفحات القرآن الكريم")
            item_name = "الصفحة"
        elif index == 2:
            self.surahs = functions.quranJsonControl.getJuz()
            self.setWindowTitle("تحديد أجزاء القرآن الكريم")
            item_name = "الجزء"
        elif index == 3:
            self.surahs = functions.quranJsonControl.getHezb()
            self.setWindowTitle("تحديد أرباع القرآن الكريم")
            item_name = "الربع"
        elif index == 4:
            self.surahs = functions.quranJsonControl.getHizb()
            self.setWindowTitle("تحديد أحزاب القرآن الكريم")
            item_name = "الحزب"
        self.label_from_surah = qt.QLabel(f"من {item_name}")
        self.combo_from_surah = qt.QComboBox()
        self.combo_from_surah.setAccessibleName(f"من {item_name}")
        self.combo_from_surah.addItems(self.surahs.keys())
        self.combo_from_surah.setFont(font)
        self.label_from_verse = qt.QLabel("من الآية")
        self.spin_from_verse = qt.QSpinBox()
        self.spin_from_verse.setAccessibleName("من الآية")
        self.spin_from_verse.setMinimumWidth(120)
        self.spin_from_verse.setFont(font)
        self.label_to_surah = qt.QLabel(f"إلى {item_name}")
        self.combo_to_surah = qt.QComboBox()
        self.combo_to_surah.setAccessibleName(f"إلى {item_name}")
        self.combo_to_surah.addItems(self.surahs.keys())
        self.combo_to_surah.setFont(font)
        self.label_to_verse = qt.QLabel("إلى الآية")
        self.spin_to_verse = qt.QSpinBox()
        self.spin_to_verse.setAccessibleName("إلى الآية")
        self.spin_to_verse.setMinimumWidth(120)
        self.spin_to_verse.setFont(font)
        self.go = guiTools.QPushButton("خيارات")
        self.go.setStyleSheet("""
        QPushButton {
            background-color: #1e7e34; color: white; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold;
        }
        QPushButton:hover { background-color: #19692c; }
        """)
        self.go.setFont(font)
        self.merge_feedback_label = guiTools.QNavigableLabel()
        self.merge_feedback_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.merge_feedback_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_progress_bar = qt.QProgressBar()
        self.merge_progress_bar.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.merge_action_button = guiTools.QPushButton("إلغاء العملية")
        self.merge_action_button.setAutoDefault(False)
        self.merge_action_button.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 8px 18px; border-radius: 5px; font-weight: bold;} QPushButton:hover {background-color: #A52A2A;}")
        self.merge_action_button.clicked.connect(self.handle_merge_action)
        merge_layout = qt.QVBoxLayout()
        merge_layout.addWidget(self.merge_feedback_label)
        merge_layout.addWidget(self.merge_progress_bar)
        merge_layout.addWidget(self.merge_action_button)
        self.merge_widget = qt.QWidget()
        self.merge_widget.setLayout(merge_layout)
        self.merge_widget.setVisible(False)
        h_layout1 = qt.QHBoxLayout()
        h_layout1.setSpacing(10)
        h_layout1.addWidget(self.combo_from_surah)
        h_layout1.addWidget(self.label_from_surah)
        h_layout1.addStretch()
        h_layout2 = qt.QHBoxLayout()
        h_layout2.setSpacing(10)
        h_layout2.addWidget(self.spin_from_verse)
        h_layout2.addWidget(self.label_from_verse)
        h_layout2.addStretch()
        h_layout3 = qt.QHBoxLayout()
        h_layout3.setSpacing(10)
        h_layout3.addWidget(self.combo_to_surah)
        h_layout3.addWidget(self.label_to_surah)
        h_layout3.addStretch()
        h_layout4 = qt.QHBoxLayout()
        h_layout4.setSpacing(10)
        h_layout4.addWidget(self.spin_to_verse)
        h_layout4.addWidget(self.label_to_verse)
        h_layout4.addStretch()
        self.controls_widget = qt.QWidget()
        controls_layout = qt.QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        controls_layout.addLayout(h_layout1)
        controls_layout.addLayout(h_layout2)
        controls_layout.addLayout(h_layout3)
        controls_layout.addLayout(h_layout4)
        controls_layout.addWidget(self.go)
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addWidget(self.controls_widget)
        main_layout.addWidget(self.merge_widget)
        self.combo_from_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.combo_to_surah.currentIndexChanged.connect(self.update_spin_boxes)
        self.spin_from_verse.valueChanged.connect(self.validate_verse_ranges)
        self.spin_to_verse.valueChanged.connect(self.validate_verse_ranges)
        self.go.clicked.connect(self.onGo)
        self.update_spin_boxes(set_to_verse_to_max=True)
        qt1.QShortcut("ctrl+o", self).activated.connect(self.onOpen)
        qt1.QShortcut("ctrl+p", self).activated.connect(self.onListenActionTriggert)
        qt1.QShortcut("ctrl+t", self).activated.connect(self.onTafseerActionTriggered)
        qt1.QShortcut("ctrl+l", self).activated.connect(self.onTranslationActionTriggered)
        qt1.QShortcut("ctrl+i", self).activated.connect(self.onIarabActionTriggered)
        qt1.QShortcut("ctrl+e", self).activated.connect(self.onQiraatActionTriggered)
        qt1.QShortcut("ctrl+u", self).activated.connect(self.onMeaningsActionTriggered)
        qt1.QShortcut("ctrl+k", self).activated.connect(self.onSarfActionTriggered)
        qt1.QShortcut("ctrl+d", self).activated.connect(self.onMergeActionTriggered)
        qt1.QShortcut("ctrl+h", self).activated.connect(self.onSaveActionTriggered)
        qt1.QShortcut("escape", self).activated.connect(self.close)

    def update_spin_boxes(self, set_to_verse_to_max=False):
        self.spin_from_verse.blockSignals(True)
        self.spin_to_verse.blockSignals(True)
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()
        if to_surah_index < from_surah_index:
            self.combo_to_surah.setCurrentIndex(from_surah_index)
            to_surah_index = from_surah_index
        surah_from_text = self.combo_from_surah.currentText()
        surah_to_text = self.combo_to_surah.currentText()
        num_verses_from = len(self.surahs[surah_from_text][1].split("\n")) if len(self.surahs[surah_from_text]) > 1 else 1
        num_verses_to = len(self.surahs[surah_to_text][1].split("\n")) if len(self.surahs[surah_to_text]) > 1 else 1
        self.spin_from_verse.setRange(1, num_verses_from)
        self.spin_to_verse.setRange(1, num_verses_to)
        if self.spin_from_verse.value() > num_verses_from or self.spin_from_verse.value() < 1:
            self.spin_from_verse.setValue(1)
        if set_to_verse_to_max or self.spin_to_verse.value() > num_verses_to or self.spin_to_verse.value() < 1:
            self.spin_to_verse.setValue(num_verses_to)
        self.spin_from_verse.blockSignals(False)
        self.spin_to_verse.blockSignals(False)
        self.validate_verse_ranges()

    def validate_verse_ranges(self):
        from_surah_index = self.combo_from_surah.currentIndex()
        to_surah_index = self.combo_to_surah.currentIndex()
        from_verse_val = self.spin_from_verse.value()
        to_verse_val = self.spin_to_verse.value()
        if from_surah_index == to_surah_index:
            if to_verse_val < from_verse_val:
                self.spin_to_verse.blockSignals(True)
                self.spin_to_verse.setValue(from_verse_val)
                self.spin_to_verse.blockSignals(False)
        elif from_surah_index > to_surah_index:
            self.combo_to_surah.setCurrentIndex(from_surah_index)
            self.update_spin_boxes(set_to_verse_to_max=True)

    def get_range_label(self):
        from_item = self.combo_from_surah.currentText()
        to_item = self.combo_to_surah.currentText()
        from_ayah = self.spin_from_verse.value()
        to_ayah = self.spin_to_verse.value()
        item_type = ""
        if self.index == 0: item_type = "سورة"
        elif self.index == 1: item_type = "الصفحة"
        elif self.index == 2: item_type = "الجزء"
        elif self.index == 3: item_type = "الربع"
        elif self.index == 4: item_type = "الحزب"
        if from_item == to_item:
            return f"من {item_type} {from_item} آية {from_ayah} إلى آية {to_ayah}"
        else:
            return f"من {item_type} {from_item} آية {from_ayah} إلى {item_type} {to_item} آية {to_ayah}"

    def _get_selected_ayahs(self):
        self.validate_verse_ranges()
        return functions.quranJsonControl.getFromTo(
            self.combo_from_surah.currentIndex() + 1,
            self.spin_from_verse.value(),
            self.combo_to_surah.currentIndex() + 1,
            self.spin_to_verse.value(),
            self.index
        )

    def closeEvent(self, event):
        if self.is_merging:
            if self.merge_phase == 'preparing':
                self.cancellation_requested = True
                if hasattr(self, 'pre_merge_thread') and self.pre_merge_thread.isRunning():
                    self.pre_merge_thread.terminate()
                event.accept()
            elif self.merge_phase == 'downloading':
                guiTools.qMessageBox.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء تحميل الآيات. الرجاء الانتظار.")
                event.ignore()
            elif self.merge_phase == 'saving':
                guiTools.qMessageBox.MessageBox.error(self, "غير مسموح", "لا يمكن إغلاق النافذة أثناء حفظ الآيات. الرجاء الانتظار.")
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
            super().closeEvent(event)


QuranRangeWidget = QuranRange
FromToSurahWidget = QuranRange
