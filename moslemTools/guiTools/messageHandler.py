import json,requests,os,time
from settings import settings_handler
from .textViewer import TextViewer
def check(p):
    try:
        r=requests.get("https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/moslemTools_GUI/main/message.json", params={'t': int(time.time())}, timeout=10)
        r.raise_for_status()
        data=r.json()
        target_dir = os.path.join(os.getenv('appdata'), settings_handler.appName)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        with open(os.path.join(target_dir, "message.json"),"w",encoding="utf-8") as file:
            json.dump(data,file,ensure_ascii=False,indent=4)
        try:
            idMessage=int(settings_handler.get("g","messageID"))
        except (ValueError, TypeError):
            idMessage = 0
        remote_id = int(data.get("id", 0))
        if remote_id > idMessage:
            TextViewer(p,"رسالة من المطور",data.get("message", "")).exec()
            settings_handler.set("g","messageID",str(remote_id))
    except:
        pass