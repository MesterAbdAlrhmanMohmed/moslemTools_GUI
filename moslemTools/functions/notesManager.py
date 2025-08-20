import json, os
from settings import app
notesPath = os.path.join(os.getenv('appdata'), app.appName, "notes.json")
def openNotesFile():
    try:
        if not os.path.exists(notesPath):
            with open(notesPath, "w", encoding="utf-8") as file:
                json.dump({"quran": [], "ahadeeth": [], "islamicBooks": [], "stories": []}, file, ensure_ascii=False, indent=4)
        with open(notesPath, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {"quran": [], "ahadeeth": [], "islamicBooks": [], "stories": []}
def saveNotes(notesList: dict):
    with open(notesPath, "w", encoding="utf-8") as file:
        json.dump(notesList, file, ensure_ascii=False, indent=4)
def addNewNote(category_type, note_data):
    notesList = openNotesFile()
    category_notes = notesList.get(category_type, [])
    category_notes.append(note_data)
    notesList[category_type] = category_notes
    saveNotes(notesList)
def removeNote(category_type, note_name):
    notesList = openNotesFile()
    category_notes = notesList.get(category_type, [])
    for note in category_notes:
        if note["name"] == note_name:
            category_notes.remove(note)
            break
    notesList[category_type] = category_notes
    saveNotes(notesList)
def updateNote(category_type, old_name, new_note_data):
    notesList = openNotesFile()
    category_notes = notesList.get(category_type, [])
    found = False
    for i, note in enumerate(category_notes):
        if note["name"] == old_name:
            # الحفاظ على بيانات الموضع إذا لم يتم توفيرها في التحديث
            if "position_data" not in new_note_data and "position_data" in note:
                new_note_data["position_data"] = note["position_data"]
            category_notes[i] = new_note_data
            found = True
            break
    notesList[category_type] = category_notes
    saveNotes(notesList)
    return found
def getNoteByName(category_type, name):
    notesList = openNotesFile()
    for note in notesList.get(category_type, []):
        if note["name"] == name:
            return note
    return None
def getNotesForPosition(category_type, position_data):
    notesList = openNotesFile()
    for note in notesList.get(category_type, []):
        if "position_data" in note and note["position_data"] == position_data:
            return note
    return None
def removeAllNotesForCategory(category_type):
    notesList = openNotesFile()
    notesList[category_type] = []
    saveNotes(notesList)
def removeAllNotes():
    saveNotes({"quran": [], "ahadeeth": [], "islamicBooks": [], "stories": []})