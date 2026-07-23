import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import guiTools, requests, pyperclip, winsound, webbrowser, re
from settings import settings_handler

class AIChatThread(qt2.QThread):
    finished = qt2.pyqtSignal(dict, bool)
    
    def __init__(self, api_key, message):
        super().__init__()
        self.api_key = api_key
        self.message = message
        
    def run(self):
        url = "https://api.fanar.qa/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "Fanar-Sadiq",
            "messages": [
                {
                    "role": "user",
                    "content": self.message
                }
            ],
            "search": True
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                                
                references = []
                try:
                    if 'message' in result['choices'][0] and 'references' in result['choices'][0]['message']:
                        references = result['choices'][0]['message']['references']
                    elif 'references' in result['choices'][0]:
                        references = result['choices'][0]['references']
                    elif 'references' in result:
                        references = result['references']
                except Exception:
                    references = []
                
                self.finished.emit({"content": content, "references": references}, True)
            else:
                self.finished.emit({"error": f"خطأ من الخادم: {response.status_code}\n{response.text}"}, False)
        except Exception as e:
            self.finished.emit({"error": f"حدث خطأ أثناء الاتصال: {str(e)}"}, False)

class SourcesDialog(qt.QDialog):
    def __init__(self, parent, sources):
        super().__init__(parent)
        self.resize(450, 180)
        self.setWindowTitle("المصادر والمراجع")        
        lec = "اختر المصدر الذي تريد الذهاب إليه:"
        label = qt.QLabel(lec)        
        self.combo = qt.QComboBox()
        self.combo.setMinimumHeight(60)
        self.combo.setAccessibleName(lec)
        font = qt1.QFont()
        font.setBold(True)
        self.combo.setFont(font)
        for i, url in enumerate(sources):
            self.combo.addItem(f"المصدر {i+1}\n{url}", url)        
        self.ok = qt.QPushButton("الذهاب")
        self.ok.setDefault(True)
        self.ok.setStyleSheet("background-color: #008000; color: #e0e0e0; font-weight: bold;")
        self.ok.clicked.connect(self.go_to_source)        
        self.copy_btn = qt.QPushButton("نسخ رابط المصدر")        
        self.copy_btn.setStyleSheet("background-color: #0000AA; color: #e0e0e0; font-weight: bold;")
        self.copy_btn.clicked.connect(self.copy_source_link)
        self.cancel = qt.QPushButton("خروج")        
        self.cancel.setStyleSheet("background-color: #AA0000; color: #e0e0e0; font-weight: bold;")
        self.cancel.clicked.connect(self.reject)        
        layout = qt.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.combo)        
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.addWidget(self.ok)
        buttons_layout.addWidget(self.copy_btn)
        buttons_layout.addWidget(self.cancel)
        layout.addLayout(buttons_layout)        
        self.setLayout(layout)        
        
    def go_to_source(self):
        url = self.combo.currentData()
        if url:
            webbrowser.open(url)
            self.accept()
        else:
            guiTools.MessageBox.view(self, "تنبيه", "لا يوجد رابط متاح لهذا المصدر")

    def copy_source_link(self):
        url = self.combo.currentData()
        if url:
            pyperclip.copy(url)
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ رابط المصدر بنجاح")
        else:
            guiTools.MessageBox.view(self, "تنبيه", "لا يوجد رابط متاح لهذا المصدر")

