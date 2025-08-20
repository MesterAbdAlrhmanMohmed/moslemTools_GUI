import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
from guiTools import QReadOnlyTextEdit
from guiTools import qMessageBox
class NoteDialog(qt.QDialog):
    saved = qt2.pyqtSignal(str, str, str)
    edit_requested = qt2.pyqtSignal(str) 
    refresh_requested = qt2.pyqtSignal()    
    def __init__(self, parent, title="", content="", mode="add", old_name=""):
        super().__init__(parent)
        self.setWindowTitle("إضافة ملاحظة" if mode == "add" else "عرض الملاحظة")
        self.mode = mode
        self.old_name = old_name
        self.came_from_view_mode = (mode == "view")
        self.setMinimumWidth(600)
        self.setMaximumWidth(600)        
        layout = qt.QVBoxLayout(self)        
        self.title_label = qt.QLabel("عنوان الملاحظة:")
        self.title_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.title_edit = qt.QLineEdit()
        self.title_edit.setAccessibleName(self.title_label.text())
        self.title_edit.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        self.title_edit.setText(title)
        layout.addWidget(self.title_label)
        layout.addWidget(self.title_edit)        
        self.content_label = qt.QLabel("محتوى الملاحظة:")
        self.content_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)                
        if self.mode == "view":
            self.content_edit = QReadOnlyTextEdit()
            self.content_edit.setPlainText(content)
        else:
            self.content_edit = qt.QTextEdit()
            self.content_edit.setText(content)        
        self.content_edit.setAccessibleName(self.content_label.text())
        self.content_edit.setTabChangesFocus(True)
        layout.addWidget(self.content_label)
        layout.addWidget(self.content_edit)        
        button_layout = qt.QHBoxLayout()                
        if self.mode == "add":
            self.action_button = qt.QPushButton("إضافة ملاحظة")
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #008000;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 18px;
                    font-size: 14px;
                }
            """)
            self.action_button.clicked.connect(self.save_note)
            button_layout.addWidget(self.action_button)            
        elif self.mode == "view":
            self.edit_button = qt.QPushButton("تعديل الملاحظة")
            self.edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #0000AA;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 18px;
                    font-size: 14px;
                }
            """)
            self.edit_button.clicked.connect(self.switch_to_edit_mode)
            button_layout.addWidget(self.edit_button)            
            self.action_button = qt.QPushButton("حفظ التعديلات")
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #008000;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 18px;
                    font-size: 14px;
                }
            """)
            self.action_button.setVisible(False)
            self.action_button.clicked.connect(self.save_note)
            button_layout.addWidget(self.action_button)            
        elif self.mode == "edit":
            self.setWindowTitle("تعديل الملاحظة")
            self.action_button = qt.QPushButton("حفظ التعديلات")
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #008000;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 18px;
                    font-size: 14px;
                }
            """)
            self.action_button.clicked.connect(self.save_note)
            button_layout.addWidget(self.action_button)            
            self.edit_button = qt.QPushButton("تعديل الملاحظة")
            self.edit_button.setVisible(False)
            button_layout.addWidget(self.edit_button)                
        self.cancel_button = qt.QPushButton("إلغاء")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 14px;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)        
        wrapper_layout = qt.QHBoxLayout()
        wrapper_layout.addLayout(button_layout)
        wrapper_layout.setAlignment(qt2.Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(wrapper_layout)
    def switch_to_edit_mode(self):
        self.mode = "edit"
        self.setWindowTitle("تعديل الملاحظة")
        self.title_edit.setReadOnly(False)                
        old_content = self.content_edit.toPlainText()
        new_content_edit = qt.QTextEdit()
        new_content_edit.setText(old_content)
        new_content_edit.setAccessibleName(self.content_label.text())
        new_content_edit.setTabChangesFocus(True)                
        layout = self.layout()
        layout.replaceWidget(self.content_edit, new_content_edit)
        self.content_edit.deleteLater()
        self.content_edit = new_content_edit        
        self.edit_button.setVisible(False)
        self.action_button.setVisible(True)
        try:
            self.action_button.clicked.disconnect()
        except:
            pass
        self.action_button.clicked.connect(self.save_note)
        self.edit_requested.emit(self.old_name)
        self.close()
    def save_note(self):
        new_title = self.title_edit.text().strip()
        new_content = self.content_edit.toPlainText().strip()        
        if not new_title:
            qMessageBox.MessageBox.error(self, "خطأ", "عنوان الملاحظة لا يمكن أن يكون فارغًا.")
            return            
        if self.mode == "add":
            self.saved.emit(self.old_name, new_title, new_content)
            self.close()            
        elif self.mode == "edit":
            self.saved.emit(self.old_name, new_title, new_content)
            self.close()