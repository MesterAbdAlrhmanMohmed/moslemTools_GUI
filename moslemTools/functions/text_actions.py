import os
import pyperclip
import winsound
import guiTools
from PyQt6 import QtWidgets as qt
from PyQt6 import QtGui as qt1
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

def increase_font_size(spinbox):
    if spinbox.value() < 100:
        spinbox.setValue(spinbox.value() + 1)

def decrease_font_size(spinbox):
    if spinbox.value() > 1:
        spinbox.setValue(spinbox.value() - 1)

def copy_current_selection(parent, widget, fallback_func=None):
    try:
        if hasattr(widget, 'textCursor'):
            cursor = widget.textCursor()
            if cursor.hasSelection():
                pyperclip.copy(cursor.selectedText())
                winsound.Beep(1000, 100)
                guiTools.speak("تم نسخ النص المحدد")
                return True
        if fallback_func:
            fallback_func()
            return True
        return False
    except Exception as error:
        guiTools.MessageBox.error(parent, "تنبيه حدث خطأ", str(error))
        return False

def copy_all_text(parent, text_or_widget, message="تم نسخ كل المحتوى بنجاح", header_text=None):
    try:
        if hasattr(text_or_widget, 'toPlainText'):
            body = text_or_widget.toPlainText()
        else:
            body = str(text_or_widget)
        full_text = f"{header_text}\n\n{body}" if header_text else body
        pyperclip.copy(full_text)
        winsound.Beep(1000, 100)
        guiTools.speak(message)
    except Exception as error:
        guiTools.MessageBox.error(parent, "تنبيه حدث خطأ", str(error))

def print_text_content(parent, widget_or_text, header_text=None):
    try:
        printer = QPrinter()
        dialog = QPrintDialog(printer, parent)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            if header_text:
                doc = qt1.QTextDocument()
                if hasattr(widget_or_text, 'toPlainText'):
                    body = widget_or_text.toPlainText()
                    doc.setDefaultFont(widget_or_text.font())
                else:
                    body = str(widget_or_text)
                doc.setPlainText(f"{header_text}\n\n{body}")
                doc.print(printer)
            else:
                if hasattr(widget_or_text, 'print'):
                    widget_or_text.print(printer)
                else:
                    doc = qt1.QTextDocument(str(widget_or_text))
                    doc.print(printer)
    except Exception as error:
        guiTools.MessageBox.error(parent, "تنبيه حدث خطأ", str(error))

def save_text_file(parent, widget_or_text, default_filename="مستند نصي.txt", header_text=None):
    try:
        file_dialog = qt.QFileDialog(parent)
        file_dialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
        file_dialog.setDefaultSuffix("txt")
        if file_dialog.exec() == qt.QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_name = selected_files[0]
                if hasattr(widget_or_text, 'toPlainText'):
                    body = widget_or_text.toPlainText()
                else:
                    body = str(widget_or_text)
                full_text = f"{header_text}\n\n{body}" if header_text else body
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(full_text)
    except Exception as error:
        guiTools.MessageBox.error(parent, "تنبيه حدث خطأ", str(error))

def format_arabic_time_unit(number, singular, dual, plural, singular_acc):
    if number == 0:
        return ""
    if number == 1:
        return singular
    elif number == 2:
        return dual
    elif 3 <= number <= 10:
        return f"{number} {plural}"
    else:
        return f"{number} {singular_acc}"

def format_arabic_time(ms_or_sec, is_ms=True):
    total_seconds = int(ms_or_sec // 1000) if is_ms else int(ms_or_sec)
    if total_seconds <= 0:
        return "0 ثانية"
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    h_str = format_arabic_time_unit(hours, "ساعة", "ساعتين", "ساعات", "ساعة")
    m_str = format_arabic_time_unit(minutes, "دقيقة", "دقيقتين", "دقائق", "دقيقة")
    s_str = format_arabic_time_unit(seconds, "ثانية", "ثانيتين", "ثواني", "ثانية")
    parts = [p for p in [h_str, m_str, s_str] if p]
    return " و ".join(parts) if parts else "0 ثانية"

def format_arabic_bayt_count(n):
    try:
        n = int(n)
    except:
        return f"{n} بيت"
    if n == 1:
        return "بيت واحد"
    elif n == 2:
        return "بيتان"
    elif 3 <= n <= 10:
        return f"{n} أبيات"
    elif 11 <= n <= 99:
        return f"{n} بيتاً"
    else:
        last_two = n % 100
        if last_two == 0:
            return f"{n} بيت"
        elif last_two == 1:
            return f"{n} بيت"
        elif last_two == 2:
            return f"{n} بيت"
        elif 3 <= last_two <= 10:
            return f"{n} أبيات"
        else:
            return f"{n} بيتاً"

