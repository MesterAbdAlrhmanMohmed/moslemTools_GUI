from functions import tafseer, translater
from settings import settings_handler, app
import os, shutil, json, guiTools
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2


class TafaseerSettings(qt.QWidget):
    def __init__(self):
        super().__init__()
        tafseer.reload_tafaseers()
        translater.reload_translations()
        self.setStyleSheet("""
            QComboBox, QLineEdit, QLabel {
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        group_box = qt.QGroupBox()
        group_layout = qt.QVBoxLayout(group_box)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(12, 15, 12, 15)

        tafaseer_layout = qt.QHBoxLayout()
        tafaseer_layout.setSpacing(10)
        self.selectTafaseer_laybol = qt.QLabel("اختر تفسير للقرآن الكريم")
        self.selectTafaseer = qt.QComboBox()
        self.selectTafaseer.addItems(tafseer.tafaseers.keys())
        current_taf = tafseer.getTafaseerByIndex(settings_handler.get("tafaseer", "tafaseer"))
        if current_taf and current_taf in tafseer.tafaseers:
            self.selectTafaseer.setCurrentText(current_taf)
        elif self.selectTafaseer.count() > 0:
            self.selectTafaseer.setCurrentIndex(0)
        self.selectTafaseer.setAccessibleName("اختر تفسير للقرآن الكريم")
        tafaseer_layout.addWidget(self.selectTafaseer)
        tafaseer_layout.addWidget(self.selectTafaseer_laybol)
        tafaseer_layout.addStretch()
        group_layout.addLayout(tafaseer_layout)

        self.translation_header = guiTools.QNavigableLabel("اختيار ترجمة لمعاني القرآن الكريم")
        self.translation_header.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.translation_header.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.translation_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        group_layout.addWidget(self.translation_header)

        lang_layout = qt.QHBoxLayout()
        lang_layout.setSpacing(10)
        self.selectLanguage_laybol = qt.QLabel("اختر اللغة:")
        self.selectLanguage = qt.QComboBox()
        self.selectLanguage.setAccessibleName("اختر اللغة")
        self.selectLanguage.setAccessibleDescription("لحذف جميع الترجمات للغة محددة، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.selectLanguage.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selectLanguage.customContextMenuRequested.connect(self.onDeleteLanguage)
        lang_layout.addWidget(self.selectLanguage)
        lang_layout.addWidget(self.selectLanguage_laybol)
        lang_layout.addStretch()
        group_layout.addLayout(lang_layout)

        translation_layout = qt.QHBoxLayout()
        translation_layout.setSpacing(10)
        self.selecttranslation_laybol = qt.QLabel("اختر الترجمة:")
        self.selecttranslation = qt.QComboBox()
        self.selecttranslation.setAccessibleName("اختر الترجمة")
        self.selecttranslation.setAccessibleDescription("لحذف أيا من الترجمات، نستخدم مفتاح التطبيقات أو click الأيمن")
        self.selecttranslation.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selecttranslation.customContextMenuRequested.connect(self.onDelete1)
        translation_layout.addWidget(self.selecttranslation)
        translation_layout.addWidget(self.selecttranslation_laybol)
        translation_layout.addStretch()
        group_layout.addLayout(translation_layout)

        self.selectTafaseer.setContextMenuPolicy(qt2.Qt.ContextMenuPolicy.CustomContextMenu)
        self.selectTafaseer.customContextMenuRequested.connect(self.onDelete)
        self.selectTafaseer.setAccessibleDescription("لحذف أيا من التفاسير قم باستخدام زر التطبيقات")

        current_trans = translater.gettranslationByIndex(settings_handler.get("translation", "translation"))
        self.load_language_groups()
        target_lang = None
        for lang, t_list in self.lang_groups.items():
            if current_trans in t_list:
                target_lang = lang
                break
        self.update_languages_ui(preferred_lang=target_lang, preferred_trans=current_trans)
        self.selectLanguage.currentIndexChanged.connect(lambda: self.on_language_changed())

        main_layout.addWidget(group_box)
        main_layout.addSpacing(25)
        self.info = guiTools.QNavigableLabel("لحذف أيا من التفاسير أو الترجمات، نستخدم مفتاح التطبيقات أو click الأيمن، ولحذف جميع الترجمات للغة محددة، نستخدم نفس المفاتيح على قائمة اللغات")
        self.info.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.info.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.info)
        main_layout.addStretch(1)

    def load_language_groups(self):
        translater.reload_translations()
        downloaded = translater.translations
        manifest_path = os.path.join("data", "json", "files", "all_translater.json")
        catalog = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
            except Exception:
                catalog = {}
        self.lang_groups = {}
        for display_name, rel_path in downloaded.items():
            norm_path = rel_path.replace("\\", "/")
            parts = norm_path.split("/")
            if len(parts) > 1 and parts[0]:
                lang = parts[0]
            else:
                cat_path = catalog.get(display_name, "")
                cat_parts = cat_path.replace("\\", "/").split("/")
                lang = cat_parts[0] if (len(cat_parts) > 1 and cat_parts[0]) else "الإنجليزية English"
            self.lang_groups.setdefault(lang, []).append(display_name)
        self.sorted_langs = sorted(self.lang_groups.keys())

    def update_languages_ui(self, preferred_lang=None, preferred_trans=None):
        self.load_language_groups()
        self.selectLanguage.blockSignals(True)
        self.selectLanguage.clear()
        self.selectLanguage.addItems(self.sorted_langs)
        if preferred_lang and preferred_lang in self.sorted_langs:
            self.selectLanguage.setCurrentText(preferred_lang)
        elif self.selectLanguage.count() > 0:
            self.selectLanguage.setCurrentIndex(0)
        self.selectLanguage.blockSignals(False)
        self.on_language_changed(preferred_trans=preferred_trans)

    def on_language_changed(self, preferred_trans=None):
        selected_lang = self.selectLanguage.currentText()
        trans_list = sorted(self.lang_groups.get(selected_lang, []))
        self.selecttranslation.blockSignals(True)
        self.selecttranslation.clear()
        self.selecttranslation.addItems(trans_list)
        if preferred_trans and preferred_trans in trans_list:
            self.selecttranslation.setCurrentText(preferred_trans)
        elif self.selecttranslation.count() > 0:
            self.selecttranslation.setCurrentIndex(0)
        self.selecttranslation.blockSignals(False)

    def onDelete1(self):
        selectedItem = self.selecttranslation.currentText()
        if selectedItem:
            itemText = selectedItem
            if itemText == "English by Talal Itani":
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذه الترجمة")
            else:
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", f"هل تريد حذف الترجمة {itemText}", "نعم", "لا")
                if question == 0:
                    name = translater.translations.get(itemText)
                    if name:
                        file_path = translater._find_in_appdata(name)
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                        else:
                            direct_path = os.path.join(os.getenv('appdata'), app.appName, "Quran Translations", name)
                            if os.path.exists(direct_path):
                                try:
                                    os.remove(direct_path)
                                except Exception:
                                    pass
                    current_lang = self.selectLanguage.currentText()
                    self.update_languages_ui(preferred_lang=current_lang)
                    guiTools.speak("تم الحذف")

    def onDeleteLanguage(self):
        selected_lang = self.selectLanguage.currentText()
        if not selected_lang:
            return
        trans_list = list(self.lang_groups.get(selected_lang, []))
        deletable_trans = [t for t in trans_list if t != "English by Talal Itani"]
        if not deletable_trans:
            guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذه الترجمة")
            return
        question = guiTools.QQuestionMessageBox.view(self, "تنبيه", f"هل تريد حذف جميع ترجمات لغة {selected_lang}؟", "نعم", "لا")
        if question == 0:
            for itemText in deletable_trans:
                name = translater.translations.get(itemText)
                if name:
                    file_path = translater._find_in_appdata(name)
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                    else:
                        direct_path = os.path.join(os.getenv('appdata'), app.appName, "Quran Translations", name)
                        if os.path.exists(direct_path):
                            try:
                                os.remove(direct_path)
                            except Exception:
                                pass
            lang_dir = os.path.join(os.getenv('appdata'), app.appName, "Quran Translations", selected_lang)
            if os.path.exists(lang_dir):
                try:
                    shutil.rmtree(lang_dir, ignore_errors=True)
                except Exception:
                    pass
            self.update_languages_ui()
            guiTools.speak("تم الحذف")

    def onDelete(self):
        selectedItem = self.selectTafaseer.currentText()
        if selectedItem:
            itemText = selectedItem
            if itemText == "الميصر":
                guiTools.qMessageBox.MessageBox.error(self, "تنبيه", "لا يمكنك حذف هذا التفسير")
            else:
                question = guiTools.QQuestionMessageBox.view(self, "تنبيه", f"هل تريد حذف تفسير {itemText}", "نعم", "لا")
                if question == 0:
                    name = tafseer.tafaseers[itemText]
                    os.remove(os.path.join(os.getenv('appdata'), app.appName, "tafaseer", name))
                    tafseer.reload_tafaseers()
                    self.selectTafaseer.blockSignals(True)
                    self.selectTafaseer.clear()
                    self.selectTafaseer.addItems(tafseer.tafaseers.keys())
                    self.selectTafaseer.blockSignals(False)
                    self.selectTafaseer.setCurrentText("الميصر")
                    guiTools.speak("تم الحذف")
