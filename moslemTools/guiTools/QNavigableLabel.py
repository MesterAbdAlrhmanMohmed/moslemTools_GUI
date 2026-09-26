from PyQt6.QtWidgets import QLineEdit, QWidget, QPushButton, QDialog, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

try:
    from .QCustomContextMenu import QCustomContextMenu
except ImportError:
    try:
        from guiTools.QCustomContextMenu import QCustomContextMenu
    except ImportError:
        QCustomContextMenu = QMenu


class QNavigableLabel(QLineEdit):
    def __init__(self, text="", parent=None):
        if isinstance(text, QWidget) and parent is None:
            parent = text
            text = ""
        super().__init__(str(text) if text is not None else "", parent)

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

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            self.setCursorPosition(0)
            self.deselect()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return

        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy()
            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Menu or (event.key() == Qt.Key.Key_F10 and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
            self.show_context_menu(self.mapToGlobal(self.rect().center()))
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            window = self.window()
            if window:
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

    def show_context_menu(self, pos):
        menu = QCustomContextMenu("الخيارات", self)
        copy_action = menu.addAction("نسخ")
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(self.hasSelectedText())
        copy_action.triggered.connect(self.copy)

        select_all_action = menu.addAction("تحديد الكل")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.setEnabled(bool(self.text()))
        select_all_action.triggered.connect(self.selectAll)

        if pos.isNull() or pos.x() < 0 or pos.y() < 0:
            pos = self.mapToGlobal(self.rect().center())
        menu.exec(pos)

    def contextMenuEvent(self, event):
        pos = event.globalPos()
        if pos.isNull() or pos.x() < 0 or pos.y() < 0:
            pos = self.mapToGlobal(self.rect().center())
        self.show_context_menu(pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def inputMethodEvent(self, event):
        event.accept()

    def dragEnterEvent(self, event):
        event.ignore()

    def dragMoveEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        event.ignore()