class ChatInputTextEdit(qt.QTextEdit):
    enterPressed = qt2.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(qt.QTextEdit.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(qt1.QTextOption.WrapMode.WordWrap)
        self.setAcceptRichText(True)
        self.document().setDefaultCursorMoveStyle(qt2.Qt.CursorMoveStyle.VisualMoveStyle)

    def setText(self, text):
        if text:
            text = "\n".join([line if line.strip() else "\u200b" for line in text.split("\n")])
        super().setText(text)

    def keyPressEvent(self, event):
        if event.key() in (qt2.Qt.Key.Key_Return, qt2.Qt.Key.Key_Enter):
            if event.modifiers() == qt2.Qt.KeyboardModifier.NoModifier:
                self.enterPressed.emit()
                return
            elif event.modifiers() == qt2.Qt.KeyboardModifier.ShiftModifier:
                self.insertPlainText("\n\u200b")
                return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasText():
            text = source.text()
            text = "\n".join([line if line.strip() else "\u200b" for line in text.split("\n")])
            self.insertPlainText(text)
        else:
            super().insertFromMimeData(source)

class AskAI(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.font_is_bold = settings_handler.get("font", "bold") == "True"
        self.font_size = int(settings_handler.get("font", "size"))
        self.current_urls = []        
        self.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                min-height: 40px;
                font-weight: bold;
            }
            QPushButton#sendButton:hover {
                background-color: #218838;
            }
            QPushButton#sendButton:pressed {
                background-color: #218838;
            }
            QPushButton#sendButton:disabled {
                background-color: #6c757d;
                color: #d3d3d3;
            }
            QPushButton#clearButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                min-height: 40px;
                font-weight: bold;
                outline: none;
            }
            QPushButton#clearButton:hover {
                background-color: #c82333;
            }
            QPushButton#clearButton:pressed {
                background-color: #bd2130;
            }
            QPushButton#clearButton:disabled {
                background-color: #6c757d;
                color: #d3d3d3;
            }
            QPushButton#sourcesButton {
                background-color: #0056b3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                min-height: 40px;
                font-weight: bold;
            }
            QPushButton#sourcesButton:hover {
                background-color: #003d80;
            }
            QPushButton#sourcesButton:pressed {
                background-color: #003d80;
            }
            QTextEdit#inputBox {
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #1E1E1E;
            }
        """)
        self.init_ui()
        self.create_shortcuts()
        
    def create_shortcuts(self):
        qt1.QShortcut("Ctrl+C", self).activated.connect(self.copy_selection)
        qt1.QShortcut("Ctrl+A", self).activated.connect(self.copy_all)
        qt1.QShortcut("Ctrl+S", self).activated.connect(self.save_as_txt)
        qt1.QShortcut("Ctrl+P", self).activated.connect(self.print_results)
        qt1.QShortcut("ctrl+=", self).activated.connect(self.increase_font_size)
        qt1.QShortcut("ctrl+-", self).activated.connect(self.decrease_font_size)
        qt1.QShortcut("ctrl+del", self).activated.connect(self.clear_results)
        
    def init_ui(self):
        layout = qt.QVBoxLayout(self)                
        self.disclaimer = qt.QLabel("تنبيه مهم: هذا ذكاء اصطناعي للمساعدة، ويرجى سؤال أهل العلم في المسائل الإسلامية المهمة.")
        self.disclaimer.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 14px;")
        self.disclaimer.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.disclaimer.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.disclaimer)                
        
        input_layout = qt.QHBoxLayout()
        self.input_box = ChatInputTextEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("اكتب سؤالك هنا...")
        self.input_box.setTabChangesFocus(True)
        self.input_box.setMaximumHeight(100)
        self.input_box.setAccessibleName("اكتب سؤالك هنا")
        self.input_box.enterPressed.connect(self.on_send_clicked)
        
        self.send_button = guiTools.QPushButton("إرسال الرسالة")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.on_send_clicked)        
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)                
        
        self.results = guiTools.QReadOnlyTextEdit(viewer_name="aiChat")
        self.results.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.results)                
        
        bottom_layout = qt.QHBoxLayout()        
        self.clear_button = guiTools.QPushButton("حذف النتائج")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setAccessibleDescription("control plus delete")
        self.clear_button.setEnabled(False)
        
        font_layout = qt.QVBoxLayout()
        self.font_label = qt.QLabel("حجم الخط")
        self.font_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.font_spin = qt.QSpinBox()
        self.font_spin.setRange(1, 100)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.font_spin.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.font_spin.setAccessibleName("حجم الخط")
        self.font_spin.valueChanged.connect(self.font_size_changed)
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(self.font_spin)        
        
        self.sources_button = guiTools.QPushButton("المصادر والمراجع")        
        self.sources_button.setObjectName("sourcesButton")
        self.sources_button.setShortcut("ctrl+r")
        self.sources_button.setAccessibleDescription("control plus R")
        self.sources_button.setVisible(False)
        self.sources_button.clicked.connect(self.show_sources_dialog)        
        
        bottom_layout.addWidget(self.clear_button)
        bottom_layout.addStretch(1)
        bottom_layout.addLayout(font_layout)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.sources_button)
        layout.addLayout(bottom_layout)        
        self.update_font_size()
        
    def show_sources_dialog(self):
        if self.current_urls:
            SourcesDialog(self, self.current_urls).exec()
            
    def show_context_menu(self, pos):
        menu = qt.QMenu(self)
        font = qt1.QFont()
        font.setBold(True)
        menu.setFont(font)        
        copy_sel = menu.addAction("نسخ النص المحدد")
        copy_sel.setShortcut("Ctrl+C")
        copy_sel.triggered.connect(self.copy_selection)        
        copy_all_act = menu.addAction("نسخ النص كاملا")
        copy_all_act.setShortcut("Ctrl+A")
        copy_all_act.triggered.connect(self.copy_all)        
        menu.addSeparator()        
        save_act = menu.addAction("حفظ كملف نصي")
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self.save_as_txt)        
        print_act = menu.addAction("طباعة")
        print_act.setShortcut("Ctrl+P")
        print_act.triggered.connect(self.print_results)        
        menu.exec(self.results.mapToGlobal(pos))
        
    def on_send_clicked(self):
        message = self.input_box.toPlainText().strip()
        if not message:
            guiTools.MessageBox.error(self, "تنبيه", "يرجى كتابة سؤال")
            return            
        api_key = settings_handler.get("fanar", "api_key")
        if not api_key:
            guiTools.MessageBox.error(self, "تنبيه", "يرجى إضافة مفتاح الـ API في الإعدادات أولاً لاستخدام هذه الميزة.")
            return
        self.send_button.setEnabled(False)
        self.send_button.setText("جاري الإرسال...")
        self.results.setText("جاري معالجة طلبك، يرجى الانتظار...")
        self.sources_button.setVisible(False)
        self.clear_button.setEnabled(False)
        self.current_urls = []        
        self.thread = AIChatThread(api_key, message)
        self.thread.finished.connect(self.on_ai_finished)
        self.thread.start()
        self.results.setFocus()
        
    def extract_and_clean(self, text):
        text = text.replace("<quran_start>", "").replace("<quran_end>", "")
        url_pattern = r'(?:https?://|www\.)[^\s<>"\(\)\[\]{}|\\^`]+'
        urls = re.findall(url_pattern, text)
        clean_text = text
        
        clean_text = re.sub(r'^\s*[\-\*\d\.]*\s*(?:المصدر|المرجع|Source|Reference)?\s*\d*[:\-]?\s*(?:https?://|www\.)[^\s<>"]+\s*$', '', clean_text, flags=re.MULTILINE | re.IGNORECASE)
        for u in urls:
            clean_text = clean_text.replace(u, "")
        clean_text = re.sub(r'\n+(?:المصادر|المراجع|Sources|References|Citations):?.*$', '', clean_text, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
        clean_text = re.sub(r'\[\d+\]|\(\d+\)', '', clean_text)
        clean_text = re.sub(r'^\s*(?:المصدر|المرجع|Source|Reference)\s*\d*[:\-]?\s*$', '', clean_text, flags=re.MULTILINE | re.IGNORECASE)
        clean_text = clean_text.replace("()", "").replace("[]", "").replace("<>", "")
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        
        unique_urls = []
        seen = set()
        for u in urls:
            normalized = u.strip()
            if normalized.startswith("www."):
                normalized = "http://" + normalized
            elif not normalized.startswith("http"):
                normalized = "http://" + normalized
                
            if normalized not in seen:
                unique_urls.append(normalized)
                seen.add(normalized)
                
        return clean_text.strip(), unique_urls
        
    def on_ai_finished(self, response_data, success):
        self.send_button.setEnabled(True)
        self.send_button.setText("إرسال الرسالة")
        if success:
            response_text = response_data.get("content", "")
            json_references = response_data.get("references", [])
            
            clean_text, extracted_urls = self.extract_and_clean(response_text)
            self.results.setText(clean_text)
            
            final_urls = []
            seen = set()
            
            def add_url(u):
                if not u or not isinstance(u, str): return
                u = u.strip()
                if not u: return
                normalized = u if u.startswith("http") else "http://" + u
                if normalized not in seen:
                    final_urls.append(normalized)
                    seen.add(normalized)

            # 1. قراءة الروابط من المراجع المستخرجة من الـ JSON (مفتاح source جواه)
            for item in json_references:
                if isinstance(item, dict) and 'source' in item:
                    add_url(item.get('source'))
                elif isinstance(item, str):
                    add_url(item)
            
            # 2. إضافة أي روابط تم استخراجها من النص كخيار احتياطي
            for url in extracted_urls:
                add_url(url)
            
            self.current_urls = final_urls            
            if final_urls:
                self.sources_button.setVisible(True)
            else:
                self.sources_button.setVisible(False)            
            self.clear_button.setEnabled(True)
            self.update_font_size()
            guiTools.speak("تمت الإجابة على سؤالك، يمكنك قراءة النتيجة الآن.")
            self.results.setFocus()
        else:
            error_msg = response_data.get("error", "حدث خطأ غير معروف")
            if "Connection" in error_msg or "timeout" in error_msg:
                 guiTools.MessageBox.error(self, "خطأ في الاتصال", "لا يوجد اتصال بالإنترنت أو فشل الاتصال بالخادم. يرجى التحقق من الشبكة والمحاولة مرة أخرى.")
            else:
                 guiTools.MessageBox.error(self, "خطأ", error_msg)
            self.results.clear()
            self.input_box.setFocus()
            
    def clear_results(self):
        self.results.clear()
        self.input_box.clear()
        self.current_urls = []
        self.sources_button.setVisible(False)
        self.clear_button.setEnabled(False)
        guiTools.speak("تم حذف النتائج")
        
    def font_size_changed(self, value):
        self.font_size = value
        self.update_font_size()
        guiTools.speak(str(self.font_size))
        
    def increase_font_size(self):
        if self.font_spin.value() < 100:
            self.font_spin.setValue(self.font_spin.value() + 1)
            
    def decrease_font_size(self):
        if self.font_spin.value() > 1:
            self.font_spin.setValue(self.font_spin.value() - 1)
            
    def update_font_size(self):
        cursor = self.results.textCursor()
        self.results.selectAll()
        font = qt1.QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_is_bold)
        self.results.setCurrentFont(font)
        self.results.setTextCursor(cursor)        
        
    def copy_selection(self):
        try:
            cursor = self.results.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
            else:
                cursor.select(qt1.QTextCursor.SelectionType.BlockUnderCursor)
                pyperclip.copy(cursor.selectedText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ النص المحدد بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))
            
    def copy_all(self):
        try:
            pyperclip.copy(self.results.toPlainText())
            winsound.Beep(1000, 100)
            guiTools.speak("تم نسخ كل المحتوى بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))
            
    def save_as_txt(self):
        if not self.results.toPlainText():
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(self.results.toPlainText())
                guiTools.speak("تم الحفظ بنجاح")
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))
            
    def print_results(self):
        if not self.results.toPlainText():
            return
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.results.print(printer)
        except Exception as e:
            guiTools.MessageBox.error(self, "تنبيه حدث خطأ", str(e))