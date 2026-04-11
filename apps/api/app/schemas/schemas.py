"""Pydantic schemas for request/response validation."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


# ─── Auth ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    role: str

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=255)

class PublicLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    name: str


# ─── Source ──────────────────────────────────────────────────────────

class SourceCreate(BaseModel):
    name: str
    url: str
    category: str = "general"
    office: Optional[str] = None
    crawl_frequency_hours: int = 168
    authority_score: float = 1.0

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    office: Optional[str] = None
    is_active: Optional[bool] = None
    crawl_frequency_hours: Optional[int] = None
    authority_score: Optional[float] = None

class SourceOut(BaseModel):
    id: UUID
    name: str
    url: str
    category: str
    office: Optional[str]
    is_active: bool
    crawl_frequency_hours: int
    authority_score: float
    last_crawled_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Document ────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: UUID
    source_id: UUID
    title: str
    source_url: str
    content_type: str
    status: str
    audience: str
    academic_term: Optional[str]
    is_archived: bool
    version: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class DocumentDetail(DocumentOut):
    raw_content: Optional[str]
    cleaned_content: Optional[str]
    content_hash: Optional[str]
    chunk_count: int = 0


# ─── Chunk ───────────────────────────────────────────────────────────

class ChunkOut(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    heading: Optional[str]
    token_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Chat ────────────────────────────────────────────────────────────

class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None

class Citation(BaseModel):
    title: str
    url: str
    snippet: str
    office: Optional[str] = None
    category: Optional[str] = None

class OfficeRouting(BaseModel):
    name: str
    office_key: str
    phone: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    reason: str = ""

class ChatQueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    office_routing: Optional[OfficeRouting] = None
    follow_up_questions: list[str] = []
    confidence_score: float = 0.0
    session_id: str
    warning: Optional[str] = None


# ─── FAQ ─────────────────────────────────────────────────────────────

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str = "general"
    office_key: Optional[str] = None
    priority: int = 0

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    office_key: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class FAQOut(BaseModel):
    id: UUID
    question: str
    answer: str
    category: str
    office_key: Optional[str]
    is_active: bool
    priority: int
    hit_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Feedback ────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    message_id: Optional[UUID] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    feedback_type: str = "general"

class FeedbackOut(BaseModel):
    id: UUID
    message_id: Optional[UUID]
    rating: Optional[int]
    comment: Optional[str]
    feedback_type: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Jobs ────────────────────────────────────────────────────────────

class CrawlJobOut(BaseModel):
    id: UUID
    source_id: Optional[UUID]
    status: str
    pages_found: int
    pages_ingested: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}

class IndexJobOut(BaseModel):
    id: UUID
    status: str
    documents_processed: int
    chunks_created: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Conversations / Messages ────────────────────────────────────────

class ChatMessageOut(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict]
    confidence_score: Optional[float]
    office_routing: Optional[dict]
    created_at: datetime
    model_config = {"from_attributes": True}

class ChatSessionOut(BaseModel):
    id: UUID
    session_token: str
    started_at: datetime
    last_active_at: datetime
    message_count: int = 0
    model_config = {"from_attributes": True}


# ─── Dashboard ───────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_sources: int
    active_sources: int
    total_documents: int
    indexed_documents: int
    total_chunks: int
    total_sessions: int
    total_messages: int
    total_feedback: int
    avg_confidence: Optional[float]
    recent_crawl_jobs: list[CrawlJobOut]
    recent_index_jobs: list[IndexJobOut]


# ─── Evaluation ──────────────────────────────────────────────────────

class EvaluationRunOut(BaseModel):
    id: UUID
    name: str
    status: str
    total_cases: int
    passed_cases: int
    avg_retrieval_score: Optional[float]
    avg_answer_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    model_config = {"from_attributes": True}

class EvaluationCaseOut(BaseModel):
    id: UUID
    run_id: UUID
    question: str
    expected_answer: Optional[str]
    actual_answer: Optional[str]
    retrieval_score: Optional[float]
    answer_score: Optional[float]
    passed: Optional[bool]
    notes: Optional[str]
    model_config = {"from_attributes": True}


# ─── Office Contact ─────────────────────────────────────────────────

class OfficeContactOut(BaseModel):
    id: UUID
    name: str
    office_key: str
    description: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    url: Optional[str]
    location: Optional[str]
    hours: Optional[str]
    category: str
    model_config = {"from_attributes": True}


# ─── Search / Topics ────────────────────────────────────────────────

class TopicOut(BaseModel):
    key: str
    name: str
    description: str
    icon: Optional[str] = None

class SearchResult(BaseModel):
    documents: list[DocumentOut]
    total: int

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
