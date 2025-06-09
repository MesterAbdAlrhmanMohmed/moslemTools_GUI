import re
import PyQt6.QtWidgets as qt
import PyQt6.QtGui as qt1
import PyQt6.QtCore as qt2
class ChangeReciter(qt.QDialog):
    def __init__(self,p,reciters:list,selectedReciter:int):
        super().__init__(p)
        self.reciters=reciters
        self.resize(600,400)
        layout=qt.QVBoxLayout(self)
        serch=qt.QLabel("بحث")
        serch.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(serch)
        self.search_bar=qt.QLineEdit()        
        self.search_bar.setPlaceholderText("بحث ...")
        self.search_bar.textChanged.connect(self.onsearch)        
        self.search_bar.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.search_bar)
        self.recitersListWidget=qt.QListWidget()
        self.recitersListWidget.addItems(self.reciters)
        self.recitersListWidget.setCurrentRow(selectedReciter)
        self.recitersListWidget.itemActivated.connect(self.accept)
        layout.addWidget(self.recitersListWidget)
    def search(self,pattern,text_list):    
        tashkeel_pattern=re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')        
        normalized_pattern=tashkeel_pattern.sub('', pattern)        
        matches=[
            text for text in text_list
            if normalized_pattern in tashkeel_pattern.sub('', text)
        ]        
        return matches        
    def onsearch(self):
        search_text=self.search_bar.text().lower()
        self.recitersListWidget.clear()
        result=self.search(search_text,self.reciters)
        self.recitersListWidget.addItems(result)