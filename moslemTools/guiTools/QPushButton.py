import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class QPushButton(qt.QPushButton):
    def keyPressEvent(self, event):        
        super().keyPressEvent(event)        
        if event.key() in {
            qt2.Qt.Key.Key_Space,
            qt2.Qt.Key.Key_Return,
            qt2.Qt.Key.Key_Enter,
        }:
            if self.isEnabled():
                self.clicked.emit()