---
language:
- ar
- en
license: mit
task_categories:
- question-answering
- text-generation
- text-retrieval
- fill-mask
pretty_name: Athar Islamic QA Datasets
tags:
- islamic-studies
- quran
- hadith
- fiqh
- arabic
- rag
- multi-agent
- citation-grounded
dataset_info:
  features:
  - name: content
    dtype: string
  - name: content_type
    dtype: string
  - name: book_id
    dtype: int64
  - name: book_title
    dtype: string
  - name: category
    dtype: string
  - name: author
    dtype: string
  - name: author_death
    dtype: int64
  - name: collection
    dtype: string
  - name: page_number
    dtype: int64
  - name: section_title
    dtype: string
  - name: hierarchy
    sequence: string
  - name: title
    dtype: string
  - name: chapter
    dtype: string
  - name: section
    dtype: string
  - name: page
    dtype: int64
  splits:
  - name: train
    num_examples: 18701966
  download_size: 40000000000
  dataset_size: 40000000000
---

# 🕌 Athar Islamic QA Datasets

> **18.7M passages from classical Islamic books spanning 1,400 years of scholarship**

A comprehensive collection of Islamic texts covering Quran, Hadith, Fiqh, Tafsir, Aqeedah, Seerah, and more — sourced from the Shamela library and enriched with scholarly metadata for RAG-based Islamic QA systems.

**Based on the Fanar-Sadiq Architecture** for grounded, citation-backed Islamic question answering.

---

## 📊 Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Passages** | 18,701,966 |
| **Total Size** | ~40 GB |
| **Collections** | 10 |
| **Source** | ElShamela Library (المكتبة الشاملة) |
| **Languages** | Arabic (primary), English (metadata) |
| **Time Span** | 0-1400 AH (7th-21st century CE) |

---

## 📚 Collections

