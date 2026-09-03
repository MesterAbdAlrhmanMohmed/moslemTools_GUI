import os
import re
import custom_errors

class MotonDataLoader:
    def __init__(self, base_data_path="data/DataMoton"):
        self.base_data_path = base_data_path
        self.categories_arabic = []
        self.categories_english = []
        self.dic_moton_arabic = {}
        self.dic_moton_english = {}
        self.arabic_to_slug = {}
        self.load_data()

    def load_data(self):
        cat_ar_path = os.path.join(self.base_data_path, "ListMotonArabic")
        cat_en_path = os.path.join(self.base_data_path, "ListMotonEnglish")
        dic_ar_path = os.path.join(self.base_data_path, "DicListMotonArabic")
        dic_en_path = os.path.join(self.base_data_path, "DicListMotonEnglish")

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
        txt_path = os.path.join(self.base_data_path, "TextFiles", f"{slug}.txt")
        if not os.path.exists(txt_path):
            return ["المتن كاملا"]
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
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
