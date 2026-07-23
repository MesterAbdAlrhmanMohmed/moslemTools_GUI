import os,settings
import ujson as json

_ahadeeths=None

def load_ahadeeths():
    global _ahadeeths
    if _ahadeeths is None:
        with open("data/json/files/all_ahadeeth.json","r",encoding="utf-8") as file:
            raw_data = json.load(file)
        filtered = {}
        appdata_path = os.getenv('appdata')
        app_name = settings.app.appName
        for key, value in raw_data.items():
            if os.path.exists(os.path.join(appdata_path, app_name, "ahadeeth", value)):
                filtered[key] = value
        _ahadeeths = filtered

def reload_ahadeeths():
    global _ahadeeths
    _ahadeeths = None
    load_ahadeeths()

def __getattr__(name):
    if name == "ahadeeths":
        load_ahadeeths()
        return _ahadeeths
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def getahadeethByIndex(val: str):
    load_ahadeeths()
    for k, v in _ahadeeths.items():
        if v == val:
            return k
    raise KeyError(val)