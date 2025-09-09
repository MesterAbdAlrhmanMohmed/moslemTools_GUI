import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
class QListWidget(qt.QListWidget):
    def keyPressEvent(self,event):
        super().keyPressEvent(event)        
        try:
            if event.key()==qt2.Qt.Key.Key_Return or event.key()==qt2.Qt.Key.Key_Enter:
                if self.currentItem():
                    self.clicked.emit(self.currentIndex())
        except Exception as error:
            pass