import os,json,settings
books={}
def getBookByIndex(index:str):
    rbooks={}
    for key,value in books.items():
        rbooks[value]=key
    return rbooks[index]
def setbook():
    global books
    with open("data/json/files/all_islamic_books.json","r",encoding="utf-8") as file:
        books=json.load(file)
    values=books.copy().values()
    for value in values:
        if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"islamicBooks",value)):
            del books[getBookByIndex(value)]
setbook()