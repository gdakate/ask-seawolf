"""Tests for core backend logic."""
import pytest
from app.core.auth import hash_password, verify_password, create_access_token, decode_token
from app.services.ingestion import clean_html, chunk_by_headings, compute_hash
from app.services.answering import build_prompt, should_warn_term_dependent
from app.services.retrieval import build_citations, generate_follow_ups
from app.schemas.schemas import Citation


# ─── Auth Tests ──────────────────────────────────────────────────────

def test_password_hashing():
    hashed = hash_password("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_token():
    token = create_access_token({"sub": "admin@test.com", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "admin@test.com"
    assert payload["role"] == "admin"


# ─── Ingestion Tests ────────────────────────────────────────────────

def test_clean_html():
    html = """
    <html><head><title>Test</title><style>body{}</style></head>
    <body><nav>Nav</nav><main><h1>Hello</h1><p>World</p></main>
    <footer>Footer</footer></body></html>
    """
    cleaned = clean_html(html)
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert "Nav" not in cleaned
    assert "Footer" not in cleaned
    assert "<h1>" not in cleaned


def test_compute_hash():
    h1 = compute_hash("test content")
    h2 = compute_hash("test content")
    h3 = compute_hash("different content")
    assert h1 == h2
    assert h1 != h3


def test_chunk_by_headings():
    text = """# Introduction
This is the introduction paragraph with enough content to be meaningful.

# Admissions Requirements
You need to submit your application by January 15.
Include transcripts and test scores.

# Financial Aid
Complete the FAFSA form.
"""
    chunks = chunk_by_headings(text, max_chunk_size=500)
    assert len(chunks) >= 2
    assert all("content" in c and "chunk_index" in c for c in chunks)


def test_chunk_by_headings_long_text():
    text = "Long paragraph. " * 200
    chunks = chunk_by_headings(text, max_chunk_size=200)
    assert len(chunks) > 1


# ─── Retrieval Tests ────────────────────────────────────────────────

def test_build_citations():
    chunks = [
        {"title": "Page 1", "source_url": "https://example.com/1", "content": "Short", "office": "admissions", "category": "admissions"},
        {"title": "Page 2", "source_url": "https://example.com/2", "content": "A" * 300, "office": None, "category": "general"},
        {"title": "Page 1 Dup", "source_url": "https://example.com/1", "content": "Duplicate", "office": "admissions", "category": "admissions"},
    ]
    citations = build_citations(chunks)
    assert len(citations) == 2  # Deduped by URL
    assert citations[0].title == "Page 1"
    assert citations[1].snippet.endswith("...")  # Truncated


def test_generate_follow_ups():
    chunks = [{"category": "admissions"}, {"category": "financial_aid"}]
    follow_ups = generate_follow_ups("test", chunks)
    assert len(follow_ups) <= 3
    assert all(isinstance(q, str) for q in follow_ups)


def test_generate_follow_ups_empty():
    follow_ups = generate_follow_ups("test", [])
    assert len(follow_ups) == 3  # Default questions


# ─── Answering Tests ────────────────────────────────────────────────

def test_build_prompt():
    chunks = [
        {"title": "Test Doc", "content": "Some content here", "office": "admissions"},
        {"title": "Test Doc 2", "content": "More content", "office": None},
    ]
    prompt = build_prompt("What is tuition?", chunks)
    assert "What is tuition?" in prompt
    assert "Some content here" in prompt
    assert "[Source 1: Test Doc]" in prompt


def test_should_warn_term_dependent():
    chunks = [{"category": "bursar"}]
    assert should_warn_term_dependent(chunks, "What is the tuition?") is not None
    assert should_warn_term_dependent(chunks, "Where is the admissions office?") is None


# ─── Schema Tests ────────────────────────────────────────────────────

def test_citation_model():
    c = Citation(title="Test", url="https://test.com", snippet="Hello", office="admissions")
    assert c.title == "Test"
    data = c.model_dump()
    assert "title" in data
