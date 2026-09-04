import os
import re
import socket
import requests
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
import guiTools
from functions.moton_data import MotonDataLoader, get_moton_appdata_dir


class DownloadObjects(qt2.QObject):
    progress = qt2.pyqtSignal(int)
    downloaded = qt2.pyqtSignal(int)
    pauseDownloading = qt2.pyqtSignal(str)
    finch = qt2.pyqtSignal(bool)
    network_error = qt2.pyqtSignal(str)


class DownloadMotonThread(qt2.QThread):
    def __init__(self, parent, reciter_slug, matn_slug, total_verses):
        super().__init__(parent)
        self.objects = DownloadObjects()
        self.reciter_slug = reciter_slug
        self.matn_slug = matn_slug
        self.total_verses = total_verses
        self.is_paused = False
        self.is_cancelled = False
        self.current_file = None
        self.objects.pauseDownloading.connect(self.cancel)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def cancel(self):
        self.is_cancelled = True
        self.is_paused = False

    def run(self):
        try:
            base_dir = get_moton_appdata_dir(self.reciter_slug, self.matn_slug)
            os.makedirs(base_dir, exist_ok=True)
            base_url = f"https://huggingface.co/datasets/alcoder01/DataMoton/resolve/main/Qasaed/{self.reciter_slug}/{self.matn_slug}/"
            count = 0

            for bayt_num in range(1, self.total_verses + 1):
                if self.is_cancelled:
                    return

                file_name = f"{bayt_num}.mp3"
                file_path = os.path.join(base_dir, file_name)
                self.current_file = file_path

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    count += 1
                    self.objects.downloaded.emit(count)
                    continue

                downloaded_current = False
                while not downloaded_current and not self.is_cancelled:
                    while self.is_paused and not self.is_cancelled:
                        self.msleep(200)

                    if self.is_cancelled:
                        return

                    try:
                        with requests.get(base_url + file_name, stream=True, timeout=(5, 5)) as r:
                            if r.status_code != 200:
                                self.objects.finch.emit(False)
                                return

                            size = r.headers.get("content-length")
                            try:
                                size = int(size)
                            except (TypeError, ValueError):
                                size = 0

                            recieved = 0
                            progress = 0
                            with open(file_path, "wb") as f:
                                for pk in r.iter_content(1024):
                                    if self.is_cancelled:
                                        break
                                    f.write(pk)
                                    recieved += len(pk)
                                    if size > 0:
                                        progress = int((recieved / size) * 100)
                                        self.objects.progress.emit(progress)

                            if self.is_cancelled:
                                if os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except Exception:
                                        pass
                                return

                        downloaded_current = True
                        count += 1
                        self.objects.downloaded.emit(count)
                    except (requests.exceptions.RequestException, Exception) as e:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                        if self.is_cancelled:
                            return
                        self.is_paused = True
                        self.objects.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")

            if not self.is_cancelled:
                self.objects.finch.emit(True)
        except Exception as e:
            print(f"Error in DownloadMotonThread: {e}")
            self.objects.finch.emit(False)


