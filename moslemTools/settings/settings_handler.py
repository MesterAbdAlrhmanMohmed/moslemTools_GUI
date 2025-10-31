from configparser import ConfigParser
import os,shutil
from . import app
appName=app.appName
cpath=os.path.join(os.getenv('appdata'),appName,"settings.ini")
if not os.path.exists(os.path.join(os.getenv('appdata'),appName)):
    os.mkdir(os.path.join(os.getenv('appdata'),appName))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"audio_stories")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"audio_stories"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"islamicBooks")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"islamicBooks"))
    shutil.copy("data/json/islamicBooks/elShabahLibe.json",os.path.join(os.getenv('appdata'),appName,"islamicBooks","elShabahLibe.json"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"addan")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"addan"))    
    shutil.copy("data/sounds/adaan/fajr.mp3",os.path.join(os.getenv('appdata'),appName,"addan","fajr.mp3"))
    shutil.copy("data/sounds/adaan/genral.mp3",os.path.join(os.getenv('appdata'),appName,"addan","dhuhr.mp3"))
    shutil.copy("data/sounds/adaan/genral.mp3",os.path.join(os.getenv('appdata'),appName,"addan","asr.mp3"))
    shutil.copy("data/sounds/adaan/genral.mp3",os.path.join(os.getenv('appdata'),appName,"addan","maghrib.mp3"))
    shutil.copy("data/sounds/adaan/genral.mp3",os.path.join(os.getenv('appdata'),appName,"addan","isha.mp3"))
    shutil.copy("data/sounds/adaan/ecama_alsalah.m4a",os.path.join(os.getenv('appdata'),appName,"addan","ecama_alsalah.m4a"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"quran surah reciters")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"quran surah reciters"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"athkar")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"athkar"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"Quran Translations")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"Quran Translations"))
    shutil.copy("data/json/Quran Translations/en.itani.json",os.path.join(os.getenv('appdata'),appName,"Quran Translations","en.itani.json"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"reciters")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"reciters"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"tafaseer")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"tafaseer"))
    shutil.copy("data/json/tafaseer/muyassar.json",os.path.join(os.getenv('appdata'),appName,"tafaseer","muyassar.json"))
if not os.path.exists(os.path.join(os.getenv('appdata'),appName,"ahadeeth")):
    os.mkdir(os.path.join(os.getenv('appdata'),appName,"ahadeeth"))
    shutil.copy("data/json/ahadeeth/nawawi40.json",os.path.join(os.getenv('appdata'),appName,"ahadeeth","nawawi40.json"))
    shutil.copy("data/json/ahadeeth/qudsi40.json",os.path.join(os.getenv('appdata'),appName,"ahadeeth","qudsi40.json"))
settingsConfig={
    "g":{       
        "messageID":"0",
        "exitdialog":"True",
        "reciter":"0"
    },
    "tafaseer":{
        "tafaseer":"muyassar.json"
    },
    "translation":{
        "translation":"en.itani.json"
    },
    "athkar":{
        "voice":"0",
        "voiceVolume":"100",
        "text":"0"
    },
    "prayerTimes":{
        "adaanReminder":"True",
        "playPrayerAfterAdhaan":"True",
        "volume":"100",        
        "remindBeforeAdaan":"0",
        "remindAfterAdaan":"3",
        "iqamaVolume":"100"
    },
    "location":{
        "autoDetect":"True",
        "LT1":"33",
        "LT2":"33"
    },
    "update":{
        "autoCheck":"True",
        "beta":"False"
    },
    "quranPlayer":{
        "times":"1",
        "duration":"0",
        "replay":"True"
    },
    "adhanSounds": {
        "fajr": "fajr.mp3",
        "dhuhr": "dhuhr.mp3",
        "asr": "asr.mp3",
        "maghrib": "maghrib.mp3",
        "isha": "isha.mp3",
        "iqama": "ecama_alsalah.m4a"
    },
    "font":{
        "bold":"False",
        "size":"12"
    }
}
if not os.path.exists(cpath):
    config = ConfigParser() 
    for section,values in settingsConfig.items():
        config.add_section(section)
        for key,value in values.items():
            config[section][key]=value
    with open(cpath, "w",encoding="utf-8") as file:
        config.write(file)
def get(section,key):
    try:
        config = ConfigParser()
        config.read(cpath)
        value = config[section][key]
        return value
    except:        
        try:
            return settingsConfig[section][key]
        except:
            return ""
def set(section,key, value):
        config = ConfigParser()
        config.read(cpath)
        try:
            config[section][key] = value
        except KeyError:            
            config.add_section(section)
            config[section][key] = value
        with open(cpath, "w",encoding="utf-8") as file:
            config.write(file)