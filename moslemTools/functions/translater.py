import os,settings,json
_translations=None
def load_translations():
    global _translations
    if _translations is None:
        with open("data/json/files/all_translater.json","r",encoding="utf-8") as file:
            _translations=json.load(file)
        values=_translations.copy().values()
        for value in values:
            if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"Quran Translations",value)):
                del _translations[gettranslationByIndex(value)]
def reload_translations():
    global _translations
    _translations = None
    load_translations()
def __getattr__(name):
    if name == "translations":
        load_translations()
        return _translations
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def gettranslationByIndex(index:str):
    load_translations()
    try:
        rtranslations={}
        for key,value in _translations.items():
            rtranslations[value]=key
        return rtranslations[index]
    except:
        return ""
def gettranslation(translationName:str,From:int,to:int):
    load_translations()
    try:
        with open(os.path.join(os.getenv('appdata'),settings.app.appName,"Quran Translations",_translations[translationName]),"r",encoding="utf-8") as file:
            data=json.load(file)
        result=[]
        for ayah in data:
            index=data.index(ayah)+1
            if index>=From and index<=to:
                result.append(ayah)
        return "\n".join(result)
    except:
        return ("لم يتم العثور على ترجمات متاحة ,يرجى تحميل ترجمة واحدة على الأقل")