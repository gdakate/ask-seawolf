# Architecture

## Overview

The Stony Brook AI Assistant is a RAG (Retrieval-Augmented Generation) platform that answers questions about Stony Brook University using officially sourced content. The architecture follows a service-oriented design within a monorepo.

## System Components

### Frontend Layer
- **Public Web App** (Next.js): Student/visitor-facing chatbot, topic browsing, document search
- **Admin Dashboard** (Next.js): Content management, monitoring, evaluation

### API Layer
- **FastAPI Application**: Serves both public and admin REST APIs
- **Authentication**: JWT-based admin auth, ready for AWS Cognito integration
- **OpenAPI Documentation**: Auto-generated at `/docs`

### Service Layer
- **Ingestion Service**: Crawls sources, cleans HTML, extracts content, computes hashes for versioning
- **Indexing Service**: Chunks documents using heading-aware splitting, generates embeddings, stores in pgvector
- **Retrieval Service**: Hybrid vector + keyword search, citation bundling, office routing detection
- **Answering Service**: Prompt orchestration with RAG context, confidence scoring, term-dependency warnings

### Data Layer
- **PostgreSQL + pgvector**: Primary database with vector similarity search
- **Redis**: Job queue backend for Celery workers
- **S3/Local Storage**: Document and file storage abstraction

### AI Provider Abstraction
All AI operations (embeddings, text generation) go through an abstraction layer supporting:
- Mock provider (local development)
- OpenAI (GPT-4o + text-embedding-3-small)
- AWS Bedrock (Claude + Titan Embeddings)

## Data Flow

### Chat Query Flow
1. User submits question via web UI
2. API checks FAQ matches first (fast path)
3. Query is embedded using the configured provider
4. pgvector performs cosine similarity search
5. Top-k chunks are retrieved with metadata
6. Citations are bundled, office routing is detected
7. LLM generates grounded answer from retrieved context
8. Response includes answer, citations, follow-ups, confidence score

### Ingestion Flow
1. Admin adds source URL to registry
2. Crawler fetches page content
3. HTML is cleaned (scripts, nav, footer stripped)
4. Content is hashed for version detection
5. Document record is created/updated

### Indexing Flow
1. Admin triggers reindex job
2. Each ingested document is chunked by headings
3. Embeddings are generated for each chunk
4. Chunks with embeddings are stored in pgvector
5. Document status is updated to "indexed"

## Infrastructure

### Local Development
Docker Compose orchestrates all services:
- PostgreSQL with pgvector extension
- Redis
- API server with hot reload
- Web and Admin frontends with hot reload

### AWS Deployment
- ECS/Fargate for API and workers
- RDS PostgreSQL for database
- S3 for document storage
- ALB for API load balancing
- Amplify Hosting for frontends
- CloudWatch for logging
