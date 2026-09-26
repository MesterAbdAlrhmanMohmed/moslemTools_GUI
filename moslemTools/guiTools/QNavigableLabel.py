from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt

class QNavigableLabel(QLineEdit):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self.setText(text)
        self.setFrame(False)
        self.setAcceptDrops(False)
        self.setCursorPosition(0)
        self.setCursorMoveStyle(Qt.CursorMoveStyle.VisualMoveStyle)

        self.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        self.selectionChanged.connect(self.deselect)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.deselect()
        self.setCursorPosition(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            window = self.window()
            if window:
                from PyQt6.QtWidgets import QPushButton, QDialog
                default_btn = None
                buttons = window.findChildren(QPushButton)
                for btn in buttons:
                    if btn.isEnabled() and btn.isDefault():
                        default_btn = btn
                        break
                if not default_btn and isinstance(window, QDialog):
                    for btn in buttons:
                        if btn.isEnabled() and btn.autoDefault():
                            default_btn = btn
                            break
                if not default_btn and hasattr(window, "OKBTN") and isinstance(window.OKBTN, QPushButton) and window.OKBTN.isEnabled():
                    default_btn = window.OKBTN
                if not default_btn and buttons:
                    for btn in buttons:
                        if btn.isEnabled():
                            default_btn = btn
                            break
                if default_btn:
                    default_btn.click()
                    event.accept()
                    return
            event.ignore()
            return

        navigation_keys = {
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
            Qt.Key.Key_PageUp,
            Qt.Key.Key_PageDown,
        }

        if event.key() in navigation_keys:
            super().keyPressEvent(event)
            return

        event.accept()

    def inputMethodEvent(self, event):
        event.accept()

    def contextMenuEvent(self, event):
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        event.accept()

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        event.accept()
        