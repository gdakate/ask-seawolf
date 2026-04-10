"""
CampusIQ - Chunker
Splits documents_v5_pruned.json into fixed-size overlapping chunks.
Output: documents_chunked.json

Each chunk:
  chunk_id    : "{category}__{url_slug}__{index}"
  url         : source URL
  title       : page title
  category    : category label
  chunk_index : 0-based index within the document
  total_chunks: total chunks for this document
  text        : chunk text
"""

import json
import re
import sys
import hashlib
from collections import Counter

CHUNK_SIZE  = 400   # target words per chunk
OVERLAP     = 50    # words to carry over from previous chunk
MIN_CHUNK   = 80    # discard trailing chunks shorter than this (words)


def split_sentences(text: str) -> list[str]:
    """Rough sentence splitter — splits on '. ', '! ', '? ', '\n'."""
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks of ~CHUNK_SIZE words."""
    sentences = split_sentences(text)
    chunks = []
    current_words = []
    current_len = 0

    for sent in sentences:
        sent_words = sent.split()
        if current_len + len(sent_words) > CHUNK_SIZE and current_words:
            chunks.append(" ".join(current_words))
            # carry over last OVERLAP words
            current_words = current_words[-OVERLAP:]
            current_len = len(current_words)
        current_words.extend(sent_words)
        current_len += len(sent_words)

    if current_words:
        chunks.append(" ".join(current_words))

    # Drop trailing micro-chunks
    chunks = [c for c in chunks if len(c.split()) >= MIN_CHUNK]
    return chunks if chunks else [text]  # fallback: keep whole text


def url_slug(url: str) -> str:
    """Short stable slug from URL."""
    return hashlib.md5(url.encode()).hexdigest()[:8]


def build_chunks(input_path: str, output_path: str):
    with open(input_path, encoding="utf-8") as f:
        docs = json.load(f)

    all_chunks = []
    cat_counts = Counter()

    for doc in docs:
        text     = doc.get("clean_text", "").strip()
        url      = doc.get("url", "")
        title    = doc.get("title", "")
        category = doc.get("category", "")

        if not text:
            continue

        parts = chunk_text(text)
        total = len(parts)

        for idx, chunk_text_part in enumerate(parts):
            chunk_id = f"{category}__{url_slug(url)}__{idx:03d}"
            all_chunks.append({
                "chunk_id"    : chunk_id,
                "url"         : url,
                "title"       : title,
                "category"    : category,
                "chunk_index" : idx,
                "total_chunks": total,
                "text"        : chunk_text_part,
            })
            cat_counts[category] += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Chunked → {output_path}")
    print(f"   docs   : {len(docs)}")
    print(f"   chunks : {len(all_chunks)}")
    print(f"   avg chunks/doc: {len(all_chunks)/max(len(docs),1):.1f}")
    print()
    print("── Chunks per category ──")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat:25s}: {cnt:5d}")


if __name__ == "__main__":
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "documents_v5_pruned.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "documents_chunked.json"
    build_chunks(input_file, output_file)
