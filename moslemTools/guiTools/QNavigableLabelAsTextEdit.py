from PyQt6.QtWidgets import QTextEdit, QFrame, QWidget, QPushButton, QDialog, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextOption, QKeySequence

try:
    from .QCustomContextMenu import QCustomContextMenu
except ImportError:
    try:
        from guiTools.QCustomContextMenu import QCustomContextMenu
    except ImportError:
        QCustomContextMenu = QMenu


class QNavigableLabelAsTextEdit(QTextEdit):
    def __init__(self, text="", parent=None, viewer_name=None, wrap=None, *args, **kwargs):
        if isinstance(text, QWidget) and parent is None:
            parent = text
            text = ""
        if viewer_name is None:
            viewer_name = kwargs.pop("viewer_name", None)
        if wrap is None:
            wrap = kwargs.pop("wrap", None)

        super().__init__(parent)
        if viewer_name is None and parent is not None:
            p_name = parent.__class__.__name__
            if p_name in ("MessageBox", "QQuestionMessageBox", "MessageBoxForGame"):
                viewer_name = "qMessageBox"
            elif p_name == "ExitApp":
                viewer_name = "exitApp"
            elif p_name in ("download", "CheckForUpdate"):
                viewer_name = "checkForUpdate"

        self.viewer_name = viewer_name
        self.setTabChangesFocus(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setAcceptDrops(False)
        self.setAcceptRichText(False)
        self.document().setDefaultCursorMoveStyle(Qt.CursorMoveStyle.VisualMoveStyle)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

        self.apply_wrap_mode(wrap)

        if text:
            self.setText(str(text))

    def setWrap(self, enable: bool):
        if enable:
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    def apply_wrap_mode(self, wrap=None):
        if wrap is True:
            self.setWrap(True)
        elif wrap is False:
            self.setWrap(False)
        else:
            try:
                from settings import settings_handler
                v_name = self.viewer_name
                if not v_name:
                    win = self.window()
                    win_name = win.__class__.__name__ if win else ""
                    if win_name in ("MessageBox", "QQuestionMessageBox", "MessageBoxForGame"):
                        v_name = "qMessageBox"
                    elif win_name == "ExitApp":
                        v_name = "exitApp"
                    elif win_name in ("download", "CheckForUpdate"):
                        v_name = "checkForUpdate"
                    if v_name:
                        self.viewer_name = v_name

                wrap_val = settings_handler.get("font_wrap", v_name) if v_name else ""
                if wrap_val == "True" or (wrap_val == "" and settings_handler.get("font", "wrap") == "True"):
                    self.setWrap(True)
                else:
                    self.setWrap(False)
            except Exception:
                self.setWrap(False)

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
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_wrap_mode()

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
        copy_action.setEnabled(self.textCursor().hasSelection())
        copy_action.triggered.connect(self.copy)

        select_all_action = menu.addAction("تحديد الكل")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.setEnabled(bool(self.toPlainText()))
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
