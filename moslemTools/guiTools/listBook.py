import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from PyQt6.QtCore import Qt
from settings import *
class listBook(qt.QListWidget):
    def __init__(self):
        super().__init__()
        self.w=qt.QStackedWidget()
        self.currentRowChanged.connect(self.changeI)
        qt1.QShortcut("ctrl+tab",self).activated.connect(self.Nexttab)
        qt1.QShortcut("ctrl+shift+tab",self).activated.connect(self.previousTab)
    def add(self,text,tabWidget):
        self.w.addWidget(tabWidget)
        self.addItem(text)
    def changeI(self,index):
        self.w.setCurrentIndex(index)
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