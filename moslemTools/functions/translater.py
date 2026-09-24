import os
import settings
import ujson as json

_translations = None
_index_to_name = {}
_catalog_items = []


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


def _resolve_file_path(rel_path):
    if not rel_path:
        return None
    # 1. Check relative to current working dir data/json/Quran Translations
    p1 = os.path.join("data", "json", "Quran Translations", rel_path)
    if os.path.exists(p1) and os.path.isfile(p1):
        return p1
    p1_norm = os.path.normpath(p1)
    if os.path.exists(p1_norm) and os.path.isfile(p1_norm):
        return p1_norm

    # 2. Check in AppData
    appdata_dir = os.path.join(os.getenv("appdata", ""), settings.app.appName, "Quran Translations")
    p2 = os.path.join(appdata_dir, rel_path)
    if os.path.exists(p2) and os.path.isfile(p2):
        return p2
    p2_norm = os.path.normpath(p2)
    if os.path.exists(p2_norm) and os.path.isfile(p2_norm):
        return p2_norm

    # 3. Check AppData flat filename
    fname = os.path.basename(rel_path)
    p3 = os.path.join(appdata_dir, fname)
    if os.path.exists(p3) and os.path.isfile(p3):
        return p3

    # 4. Check data/json/Quran Translations flat filename
    p4 = os.path.join("data", "json", "Quran Translations", fname)
    if os.path.exists(p4) and os.path.isfile(p4):
        return p4

    # 5. Search recursively in data/json/Quran Translations
    base_dir = os.path.join("data", "json", "Quran Translations")
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir):
            if fname in files:
                return os.path.join(root, fname)

    return None


def _format_display_name(item):
    lang_folder = item.get("language_folder", "")
    author = (item.get("author") or item.get("title") or item.get("name") or "").strip()
    folder_parts = lang_folder.split()
    en_lang = folder_parts[1] if len(folder_parts) > 1 else (folder_parts[0] if folder_parts else "")
    lang_name = item.get("language", "")
    if len(lang_name) <= 3:
        lang_name = en_lang

    if " by " in author:
        display = author
    elif author.lower().startswith(en_lang.lower()) or author.lower().startswith(lang_name.lower()):
        display = author
    elif "translation" in author.lower():
        display = f"{en_lang} - {author}"
    else:
        display = f"{lang_name} by {author}"
    return display.strip()


def load_translations():
    global _translations, _index_to_name, _catalog_items
    if _translations is not None:
        return

    _translations = {}
    _index_to_name = {}
    _catalog_items = []

    # Priority 1: translations_catalog.json
    catalog_path = None
    for cp in [
        os.path.join("data", "json", "Quran Translations", "translations_catalog.json"),
        os.path.join("data", "json", "files", "translations_catalog.json"),
    ]:
        if os.path.exists(cp):
            catalog_path = cp
            break

    if catalog_path:
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                _catalog_items = json.load(f)
        except Exception:
            _catalog_items = []

    if _catalog_items and isinstance(_catalog_items, list):
        name_counts = {}
        for item in _catalog_items:
            d_name = _format_display_name(item)
            name_counts[d_name] = name_counts.get(d_name, 0) + 1

        seen = {}
        for item in _catalog_items:
            d_name = _format_display_name(item)
            if name_counts.get(d_name, 0) > 1:
                seen[d_name] = seen.get(d_name, 0) + 1
                d_name = f"{d_name} ({seen[d_name]})"

            data_path = item.get("data_file_path", "").replace("\\", "/")
            _translations[d_name] = data_path

            # Map all index variants to display name
            _index_to_name[d_name] = d_name
            _index_to_name[data_path] = d_name
            _index_to_name[os.path.normpath(data_path)] = d_name
            if item.get("name"):
                _index_to_name[item["name"]] = d_name
                _index_to_name[f"{item['name']}.json"] = d_name
            if item.get("data_file"):
                _index_to_name[item["data_file"]] = d_name
                _index_to_name[item["data_file"].replace(".json", "")] = d_name
            if item.get("author"):
                _index_to_name[item["author"]] = d_name
    else:
        # Fallback to all_translater.json if catalog not found
        fallback_path = os.path.join("data", "json", "files", "all_translater.json")
        if os.path.exists(fallback_path):
            with open(fallback_path, "r", encoding="utf-8") as f:
                _translations = json.load(f)
            for k, v in _translations.items():
                _index_to_name[k] = k
                _index_to_name[v] = k
                _index_to_name[os.path.basename(v)] = k

    # Ensure Talal Itani alias always maps to English by Talal Itani
    _index_to_name["en.itani.json"] = "English by Talal Itani"
    _index_to_name["en.itani"] = "English by Talal Itani"
    if "English by Talal Itani" not in _translations:
        _translations["English by Talal Itani"] = "الإنجليزية English/en.itani/en.itani.json"


def reload_translations():
    global _translations, _index_to_name, _catalog_items
    _translations = None
    _index_to_name = {}
    _catalog_items = []
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

    # Case-insensitive and partial lookup
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

        file_path = _resolve_file_path(rel_path)
        if not file_path or not os.path.exists(file_path):
            file_path = _resolve_file_path("الإنجليزية English/en.itani/en.itani.json") or _resolve_file_path("en.itani.json")

        if not file_path or not os.path.exists(file_path):
            return "الترجمة غير متوفرة حالياً"

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        verses = _extract_verses(data)
        result = []
        for index, ayah in enumerate(verses, 1):
            if From <= index <= to:
                result.append(ayah)
        return "\n".join(result)
    except Exception as e:
        print(f"Error loading translation: {e}")
        return "تعذر تحميل نص الترجمة"
