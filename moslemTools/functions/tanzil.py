import json
_tanzil_data = None
def gettanzil(From:int):
    global _tanzil_data
    try:
        if _tanzil_data is None:
            with open("data/json/tanzil.json","r",encoding="utf-8") as file:
                _tanzil_data=json.load(file)
        data = _tanzil_data
        result=""
        for ayah in data:
            index=data.index(ayah)+1
            if index==From:
                result=ayah
                break
        return result
    except:
        return ("لم يتم العثور على أسباب نزول متاحة , الرجاء إعادة تثبيت البرنامج")