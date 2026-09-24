import os
import settings
import ujson as json

_translations = None
_index_to_name = {}


def _extract_verses(data):
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return [item.get("translation") or item.get("text") or "" for item in data]
        return [str(item) for item in data]
    elif isinstance(data, dict):
        verses_list = data.get("quran") or data.get("verses") or data.get("data")
        if isinstance(verses_list, list):
            if verses_list and isinstance(verses_list[0], dict):
                return [item.get("translation") or item.get("text") or "" for item in verses_list]
            return [str(item) for item in verses_list]
    return []


def _get_appdata_dir():
    app_name = getattr(settings.app, "appName", "moslemTools_GUI")
    return os.path.join(os.getenv("appdata", ""), app_name, "Quran Translations")


def _find_in_appdata(rel_path):
    if not rel_path:
        return None
    appdata_dir = _get_appdata_dir()
    if not os.path.exists(appdata_dir):
        return None

    # 1. Check exact relative path in AppData
    p1 = os.path.join(appdata_dir, rel_path)
    if os.path.exists(p1) and os.path.isfile(p1):
        return p1
    p1_norm = os.path.normpath(p1)
    if os.path.exists(p1_norm) and os.path.isfile(p1_norm):
        return p1_norm

    # 2. Check flat filename in AppData root
    fname = os.path.basename(rel_path)
    p2 = os.path.join(appdata_dir, fname)
    if os.path.exists(p2) and os.path.isfile(p2):
        return p2

    # 3. Check recursive search in AppData
    for root, dirs, files in os.walk(appdata_dir):
        if fname in files:
            return os.path.join(root, fname)

    return None


def load_translations():
    global _translations, _index_to_name
    if _translations is not None:
        return

    _translations = {}
    _index_to_name = {}

    # 1. Load manifest of all translations
    all_manifest = {}
    manifest_path = os.path.join("data", "json", "files", "all_translater.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                all_manifest = json.load(f)
        except Exception:
            all_manifest = {}

    # 2. Only keep translations that ACTUALLY exist in AppData!
    for display_name, rel_path in all_manifest.items():
        found = _find_in_appdata(rel_path)
        if found:
            _translations[display_name] = rel_path
            _index_to_name[display_name] = display_name
            _index_to_name[rel_path] = display_name
            _index_to_name[os.path.normpath(rel_path)] = display_name
            fname = os.path.basename(rel_path)
            _index_to_name[fname] = display_name
            _index_to_name[fname.replace(".json", "")] = display_name

    # 3. Always guarantee at least one translation (en.itani) if present in AppData
    if "English by Talal Itani" not in _translations:
        itani_found = _find_in_appdata("en.itani.json") or _find_in_appdata("الإنجليزية English/en.itani/en.itani.json")
        if itani_found:
            _translations["English by Talal Itani"] = "en.itani.json"

    # Always ensure default aliases resolve to Talal Itani
    _index_to_name["en.itani.json"] = "English by Talal Itani"
    _index_to_name["en.itani"] = "English by Talal Itani"


def reload_translations():
    global _translations, _index_to_name
    _translations = None
    _index_to_name = {}
    load_translations()


def __getattr__(name):
    if name == "translations":
        load_translations()
        return _translations
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def gettranslationByIndex(index: str):
    load_translations()
    if not index:
        return "English by Talal Itani"
    if index in _index_to_name:
        return _index_to_name[index]
    norm = os.path.normpath(index).replace("\\", "/")
    if norm in _index_to_name:
        return _index_to_name[norm]
    base = os.path.basename(index)
    if base in _index_to_name:
        return _index_to_name[base]
    if index in _translations:
        return index

    # Case-insensitive lookup
    idx_lower = index.lower().strip()
    for k, v in _index_to_name.items():
        if k.lower() == idx_lower:
            return v
    for name, path in _translations.items():
        if path.lower() == idx_lower or os.path.basename(path).lower() == idx_lower:
            return name
        if idx_lower in name.lower() or idx_lower in path.lower():
            return name

    return "English by Talal Itani"


def gettranslation(translationName: str, From: int, to: int):
    load_translations()
    try:
        rel_path = _translations.get(translationName)
        if not rel_path:
            resolved_name = gettranslationByIndex(translationName)
            rel_path = _translations.get(resolved_name) or translationName

        # Only load from AppData!
        file_path = _find_in_appdata(rel_path)
        if not file_path:
            file_path = _find_in_appdata("en.itani.json")

        if not file_path or not os.path.exists(file_path):
            return "الترجمة غير متوفرة في مجلد البرنامج (AppData)"

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        verses = _extract_verses(data)
        result = []
        for index, ayah in enumerate(verses, 1):
            if From <= index <= to:
                result.append(ayah)
        return "\n".join(result)
    except Exception as e:
        print(f"Error loading translation from AppData: {e}")
        return "تعذر تحميل نص الترجمة"
