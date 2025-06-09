import json
with open("data/json/quran.json","r",encoding="utf-8-sig") as file:
    data=json.load(file)
def getSurahs():
    surahs={}
    for key,value in data.items():
        ayahs={}
        for ayah in value["ayahs"]:
            ayahs["{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))]=ayah["numberInSurah"]
        surahs[str(value["number"])+value["name"]]=[key,"\n".join(ayahs),key]
    return surahs
def getJuz():
    juz={}
    for key,value in data.items():
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
    juz={}
    for key,value in data.items():
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
    juz={}
    for key,value in data.items():
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
    juz={}
    times=1
    juzNumber=1
    Q=1
    for key,value in data.items():
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
def getAyah(text):
    for key,value in data.items():
        for ayah in value["ayahs"]:
            t="{} ({})".format(ayah["text"],str(ayah["numberInSurah"]))
            if t==text:
                return ayah["numberInSurah"],key,[ayah["juz"],value["name"],ayah["hizbQuarter"],ayah["sajda"]],ayah["page"],ayah["number"]
    return 1,"1",["1","","",False],"1",1
def getQuran():
    result=[]
    for Surah,value in data.items():
            for Ayah in value["ayahs"]:
                result.append(str(Surah) + value["name"] + " " + Ayah["text"] + "(" + str(Ayah["numberInSurah"]) + ")")
    return result
def getFromToSurahs(from_surah, from_ayah, to_surah, to_ayah):
    result=[]
    for surah_key in sorted(data.keys(), key=lambda x: int(x)):
        surah_num=int(surah_key)
        ayahs=data[surah_key]["ayahs"]
        
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

    # Ensure correct order of types
    sorted_keys = sorted(result.keys(), key=lambda x: int(x))
    for key in sorted_keys:
        key_int = int(key)
        ayahs = result[key][1].split("\n")

        for ayah in ayahs:
            i=ayahs.index(ayah)+1
            # Start collecting at the exact from_type/from_vers
            if key_int == from_type and i == from_vers:
                collecting = True
            if collecting:
                ayah_list.append(ayah)

            # Stop collecting after reaching to_type/to_vers
            if key_int == to_type and i == to_vers:
                return ayah_list

    return ayah_list  # fallback

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