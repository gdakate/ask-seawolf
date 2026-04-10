"""Seawolf Ask - FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import get_settings
from app.routers.public import router as public_router
from app.routers.admin import router as admin_router

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Seawolf Ask API", environment=settings.environment)
    yield
    logger.info("Shutting down Seawolf Ask API")


app = FastAPI(
    title="Seawolf Ask API",
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


@app.get("/")
async def root():
    return {"name": "Seawolf Ask API", "version": "1.0.0", "docs": "/docs"}
