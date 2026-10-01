import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2


class QListWidget(qt.QListWidget):
    def keyPressEvent(self, event):
        try:
            modifiers = event.modifiers()
            has_ctrl_or_alt = bool(modifiers & (qt2.Qt.KeyboardModifier.ControlModifier | qt2.Qt.KeyboardModifier.AltModifier | qt2.Qt.KeyboardModifier.ShiftModifier))
            if not has_ctrl_or_alt:
                count = self.count()
                if count > 0:
                    cur = self.currentRow()
                    if event.key() == qt2.Qt.Key.Key_Up and cur == 0:
                        self.setCurrentRow(count - 1)
                        event.accept()
                        return
                    elif event.key() == qt2.Qt.Key.Key_Down and cur == count - 1:
                        self.setCurrentRow(0)
                        event.accept()
                        return
        except Exception:
            pass
        super().keyPressEvent(event)
        try:
            if event.key() == qt2.Qt.Key.Key_Return or event.key() == qt2.Qt.Key.Key_Enter:
                if self.currentItem():
                    self.clicked.emit(self.currentIndex())
        except Exception as error:
            pass
