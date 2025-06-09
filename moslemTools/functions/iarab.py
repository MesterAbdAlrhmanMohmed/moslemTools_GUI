import os
import json
def getIarab(From:int,to:int):
    try:
        with open("data/json/i raab.json","r",encoding="utf-8") as file:
            data=json.load(file)
        result=[]
        for ayah in data:
            index=data.index(ayah)+1
            if index>=From and index<=to:
                result.append(ayah)
        return "\n".join(result)
    except:
        return _("لم يتم العثور على ملفات الإعراب, الرجاء إعادة تثبيت البرنامج مرة أخرى")