import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
from settings import *
class ComboBook(qt.QComboBox):
    def __init__(self):
        super().__init__()
        self.w=qt.QStackedWidget()
        self.currentIndexChanged.connect(self.changeI)
        qt1.QShortcut("ctrl+tab",self).activated.connect(self.Nexttab)
        qt1.QShortcut("ctrl+shift+tab",self).activated.connect(self.previousTab)
    def add(self,text,tabWidget):
        self.w.addWidget(tabWidget)
        self.addItem(text)
    def changeI(self,index):
        self.w.setCurrentIndex(index)
    def Nexttab(self):
        if self.currentIndex()==self.count()-1:
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(int(self.currentIndex())+1)
    def previousTab(self):
        if self.currentIndex()==0:
            self.setCurrentIndex(self.count()-1)
        else:
            self.setCurrentIndex(self.currentIndex()-1)