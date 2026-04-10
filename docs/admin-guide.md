# Admin Guide

## Accessing the Admin Dashboard

Navigate to `http://localhost:3001` (local) or your deployed admin URL. Sign in with your admin credentials.

Default credentials: `admin@stonybrook.edu` / `admin123`

## Dashboard

The dashboard provides an overview of platform health:
- Total and active sources
- Document and chunk counts
- Chat session and message counts
- Average confidence score across responses
- Recent crawl and index job status

## Managing Sources

Sources are the URLs that the platform crawls for content.

### Adding a Source
1. Click "Add Source"
2. Enter name, URL, category, and optional office key
3. Set authority score (higher = preferred in retrieval)
4. Click "Add Source"

### Categories
- admissions, registrar, bursar, financial_aid, housing, dining, academics, student_affairs, it_services, general

### Toggling Sources
Click the Active/Inactive badge on any source to enable or disable it. Inactive sources are excluded from retrieval.

## Documents

View all ingested documents with their status:
- **pending**: Awaiting ingestion
- **ingested**: Content extracted, awaiting indexing
- **indexed**: Fully processed with vector embeddings
- **failed**: Processing error occurred
- **archived**: Marked as outdated

## Chunks

Browse individual text chunks that make up the vector index. Each chunk shows heading, content preview, token count, and document association.

## Running Jobs

### Crawl
Triggers content fetching from registered sources. Click "Run Crawl" from the dashboard.

### Reindex
Processes all ingested-but-unindexed documents: chunks them, generates embeddings, and stores vectors. Click "Reindex" from the dashboard.

## FAQ Overrides

Curated FAQ entries take priority over RAG retrieval for matching questions. Use these for commonly asked questions where you want a guaranteed, reviewed answer.

### Adding an FAQ
1. Click "Add FAQ"
2. Enter the question and answer
3. Set category, office key, and priority
4. Higher priority FAQs are matched first

## Conversations

Review all chat sessions and their messages. Click a session to see the full conversation thread with confidence scores and citations.

## Feedback

View user ratings and comments on chat responses. Use this to identify answers that need improvement.

## Evaluations

Run quality evaluations to measure retrieval and answer accuracy. Results show pass/fail rates, average scores, and individual case details.
