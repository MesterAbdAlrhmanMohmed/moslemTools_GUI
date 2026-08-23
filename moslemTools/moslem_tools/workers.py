import PyQt6.QtCore as qt2
import guiTools


class MessageCheckWorker(qt2.QObject):
    finished = qt2.pyqtSignal()

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

    def check_for_message(self):
        try:
            guiTools.messageHandler.check(self.parent_window)
        except Exception as e:
            print(f"Error checking for message in thread: {e}")
        finally:
            self.finished.emit()
