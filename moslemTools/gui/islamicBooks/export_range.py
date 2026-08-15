from guiTools import note_dialog
import functions.notesManager as notesManager
import guiTools, pyperclip, winsound, functions, settings
import PyQt6.QtWidgets as qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6 import QtGui as qt1
from PyQt6 import QtCore as qt2
from docx import Document
import re
from gui.quranViewer.threads import SearchModeDialog


class BookExportRangeMixin:
    def get_page_range(self):
        start_page, ok1 = guiTools.QInputDialog.getInt(self, "بداية النطاق", "أدخل رقم صفحة البداية:", value=self.index + 1, min=1, max=len(self.data))
        if not ok1:
            return None, None
        end_page, ok2 = guiTools.QInputDialog.getInt(self, "نهاية النطاق", f"أدخل رقم صفحة النهاية (1-{len(self.data)}):", value=len(self.data), min=1, max=len(self.data))
        if not ok2:
            return None, None
        if start_page > end_page:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "صفحة البداية لا يمكن أن تكون أكبر من صفحة النهاية")
            return None, None
        return start_page, end_page

    def copy_page_range(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        content = ""
        for i in range(start-1, end):
            content += self.data[i] + "\n\n"
        try:
            pyperclip.copy(content)
            winsound.Beep(1000, 100)
            guiTools.qMessageBox.MessageBox.view(self, "تم النسخ", f"تم نسخ المحتوى من الصفحة {start} إلى الصفحة {end}")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في النسخ", str(e))

    def save_page_range_as_txt(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
            file_dialog.setDefaultSuffix("txt")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                with open(file_name, 'w', encoding='utf-8') as file:
                    for i in range(start-1, end):
                        file.write(self.data[i] + "\n\n")
                guiTools.speak(f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف نصي")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))

    def save_page_range_as_docx(self):
        start, end = self.get_page_range()
        if start is None or end is None:
            return
        try:
            file_dialog = qt.QFileDialog()
            file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("Word Documents (*.docx);;All Files (*)")
            file_dialog.setDefaultSuffix("docx")
            if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
                file_name = file_dialog.selectedFiles()[0]
                doc = Document()
                for i in range(start-1, end):
                    p = doc.add_paragraph(self.data[i])
                    if i < end-1:
                        doc.add_page_break()
                doc.save(file_name)
                guiTools.qMessageBox.MessageBox.view(self, "تم الحفظ", f"تم حفظ المحتوى من الصفحة {start} إلى الصفحة {end} في ملف Word")
        except Exception as e:
            guiTools.qMessageBox.MessageBox.error(self, "خطأ في الحفظ", str(e))
