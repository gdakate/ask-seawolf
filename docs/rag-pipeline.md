# RAG Pipeline

## Overview

The Retrieval-Augmented Generation (RAG) pipeline is the core knowledge mechanism. All answers are grounded in retrieved context from official Stony Brook University sources.

## Pipeline Stages

### 1. Ingestion
- **Source Registry**: Admin adds URLs to crawl
- **HTML Cleaning**: BeautifulSoup strips scripts, nav, footer, style tags
- **Content Hashing**: SHA-256 hash for version/duplicate detection
- **Document Storage**: Raw and cleaned content stored in PostgreSQL

### 2. Chunking
- **Heading-Aware Splitting**: Respects heading boundaries (H1-H4, ALL-CAPS headings)
- **Max Chunk Size**: 800 characters default with 100-character overlap
- **Metadata Preservation**: Each chunk retains heading context and position index

### 3. Embedding
- **Provider Abstraction**: Supports Mock, OpenAI (text-embedding-3-small), and Bedrock (Titan)
- **Dimensions**: 384-dimensional vectors (configurable)
- **Mock Mode**: Deterministic MD5-seeded random vectors for local development

### 4. Indexing
- **pgvector Storage**: Embeddings stored alongside chunk content
- **IVFFlat Index**: Approximate nearest neighbor index with 10 lists
- **Status Tracking**: Document status transitions: pending → ingested → indexed

### 5. Retrieval
- **Vector Search**: Cosine similarity via pgvector (`<=>` operator)
- **Keyword Fallback**: ILIKE-based search when vector search returns no results
- **Filters**: Active sources only, non-archived documents, indexed status
- **Top-K**: Default 5 chunks retrieved per query
- **FAQ Fast Path**: Exact FAQ matches bypass vector search entirely

### 6. Citation Bundling
- Deduplication by source URL
- Snippet generation (200-char truncation)
- Office and category metadata attached to each citation

### 7. Answer Generation
- **System Prompt**: Enforces grounding rules (answer only from context, no fabrication)
- **Context Injection**: Retrieved chunks formatted with source attribution
- **Confidence Scoring**: Based on average vector distance of retrieved chunks
- **Term Warnings**: Detects tuition/deadline/fee questions and adds variability warnings

### 8. Office Routing
- Analyzes retrieved chunks for office associations
- Finds most common office in results
- Returns contact info (phone, email, URL) from office directory

## Prompt Template

```
Context from official Stony Brook University sources:

[Source 1: Document Title] (Office: office_name)
<chunk content>

---

Question: <user question>

Provide a clear, helpful answer based solely on the context above.
```

## Retrieval Abstraction

The retrieval layer is designed with an abstraction that allows future migration from pgvector to OpenSearch:
- Vector search interface defined in `retrieval.py`
- Document/chunk queries use SQLAlchemy (can be swapped for OpenSearch client)
- Embedding generation is provider-agnostic

## Evaluation

The evaluation framework supports:
- Benchmark datasets (question + expected answer pairs)
- Retrieval scoring (were relevant chunks found?)
- Answer scoring (does the answer match expected content?)
- Admin UI for reviewing evaluation results
