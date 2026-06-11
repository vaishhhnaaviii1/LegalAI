import os
from dotenv import load_dotenv
# FORCE LOAD THE ENVIRONMENT VARIABLES BEFORE ANYTHING ELSE
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import legal
from app.api.routes import cases, auth
from app.db.database import init_db
import contextlib
import logging
from app.core.logging_config import setup_logging
from app.middleware.logging import APILoggingMiddleware

setup_logging()

# This turns on Python’s internal messaging system. Instead of using print(), professional apps use logger.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Its main job is to ensure that your database tables are actually created before the server starts accepting any traffic from users.
# 2. Define the lifespan manager outside the factory
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏳ Initializing PostgreSQL Database...")
    await init_db()
    logger.info("✅ Database tables created successfully!") ######these were uncommented
    yield
    logger.info("🛑 Server shutting down...")
# This code guarantees that PostgreSQL is fully connected and 
# your tables are built the split-second before your API goes live to the internet.

def create_app() -> FastAPI:
    app = FastAPI(
        title="Legal AI API",
        version="v1.0.0",
        description="Production-grade API for extracting IPC and BNS sections from legal case facts.",
        lifespan=lifespan  # <-- Attach the lifespan manager to the app
    )

    # Standard security middleware for frontend communication

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173", 
            "http://127.0.0.1:5173", 
            "http://localhost:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(APILoggingMiddleware)
    
    # Register the legal routing module
    app.include_router(legal.router, prefix="/api/v1")
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1/auth")

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "operational", "service": "Legal AI API"}

    return app

app = create_app()