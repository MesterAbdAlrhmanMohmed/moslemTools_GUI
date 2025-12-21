import os,json,settings
_books=None
def load_books():
    global _books
    if _books is None:
        with open("data/json/files/all_islamic_books.json","r",encoding="utf-8") as file:
            _books=json.load(file)
        values=_books.copy().values()
        for value in values:
            if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"islamicBooks",value)):
                del _books[getBookByIndex(value)]
def reload_books():
    global _books
    _books = None
    load_books()
def __getattr__(name):
    if name == "books":
        load_books()
        return _books
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def getBookByIndex(index:str):
    load_books()
    rbooks={}
    for key,value in _books.items():
        rbooks[value]=key
    return rbooks[index]