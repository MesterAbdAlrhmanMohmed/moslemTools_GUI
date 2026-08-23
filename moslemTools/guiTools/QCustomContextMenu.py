from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import QMenu, QWidgetAction


class QCustomContextMenu(QMenu):
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not isinstance(args[0], str):
            super().__init__(args[0])
        elif len(args) >= 1 and isinstance(args[0], str):
            super().__init__(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def addMenu(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            menu = QCustomContextMenu(args[0], self)
            super().addMenu(menu)
            return menu
        return super().addMenu(*args)

    def _navigation_actions(self):
        return [
            action
            for action in self.actions()
            if action.isVisible()
            and not action.isSeparator()
            and action.isEnabled()
        ]

    def _send_navigation_key(self, key, count):
        for _ in range(count):
            event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                key,
                Qt.KeyboardModifier.NoModifier
            )
            super().keyPressEvent(event)

    def _go_home(self):
        actions = self._navigation_actions()

        if not actions:
            return

        current = self.activeAction()

        if current not in actions:
            self._send_navigation_key(
                Qt.Key.Key_Home,
                1
            )
            return

        index = actions.index(current)

        self._send_navigation_key(
            Qt.Key.Key_Up,
            index
        )

    def _go_end(self):
        actions = self._navigation_actions()

        if not actions:
            return

        current = self.activeAction()

        if current not in actions:
            self._send_navigation_key(
                Qt.Key.Key_End,
                1
            )
            return

        index = actions.index(current)

        self._send_navigation_key(
            Qt.Key.Key_Down,
            len(actions) - index - 1
        )

    def _page_size(self):
        actions = self._navigation_actions()

        if not actions:
            return 1

        heights = [
            self.actionGeometry(action).height()
            for action in actions
            if self.actionGeometry(action).height() > 0
        ]

        if not heights:
            return 1

        average_height = sum(heights) / len(heights)

        if average_height <= 0 or self.height() <= 0:
            return 1

        return max(
            1,
            int(self.height() / average_height) - 1
        )

    def _page_up(self):
        actions = self._navigation_actions()

        if not actions:
            return

        current = self.activeAction()

        if current not in actions:
            self._send_navigation_key(
                Qt.Key.Key_Up,
                1
            )
            return

        count = min(
            self._page_size(),
            actions.index(current)
        )

        self._send_navigation_key(
            Qt.Key.Key_Up,
            count
        )

    def _page_down(self):
        actions = self._navigation_actions()

        if not actions:
            return

        current = self.activeAction()

        if current not in actions:
            self._send_navigation_key(
                Qt.Key.Key_Down,
                1
            )
            return

        count = min(
            self._page_size(),
            len(actions) - actions.index(current) - 1
        )

        self._send_navigation_key(
            Qt.Key.Key_Down,
            count
        )

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