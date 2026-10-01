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
                    key = event.key()
                    is_grid = (self.viewMode() == qt.QListView.ViewMode.IconMode)
                    is_horizontal_1d = (not is_grid and self.flow() == qt.QListView.Flow.LeftToRight)
                    is_vertical = (not is_grid and not is_horizontal_1d)

                    if is_vertical:
                        if key == qt2.Qt.Key.Key_Right:
                            next_row = 0 if (cur >= count - 1 or cur < 0) else cur + 1
                            self.setCurrentRow(next_row)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Left:
                            next_row = count - 1 if cur <= 0 else cur - 1
                            self.setCurrentRow(next_row)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Down and (cur >= count - 1 or cur < 0):
                            self.setCurrentRow(0)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Up and cur <= 0:
                            self.setCurrentRow(count - 1)
                            event.accept()
                            return
                    elif is_horizontal_1d:
                        if key == qt2.Qt.Key.Key_Down:
                            next_row = 0 if (cur >= count - 1 or cur < 0) else cur + 1
                            self.setCurrentRow(next_row)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Up:
                            next_row = count - 1 if cur <= 0 else cur - 1
                            self.setCurrentRow(next_row)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Right and (cur >= count - 1 or cur < 0):
                            self.setCurrentRow(0)
                            event.accept()
                            return
                        elif key == qt2.Qt.Key.Key_Left and cur <= 0:
                            self.setCurrentRow(count - 1)
                            event.accept()
                            return
                    else:
                        if key in (qt2.Qt.Key.Key_Down, qt2.Qt.Key.Key_Right) and (cur >= count - 1 or cur < 0):
                            self.setCurrentRow(0)
                            event.accept()
                            return
                        elif key in (qt2.Qt.Key.Key_Up, qt2.Qt.Key.Key_Left) and cur <= 0:
                            self.setCurrentRow(count - 1)
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
