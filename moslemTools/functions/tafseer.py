import os,settings
import ujson as json
_tafaseers=None


def load_tafaseers():
    global _tafaseers
    if _tafaseers is None:
        with open("data/json/files/all_tafaseers.json","r",encoding="utf-8") as file:
            _tafaseers=json.load(file)
        values=_tafaseers.copy().values()
        for value in values:
            if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"tafaseer",value)):
                del _tafaseers[getTafaseerByIndex(value)]


def reload_tafaseers():
    global _tafaseers
    _tafaseers = None
    load_tafaseers()


def __getattr__(name):
    if name == "tafaseers":
        load_tafaseers()
        return _tafaseers
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def getTafaseerByIndex(index:str):
    load_tafaseers()
    try:
        rtafaseers={}
        for key,value in _tafaseers.items():
            rtafaseers[value]=key
        return rtafaseers[index]
    except:
        return ""


def getTafaseer(tafaseerName:str,From:int,to:int):
    load_tafaseers()
    import functions.quranJsonControl
    try:
        with open(os.path.join(os.getenv('appdata'),settings.app.appName,"tafaseer",_tafaseers[tafaseerName]),"r",encoding="utf-8") as file:
            data=json.load(file)
        result=[]
        for index, ayah in enumerate(data, 1):
            if index>=From and index<=to:
                ayahText=functions.quranJsonControl.getAyahTextByNumber(index)
                content = ayah.strip() if ayah else ""
                if not content:
                    content = "(لم يذكر المؤلف تفسيراً لهذه الآية في هذا الكتاب)"
                result.append(ayahText + "\n" + content)
        return "\n".join(result)
    except:
        return ("لا توجد بيانات لهذا التفسير , الرجاء اعادة تحميل هذا التفسير")
