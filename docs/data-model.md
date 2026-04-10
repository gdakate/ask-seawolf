# Data Model

## Entity Relationship Overview

```
Source ──< Document ──< Chunk (with vector embedding)
OfficeContact
FAQEntry
ChatSession ──< ChatMessage ──< UserFeedback
CrawlJob (linked to Source)
IndexJob
EvaluationRun ──< EvaluationCase
AdminUser
AuditLog
```

## Core Entities

### Source
Content origin URLs that the platform crawls and ingests.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Display name |
| url | Text | Source URL (unique) |
| category | Enum | admissions, registrar, bursar, etc. |
| office | String | Associated office key |
| is_active | Boolean | Whether to include in crawls |
| crawl_frequency_hours | Integer | How often to re-crawl |
| authority_score | Float | Weight in retrieval ranking |

### Document
Individual pages/files ingested from sources.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| source_id | FK→Source | Parent source |
| title | String | Page/document title |
| source_url | Text | Original URL |
| content_type | Enum | html, pdf, markdown, text |
| raw_content | Text | Original content |
| cleaned_content | Text | Processed content |
| content_hash | String | SHA-256 for version detection |
| status | Enum | pending, ingested, indexed, failed, archived |
| audience | Enum | undergraduate, graduate, prospective, all |
| is_archived | Boolean | Whether content is outdated |

### Chunk
Vector-indexed segments of documents.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| document_id | FK→Document | Parent document |
| chunk_index | Integer | Order within document |
| content | Text | Chunk text |
| heading | String | Section heading if available |
| token_count | Integer | Word count |
| embedding | Vector(384) | pgvector embedding |

### OfficeContact
University office directory entries used for routing.

### FAQEntry
Curated question-answer pairs that override RAG retrieval for exact matches.

### ChatSession / ChatMessage
Conversation tracking with full message history, citations, confidence scores, and office routing data.

### UserFeedback
User ratings and comments on chat responses.

### CrawlJob / IndexJob
Job tracking for background ingestion and indexing operations.

### EvaluationRun / EvaluationCase
Quality evaluation framework for measuring retrieval and answer accuracy.

### AdminUser
Admin dashboard users with hashed passwords and role-based access.

### AuditLog
Tracks all admin actions for accountability.
