import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent


class QCustomTabBar(qt.QTabBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _navigation_tabs(self):
        return [
            i
            for i in range(self.count())
            if self.isTabEnabled(i) and self.isTabVisible(i)
        ]

    def _go_home(self):
        tabs = self._navigation_tabs()
        if not tabs:
            return
        self.setCurrentIndex(tabs[0])

    def _go_end(self):
        tabs = self._navigation_tabs()
        if not tabs:
            return
        self.setCurrentIndex(tabs[-1])

    def _page_size(self):
        tabs = self._navigation_tabs()
        if not tabs:
            return 1
        widths = [
            self.tabRect(i).width()
            for i in tabs
            if self.tabRect(i).width() > 0
        ]
        if not widths or self.width() <= 0:
            return 5
        average_width = sum(widths) / len(widths)
        if average_width <= 0:
            return 5
        visible_count = int(self.width() / average_width)
        if visible_count > 2:
            return visible_count - 1
        return 5

    def _page_up(self):
        tabs = self._navigation_tabs()
        if not tabs:
            return
        current = self.currentIndex()
        if current not in tabs:
            self.setCurrentIndex(tabs[0])
            return
        idx = tabs.index(current)
        step = min(self._page_size(), idx)
        target_idx = max(0, idx - step)
        self.setCurrentIndex(tabs[target_idx])

    def _page_down(self):
        tabs = self._navigation_tabs()
        if not tabs:
            return
        current = self.currentIndex()
        if current not in tabs:
            self.setCurrentIndex(tabs[-1])
            return
        idx = tabs.index(current)
        step = min(self._page_size(), len(tabs) - idx - 1)
        target_idx = min(len(tabs) - 1, idx + step)
        self.setCurrentIndex(tabs[target_idx])

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key.Key_Home:
            self._go_home()
            event.accept()
            return

        if key == Qt.Key.Key_End:
            self._go_end()
            event.accept()
            return

        if key == Qt.Key.Key_PageUp:
            self._page_up()
            event.accept()
            return

        if key == Qt.Key.Key_PageDown:
            self._page_down()
            event.accept()
            return

        super().keyPressEvent(event)


class QCustomTabWidget(qt.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabBar(QCustomTabBar(self))

    def setExpanding(self, expanding: bool):
        self.tabBar().setExpanding(expanding)

    def addTab(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            dummy = qt.QWidget()
            return super().addTab(dummy, args[0])
        return super().addTab(*args)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        tab_bar = self.tabBar()

        if isinstance(tab_bar, QCustomTabBar):
            is_ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self.hasFocus() or tab_bar.hasFocus() or is_ctrl:
                if key == Qt.Key.Key_Home and not is_ctrl:
                    tab_bar._go_home()
                    event.accept()
                    return

                if key == Qt.Key.Key_End and not is_ctrl:
                    tab_bar._go_end()
                    event.accept()
                    return

                if key == Qt.Key.Key_PageUp:
                    tab_bar._page_up()
                    event.accept()
                    return

                if key == Qt.Key.Key_PageDown:
                    tab_bar._page_down()
                    event.accept()
                    return

        super().keyPressEvent(event)
