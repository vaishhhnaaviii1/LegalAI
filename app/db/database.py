import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# This forces SQLModel to read your tables before building the database
import app.models

# This file is the bridge between your Python code and your PostgreSQL database. It sets up the connection, defines how to create tables, and provides a way to get a database session for your API routes.
# Create the async PostgreSQL engine
load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL") 

# # ---> ADD THIS EXACT LINE <---
# print(f"🚨 DEBUG DATABASE_URL: '{DATABASE_URL}' 🚨")
# engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# 1. Read the environment variable
db_url = os.getenv("DATABASE_URL")

# 2. Safety fallback: If it's missing from os.getenv, check settings
if not db_url:
    db_url = str(settings.DATABASE_URL)

# 3. FORCE THE ASYNC DRIVER MANUALLY TO BYPASS MACHINE MEMORY GLITCHES
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"🚨 FORCED ASYNC DATABASE_URL ROUTE: '{db_url}' 🚀")

# 4. Pass our newly fixed db_url string into the engine configuration
engine = create_async_engine(db_url, echo=True, future=True)


async def init_db():
    """
    Creates all the tables in PostgreSQL when the server starts.
    In a real massive production app, you would use Alembic for this,
    but this is perfect for building and testing.
    """
    async with engine.begin() as conn:
        # This reads db_models.py and generates the SQL CREATE TABLE commands
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency injection to get a database session for your routes."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
