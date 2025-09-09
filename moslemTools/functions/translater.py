import os,settings,json
translations={}
def gettranslationByIndex(index:str):
    try:
        rtranslations={}
        for key,value in translations.items():
            rtranslations[value]=key
        return rtranslations[index]
    except:
        return ""
def gettranslation(translationName:str,From:int,to:int):
    try:
        with open(os.path.join(os.getenv('appdata'),settings.app.appName,"Quran Translations",translations[translationName]),"r",encoding="utf-8") as file:
            data=json.load(file)
        result=[]
        for ayah in data:
            index=data.index(ayah)+1
            if index>=From and index<=to:
                result.append(ayah)
        return "\n".join(result)
    except:
        return ("لم يتم العثور على ترجمات متاحة ,يرجا تحميل ترجمة واحدة على الأقل")
def settranslation():
    global translations
    with open("data/json/files/all_translater.json","r",encoding="utf-8") as file:
        translations=json.load(file)
    values=translations.copy().values()
    for value in values:
        if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"Quran Translations",value)):
            del translations[gettranslationByIndex(value)]
settranslation()