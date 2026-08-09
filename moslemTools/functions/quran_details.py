import os
import ujson as json
import functions.quranJsonControl

_quran_details_data = None


def _load_details_data():
    global _quran_details_data
    if _quran_details_data is None:
        file_path = os.path.join("data", "json", "quran_data.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                _quran_details_data = json.load(f)
        except Exception:
            _quran_details_data = {}
    return _quran_details_data


def get_ayah_details(surah_no, ayah_no):
    data = _load_details_data()
    s_key = str(surah_no)
    a_key = str(ayah_no)
    if isinstance(data, dict) and s_key in data:
        surah_data = data[s_key]
        if isinstance(surah_data, dict) and a_key in surah_data:
            return surah_data[a_key]
    return None


def get_single_ayah_detailed_irab(surah_no, ayah_no):
    details = get_ayah_details(surah_no, ayah_no)
    if details and isinstance(details, dict):
        irab = details.get("irab", "")
        if irab:
            return irab.strip()
    return "لا يتوفر إعراب مفصل لهذه الآية."


def get_range_detailed_irab(ayah_text_list, category=None, type=None):
    results = []
    for line in ayah_text_list:
        if not line or not line.strip():
            continue
        try:
            Ayah, surah, juz, page, AyahNumber = functions.quranJsonControl.getAyah(line, category, type)
            details = get_ayah_details(surah, Ayah)
            if details and isinstance(details, dict) and "irab" in details:
                irab_text = details["irab"].strip()
                results.append(irab_text)
            else:
                results.append("لا تتوفر بيانات إعراب مفصل لهذه الآية.")
        except Exception:
            results.append("تعذر جلب الإعراب المفصل.")
    return "\n\n\n".join(results) if results else "لا توجد بيانات متاحة."


def get_single_ayah_meanings(surah_no, ayah_no, ayah_text=None):
    details = get_ayah_details(surah_no, ayah_no)
    header = f"{ayah_text}:\n" if ayah_text else ""
    if not details or not isinstance(details, dict) or "words" not in details:
        return f"{header}لا تتوفر معاني الكلمات لهذه الآية."
    words = details.get("words", [])
    if not words:
        return f"{header}لا تتوفر معاني الكلمات لهذه الآية."
    sorted_words = sorted(words, key=lambda w: w.get("wordNo", 0))
    lines = []
    for w in sorted_words:
        word = w.get("word", "").strip()
        meaning = w.get("meaning", "").strip()
        if word:
            meaning_str = meaning if meaning else "غير متوفر"
            lines.append(f"{word} — {meaning_str}")
    words_str = "\n".join(lines) if lines else "لا تتوفر معاني الكلمات لهذه الآية."
    return f"{header}{words_str}"


def get_range_meanings(ayah_text_list, category=None, type=None):
    output_blocks = []
    for line in ayah_text_list:
        if not line or not line.strip():
            continue
        try:
            Ayah, surah, juz, page, AyahNumber = functions.quranJsonControl.getAyah(line, category, type)
            meanings = get_single_ayah_meanings(surah, Ayah, ayah_text=line)
            output_blocks.append(meanings)
        except Exception:
            output_blocks.append(f"{line}:\nتعذر جلب معاني الكلمات.")
    return "\n\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."


def get_single_ayah_sarf(surah_no, ayah_no, ayah_text=None):
    details = get_ayah_details(surah_no, ayah_no)
    header = f"{ayah_text}\n\n" if ayah_text else ""
    if not details or not isinstance(details, dict) or "words" not in details:
        return f"{header}لا تتوفر بيانات صرف الكلمات لهذه الآية."
    words = details.get("words", [])
    if not words:
        return f"{header}لا تتوفر بيانات صرف الكلمات لهذه الآية."
    sorted_words = sorted(words, key=lambda w: w.get("wordNo", 0))
    blocks = []
    for w in sorted_words:
        word = w.get("word", "").strip()
        sarf = w.get("sarf", "").strip()
        root = w.get("root", "").strip()
        if word:
            sarf_str = sarf if sarf else "غير متوفر"
            root_str = root if root else "غير متوفر"
            blocks.append(f"الكلمة:\n{word}\nالصرف:\n{sarf_str}\nالجذر:\n{root_str}")
    sarf_str = "\n\n".join(blocks) if blocks else "لا تتوفر بيانات صرف الكلمات لهذه الآية."
    return f"{header}{sarf_str}"


def get_range_sarf(ayah_text_list, category=None, type=None):
    output_blocks = []
    for line in ayah_text_list:
        if not line or not line.strip():
            continue
        try:
            Ayah, surah, juz, page, AyahNumber = functions.quranJsonControl.getAyah(line, category, type)
            sarf = get_single_ayah_sarf(surah, Ayah, ayah_text=line)
            output_blocks.append(sarf)
        except Exception:
            output_blocks.append(f"{line}\n\nتعذر جلب بيانات صرف الكلمات.")
    return "\n\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."
