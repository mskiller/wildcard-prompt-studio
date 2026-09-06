"""
Danbooru Lexicon SQLite Builder Script
Processes docs/danbooru_tags_cooccurrence.csv into an optimized SQLite B-tree database
at backend/app/data/danbooru_lexicon.db with sub-millisecond query indices.
"""

import os
import sys
import sqlite3
import csv
import time

def classify_danbooru_tag(tag: str) -> str:
    t = tag.lower().strip()
    if t.startswith('by ') or t.endswith('_(artist)') or 'artist' in t:
        return 'artist'
    if any(k in t for k in [
        '1girl', '1boy', '2girls', '2boys', '6+girls', 'multiple_girls', 'solo',
        'female', 'male', 'hair', 'eyes', 'skin', 'breasts', 'horns', 'wings',
        'tail', 'ears', 'girl', 'boy', 'woman', 'man', 'smile', 'blush', 'dress',
        'hat', 'uniform', 'gloves', 'boots', 'skirt', 'jacket', 'shirt', 'pants',
        'swimsuit', 'bikini'
    ]):
        return 'character'
    if any(k in t for k in [
        'genshin', 'touhou', 'fate', 'kantai', 'vocaloid', 'arknights', 'azur_lane',
        'idolmaster', 'hololive', 'pokemon', 'blue_archive', 'granblue', 'dragon_ball',
        'naruto', 'one_piece', 'eva', 'honkai'
    ]):
        return 'copyright'
    if any(k in t for k in [
        'masterpiece', 'best_quality', 'highres', 'absurdres', 'bad_anatomy',
        'watermark', 'signature', 'username', 'score_', 'monochrome', 'greyscale',
        'comic', 'parody'
    ]):
        return 'meta'
    return 'general'


def build_danbooru_db(csv_path: str = None, output_db_path: str = None):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if not csv_path:
        candidates = [
            os.path.join(project_root, "docs", "danbooru_tags_cooccurrence.csv"),
            os.path.join("/docs", "danbooru_tags_cooccurrence.csv"),
            "docs/danbooru_tags_cooccurrence.csv"
        ]
        for c in candidates:
            if os.path.exists(c):
                csv_path = os.path.abspath(c)
                break

    if not csv_path or not os.path.exists(csv_path):
        print(f"[Error] Danbooru co-occurrence CSV not found at: {csv_path}")
        return False

    if not output_db_path:
        output_db_path = os.path.join(project_root, "backend", "app", "data", "danbooru_lexicon.db")

    os.makedirs(os.path.dirname(output_db_path), exist_ok=True)
    temp_db_path = output_db_path + ".tmp"
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)

    print(f"[*] Reading co-occurrence CSV from: {csv_path}")
    print(f"[*] Writing Danbooru SQLite database to: {output_db_path}")

    t0 = time.time()
    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA synchronous = OFF")
    cur.execute("PRAGMA journal_mode = MEMORY")

    cur.execute("""
        CREATE TABLE cooccurrences (
            tag_a TEXT NOT NULL,
            tag_b TEXT NOT NULL,
            count REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE danbooru_tags (
            tag TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            total_count REAL NOT NULL
        )
    """)

    rows = []
    unique_tags = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            if len(line) < 2:
                continue
            tag_a = line[0].strip()
            tag_b = line[1].strip()
            if not tag_a or not tag_b:
                continue
            cnt = float(line[2]) if len(line) >= 3 and line[2].replace('.', '', 1).isdigit() else 1.0
            rows.append((tag_a, tag_b, cnt))
            unique_tags[tag_a] = unique_tags.get(tag_a, 0.0) + cnt
            unique_tags[tag_b] = unique_tags.get(tag_b, 0.0) + cnt

    print(f"[+] Parsed {len(rows):,} pairs and {len(unique_tags):,} unique tags in {time.time() - t0:.2f}s")

    t1 = time.time()
    cur.executemany("INSERT INTO cooccurrences VALUES (?, ?, ?)", rows)
    cur.execute("CREATE INDEX idx_cooc_tag_a ON cooccurrences(tag_a, count DESC)")

    tag_rows = [
        (tag, classify_danbooru_tag(tag), count)
        for tag, count in unique_tags.items()
    ]
    cur.executemany("INSERT INTO danbooru_tags VALUES (?, ?, ?)", tag_rows)
    cur.execute("CREATE INDEX idx_dt_category ON danbooru_tags(category)")
    cur.execute("CREATE INDEX idx_dt_count ON danbooru_tags(total_count DESC)")

    conn.commit()
    conn.close()

    if os.path.exists(output_db_path):
        os.remove(output_db_path)
    os.rename(temp_db_path, output_db_path)

    size_mb = os.path.getsize(output_db_path) / (1024 * 1024)
    print(f"[+] Successfully built Danbooru SQLite DB ({size_mb:.2f} MB) in {time.time() - t1:.2f}s")
    return True


if __name__ == "__main__":
    build_danbooru_db()
