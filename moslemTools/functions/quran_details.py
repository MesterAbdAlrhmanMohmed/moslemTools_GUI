import os
import re
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
    return "\n\n".join(results) if results else "لا توجد بيانات متاحة."


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
    return "\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."


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
    return "\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."


_word_by_word_data = None


def _load_word_by_word_data():
    global _word_by_word_data
    if _word_by_word_data is None:
        file_path = os.path.join("data", "json", "earab_and_qurat_word_by_word.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            _word_by_word_data = {}
            for item in raw_list:
                key = (int(item["surah_number"]), int(item["ayah_number"]))
                if key not in _word_by_word_data:
                    _word_by_word_data[key] = []
                _word_by_word_data[key].append(item)
        except Exception:
            _word_by_word_data = {}
    return _word_by_word_data


def get_single_ayah_analytical_irab(surah_no, ayah_no, ayah_text=None):
    data = _load_word_by_word_data()
    words = data.get((int(surah_no), int(ayah_no)), [])
    header = f"{ayah_text}\n" if ayah_text else ""
    if not words:
        return f"{header}لا تتوفر بيانات إعراب تحليلي لهذه الآية."
    blocks = []
    for w in words:
        word = w.get("word", "").strip()
        eerab = w.get("eerab", "").strip()
        if word:
            eerab_str = eerab if eerab else "غير متوفر"
            blocks.append(f"{word}: {eerab_str}")
    words_str = "\n".join(blocks) if blocks else "لا تتوفر بيانات إعراب تحليلي لهذه الآية."
    return f"{header}{words_str}"


def get_range_analytical_irab(ayah_text_list, category=None, type=None):
    output_blocks = []
    for line in ayah_text_list:
        if not line or not line.strip():
            continue
        try:
            Ayah, surah, juz, page, AyahNumber = functions.quranJsonControl.getAyah(line, category, type)
            irab = get_single_ayah_analytical_irab(surah, Ayah, ayah_text=line)
            output_blocks.append(irab)
        except Exception:
            output_blocks.append(f"{line}\nتعذر جلب بيانات الإعراب التحليلي.")
    return "\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."


def format_qiraat_section(section_text):
    if not section_text or not section_text.strip():
        return ""
    text = section_text.strip()
    if "@" not in text and "/" not in text:
        return text
    lines = []
    raw_items = re.findall(r'@([^@]+)', text)
    for raw in raw_items:
        raw = raw.strip()
        if not raw:
            continue
        if "/" in raw:
            parts = raw.split("/", 1)
            reciters = parts[0].strip()
            ruling = parts[1].strip()
            if ruling.endswith("."):
                ruling = ruling[:-1].strip()
            lines.append(f"- {reciters}: {ruling}.")
        else:
            lines.append(f"- {raw}")
    return "\n".join(lines) if lines else text


def format_qiraat_string(raw_qiraat):
    if not raw_qiraat:
        return "لا تتوفر بيانات قراءات"
    text = raw_qiraat.replace("---{عند وصل السورة}---", "{عند وصل السورة}").replace("---{عند الوصل}---", "{عند الوصل}").strip()
    surah_wasl_part = None
    if "{عند وصل السورة}" in text:
        parts = text.split("{عند وصل السورة}")
        text = parts[0].strip()
        surah_wasl_part = parts[1].strip()
    wasl_part = None
    if "{عند الوصل}" in text:
        parts = text.split("{عند الوصل}")
        main_part = parts[0].strip()
        wasl_part = parts[1].strip()
    else:
        main_part = text
    output_parts = []
    if main_part:
        output_parts.append(format_qiraat_section(main_part))
    if wasl_part:
        output_parts.append("[عند الوصل]:\n" + format_qiraat_section(wasl_part))
    if surah_wasl_part:
        output_parts.append("[عند وصل السورة]:\n" + format_qiraat_section(surah_wasl_part))
    return "\n\n".join(output_parts)


def get_single_ayah_qiraat(surah_no, ayah_no, ayah_text=None):
    data = _load_word_by_word_data()
    words = data.get((int(surah_no), int(ayah_no)), [])
    header = f"{ayah_text}\n\n" if ayah_text else ""
    if not words:
        return f"{header}لا تتوفر بيانات قراءات لهذه الآية."
    blocks = []
    for w in words:
        word = w.get("word", "").strip()
        qiraat = w.get("qiraat", "")
        if word:
            qiraat_str = format_qiraat_string(qiraat) if qiraat else "غير متوفر"
            blocks.append(f"الكلمة:\n{word}\nالقراءات:\n{qiraat_str}")
    words_str = "\n\n".join(blocks) if blocks else "لا تتوفر بيانات قراءات لهذه الآية."
    return f"{header}{words_str}"


def get_range_qiraat(ayah_text_list, category=None, type=None):
    output_blocks = []
    for line in ayah_text_list:
        if not line or not line.strip():
            continue
        try:
            Ayah, surah, juz, page, AyahNumber = functions.quranJsonControl.getAyah(line, category, type)
            qiraat = get_single_ayah_qiraat(surah, Ayah, ayah_text=line)
            output_blocks.append(qiraat)
        except Exception:
            output_blocks.append(f"{line}\n\nتعذر جلب بيانات القراءات.")
    return "\n\n".join(output_blocks) if output_blocks else "لا توجد بيانات متاحة."
