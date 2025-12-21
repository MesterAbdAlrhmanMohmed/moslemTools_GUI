import os,json,settings
_ahadeeths=None
def load_ahadeeths():
    global _ahadeeths
    if _ahadeeths is None:
        with open("data/json/files/all_ahadeeth.json","r",encoding="utf-8") as file:
            _ahadeeths=json.load(file)
        values=_ahadeeths.copy().values()
        for value in values:
            if not os.path.exists(os.path.join(os.getenv('appdata'),settings.app.appName,"ahadeeth",value)):
                del _ahadeeths[getahadeethByIndex(value)]
def reload_ahadeeths():
    global _ahadeeths
    _ahadeeths = None
    load_ahadeeths()
def __getattr__(name):
    if name == "ahadeeths":
        load_ahadeeths()
        return _ahadeeths
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def getahadeethByIndex(index:str):
    load_ahadeeths()
    rahadeeths={}
    for key,value in _ahadeeths.items():
        rahadeeths[value]=key
    return rahadeeths[index]