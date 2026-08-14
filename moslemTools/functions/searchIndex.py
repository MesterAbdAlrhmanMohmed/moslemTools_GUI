import os, re, sqlite3, settings
import ujson as json

def remove_tashkeel(text):
    return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)

def normalize_hamza(text):
    return re.sub(r'[أإآ]', 'ا', text)

def remove_symbols(text):
    return re.sub(r'[^\w\s]', '', text)

def normalize(text, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True):
    normalized_text = text
    if ignore_tashkeel:
        normalized_text = remove_tashkeel(normalized_text)
    if ignore_hamza:
        normalized_text = normalize_hamza(normalized_text)
    if ignore_symbols:
        normalized_text = remove_symbols(normalized_text)
    return normalized_text

def prepare_fts5_query(term):
    clean = re.sub(r'[^\w\s]', ' ', term).strip()
    words = clean.split()
    if not words:
        return ""
    if len(words) == 1:
        return f'"{words[0]}"*'
    else:
        return f'"{" ".join(words)}"'

def get_book_json_path(book_name):
    if not book_name:
        return None
    appdata_path = os.path.join(os.getenv('appdata'), settings.app.appName, "islamicBooks", book_name)
    if os.path.exists(appdata_path):
        return appdata_path
    local_path = os.path.join("data", "json", "islamicBooks", book_name)
    if os.path.exists(local_path):
        return local_path
    return None

def get_index_db_path(json_path):
    if not json_path:
        return None
    filename = os.path.basename(json_path)
    base_dir = os.path.join(os.getenv('appdata'), settings.app.appName, "islamicBooks", "indexes")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename + ".search.db")

def is_index_valid(json_path, db_path):
    if not json_path or not db_path or not os.path.exists(json_path) or not os.path.exists(db_path):
        return False
    try:
        stat = os.stat(json_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT value FROM metadata WHERE key = 'mtime'")
        r_mtime = cur.fetchone()
        cur.execute("SELECT value FROM metadata WHERE key = 'size'")
        r_size = cur.fetchone()
        conn.close()
        if r_mtime and r_size:
            if float(r_mtime[0]) == stat.st_mtime and int(r_size[0]) == stat.st_size:
                return True
    except Exception:
        pass
    return False

def build_index(json_path, db_path):
    if not json_path or not db_path or not os.path.exists(json_path):
        return False
    temp_db = db_path + ".tmp"
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
        except Exception:
            pass
    try:
        stat = os.stat(json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)

        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE VIRTUAL TABLE pages_fts USING fts5(part_name UNINDEXED, page_idx UNINDEXED, line_idx UNINDEXED, line_text UNINDEXED, norm_text)")

        rows = []
        for part_name, pages in book_data.items():
            for page_idx, page_content in enumerate(pages):
                lines = page_content.splitlines()
                for line_idx, line in enumerate(lines):
                    if not line.strip():
                        continue
                    norm = normalize(line, True, True, True)
                    rows.append((part_name, page_idx, line_idx, line, norm))

        conn.executemany("INSERT INTO pages_fts (part_name, page_idx, line_idx, line_text, norm_text) VALUES (?, ?, ?, ?, ?)", rows)
        conn.execute("INSERT INTO metadata VALUES ('mtime', ?)", (str(stat.st_mtime),))
        conn.execute("INSERT INTO metadata VALUES ('size', ?)", (str(stat.st_size),))
        conn.commit()
        conn.close()

        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
        os.replace(temp_db, db_path)
        return True
    except Exception:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except Exception:
                pass
        return False

def query_index(db_path, part_name, search_term, ignore_tashkeel=True, ignore_hamza=True, ignore_symbols=True, offset=0, limit=100):
    if not db_path or not os.path.exists(db_path):
        return {}, 0, 0
    norm_search = normalize(search_term, ignore_tashkeel, ignore_hamza, ignore_symbols)
    fts_query = prepare_fts5_query(norm_search)
    if not fts_query:
        return {}, 0, 0
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT page_idx) FROM pages_fts WHERE part_name = ? AND norm_text MATCH ?", (part_name, fts_query))
        total_count, total_book_pages = cur.fetchone()

        cur.execute("SELECT page_idx, line_idx, line_text FROM pages_fts WHERE part_name = ? AND norm_text MATCH ? LIMIT ? OFFSET ?",
                    (part_name, fts_query, limit, offset))
        rows = cur.fetchall()
        conn.close()

        results_by_page = {}
        for page_idx, line_idx, line_text in rows:
            page_idx = int(page_idx)
            line_idx = int(line_idx)
            if page_idx not in results_by_page:
                results_by_page[page_idx] = []
            results_by_page[page_idx].append((line_idx, line_text))

        return results_by_page, total_count, total_book_pages
    except Exception:
        return {}, 0, 0

