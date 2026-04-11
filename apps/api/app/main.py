"""Ask Seawolves - FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import get_settings
from app.routers.public import router as public_router
from app.routers.admin import router as admin_router
from app.routers.alumni import router as alumni_router

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Ask Seawolves API", environment=settings.environment)
    # Pre-warm the embedding model so the first user query is fast
    try:
        from app.services.ai_providers import get_embedding_provider
        provider = get_embedding_provider()
        await provider.embed_query("warm up")
        logger.info("Embedding model pre-warmed")
    except Exception as e:
        logger.warning("Embedding pre-warm failed", error=str(e))
    yield
    logger.info("Shutting down Ask Seawolves API")


app = FastAPI(
    title="Ask Seawolves API",
    description="RAG-powered Q&A platform for Stony Brook University public information",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(public_router, prefix="/api", tags=["Public"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(alumni_router, prefix="/api", tags=["Alumni"])


@app.get("/")
async def root():
    return {"name": "Ask Seawolves API", "version": "1.0.0", "docs": "/docs"}
