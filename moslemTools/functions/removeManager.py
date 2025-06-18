import json, os, settings
path = os.path.join(os.getenv('appdata'), settings.app.appName, "remover.json")
if not os.path.exists(path) or os.stat(path).st_size == 0:
    with open(path, "w", encoding="utf-8") as file:
        json.dump([], file, ensure_ascii=False, indent=4)
def addNewFile(filepath: str):
    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = []
    data.append(filepath)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
def removeExectingFile():
    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = []
    for file in data:
        try:
            os.remove(file)
        except:
            pass
    with open(path, "w", encoding="utf-8") as file:
        json.dump([], file, ensure_ascii=False, indent=4)
removeExectingFile()