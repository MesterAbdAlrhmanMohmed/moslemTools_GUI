from . import quranJsonControl
import json ,os,gui
from settings import app
bookMarksPath=os.path.join(os.getenv('appdata'),app.appName,"bookMarks.json")
if not os.path.exists(bookMarksPath):
    with open(bookMarksPath,"w",encoding="utf-8") as file:
        json.dump({"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[]},file,ensure_ascii=False,indent=4) # تم إضافة "stories" هنا
def openBookMarksFile():
    try:
        with open(bookMarksPath,"r",encoding="utf-8") as file:
            return json.load(file)
    except:        
        return {"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[]}
def saveBookMarks(bookMarksList:dict):
    with open(bookMarksPath,"w",encoding="utf-8") as file:
        json.dump(bookMarksList,file,ensure_ascii=False,indent=4)
def removeAllQuranBookMarks():
    bookMarksList = openBookMarksFile()
    bookMarksList["quran"] = []
    saveBookMarks(bookMarksList)
def removeAllAhadeethBookMarks():
    bookMarksList = openBookMarksFile()
    bookMarksList["ahadeeth"] = []
    saveBookMarks(bookMarksList)
def removeAllIslamicBookBookMarks():
    bookMarksList = openBookMarksFile()
    bookMarksList["islamicBooks"] = []
    saveBookMarks(bookMarksList)
def removeAllStoriesBookMarks():
    bookMarksList = openBookMarksFile()
    bookMarksList["stories"] = []
    saveBookMarks(bookMarksList)
def removeAllBookMarks():
    saveBookMarks({"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[]})
def addNewHadeethBookMark(bookName:str,hadeethNumber:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    ahadeethBookMarksList=bookMarksList["ahadeeth"]
    newBookMarkData={
        "bookName":bookName,
        "number":hadeethNumber,
        "name":bookMarkName
    }
    ahadeethBookMarksList.append(newBookMarkData)
    bookMarksList["ahadeeth"]=ahadeethBookMarksList
    saveBookMarks(bookMarksList)
def removeAhadeethBookMark(bookMarkName:str):
    bookMarksList=openBookMarksFile()
    ahadeethBookMarksList=bookMarksList["ahadeeth"]
    for hadeethBookMarkData in ahadeethBookMarksList:
        if hadeethBookMarkData["name"]==bookMarkName:
            ahadeethBookMarksList.remove(hadeethBookMarkData)
            break
    bookMarksList["ahadeeth"]=ahadeethBookMarksList
    saveBookMarks(bookMarksList)
def GetHadeethBookByName(name:str):
    ahadeethBookMarks=openBookMarksFile()
    for hadeethData in ahadeethBookMarks["ahadeeth"]:
        if hadeethData["name"]==name:
            return hadeethData["bookName"],hadeethData["number"]
def addNewQuranBookMark(typeIndex:int,categoryIndex,ayahIndex:int,isPlayer:bool,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    quranBookMarksList=bookMarksList["quran"]
    newQuranBookMarkData={
        "type":typeIndex,
        "category":categoryIndex,
        "ayah":ayahIndex,
        "isPlayer":isPlayer,
        "name":bookMarkName
    }
    quranBookMarksList.append(newQuranBookMarkData)
    bookMarksList["quran"]=quranBookMarksList
    saveBookMarks(bookMarksList)
def removeQuranBookMark(bookMarkName:str):
    bookMarksList=openBookMarksFile()
    quranBookMarksList=bookMarksList["quran"] # تم تغيير ahadeethBookMarksList إلى quranBookMarksList هنا
    for quranBookMarkData in quranBookMarksList: # تم تغيير hadeethBookMarkData إلى quranBookMarkData هنا
        if quranBookMarkData["name"]==bookMarkName: # تم تغيير hadeethBookMarkData إلى quranBookMarkData هنا
            quranBookMarksList.remove(quranBookMarkData) # تم تغيير hadeethBookMarkData إلى quranBookMarkData هنا
            break
    bookMarksList["quran"]=quranBookMarksList
    saveBookMarks(bookMarksList)
def openQuranByBookMarkName(p,bookMarkName:str):
    quranBookMarksList=openBookMarksFile()["quran"]
    data = None # تعريف data بقيمة افتراضية
    for bookMark in quranBookMarksList:
        if bookMark["name"]==bookMarkName:
            data=bookMark
            break
    if data is None: # إضافة تحقق إذا لم يتم العثور على العلامة المرجعية
        return
    result=""
    if data["type"]==0:
        result=quranJsonControl.getSurahs()
    elif data["type"]==1:
        result=quranJsonControl.getPage()
    elif data["type"]==2:
        result=quranJsonControl.getJuz()
    elif data["type"]==3:
        result=quranJsonControl.getHezb()
    elif data["type"]==4:
        result=quranJsonControl.getHizb()
    if data["isPlayer"]:
        gui.QuranPlayer(p,result[data["category"]][1],data["ayah"],data["type"],data["category"]).exec()
    else:
        gui.QuranViewer(p,result[data["category"]][1],data["type"],data["category"],index=data["ayah"]+1).exec()
def addNewislamicBookBookMark(bookName:str,partName:str,pageNumber:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    try:
        islamicBookBookMarksList=bookMarksList["islamicBooks"]
    except:
        islamicBookBookMarksList=bookMarksList["islamicBooks"]=[]
    newBookMarkData={
        "bookName":bookName,
        "number":pageNumber,
        "part":partName,
        "name":bookMarkName
    }
    islamicBookBookMarksList.append(newBookMarkData)
    bookMarksList["islamicBooks"]=islamicBookBookMarksList
    saveBookMarks(bookMarksList)
def removeislamicBookBookMark(bookMarkName:str):
    bookMarksList=openBookMarksFile()
    islamicBookBookMarksList=bookMarksList["islamicBooks"]
    for islamicBookBookMarkData in islamicBookBookMarksList:
        if islamicBookBookMarkData["name"]==bookMarkName:
            islamicBookBookMarksList.remove(islamicBookBookMarkData)
            break
    bookMarksList["islamicBooks"]=islamicBookBookMarksList
    saveBookMarks(bookMarksList)
def GetislamicBookBookByName(name:str):
    islamicBookBookMarks=openBookMarksFile()
    for islamicBookData in islamicBookBookMarks["islamicBooks"]:
        if islamicBookData["name"]==name:
            return islamicBookData["bookName"],islamicBookData["number"],islamicBookData["part"]
def addNewStoriesBookMark(typeIndex:int,categoryIndex,lineIndex:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    try:
        storiesBookMarksList=bookMarksList["stories"] # تم تغيير quranBookMarksList إلى storiesBookMarksList هنا
    except:
        storiesBookMarksList=bookMarksList["stories"]=[] # تم تغيير quranBookMarksList إلى storiesBookMarksList هنا
    newStoriesBookMarkData={ # تم تغيير newQuranBookMarkData إلى newStoriesBookMarkData هنا
        "type":typeIndex,
        "category":categoryIndex,
        "line":lineIndex,
        "name":bookMarkName
    }
    storiesBookMarksList.append(newStoriesBookMarkData) # تم تغيير quranBookMarksList إلى storiesBookMarksList و newQuranBookMarkData إلى newStoriesBookMarkData
    bookMarksList["stories"]=storiesBookMarksList # تم تغيير quranBookMarksList إلى storiesBookMarksList هنا
    saveBookMarks(bookMarksList)
def removeStoriesBookMark(bookMarkName:str):
    bookMarksList=openBookMarksFile()
    storiesBookMarksList=bookMarksList["stories"] # تم تغيير ahadeethBookMarksList إلى storiesBookMarksList هنا
    for storiesBookMarkData in storiesBookMarksList: # تم تغيير hadeethBookMarkData إلى storiesBookMarkData هنا
        if storiesBookMarkData["name"]==bookMarkName: # تم تغيير hadeethBookMarkData إلى storiesBookMarkData هنا
            storiesBookMarksList.remove(storiesBookMarkData) # تم تغيير hadeethBookMarkData إلى storiesBookMarkData هنا
            break
    bookMarksList["stories"]=storiesBookMarksList # تم تغيير ahadeethBookMarksList إلى storiesBookMarksList هنا
    saveBookMarks(bookMarksList)
def getStoryBookmark(p,name):
    bookMarksList=openBookMarksFile()
    storiesBookMarksList=bookMarksList["stories"]
    type=None
    category=None
    line=None
    for bkName in storiesBookMarksList:
        if bkName["name"]==name:
            type=bkName["type"]
            category=bkName["category"]
            line=bkName["line"]
            break # إضافة break للخروج بعد العثور على العلامة المرجعية
    if type is None: # إضافة تحقق إذا لم يتم العثور على العلامة المرجعية
        return
    if type==0:
        with open("data/json/prophetStories.json","r",encoding="utf-8-sig") as file:
            stories=json.load(file)
    elif type==1:
        with open("data/json/quranStories.json","r",encoding="utf-8-sig") as file:
            stories=json.load(file)
    story=stories[category]
    gui.StoryViewer(p,story,type,category,stories,index=line).exec()
def addNewaudioBookMark(tabName,typeIndex:int,categoryIndex:int,position:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    try:
        audioBookMarksList=bookMarksList["audio " + tabName] # تم تغيير quranBookMarksList إلى audioBookMarksList
    except:
        audioBookMarksList=bookMarksList["audio " + tabName]=[] # تم تغيير quranBookMarksList إلى audioBookMarksList
    newAudioBookMarkData={ # تم تغيير newQuranBookMarkData إلى newAudioBookMarkData
        "type":typeIndex,
        "category":categoryIndex,
        "position":position,
        "name":bookMarkName
    }
    audioBookMarksList.append(newAudioBookMarkData) # تم تغيير quranBookMarksList إلى audioBookMarksList و newQuranBookMarkData إلى newAudioBookMarkData
    bookMarksList["audio " + tabName]=audioBookMarksList # تم تغيير quranBookMarksList إلى audioBookMarksList
    saveBookMarks(bookMarksList)
def removeaudioBookMark(tabName,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    audioBookMarksList=bookMarksList["audio " + tabName] # تم تغيير ahadeethBookMarksList إلى audioBookMarksList
    for audioBookMarkData in audioBookMarksList: # تم تغيير hadeethBookMarkData إلى audioBookMarkData
        if audioBookMarkData["name"]==bookMarkName: # تم تغيير hadeethBookMarkData إلى audioBookMarkData
            audioBookMarksList.remove(audioBookMarkData) # تم تغيير hadeethBookMarkData إلى audioBookMarkData
            break
    bookMarksList["audio " + tabName]=audioBookMarksList # تم تغيير ahadeethBookMarksList إلى audioBookMarksList
    saveBookMarks(bookMarksList)
def GetAudioBookByName(tabName,name:str):
    audioBookMarks=openBookMarksFile() # تم تغيير ahadeethBookMarks إلى audioBookMarks
    for audioData in audioBookMarks["audio " + tabName]: # تم تغيير hadeethData إلى audioData
        if audioData["name"]==name:
            return audioData
def getQuranBookmarkName(type:int,category:str,ayah:str,isPlayer=True):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        quranBookMarksList=bookMarksList["quran"] # تم تغيير ahadeethBookMarksList إلى quranBookMarksList
    except:
        return False,""
    for quranBookMarkData in quranBookMarksList: # تم تغيير hadeethBookMarkData إلى quranBookMarkData
        if quranBookMarkData["type"]==type and quranBookMarkData["category"]==category and quranBookMarkData["ayah"]==ayah and quranBookMarkData["isPlayer"]==isPlayer:
            state=True
            name=quranBookMarkData["name"]
    return state,name
def getAhdeethBookmarkName(bookName:str,hadeethNumber:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        ahadeethBookMarksList=bookMarksList["ahadeeth"]
    except:
        return False,""

    for hadeethBookMarkData in ahadeethBookMarksList:
        if hadeethBookMarkData["bookName"]==bookName and hadeethBookMarkData["number"]==hadeethNumber:
            state=True
            name=hadeethBookMarkData["name"]
    return state,name
def getIslamicBookBookmarkName(bookName:str,hadeethNumber:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        islamicBookBookMarksList=bookMarksList["islamicBooks"] # تم تغيير ahadeethBookMarksList إلى islamicBookBookMarksList
    except:
        return False,""
    for islamicBookBookMarkData in islamicBookBookMarksList: # تم تغيير hadeethBookMarkData إلى islamicBookBookMarkData
        if islamicBookBookMarkData["bookName"]==bookName and islamicBookBookMarkData["number"]==hadeethNumber:
            state=True
            name=islamicBookBookMarkData["name"]
    return state,name
def getStoriesBookmarkName(bookName:str,hadeethNumber:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        storiesBookMarksList=bookMarksList["stories"] # تم تغيير ahadeethBookMarksList إلى storiesBookMarksList
    except:
        return False,""
    for storiesBookMarkData in storiesBookMarksList: # تم تغيير hadeethBookMarkData إلى storiesBookMarkData
        if storiesBookMarkData["category"]==bookName and storiesBookMarkData["line"]==hadeethNumber:
            state=True
            name=storiesBookMarkData["name"]
    return state,name
def getAudioBookmarkName(typeF:str,type:str,category:str,position:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        audioBookMarksList=bookMarksList["audio " + typeF] # تم تغيير ahadeethBookMarksList إلى audioBookMarksList
    except:
        return False,""
    for audioBookMarkData in audioBookMarksList: # تم تغيير hadeethBookMarkData إلى audioBookMarkData
        if audioBookMarkData["type"]==type and audioBookMarkData["category"]==category and audioBookMarkData["position"]==position:
            state=True
            name=audioBookMarkData["name"]
    return state,name