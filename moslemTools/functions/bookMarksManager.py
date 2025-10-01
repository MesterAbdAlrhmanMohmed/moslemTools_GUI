from . import quranJsonControl
import json, os, gui
from settings import app
bookMarksPath=os.path.join(os.getenv('appdata'),app.appName,"bookMarks.json")
if not os.path.exists(bookMarksPath):
    with open(bookMarksPath,"w",encoding="utf-8") as file:
        json.dump({"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[], "islamicTopics":[]},file,ensure_ascii=False,indent=4)
def openBookMarksFile():
    try:
        with open(bookMarksPath,"r",encoding="utf-8") as file:
            data = json.load(file)            
            for key in ["quran", "ahadeeth", "islamicBooks", "stories", "islamicTopics"]:
                if key not in data:
                    data[key] = []
            return data
    except:        
        return {"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[], "islamicTopics":[]}
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
def removeAllIslamicTopicsBookMarks():
    bookMarksList = openBookMarksFile()
    bookMarksList["islamicTopics"] = []
    saveBookMarks(bookMarksList)
def removeAllBookMarks():
    saveBookMarks({"quran":[],"ahadeeth":[],"islamicBooks":[],"stories":[], "islamicTopics":[]})
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
    return None, None
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
    quranBookMarksList=bookMarksList["quran"]
    for quranBookMarkData in quranBookMarksList:
        if quranBookMarkData["name"]==bookMarkName:
            quranBookMarksList.remove(quranBookMarkData)
            break
    bookMarksList["quran"]=quranBookMarksList
    saveBookMarks(bookMarksList)
def openQuranByBookMarkName(p,bookMarkName:str):
    quranBookMarksList=openBookMarksFile()["quran"]
    data = None
    for bookMark in quranBookMarksList:
        if bookMark["name"]==bookMarkName:
            data=bookMark
            break
    if data is None:
        print("error")
        return        
    if not all(key in data for key in ["type", "category", "ayah", "isPlayer"]):
        print("error")
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
    if data["category"] not in result:
        print("error")
        return        
    if data["isPlayer"]:
        gui.QuranPlayer(p,result[data["category"]][1],data["ayah"],data["type"],data["category"]).exec()
    else:
        gui.QuranViewer(p,result[data["category"]][1],data["type"],data["category"],index=data["ayah"]).exec()
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
    return None, None, None
def addNewStoriesBookMark(typeIndex:int,categoryIndex,lineIndex:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    try:
        storiesBookMarksList=bookMarksList["stories"]
    except:
        storiesBookMarksList=bookMarksList["stories"]=[]
    newStoriesBookMarkData={
        "type":typeIndex,
        "category":categoryIndex,
        "line":lineIndex,
        "name":bookMarkName
    }
    storiesBookMarksList.append(newStoriesBookMarkData)
    bookMarksList["stories"]=storiesBookMarksList
    saveBookMarks(bookMarksList)
def removeStoriesBookMark(bookMarkName:str):
    bookMarksList=openBookMarksFile()
    storiesBookMarksList=bookMarksList["stories"]
    for storiesBookMarkData in storiesBookMarksList:
        if storiesBookMarkData["name"]==bookMarkName:
            storiesBookMarksList.remove(storiesBookMarkData)
            break
    bookMarksList["stories"]=storiesBookMarksList
    saveBookMarks(bookMarksList)
def getStoryBookmark(p,name):
    bookMarksList=openBookMarksFile()
    storiesBookMarksList=bookMarksList["stories"]
    type=None
    category=None
    line=None
    for bkName in storiesBookMarksList:
        if bkName["name"]==name:            
            if "type" in bkName and "category" in bkName and "line" in bkName:
                type=bkName["type"]
                category=bkName["category"]
                line=bkName["line"]
            break
    if type is None:
        print("error")
        return
    if type==0:
        with open("data/json/prophetStories.json","r",encoding="utf-8-sig") as file:
            stories=json.load(file)
    elif type==1:
        with open("data/json/quranStories.json","r",encoding="utf-8-sig") as file:
            stories=json.load(file)
    if category in stories:
        story=stories[category]
        gui.StoryViewer(p,story,type,category,stories,index=line).exec()
    else:
        print("error")
def addNewIslamicTopicBookMark(file_path: str, title: str, line: int, bookmark_name: str):
    bookmarks_list = openBookMarksFile()
    new_bookmark = {
        "file": file_path,
        "title": title,
        "line": line,
        "name": bookmark_name
    }
    bookmarks_list["islamicTopics"].append(new_bookmark)
    saveBookMarks(bookmarks_list)
def removeIslamicTopicBookMark(bookmark_name: str):
    bookmarks_list = openBookMarksFile()
    bookmarks_list["islamicTopics"] = [bm for bm in bookmarks_list["islamicTopics"] if bm["name"] != bookmark_name]
    saveBookMarks(bookmarks_list)
def openIslamicTopicByBookmarkName(p, name: str):
    bookmarks_list = openBookMarksFile()
    bookmark_data = next((bm for bm in bookmarks_list.get("islamicTopics", []) if bm["name"] == name), None)
    if not bookmark_data:
        print("Error: Islamic Topic bookmark not found.")
        return
    file_path = bookmark_data.get("file")
    title = bookmark_data.get("title")
    line = bookmark_data.get("line", 0)
    if not file_path or not title:
        print("Error: Invalid Islamic Topic bookmark data.")
        return
    full_path = os.path.join("data", "json", "IslamicTopics", file_path)
    if not os.path.exists(full_path):        
        base_search_path = os.path.join("data", "json", "IslamicTopics")
        found = False
        for root, _, files in os.walk(base_search_path):
            if os.path.basename(file_path) in files:
                full_path = os.path.join(root, os.path.basename(file_path))
                found = True
                break
        if not found:
            print(f"Error: Could not find file {file_path}")
            return
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)        
        all_topics = {item.get("number", str(i)): item.get("label", "") for i, item in enumerate(data)}
        content = all_topics.get(title)        
        if content:
            from gui.islamicTopicViewer import IslamicTopicViewer            
            IslamicTopicViewer(p, file_path, title, content, all_topics, index=line).exec()
        else:
            print(f"Error: Topic '{title}' not found in file '{file_path}'.")
    except Exception as e:
        print(f"Error opening Islamic Topic bookmark: {e}")
def getIslamicTopicBookmarkName(file_path: str, title: str, line: int):
    bookmarks_list = openBookMarksFile()
    for bm in bookmarks_list.get("islamicTopics", []):
        if bm.get("file") == file_path and bm.get("title") == title and bm.get("line") == line:
            return True, bm["name"]
    return False, ""
def getIslamicTopicsBookmarks():
    bookmarks_list = openBookMarksFile()
    return bookmarks_list.get("islamicTopics", [])
def addNewaudioBookMark(tabName,typeIndex:int,categoryIndex:int,position:int,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    try:
        audioBookMarksList=bookMarksList["audio " + tabName]
    except:
        audioBookMarksList=bookMarksList["audio " + tabName]=[]
    newAudioBookMarkData={
        "type":typeIndex,
        "category":categoryIndex,
        "position":position,
        "name":bookMarkName
    }
    audioBookMarksList.append(newAudioBookMarkData)
    bookMarksList["audio " + tabName]=audioBookMarksList
    saveBookMarks(bookMarksList)
def removeaudioBookMark(tabName,bookMarkName:str):
    bookMarksList=openBookMarksFile()
    audioBookMarksList=bookMarksList["audio " + tabName]
    for audioBookMarkData in audioBookMarksList:
        if audioBookMarkData["name"]==bookMarkName:
            audioBookMarksList.remove(audioBookMarkData)
            break
    bookMarksList["audio " + tabName]=audioBookMarksList
    saveBookMarks(bookMarksList)
def GetAudioBookByName(tabName,name:str):
    audioBookMarks=openBookMarksFile()
    for audioData in audioBookMarks["audio " + tabName]:
        if audioData["name"]==name:
            return audioData
    return None
def getQuranBookmarkName(type:int,category:str,ayah:str,isPlayer=True):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        quranBookMarksList=bookMarksList["quran"]
    except:
        return False,""
    for quranBookMarkData in quranBookMarksList:
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
        islamicBookBookMarksList=bookMarksList["islamicBooks"]
    except:
        return False,""
    for islamicBookBookMarkData in islamicBookBookMarksList:
        if islamicBookBookMarkData["bookName"]==bookName and islamicBookBookMarkData["number"]==hadeethNumber:
            state=True
            name=islamicBookBookMarkData["name"]
    return state,name
def getStoriesBookmarkName(bookName:str,hadeethNumber:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        storiesBookMarksList=bookMarksList["stories"]
    except:
        return False,""
    for storiesBookMarkData in storiesBookMarksList:
        if storiesBookMarkData["category"]==bookName and storiesBookMarkData["line"]==hadeethNumber:
            state=True
            name=storiesBookMarkData["name"]
    return state,name
def getAudioBookmarkName(typeF:str,type:str,category:str,position:int):
    name=""
    state=False
    bookMarksList=openBookMarksFile()
    try:
        audioBookMarksList=bookMarksList["audio " + typeF]
    except:
        return False,""
    for audioBookMarkData in audioBookMarksList:
        if audioBookMarkData["type"]==type and audioBookMarkData["category"]==category and audioBookMarkData["position"]==position:
            state=True
            name=audioBookMarkData["name"]
    return state,name
def getQuranBookmarks():
    bookMarksList = openBookMarksFile()
    return bookMarksList["quran"]
def getAhadeethBookmarks():
    bookMarksList = openBookMarksFile()
    return bookMarksList["ahadeeth"]
def getIslamicBookBookmarks():
    bookMarksList = openBookMarksFile()
    return bookMarksList["islamicBooks"]
def getStoriesBookmarks():
    bookMarksList = openBookMarksFile()
    return bookMarksList["stories"]