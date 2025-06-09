import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class QPushButton(qt.QPushButton):
    def keyPressEvent(self,event):
        super().keyPressEvent(event)
        
        if event.key()==qt2.Qt.Key.Key_Space or event.key()==qt2.Qt.Key.Key_Return or event.key()==qt2.Qt.Key.Key_Enter:
            self.clicked.emit()