import json,requests,os
from settings import settings_handler
from .textViewer import TextViewer
def check(p):
    try:
        r=requests.get("https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/main/message.json")
        data=r.json()
        with open(os.path.join(os.getenv('appdata'),settings_handler.appName,"message.json"),"w",encoding="utf-8") as file:
            json.dump(data,file,ensure_ascii=False,indent=4)
        idMessage=int(settings_handler.get("g","messageID"))
        if data["id"]>idMessage:
            settings_handler.set("g","messageID",str(data["id"]))
            TextViewer(p,"رسالة من المطور",data["message"]).exec()
    except Exception as e:
        print(e)
        pass