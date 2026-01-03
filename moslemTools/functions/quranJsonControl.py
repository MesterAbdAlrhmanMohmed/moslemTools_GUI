import json,re
_data = None
def _load_data():
    global _data
    if _data is None:
        with open("data/json/quran.json","r",encoding="utf-8-sig") as file:
            _data=json.load(file)
def __getattr__(name):
    if name == "data":
        _load_data()
        return _data
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def getSurahs():
    _load_data()
    surahs={}
    for key,value in _data.items():
        ayahs={}
        for ayah in value["ayahs"]:
            ayahs["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]=ayah["numberInSurah"]
        surahs[str(value["number"])+value["name"]]=[key,"\n".join(ayahs),key]
    return surahs
def getJuz():
    _load_data()
    juz={}
    for key,value in _data.items():
        for ayah in value["ayahs"]:
            juzNumber=ayah["juz"]
            if str(juzNumber) in juz:
                List=juz[str(juzNumber)]
                List.append("{} ({})".format(ayah["text"],str(ayah["numberInSurah"])))
            else:
                List=["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]
            juz[str(juzNumber)]=List
    for j in juz:
        content=juz[j]
        juz[j]=[j,"\n".join(content)]
    return juz
def getPage():
    _load_data()
    juz={}
    for key,value in _data.items():
        for ayah in value["ayahs"]:
            juzNumber=ayah["page"]
            if str(juzNumber) in juz:
                List=juz[str(juzNumber)]
                List.append("{} ({})".format(ayah["text"],str(ayah["numberInSurah"])))
            else:
                List=["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]
            juz[str(juzNumber)]=List
    for j in juz:
        content=juz[j]
        juz[j]=[j,"\n".join(content)]
    return juz
def getHezb():
    _load_data()
    juz={}
    for key,value in _data.items():
        for ayah in value["ayahs"]:
            juzNumber=ayah["hizbQuarter"]
            if str(juzNumber) in juz:
                List=juz[str(juzNumber)]
                List.append("{} ({})".format(ayah["text"],str(ayah["numberInSurah"])))
            else:
                List=["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]
            juz[str(juzNumber)]=List
    for j in juz:
        content=juz[j]
        juz[j]=[j,"\n".join(content)]
    return juz
def getHizb():
    _load_data()
    juz={}
    times=1
    juzNumber=1
    Q=1
    for key,value in _data.items():
        for ayah in value["ayahs"]:
            qNumber=ayah["hizbQuarter"]
            if Q!=qNumber:
                times+=1
                Q+=1
            if times==5:
                times=1
                juzNumber+=1    
            if str(juzNumber) in juz:
                List=juz[str(juzNumber)]
                List.append("{} ({})".format(ayah["text"],str(ayah["numberInSurah"])))
            else:
                List=["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]
            juz[str(juzNumber)]=List
    for j in juz:
        content=juz[j]
        juz[j]=[j,"\n".join(content)]
    return juz
def getAyah(text, category=None, type=None):
    _load_data()
    if type == 0 and category:
        match = re.match(r"(\d+)", category)
        if match:
            surah_key = match.group(1)                        
            special_surahs = ["3", "28", "29", "30", "31", "32", "41", "43", "44", "45", "46"]
            if surah_key in special_surahs:
                if surah_key in _data:
                    for ayah in _data[surah_key]["ayahs"]:
                        t = "{} ({})".format(ayah["text"], str(ayah["numberInSurah"]))
                        if t == text:
                            return ayah["numberInSurah"], surah_key, [ayah["juz"], _data[surah_key]["name"], ayah["hizbQuarter"], ayah["sajda"]], ayah["page"], ayah["number"]    
    for key, value in _data.items():
        for ayah in value["ayahs"]:
            t = "{} ({})".format(ayah["text"], str(ayah["numberInSurah"]))
            if t == text:
                return ayah["numberInSurah"], key, [ayah["juz"], value["name"], ayah["hizbQuarter"], ayah["sajda"]], ayah["page"], ayah["number"]
    return 1, "1", ["1", "", "", False], "1", 1
def getQuran():
    _load_data()
    result=[]
    for Surah,value in _data.items():
            for Ayah in value["ayahs"]:
                result.append(str(Surah) + value["name"] + " " + Ayah["text"] + "(" + str(Ayah["numberInSurah"]) + ")")
    return result
def getFromToSurahs(from_surah, from_ayah, to_surah, to_ayah):
    _load_data()
    result=[]
    for surah_key in sorted(_data.keys(), key=lambda x: int(x)):
        surah_num=int(surah_key)
        ayahs=_data[surah_key]["ayahs"]        
        if from_surah < surah_num < to_surah:
            for ayah in ayahs:
                result.append(f"{ayah['text']} ({ayah['numberInSurah']})")
        elif surah_num == from_surah:
            for ayah in ayahs:
                ayah_num=int(ayah["numberInSurah"])
                if from_surah == to_surah:
                    if from_ayah <= ayah_num <= to_ayah:
                        result.append(f"{ayah['text']} ({ayah['numberInSurah']})")
                else:
                    if ayah_num >= from_ayah:
                        result.append(f"{ayah['text']} ({ayah['numberInSurah']})")                        
        elif surah_num == to_surah:
            for ayah in ayahs:
                ayah_num=int(ayah["numberInSurah"])
                if ayah_num <= to_ayah:
                    result.append(f"{ayah['text']} ({ayah['numberInSurah']})")
    return result
def getFromToTypes(result, from_type, from_vers, to_type, to_vers):
    from_type = int(from_type)
    to_type = int(to_type)
    from_vers = int(from_vers)
    to_vers = int(to_vers)
    ayah_list = []
    collecting = False    
    sorted_keys = sorted(result.keys(), key=lambda x: int(x))
    for key in sorted_keys:
        key_int = int(key)
        ayahs = result[key][1].split("\n")
        for ayah in ayahs:
            i=ayahs.index(ayah)+1            
            if key_int == from_type and i == from_vers:
                collecting = True
            if collecting:
                ayah_list.append(ayah)            
            if key_int == to_type and i == to_vers:
                return ayah_list
    return ayah_list
def getFromTo(from_surah, from_ayah, to_surah, to_ayah,index):
    if index==0:
        return getFromToSurahs(from_surah,from_ayah,to_surah,to_ayah)
    elif index==1:
        result=getPage()
    elif index==2:
        result=getJuz()
    elif index==3:
        result=getHezb()
    elif index==4:
        result=getHizb()
    return getFromToTypes(result,from_surah,from_ayah,to_surah,to_ayah)
def getAyahTextByNumber(number):
    _load_data()
    number = int(number)
    for value in _data.values():
        for ayah in value["ayahs"]:
            if ayah["number"] == number:
                return "{} ({})".format(ayah["text"], ayah["numberInSurah"])
    return ""