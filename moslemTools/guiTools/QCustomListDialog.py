import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
from . import QPushButton
class QCustomListDialog(qt.QDialog):
	def __init__(self, parent, title: str, label: str, items: list):
		super().__init__(parent)
		self.setWindowTitle(title)
		self.selected_item = None
		layout = qt.QVBoxLayout(self)
		self.label = qt.QLabel(label)
		self.label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.label)	
		self.list_widget = qt.QComboBox()
		self.list_widget.addItems(items)
		self.list_widget.activated.connect(self.on_ok)
		self.list_widget.setAccessibleName(label)
		layout.addWidget(self.list_widget)
		self.ok_button = QPushButton("إزالة")
		self.ok_button.setStyleSheet("background-color: #006400; color: white; padding: 5px;") # Dark Green
		self.ok_button.clicked.connect(self.on_ok)
		self.cancel_button = QPushButton("إلغاء")
		self.cancel_button.setStyleSheet("background-color: #8B0000; color: white; padding: 5px;") # Red
		self.cancel_button.clicked.connect(self.reject)
		buttons_layout = qt.QHBoxLayout()
		buttons_layout.addWidget(self.ok_button)
		buttons_layout.addWidget(self.cancel_button)
		layout.addLayout(buttons_layout)
		self.adjustSize()
	def on_ok(self):
		if self.list_widget.currentText():
			self.selected_item = self.list_widget.currentText()
			self.accept()
	@staticmethod
	def getItem(parent, title: str, label: str, items: list):
		dialog = QCustomListDialog(parent, title, label, items)
		result = dialog.exec()
		if result == qt.QDialog.DialogCode.Accepted:
			return dialog.selected_item, True
		return "", False