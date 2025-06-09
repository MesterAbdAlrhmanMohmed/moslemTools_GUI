from .bookViewer import book_viewer
import PyQt6.QtWidgets as qt
class PartSelection (qt.QDialog):
    def __init__(self,p,bookName:str,content:dict):
        super().__init__(p)
        self.setWindowTitle("اختر جزئ")
        self.resize(600,600)
        self.bookName=bookName
        self.content=content
        layout=qt.QVBoxLayout(self)
        self.parts=qt.QListWidget()
        self.parts.addItems(content)
        self.parts.itemActivated.connect(self.openPart)
        layout.addWidget(self.parts)
    def openPart(self):
        partName=self.parts.currentItem().text()
        partContent=self.content[partName]
        book_viewer(self,self.bookName,partName,partContent).exec()
        self.close()