class DownloadMotonReciters(qt.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(550, 360)
        self.setWindowTitle("تحميل قراء المتون")
        self.setStyleSheet("""
            QDialog {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                min-height: 36px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                min-height: 25px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 4px;
            }
            QSpinBox {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
                min-height: 32px;
            }
            QPushButton {
                min-height: 38px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)

        qt1.QShortcut("escape", self).activated.connect(self.close)

        self.data_loader = MotonDataLoader()
        self.categories = self.data_loader.get_categories()

        from functions.moton_data import get_all_moton_reciters
        self.all_reciters_data = get_all_moton_reciters()
        self.slug_to_ar = self.all_reciters_data.get("reciters", {})

        self.run = None
        self.total_verses = 0

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        font = qt1.QFont()
        font.setBold(True)

        cat_layout = qt.QHBoxLayout()
        cat_layout.setSpacing(10)
        cat_layout.addStretch(1)
        self.category_combo = qt.QComboBox()
        self.category_combo.setFont(font)
        self.category_combo.setAccessibleName("الفئة")
        for cat in self.categories:
            self.category_combo.addItem(cat)
        self.category_label = qt.QLabel("الفئة:")
        self.category_label.setFont(font)
        self.category_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addWidget(self.category_label)
        cat_layout.addStretch(1)
        layout.addLayout(cat_layout)

        matn_layout = qt.QHBoxLayout()
        matn_layout.setSpacing(10)
        matn_layout.addStretch(1)
        self.matn_combo = qt.QComboBox()
        self.matn_combo.setFont(font)
        self.matn_combo.setAccessibleName("المتن")
        self.matn_label = qt.QLabel("المتن:")
        self.matn_label.setFont(font)
        self.matn_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        matn_layout.addWidget(self.matn_combo)
        matn_layout.addWidget(self.matn_label)
        matn_layout.addStretch(1)
        layout.addLayout(matn_layout)

        reciter_layout = qt.QHBoxLayout()
        reciter_layout.setSpacing(10)
        reciter_layout.addStretch(1)
        self.reciter_combo = qt.QComboBox()
        self.reciter_combo.setFont(font)
        self.reciter_combo.setAccessibleName("القارئ")
        self.reciter_label = qt.QLabel("القارئ:")
        self.reciter_label.setFont(font)
        self.reciter_label.setAlignment(qt2.Qt.AlignmentFlag.AlignVCenter | qt2.Qt.AlignmentFlag.AlignRight)
        reciter_layout.addWidget(self.reciter_combo)
        reciter_layout.addWidget(self.reciter_label)
        reciter_layout.addStretch(1)
        layout.addLayout(reciter_layout)

        self.download_button = guiTools.QPushButton("تحميل القارئ")
        self.download_button.setFont(font)
        self.download_button.setAccessibleName("تحميل القارئ")
        self.download_button.setStyleSheet("background-color: #0000AA; color: white;")
        self.download_button.setAutoDefault(False)
        self.download_button.setDefault(False)
        layout.addWidget(self.download_button)

        self.progress = qt.QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.lay = qt.QLabel("عدد الأبيات التي تم تحميلها")
        self.lay.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.lay.setFont(font)
        self.lay.setVisible(False)
        layout.addWidget(self.lay)

        self.downloaded = qt.QSpinBox()
        self.downloaded.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.downloaded.setFont(font)
        self.downloaded.setAccessibleName("عدد الأبيات التي تم تحميلها")
        self.downloaded.setReadOnly(True)
        self.downloaded.setVisible(False)
        layout.addWidget(self.downloaded)

        self.pause = guiTools.QPushButton("إيقاف مؤقت")
        self.pause.setFont(font)
        self.pause.setAccessibleName("إيقاف مؤقت")
        self.pause.setStyleSheet("background-color: #0000AA; color: white;")
        self.pause.setAutoDefault(False)
        self.pause.setDefault(False)
        self.pause.setVisible(False)
        layout.addWidget(self.pause)

        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        self.matn_combo.currentIndexChanged.connect(self.on_matn_changed)
        self.reciter_combo.currentIndexChanged.connect(self.on_reciter_changed)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.pause.clicked.connect(self.on_pause_clicked)

        if self.categories:
            self.on_category_changed(0)

    def adjust_combo_width(self, combo):
        fm = combo.fontMetrics()
        current_text = combo.currentText()
        if not current_text:
            return
        text_width = fm.horizontalAdvance(current_text) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(current_text).width()
        combo.setFixedWidth(text_width + 65)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_combo_width(self.category_combo)
        self.adjust_combo_width(self.matn_combo)
        self.adjust_combo_width(self.reciter_combo)
        self.category_combo.setFocus()

    def on_category_changed(self, index):
        self.adjust_combo_width(self.category_combo)
        moton = self.data_loader.get_moton_for_category(index)
        self.matn_combo.blockSignals(True)
        self.matn_combo.clear()
        for m in moton:
            self.matn_combo.addItem(m)
        self.matn_combo.blockSignals(False)
        if moton:
            self.on_matn_changed(0)
        else:
            self.reciter_combo.blockSignals(True)
            self.reciter_combo.clear()
            self.reciter_combo.blockSignals(False)

    def on_matn_changed(self, index):
        self.adjust_combo_width(self.matn_combo)
        matn_name = self.matn_combo.currentText()
        if not matn_name:
            return
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        from functions.moton_data import get_moton_reciters_for_matn
        reciters_list = get_moton_reciters_for_matn(matn_slug)

        verse_reciters = []
        for r_ar, r_slug, r_type, r_url in reciters_list:
            if r_type == "N":
                verse_reciters.append((r_ar, r_slug))

        self.reciter_combo.blockSignals(True)
        self.reciter_combo.clear()

        if not verse_reciters:
            self.reciter_combo.addItem("لا يتوفر قراء مسجلين لهذا المتن", "")
            self.reciter_combo.setEnabled(False)
            self.download_button.setEnabled(False)
            self.download_button.setText("تحميل القارئ")
        else:
            self.reciter_combo.setEnabled(True)
            self.download_button.setEnabled(True)
            for r_ar, r_slug in verse_reciters:
                self.reciter_combo.addItem(r_ar, r_slug)

        self.reciter_combo.blockSignals(False)
        self.adjust_combo_width(self.reciter_combo)
        self.on_reciter_changed(self.reciter_combo.currentIndex())

    def on_reciter_changed(self, index):
        self.adjust_combo_width(self.reciter_combo)
        matn_name = self.matn_combo.currentText()
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        reciter_slug = self.reciter_combo.currentData()
        if matn_slug and reciter_slug:
            from functions.moton_data import get_moton_reciter_downloaded_count
            count = get_moton_reciter_downloaded_count(reciter_slug, matn_slug)
            total = self.data_loader.get_matn_length(matn_slug)
            if count >= total and total > 0:
                self.download_button.setText("إعادة تحميل القارئ (محمل بالكامل)")
            elif count > 0:
                self.download_button.setText(f"استكمال تحميل القارئ (تم تحميل {count} من {total})")
            else:
                self.download_button.setText("تحميل القارئ")
        else:
            self.download_button.setText("تحميل القارئ")

    def on_download_clicked(self):
        matn_name = self.matn_combo.currentText()
        matn_slug = self.data_loader.get_matn_slug(matn_name)
        reciter_slug = self.reciter_combo.currentData()

        if not matn_slug or not reciter_slug:
            guiTools.speak("يرجى اختيار متن وقارئ صحيحين")
            return

        self.total_verses = self.data_loader.get_matn_length(matn_slug)
        if self.total_verses <= 0:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "لم يتم العثور على عدد أبيات هذا المتن")
            return

        self.download_button.hide()
        self.category_combo.setEnabled(False)
        self.matn_combo.setEnabled(False)
        self.reciter_combo.setEnabled(False)

        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.show()

        self.lay.show()

        self.downloaded.setRange(0, self.total_verses)
        self.downloaded.setValue(0)
        self.downloaded.show()

        self.pause.setText("إيقاف مؤقت")
        self.pause.setAccessibleName("إيقاف مؤقت")
        self.pause.show()

        self.run = DownloadMotonThread(self, reciter_slug, matn_slug, self.total_verses)
        self.run.objects.finch.connect(self.on_finished)
        self.run.objects.progress.connect(self.on_progress)
        self.run.objects.downloaded.connect(self.on_downloaded)
        self.run.objects.network_error.connect(self.on_network_error)
        self.run.start()

    def check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5).close()
            return True
        except Exception:
            try:
                socket.create_connection(("1.1.1.1", 53), timeout=1.5).close()
                return True
            except Exception:
                try:
                    requests.head("https://www.google.com", timeout=1.5)
                    return True
                except Exception:
                    return False

    def on_pause_clicked(self):
        if not self.run:
            return
        if self.run.is_paused or self.pause.text() == "استئناف":
            if not self.check_internet():
                self.pause.setText("استئناف")
                self.pause.setAccessibleName("استئناف")
                guiTools.speak("لا يوجد اتصال بالإنترنت، يرجى التأكد من الاتصال أولاً")
                guiTools.qMessageBox.MessageBox.error(self, "خطأ في الاتصال", "لا يوجد اتصال بالإنترنت، يرجى التأكد من الاتصال أولاً ثم الضغط على زر الاستئناف.")
                return
            self.pause.setText("إيقاف مؤقت")
            self.pause.setAccessibleName("إيقاف مؤقت")
            guiTools.speak("تم استئناف التحميل")
            self.run.resume()
        else:
            self.run.pause()
            self.pause.setText("استئناف")
            self.pause.setAccessibleName("استئناف")
            guiTools.speak("تم إيقاف التحميل مؤقتاً")

    def on_network_error(self, msg):
        self.pause.setText("استئناف")
        self.pause.setAccessibleName("استئناف")
        guiTools.speak("تم إيقاف التحميل مؤقتاً بسبب انقطاع الاتصال بالإنترنت")
        guiTools.qMessageBox.MessageBox.error(self, "انقطاع الاتصال", msg)

    def on_finished(self, state):
        if state:
            guiTools.speak("تم التحميل بنجاح")
            guiTools.qMessageBox.MessageBox.view(self, "تم", "تم التحميل بنجاح")
            self.close()
        else:
            guiTools.speak("تعذر التحميل")
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "تعذر التحميل")
            self.reset_ui()

    def reset_ui(self):
        self.progress.hide()
        self.lay.hide()
        self.downloaded.hide()
        self.pause.hide()
        self.download_button.show()
        self.category_combo.setEnabled(True)
        self.matn_combo.setEnabled(True)
        self.reciter_combo.setEnabled(True)

    def on_progress(self, progress):
        self.progress.setValue(progress)

    def on_downloaded(self, count):
        self.downloaded.setValue(count)

    def closeEvent(self, event):
        if self.run and self.run.isRunning():
            self.run.cancel()
            self.run.terminate()
            self.run.wait(200)
            if self.run.current_file and os.path.exists(self.run.current_file):
                try:
                    os.remove(self.run.current_file)
                except Exception:
                    pass
        event.accept()


# Alias for compatibility
SelectMotonReciter = DownloadMotonReciters
