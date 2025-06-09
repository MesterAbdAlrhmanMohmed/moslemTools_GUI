import os,settings
import json
tafaseers={}
def getTafaseerByIndex(index:str):
    try:
        rtafaseers={}
        for key,value in tafaseers.items():
            rtafaseers[value]=key
        return rtafaseers[index]
    except:
        return ""
def getTafaseer(tafaseerName:str,From:int,to:int):
    try:
        with open(os.path.join(os.getenv('appdata'),settings.app.appName,"tafaseer",tafaseers[tafaseerName]),"r",encoding="utf-8") as file:
            data=json.load(file)
        result=[]
        for ayah in data:
            index=data.index(ayah)+1
            if index>=From and index<=to:
                result.append(ayah)
        return "\n".join(result)
    except:
        return _("لم يتم العثور على تفاسير متاحة , الرجاء تحميل تفسير واحد على الأقل")
def setTafaseer():
    global tafaseers
    with open("data/json/files/all_tafaseers.json","r",encoding="utf-8") as file:
        tafaseers=json.load(file)

    values=tafaseers.copy().values()
    for value in values:
        if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"tafaseer",value)):
            del tafaseers[getTafaseerByIndex(value)]
setTafaseer()