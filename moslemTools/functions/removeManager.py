import json,os,settings
path=os.path.join(os.getenv('appdata'),settings.app.appName,"remover.json")
if not os.path.exists(path):
    with open(path,"w",encoding="utf-8") as file:
        json.dump([],file,ensure_ascii=False,indent=4)
def addNewFile(filepath:str):
    with open(path,"r",encoding="utf-8") as file:
        data=json.load(file)
    data.append(filepath)
    with open(path,"w",encoding="utf-8") as file:
        json.dump(data,file,ensure_ascii=False,indent=4)
def removeExectingFile():
    with open(path,"r",encoding="utf-8") as file:
        data=json.load(file)
    for file in data:
        try:
            os.remove(file)
            data.remove(file)
        except:
            pass
    with open(path,"w",encoding="utf-8") as file:
        json.dump(data,file,ensure_ascii=False,indent=4)
removeExectingFile()