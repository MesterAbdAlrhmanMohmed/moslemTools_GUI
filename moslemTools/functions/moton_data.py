import os
import re
import json
import custom_errors

_moton_texts_cache = None
_moton_reciters_data = None


class MotonDataLoader:
    def __init__(self, base_data_path="data/DataMoton"):
        self.base_data_path = base_data_path
        self.categories_arabic = []
        self.categories_english = []
        self.dic_moton_arabic = {}
        self.dic_moton_english = {}
        self.arabic_to_slug = {}
        self.matn_lengths = {}
        self.load_data()

    def load_data(self):
        json_path = os.path.abspath("data/json/files/all_moton.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.categories_arabic = data.get("categories_arabic", [])
                self.categories_english = data.get("categories_english", [])
                self.dic_moton_arabic = data.get("dic_moton_arabic", {})
                self.dic_moton_english = data.get("dic_moton_english", {})
                self.matn_lengths = data.get("matn_lengths", {})
                self.arabic_to_slug = data.get("arabic_to_slug", {})
                return
            except Exception as e:
                print(f"Error loading {json_path}: {e}")

        cat_ar_path = os.path.join(self.base_data_path, "ListMotonArabic")
        cat_en_path = os.path.join(self.base_data_path, "ListMotonEnglish")
        dic_ar_path = os.path.join(self.base_data_path, "DicListMotonArabic")
        dic_en_path = os.path.join(self.base_data_path, "DicListMotonEnglish")
        dic_len_path = os.path.join(self.base_data_path, "DicListMotonLength")

        if os.path.exists(cat_ar_path):
            with open(cat_ar_path, "r", encoding="utf-8") as f:
                self.categories_arabic = [line.strip() for line in f if line.strip()]

        if os.path.exists(cat_en_path):
            with open(cat_en_path, "r", encoding="utf-8") as f:
                self.categories_english = [line.strip() for line in f if line.strip()]

        if os.path.exists(dic_ar_path):
            with open(dic_ar_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        self.dic_moton_arabic[k] = [item.strip() for item in v.split(",") if item.strip()]

        if os.path.exists(dic_en_path):
            with open(dic_en_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        self.dic_moton_english[k] = [item.strip() for item in v.split(",") if item.strip()]

        cat_lengths = {}
        if os.path.exists(dic_len_path):
            with open(dic_len_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        cat_lengths[k] = [int(item.strip()) for item in v.split(",") if item.strip().isdigit()]

        for k, en_list in self.dic_moton_english.items():
            lens = cat_lengths.get(k, [])
            for slug, l in zip(en_list, lens):
                self.matn_lengths[slug] = l

        for k, ar_list in self.dic_moton_arabic.items():
            en_list = self.dic_moton_english.get(k, [])
            for ar, en in zip(ar_list, en_list):
                self.arabic_to_slug[ar] = en

    def get_categories(self):
        return self.categories_arabic

    def get_category_key(self, index):
        if 0 <= index < len(self.categories_english):
            return self.categories_english[index]
        return ""

    def get_moton_for_category(self, category_index):
        key = self.get_category_key(category_index)
        return self.dic_moton_arabic.get(key, [])

    def get_matn_slug(self, matn_name):
        if matn_name in self.arabic_to_slug:
            return self.arabic_to_slug[matn_name]
        clean_name = matn_name.replace("متن ", "").replace("منظومة ", "").strip()
        for k, v in self.arabic_to_slug.items():
            k_clean = k.replace("متن ", "").replace("منظومة ", "").strip()
            if k_clean == clean_name:
                return v
        return ""

    def count_section_verses(self, verse_lines):
        count = 0
        i = 0
        while i < len(verse_lines):
            line = verse_lines[i]
            m = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))", line)
            if m:
                count += 1
                if i + 1 < len(verse_lines):
                    next_l = verse_lines[i + 1]
                    m_next = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))", next_l)
                    if not m_next:
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        return count

    def get_matn_chapters(self, matn_name):
        slug = self.get_matn_slug(matn_name)
        if not slug:
            return ["المتن كاملا"]
        content = get_matn_text(slug)
        if not content:
            return ["المتن كاملا"]
        try:
            sections = re.split(r"\*{3,}", content)
            chapters = []
            total_verses = 0
            from functions.text_actions import format_arabic_bayt_count
            if len(sections) > 1:
                for s in sections[1:]:
                    lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
                    if lines:
                        def format_ch(match):
                            raw_s = match.group(1)
                            mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                            cnt = int(raw_s.translate(mapping))
                            return f"({format_arabic_bayt_count(cnt)})"
                        ch_verses = self.count_section_verses(lines[1:])
                        total_verses += ch_verses
                        if re.search(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', lines[0]):
                            ch_title = re.sub(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', format_ch, lines[0])
                        else:
                            ch_title = f"{lines[0]} ({format_arabic_bayt_count(ch_verses)})" if ch_verses > 0 else lines[0]
                        chapters.append(ch_title)
            else:
                lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
                cnt = self.count_section_verses(lines)
                total_verses = cnt
                base = "المقدمة" if lines else "المتن"
                ch_title = f"{base} ({format_arabic_bayt_count(cnt)})" if cnt > 0 else base
                chapters.append(ch_title)
            full_title = f"المتن كاملا ({format_arabic_bayt_count(total_verses)})" if total_verses > 0 else "المتن كاملا"
            chapters.append(full_title)
            return chapters
        except Exception:
            return ["المتن كاملا"]

    def get_matn_length(self, matn_slug):
        if matn_slug in self.matn_lengths:
            return self.matn_lengths[matn_slug]
        for k, v in self.matn_lengths.items():
            if k.lower() == matn_slug.lower():
                return v
        return 0

    def get_category_for_matn_slug(self, matn_slug):
        for cat_en, moton in self.dic_moton_english.items():
            for m in moton:
                if m.lower() == matn_slug.lower():
                    return cat_en
        return ""

    def parse_matn_data(self, matn_slug):
        content = get_matn_text(matn_slug)
        if not content:
            return []
        from functions import text_actions
        sections = re.split(r"\*{3,}", content)
        sec_data = sections[1:] if len(sections) > 1 else [sections[0]]
        parsed_sections = []
        global_bayt_counter = 0

        for s_idx, s in enumerate(sec_data):
            lines = [l.strip() for l in s.strip().split("\n") if l.strip()]
            if not lines:
                continue
            def format_ch(match):
                raw_s = match.group(1)
                mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                cnt = int(raw_s.translate(mapping))
                return f"({text_actions.format_arabic_bayt_count(cnt)})"
            has_raw_num = bool(re.search(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', lines[0]))
            title = re.sub(r'\(\s*(\d+|[\u0660-\u0669]+)\s*\)', format_ch, lines[0]) if has_raw_num else lines[0]
            verse_lines = lines[1:] if len(sections) > 1 else lines
            verses = []
            i = 0
            while i < len(verse_lines):
                line = verse_lines[i]
                m = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))(.*)", line)
                if m:
                    raw_s = m.group(1) or m.group(2) or m.group(3)
                    mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                    raw_num = int(raw_s.translate(mapping))
                    sadr = m.group(4).strip()
                    if i + 1 < len(verse_lines):
                        next_l = verse_lines[i + 1]
                        m_next = re.match(r"^\s*[\*•\-]?\s*(?:\[\s*(\d+|[\u0660-\u0669]+)\s*\]|\(\s*(\d+|[\u0660-\u0669]+)\s*\)|(\d+|[\u0660-\u0669]+)(?:[\s\-\.\)\t/:]+|(?=[\u0600-\u06FF])))", next_l)
                        if not m_next:
                            ajuz = next_l.strip()
                            i += 2
                        else:
                            ajuz = ""
                            i += 1
                    else:
                        ajuz = ""
                        i += 1
                    global_bayt_counter += 1
                    verses.append({
                        "global_num": global_bayt_counter,
                        "chapter_bayt_num": len(verses) + 1,
                        "raw_num": raw_num,
                        "sadr": sadr,
                        "ajuz": ajuz,
                        "chapter_title": title,
                        "chapter_index": s_idx
                    })
                else:
                    i += 1
            if not has_raw_num and verses:
                title = f"{lines[0]} ({text_actions.format_arabic_bayt_count(len(verses))})"
                for v in verses:
                    v["chapter_title"] = title
            parsed_sections.append({"title": title, "verses": verses})
        return parsed_sections

    def get_matn_data(self, matn_slug):
        return self.parse_matn_data(matn_slug)


def get_matn_text(matn_slug):
    global _moton_texts_cache
    if _moton_texts_cache is None:
        json_texts_path = os.path.abspath("data/json/moton_texts.json")
        if os.path.exists(json_texts_path):
            try:
                with open(json_texts_path, "r", encoding="utf-8") as f:
                    _moton_texts_cache = json.load(f)
            except Exception as e:
                print(f"Error loading moton_texts.json: {e}")
                _moton_texts_cache = {}
        else:
            _moton_texts_cache = {}

    if matn_slug in _moton_texts_cache:
        return _moton_texts_cache[matn_slug]

    txt_path = os.path.abspath(os.path.join("data", "DataMoton", "TextFiles", f"{matn_slug}.txt"))
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            _moton_texts_cache[matn_slug] = content
            return content
        except Exception:
            pass
    return ""


def get_all_moton_reciters():
    global _moton_reciters_data
    if _moton_reciters_data is None:
        json_path = os.path.abspath("data/json/files/all_moton_reciters.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    _moton_reciters_data = json.load(f)
            except Exception as e:
                print(f"Error loading all_moton_reciters.json: {e}")
                _moton_reciters_data = {}
        else:
            _moton_reciters_data = {}
    return _moton_reciters_data


def get_moton_reciters_for_matn(matn_slug):
    data = get_all_moton_reciters()
    matn_map = data.get("matn_reciters", {})
    if matn_slug in matn_map:
        return [(item["name"], item["slug"], item["type"], item["url"]) for item in matn_map[matn_slug]]
    return []


def get_moton_appdata_dir(reciter_slug="", matn_slug=""):
    appdata = os.getenv('appdata') or os.path.expanduser('~')
    base = os.path.join(appdata, "moslemTools_GUI", "moton_reciters")
    if reciter_slug and matn_slug:
        return os.path.join(base, reciter_slug, matn_slug)
    elif reciter_slug:
        return os.path.join(base, reciter_slug)
    return base


def get_moton_bayt_audio_num(matn_slug, reciter_slug, bayt_num):
    if matn_slug == "hidayatmortab":
        if bayt_num <= 30:
            return bayt_num
        if bayt_num <= 37:
            return bayt_num + 1
        if bayt_num <= 46:
            return bayt_num + 2
        if bayt_num <= 65:
            return bayt_num + 3
        if bayt_num <= 73:
            return bayt_num + 4
        if bayt_num <= 101:
            return bayt_num + 5
        if bayt_num <= 205:
            return bayt_num + 6
        if bayt_num <= 242:
            return bayt_num + 7
        if bayt_num == 243:
            return 250
        if bayt_num in (244, 245):
            return 251
        if bayt_num <= 261:
            return bayt_num + 6
        if bayt_num <= 302:
            return bayt_num + 10
        if bayt_num <= 344:
            return bayt_num + 11
        if bayt_num <= 380:
            return bayt_num + 13
        if bayt_num <= 402:
            return bayt_num + 14
        if bayt_num <= 428:
            return bayt_num + 15
        return bayt_num + 16
    return bayt_num


def get_moton_bayt_audio_path(reciter_slug, matn_slug, bayt_num):
    if not reciter_slug or not matn_slug:
        return None
    actual_num = get_moton_bayt_audio_num(matn_slug, reciter_slug, bayt_num)
    appdata_path = os.path.join(get_moton_appdata_dir(reciter_slug, matn_slug), f"{actual_num}.mp3")
    if os.path.exists(appdata_path) and os.path.getsize(appdata_path) > 0:
        return appdata_path
    local_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", reciter_slug, matn_slug, f"{actual_num}.mp3"))
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path
    return None


def get_moton_bayt_audio_url(reciter_slug, matn_slug, bayt_num):
    from PyQt6.QtCore import QUrl
    local_path = get_moton_bayt_audio_path(reciter_slug, matn_slug, bayt_num)
    if local_path:
        return QUrl.fromLocalFile(local_path)
    actual_num = get_moton_bayt_audio_num(matn_slug, reciter_slug, bayt_num)
    online_url = f"https://huggingface.co/datasets/alcoder01/DataMoton/resolve/main/Qasaed/{reciter_slug}/{matn_slug}/{actual_num}.mp3"
    return QUrl(online_url)



def get_moton_continuous_audio_path(reciter_slug, matn_slug):
    if not reciter_slug or not matn_slug:
        return None
    appdata_path = os.path.join(get_moton_appdata_dir(reciter_slug), f"{matn_slug}.mp3")
    if os.path.exists(appdata_path) and os.path.getsize(appdata_path) > 0:
        return appdata_path
    local_path = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", reciter_slug, f"{matn_slug}.mp3"))
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path
    return None


def get_moton_continuous_audio_url(reciter_slug, matn_slug):
    from PyQt6.QtCore import QUrl
    local_path = get_moton_continuous_audio_path(reciter_slug, matn_slug)
    if local_path:
        return QUrl.fromLocalFile(local_path)
    online_url = f"https://huggingface.co/datasets/alcoder01/DataMoton/resolve/main/Qasaed/{reciter_slug}/{matn_slug}.mp3"
    return QUrl(online_url)


def is_moton_reciter_downloaded(reciter_slug, matn_slug):
    appdata_dir = get_moton_appdata_dir(reciter_slug, matn_slug)
    if os.path.isdir(appdata_dir):
        files = [f for f in os.listdir(appdata_dir) if f.endswith(".mp3")]
        if files:
            return True
    local_dir = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", reciter_slug, matn_slug))
    if os.path.isdir(local_dir):
        files = [f for f in os.listdir(local_dir) if f.endswith(".mp3")]
        if files:
            return True
    return False


def get_moton_reciter_downloaded_count(reciter_slug, matn_slug):
    appdata_dir = get_moton_appdata_dir(reciter_slug, matn_slug)
    count = 0
    if os.path.isdir(appdata_dir):
        count = len([f for f in os.listdir(appdata_dir) if f.endswith(".mp3")])
    if count == 0:
        local_dir = os.path.abspath(os.path.join("data", "DataMoton", "Qasaed", reciter_slug, matn_slug))
        if os.path.isdir(local_dir):
            count = len([f for f in os.listdir(local_dir) if f.endswith(".mp3")])
    return count

