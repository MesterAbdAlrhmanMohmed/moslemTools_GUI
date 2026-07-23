import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1

class QReadOnlyTextEdit(qt.QTextEdit):
    def __init__(self, parent=None, viewer_name=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setTextInteractionFlags(qt2.Qt.TextInteractionFlag.TextSelectableByMouse | qt2.Qt.TextInteractionFlag.TextSelectableByKeyboard)
        from settings import settings_handler
        wrap_val = settings_handler.get("font_wrap", viewer_name) if viewer_name else ""
        if wrap_val == "True" or (wrap_val == "" and settings_handler.get("font", "wrap") == "True"):
            self.setLineWrapMode(qt.QTextEdit.LineWrapMode.WidgetWidth)
            self.setWordWrapMode(qt1.QTextOption.WrapMode.WordWrap)
        else:
            self.setLineWrapMode(qt.QTextEdit.LineWrapMode.NoWrap)
        self.setAcceptRichText(True)
        self.document().setDefaultCursorMoveStyle(qt2.Qt.CursorMoveStyle.VisualMoveStyle)
    def setText(self, text):
        if text:
            text = "\n".join([line if line.strip() else "\u200b" for line in text.split("\n")])
        super().setText(text)