"""
AI Agent Coordination & Decision Engine — Backend Entrypoint
===============================================================
Run locally with:
    uvicorn app.main:app --reload --port 8000

Interactive API docs available at:
    http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

# Import models so SQLAlchemy's metadata knows about every table before create_all()
from app.models import dev_collab  # noqa: F401
from app.models import incident  # noqa: F401
from app.models import memory  # noqa: F401

from app.routers import dev_collab_routes, incident_routes, system_routes, websocket_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} ({settings.ENV})")
    await init_db()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-agent system coordinating Dev-Collaboration conflict "
                "prevention and AIOps incident response under one Decision Engine.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Accept any localhost/127.0.0.1 port in development — Vite may auto-pick
    # a different port (5173, 5174, ...) if the default is already in use.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dev_collab_routes.router)
app.include_router(incident_routes.router)
app.include_router(system_routes.router)
app.include_router(websocket_routes.router)


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running.",
        "docs": "/docs",
        "modules": ["dev-collaboration", "aiops-incident-response"],
    }
