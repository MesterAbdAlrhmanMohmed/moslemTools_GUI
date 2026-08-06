import os,requests,re
import ujson as json
import guiTools,settings
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class SelectAthkar(qt.QDialog):
    def __init__(self,p):
        super().__init__(p)
        self.setMinimumSize(600, 400)
        self.resize(950, 550)
        self.center()
        layout=qt.QVBoxLayout(self)
        serch=guiTools.QNavigableLabel("البحث عن فئة أذكار")
        serch.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()
        self.search_bar.setPlaceholderText("البحث عن فئة أذكار")
        self.search_bar.textChanged.connect(self.onsearch)
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        with open("data/json/athkar.json","r",encoding="utf-8-sig") as data:
            self.reciterData=json.load(data)
        self.reciters=guiTools.QListWidget()
        self.reciters.setSpacing(3)
        font=qt1.QFont()
        font.setBold(True)
        self.reciters.setFont(font)
        self.reciterData1=[]
        for athker in self.reciterData:
            self.reciterData1.append(athker["name"])
        self.reciters.clicked.connect(self.on_item_clicked)
        self.reciters.addItems(self.reciterData1)
        layout.addWidget(self.reciters)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def on_item_clicked(self):
        item = self.reciters.currentItem()
        if item:
            selected_text = item.text()
            selected_data = next((rec for rec in self.reciterData if rec["name"] == selected_text), None)
            if selected_data:
                DownloadReciter(self, selected_data["content"], selected_text).exec()

    def search(self,pattern,text_list):
        tashkeel_pattern=re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
        normalized_pattern=tashkeel_pattern.sub('', pattern)
        matches=[
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]
        return matches

    def onsearch(self):
        search_text=self.search_bar.text().lower()
        self.reciters.clear()
        result=self.search(search_text,list(self.reciterData1))
        self.reciters.addItems(result)


class downloadObjects(qt2.QObject):
    progress=qt2.pyqtSignal(int)
    downloaded=qt2.pyqtSignal(int)
    pauseDownloading=qt2.pyqtSignal(str)
    network_error=qt2.pyqtSignal(str)
    finch=qt2.pyqtSignal(bool)


class downloadThread(qt2.QRunnable):
    def __init__(self,p,url,name):
        super().__init__()
        self.objects=downloadObjects()
        self.name=name
        self.url=url
        self.pause=False
        self.cancelled=False
        self.objects.pauseDownloading.connect(self.on_pause)

    def on_pause(self,s):
        self.pause=not self.pause

    def run(self):
        try:
            count=0
            for item in self.url:
                while self.pause and not self.cancelled:
                    import time
                    time.sleep(0.2)
                if self.cancelled:
                    return
                if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar")):
                    os.makedirs(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar"))
                if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name)):
                    os.makedirs(os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name))
                file=str(self.url.index(item)) + ".mp3"
                target_file = os.path.join(os.getenv('appdata'),settings.app.appName,"athkar",self.name,file)
                if os.path.exists(target_file):
                    count+=1
                    self.objects.downloaded.emit(count)
                else:
                    try:
                        with requests.get(item["audio"],stream=True,timeout=15) as r:
                            if r.status_code!=200:
                                self.objects.finch.emit(False)
                                return
                            size=r.headers.get("content-length")
                            try:
                                size=int(size)
                            except TypeError as e:
                                print(f"Error parsing size: {e}")
                                self.objects.finch.emit(False)
                                return
                            recieved=0
                            progress=0
                            with open(target_file,"wb") as file_out:
                                for pk in r.iter_content(1024):
                                    while self.pause and not self.cancelled:
                                        import time
                                        time.sleep(0.2)
                                    if self.cancelled:
                                        return
                                    file_out.write(pk)
                                    recieved+=len(pk)
                                    progress=int((recieved/size)*100)
                                    self.objects.progress.emit(progress)
                        count+=1
                        self.objects.downloaded.emit(count)
                    except (requests.exceptions.RequestException, Exception) as net_err:
                        self.pause = True
                        self.objects.network_error.emit("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")
                        while self.pause and not self.cancelled:
                            import time
                            time.sleep(0.2)
            self.objects.finch.emit(True)
        except Exception as e:
            print(f"Error in downloadThread: {e}")
            self.objects.finch.emit(False)


class DownloadReciter(qt.QDialog):
    def __init__(self,p,url,name):
        super().__init__(p)
        self.setMinimumSize(550, 250)
        self.resize(750, 320)
        self.center()
        self.setWindowTitle("جاري التحميل")
        qt1.QShortcut("escape",self).activated.connect(self.close)

        layout = qt.QVBoxLayout(self)

        self.status_label = guiTools.QNavigableLabel(f"جاري تحميل: {name}")
        self.status_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.status_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        font = qt1.QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)

        self.progress = qt.QProgressBar()
        self.progress.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.progress.setAccessibleName("نسبة التحميل")
        layout.addWidget(self.progress)

        downloaded_label = guiTools.QNavigableLabel("عدد الأذكار التي تم تحميلها")
        downloaded_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        downloaded_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(downloaded_label)

        self.downloaded = qt.QSpinBox()
        self.downloaded.setAccessibleName("عدد الأذكار التي تم تحميلها")
        self.downloaded.setRange(0, 7000)
        self.downloaded.setReadOnly(True)
        layout.addWidget(self.downloaded)

        self.pause = guiTools.QPushButton("إيقاف مؤقت")
        self.pause.setStyleSheet("QPushButton {background-color: #0000AA; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #0000CC;}")
        self.cancel = guiTools.QPushButton("إلغاء")
        self.cancel.setStyleSheet("QPushButton {background-color: #8B0000; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; min-height: 35px;} QPushButton:hover {background-color: #A52A2A;}")

        btns_layout = qt.QHBoxLayout()
        btns_layout.addWidget(self.pause)
        btns_layout.addWidget(self.cancel)
        layout.addLayout(btns_layout)
        thread=qt2.QThreadPool(self)
        self.run=downloadThread(self,url,name)
        self.run.objects.finch.connect(self.on)
        self.run.objects.progress.connect(self.on_progress)
        self.run.objects.downloaded.connect(self.on_downloaded)
        self.run.objects.network_error.connect(self.on_network_error)
        thread.start(self.run)
        self.pause.clicked.connect(self.toggle_pause)
        self.cancel.clicked.connect(self.close)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = qt1.QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def toggle_pause(self):
        if self.run.pause:
            self.pause.setText("إيقاف مؤقت")
            self.run.objects.pauseDownloading.emit("a")
        else:
            self.pause.setText("استئناف")
            self.run.objects.pauseDownloading.emit("a")

    def on_network_error(self, msg):
        self.pause.setText("استئناف")
        guiTools.MessageBox.error(self, "انقطاع الاتصال", msg)

    def closeEvent(self, event):
        if not self.run.cancelled:
            result = guiTools.QQuestionMessageBox.view(self, "تأكيد الإلغاء", "هل تريد إلغاء عملية تحميل الأذكار؟", "نعم", "لا")
            if result == 0:
                self.run.cancelled = True
                self.run.pause = False
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def on(self,state):
        if state==True:
            guiTools.qMessageBox.MessageBox.view(self,"تم","تم التحميل بنجاح")
            self.close()
        else:
            guiTools.qMessageBox.MessageBox.error(self,"خطأ","تعذر التحميل")
            self.close()

    def on_progress(self,progress):
        self.progress.setValue(progress)

    def on_downloaded(self,count):
        self.downloaded.setValue(count)
