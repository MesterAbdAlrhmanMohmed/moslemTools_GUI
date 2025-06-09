import os,json,settings
ahadeeths={}
def getahadeethByIndex(index:str):
    rahadeeths={}
    for key,value in ahadeeths.items():
        rahadeeths[value]=key
    return rahadeeths[index]
def setahadeeth():
    global ahadeeths
    with open("data/json/files/all_ahadeeth.json","r",encoding="utf-8") as file:
        ahadeeths=json.load(file)
    values=ahadeeths.copy().values()
    for value in values:
        if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"ahadeeth",value)):
            del ahadeeths[getahadeethByIndex(value)]
setahadeeth()