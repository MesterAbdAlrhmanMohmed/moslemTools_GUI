import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qc


class QComboBox(qt.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.view().installEventFilter(self)
        except Exception:
            pass

    def setView(self, itemView):
        super().setView(itemView)
        try:
            itemView.installEventFilter(self)
        except Exception:
            pass

    def showPopup(self):
        try:
            self.view().installEventFilter(self)
        except Exception:
            pass
        super().showPopup()

    def keyPressEvent(self, event):
        try:
            if self.view().isVisible():
                is_backtab = (event.key() == qc.Qt.Key.Key_Backtab) or (
                    event.key() == qc.Qt.Key.Key_Tab and bool(event.modifiers() & qc.Qt.KeyboardModifier.ShiftModifier)
                )
                is_tab = (event.key() == qc.Qt.Key.Key_Tab and not bool(event.modifiers() & qc.Qt.KeyboardModifier.ShiftModifier))
                is_next = is_tab or event.key() == qc.Qt.Key.Key_Right
                is_prev = is_backtab or event.key() == qc.Qt.Key.Key_Left
                if is_next or is_prev:
                    count = self.count()
                    if count > 0:
                        cur = self.view().currentIndex().row()
                        if cur < 0:
                            cur = self.currentIndex()
                        if cur < 0:
                            cur = 0
                        next_row = (cur + 1) % count if is_next else (cur - 1 + count) % count
                        idx = self.model().index(next_row, 0)
                        self.view().setCurrentIndex(idx)
                        self.view().scrollTo(idx)
                    event.accept()
                    return
            elif not self.isEditable():
                modifiers = event.modifiers()
                has_ctrl_or_alt = bool(modifiers & (qc.Qt.KeyboardModifier.ControlModifier | qc.Qt.KeyboardModifier.AltModifier))
                if not has_ctrl_or_alt:
                    is_next = event.key() == qc.Qt.Key.Key_Right
                    is_prev = event.key() == qc.Qt.Key.Key_Left
                    if is_next or is_prev:
                        count = self.count()
                        if count > 0:
                            cur = self.currentIndex()
                            if cur < 0:
                                cur = 0
                            next_row = (cur + 1) % count if is_next else (cur - 1 + count) % count
                            if next_row != cur:
                                self.setCurrentIndex(next_row)
                                self.activated.emit(next_row)
                        event.accept()
                        return
        except Exception:
            pass
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        try:
            if obj == self.view() and self.view().isVisible():
                if event.type() == qc.QEvent.Type.ShortcutOverride:
                    if event.key() in (qc.Qt.Key.Key_Tab, qc.Qt.Key.Key_Backtab, qc.Qt.Key.Key_Right, qc.Qt.Key.Key_Left):
                        event.accept()
                        return True
                elif event.type() == qc.QEvent.Type.KeyPress:
                    is_backtab = (event.key() == qc.Qt.Key.Key_Backtab) or (
                        event.key() == qc.Qt.Key.Key_Tab and bool(event.modifiers() & qc.Qt.KeyboardModifier.ShiftModifier)
                    )
                    is_tab = (event.key() == qc.Qt.Key.Key_Tab and not bool(event.modifiers() & qc.Qt.KeyboardModifier.ShiftModifier))
                    is_next = is_tab or event.key() == qc.Qt.Key.Key_Right
                    is_prev = is_backtab or event.key() == qc.Qt.Key.Key_Left
                    if is_next or is_prev:
                        count = self.count()
                        if count > 0:
                            cur = self.view().currentIndex().row()
                            if cur < 0:
                                cur = self.currentIndex()
                            if cur < 0:
                                cur = 0
                            next_row = (cur + 1) % count if is_next else (cur - 1 + count) % count
                            idx = self.model().index(next_row, 0)
                            self.view().setCurrentIndex(idx)
                            self.view().scrollTo(idx)
                        return True
        except Exception:
            pass
        return super().eventFilter(obj, event)