| # | Collection | Passages | Size | Description |
|---|------------|----------|------|-------------|
| 1 | `hadith_passages` | 5,059,547 | 11 GB | Prophetic traditions (Sahih Bukhari, Muslim, etc.) |
| 2 | `general_islamic` | 3,410,436 | 6.1 GB | General Islamic knowledge, spirituality, ethics |
| 3 | `fiqh_passages` | 2,397,988 | 6.6 GB | Islamic jurisprudence (Hanafi, Maliki, Shafi'i, Hanbali) |
| 4 | `islamic_history_passages` | 2,850,288 | 5.6 GB | Islamic history (Prophetic to Ottoman era) |
| 5 | `quran_tafsir` | 2,128,606 | 4.9 GB | Quranic exegesis (Tabari, Qurtubi, Ibn Kathir, etc.) |
| 6 | `arabic_language_passages` | 1,015,311 | 2.2 GB | Arabic grammar, linguistics, rhetoric |
| 7 | `aqeedah_passages` | 738,003 | 1.7 GB | Islamic creed and theology |
| 8 | `spirituality_passages` | 438,776 | 1.1 GB | Sufism, tasawwuf, purification of the heart |
| 9 | `usul_fiqh` | 368,388 | 874 MB | Principles of Islamic jurisprudence |
| 10 | `seerah_passages` | 294,623 | 755 MB | Prophet Muhammad's biography |

---

## 📋 Schema

Each passage contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Main passage text (Arabic) |
| `content_type` | string | Type of content |
| `book_id` | int64 | Unique book identifier |
| `book_title` | string | Title of the source book |
| `category` | string | Category (e.g., "العقيدة", "الفقه") |
| `author` | string | Author name |
| `author_death` | int64 | Author's death year (Hijri) |
| `collection` | string | Collection name |
| `page_number` | int64 | Page number in source |
| `section_title` | string | Section heading |
| `hierarchy` | list | Hierarchical path [book, chapter, section] |
| `title` | string | Passage title |
| `chapter` | string | Chapter name |
| `section` | string | Section name |
| `page` | int64 | Page number |

### Example Entry

```json
{
  "content": "الحمد لله نحمده ونستعينه ونستغفره، ونعوذ بالله من شرور أنفسنا...",
  "book_id": 1234,
  "book_title": "الفوائد العذاب في الرد على من لم يحكم السنة والكتاب",
  "category": "العقيدة",
  "author": "حمد بن ناصر آل معمر",
  "author_death": 1225,
  "collection": "aqeedah_passages",
  "page_number": 1,
  "section_title": "مقدمة المحقق",
  "hierarchy": ["الفوائد العذاب", "مقدمة المحقق"],
  "title": "مقدمة المحقق",
  "chapter": null,
  "section": null,
  "page": 1
}
```

---

## 📊 Collection Breakdown

### Passages Distribution

```
hadith_passages              ████████████████████████████████  5,059,547 (27%)
general_islamic              ████████████████████             3,410,436 (18%)
fiqh_passages                ██████████████                    2,397,988 (13%)
islamic_history_passages     ██████████████                    2,850,288 (15%)
quran_tafsir                 ████████████                      2,128,606 (11%)
arabic_language_passages     ██████                            1,015,311 (5%)
aqeedah_passages             ████                               738,003 (4%)
spirituality_passages        ██                                 438,776 (2%)
usul_fiqh                    █                                  368,388 (2%)
seerah_passages              █                                  294,623 (2%)
```

---

## 🔧 How to Load

### Using HuggingFace Datasets

```python
from datasets import load_dataset

# Load full dataset
ds = load_dataset("Kandil7/Athar-Datasets")

# Access specific collection
for row in ds['train']:
    if row['collection'] == 'fiqh_passages':
        print(row['content'][:200])
        break

# Filter by collection
hadith_ds = ds['train'].filter(lambda x: x['collection'] == 'hadith_passages')
```

### Streaming Mode (Memory Efficient)

```python
from datasets import load_dataset

# Stream without downloading
ds = load_dataset("Kandil7/Athar-Datasets", split="train", streaming=True)

for i, passage in enumerate(ds):
    if i >= 5:
        break
    print(f"{passage['collection']}: {passage['title']}")
```

### Direct JSONL Access

```python
import json

# Load specific collection
with open('hadith_passages.jsonl', 'r', encoding='utf-8') as f:
    passages = [json.loads(line) for line in f]

print(f"Loaded {len(passages):,} hadith passages")
```

---

## 💡 Usage Examples

### Example 1: Semantic Search with RAG

```python
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# Load embedding model
model = SentenceTransformer('BAAI/bge-m3')

# Load a sample collection
with open('fiqh_passages.jsonl', 'r', encoding='utf-8') as f:
    passages = [json.loads(line) for line in f][:1000]

# Create embeddings
texts = [p['content'] for p in passages]
embeddings = model.encode(texts)

# Search
query = "ما حكم صلاة الجماعة؟"
query_embedding = model.encode([query])[0]

# Find most similar
scores = np.dot(embeddings, query_embedding)
top_idx = np.argsort(scores)[-5:][::-1]

for idx in top_idx:
    print(f"Score: {scores[idx]:.3f}")
    print(passages[idx]['content'][:200])
    print("---")
```

### Example 2: Filter by Era

```python
# Filter classical era scholars (200-500 AH)
classical_passages = [
    p for p in passages
    if 200 <= p.get('author_death', 0) <= 500
]

# Filter by author
imam_bukhari = [
    p for p in hadith_passages
    if 'Bukhari' in p.get('author', '')
]
```

### Example 3: Citation-Enhanced QA with Athar

```python
# Use the Athar system for grounded answers
# See: https://github.com/Kandil7/Athar

from Athar import FiqhAgent

agent = FiqhAgent()
result = await agent.execute(
    query="ما حكم صلاة الجماعة؟",
    filters={"era": "classical"}
)

# Result includes citations
for citation in result.citations:
    print(citation.source)
    print(citation.text)
```

---

## 📖 Source: ElShamela Library (المكتبة الشاملة)

This dataset is derived from **ElShamela Library** (المكتبة الشاملة) — the largest comprehensive digital library of Islamic texts.

### About ElShamela

**ElShamela** (المكتبة الشاملة) is a free, open-access digital library that has been digitizing and preserving classical Islamic texts for over two decades.

**Website:** https://shamela.ws/

### Processing Pipeline

1. **Extracted** books from ElShamela Library format
2. **Converted** from proprietary Shamela format to plain text
3. **Split** into pages and passages for granular retrieval
4. **Enriched** with metadata:
   - Author names and death years (Hijri)
   - Book titles and categories
   - Chapter and section headings
   - Page numbers
5. **Organized** into 10 scholarly collections

---

## 🏗️ Scholarly Eras

| Era | Range (AH) | Range (CE) | Description |
|-----|-----------|-----------|-------------|
| **Prophetic** | 0-100 | 622-718 | Companions of Prophet ﷺ |
| **Tabi'un** | 100-200 | 718-815 | Successors |
| **Classical** | 200-500 | 815-1106 | Golden age of Islamic scholarship |
| **Medieval** | 500-900 | 1106-1496 | Post-classical period |
| **Ottoman** | 900-1300 | 1496-1883 | Ottoman era |
| **Modern** | 1300+ | 1883+ | Modern period |

---

## 🤝 Related Projects

- **[Athar](https://github.com/Kandil7/Athar)** — Production-ready Islamic QA system using this dataset
- **[Fanar-Sadiq Architecture](docs/Fanar-Sadiq%20A%20Multi-Agent%20Architecture%20for%20Grounded%20Islamic%20QA.pdf)** — Research paper

---

## 📝 Citation

```bibtex
@misc{athar-datasets-2026,
  title={Athar Islamic QA Datasets},
  author={Kandil, Ahmed},
  year={2026},
  url={https://huggingface.co/datasets/Kandil7/Athar-Datasets},
  note={18.7M passages from 10 Islamic collections}
}
```

---

## ⚠️ Usage Notes

1. **Scholarly Context:** These texts represent classical Islamic scholarship. Always consult qualified scholars for religious rulings.

2. **Hadith Authenticity:** Hadith passages include chains of narration (esnad). Use authenticity grading to evaluate reliability.

3. **Fiqh Diversity:** The fiqh collection represents multiple schools of thought (Hanafi, Maliki, Shafi'i, Hanbali).

4. **Language:** Primary content is in Classical Arabic. Metadata includes English translations.

5. **Licensing:** MIT License — free for research and commercial use.

---

## 📁 File Structure

```
Athar-Datasets/
├── hadith_passages.jsonl              # 5,059,547 passages (11 GB)
├── general_islamic.jsonl              # 3,410,436 passages (6.1 GB)
├── fiqh_passages.jsonl                # 2,397,988 passages (6.6 GB)
├── islamic_history_passages.jsonl     # 2,850,288 passages (5.6 GB)
├── quran_tafsir.jsonl                 # 2,128,606 passages (4.9 GB)
├── arabic_language_passages.jsonl      # 1,015,311 passages (2.2 GB)
├── aqeedah_passages.jsonl             # 738,003 passages (1.7 GB)
├── spirituality_passages.jsonl         # 438,776 passages (1.1 GB)
├── usul_fiqh.jsonl                    # 368,388 passages (874 MB)
└── seerah_passages.jsonl              # 294,623 passages (755 MB)
```

---

## 📞 Contact & Support

- **GitHub:** https://github.com/Kandil7/Athar
- **HuggingFace:** https://huggingface.co/Kandil7

---

<div align="center">

**Built with ❤️ for the Muslim community**

🕌 Athar Islamic QA • 18.7M passages • 10 collections • 1,400 years of scholarship

</div>
