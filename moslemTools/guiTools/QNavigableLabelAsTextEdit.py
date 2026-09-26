from PyQt6.QtWidgets import QTextEdit, QFrame, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextOption


class QNavigableLabelAsTextEdit(QTextEdit):
    def __init__(self, text="", parent=None, *args, **kwargs):
        if isinstance(text, QWidget) and parent is None:
            parent = text
            text = ""
        super().__init__(parent)        
        self.setTabChangesFocus(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setAcceptDrops(False)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.document().setDefaultCursorMoveStyle(Qt.CursorMoveStyle.VisualMoveStyle)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self.selectionChanged.connect(self.deselect)
        if text:
            self.setText(text)

    def deselect(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.clearSelection()
            self.setTextCursor(cursor)

    def setText(self, text):
        if text:
            text = "\n".join([line if line.strip() else "\u200b" for line in text.split("\n")])
        super().setText(text)
        if hasattr(self, '_custom_alignment'):
            self.selectAll()
            super().setAlignment(self._custom_alignment)
            cursor = self.textCursor()
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)

    def setAlignment(self, alignment):
        self._custom_alignment = alignment
        self.selectAll()
        super().setAlignment(alignment)
        cursor = self.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.deselect()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

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
        self.deselect()

    def mouseDoubleClickEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.deselect()

    def mouseMoveEvent(self, event):
        event.accept()

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        event.accept()
