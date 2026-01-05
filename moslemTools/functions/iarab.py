import json
import functions.quranJsonControl
_iarab_data = None
def getIarab(From:int,to:int):
    global _iarab_data
    try:
        if _iarab_data is None:
            with open("data/json/i raab.json","r",encoding="utf-8") as file:
                _iarab_data=json.load(file)
        data = _iarab_data
        result=[]
        for index, ayah in enumerate(data, 1):
            if index>=From and index<=to:
                ayahText = functions.quranJsonControl.getAyahTextByNumber(index)
                result.append(ayahText + "\n" + ayah)
        return "\n".join(result)
    except:
        return ("لم يتم العثور على ملفات الإعراب, الرجاء إعادة تثبيت البرنامج مرة أخرى")