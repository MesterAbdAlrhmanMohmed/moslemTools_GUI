import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from settings import *


class DynamicStackedWidget(qt.QStackedWidget):
    def sizeHint(self):
        curr = self.currentWidget()
        if curr:
            return curr.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self):
        curr = self.currentWidget()
        if curr:
            return curr.minimumSizeHint()
        return super().minimumSizeHint()


class listBook(qt.QListWidget):
    def __init__(self):
        super().__init__()
        self.w = DynamicStackedWidget()
        self.currentRowChanged.connect(self.changeI)
        qt1.QShortcut("ctrl+tab", self).activated.connect(self.Nexttab)
        qt1.QShortcut("ctrl+shift+tab", self).activated.connect(self.previousTab)

    def add(self, text, tabWidget):
        self.w.addWidget(tabWidget)
        self.addItem(text)

    def changeI(self, index):
        self.w.setCurrentIndex(index)
        self.w.updateGeometry()
        p = self.w.parentWidget()
        while p:
            if isinstance(p, qt.QScrollArea):
                p.verticalScrollBar().setValue(0)
                p.horizontalScrollBar().setValue(0)
                break
            p = p.parentWidget()

    def Nexttab(self):
        if self.currentRow()==self.count()-1:
            self.setCurrentRow(0)
        else:
            self.setCurrentRow(int(self.currentRow())+1)

    def previousTab(self):
        if self.currentRow()==0:
            self.setCurrentRow(self.count()-1)
        else:
            self.setCurrentRow(self.currentRow()-1)
