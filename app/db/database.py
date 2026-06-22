import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# This forces SQLModel to read your tables before building the database
import app.models

# Load local environment variables for fallback
load_dotenv()

def get_aws_secret():
    """Fetches the database credentials securely from AWS Secrets Manager."""
    secret_name = "legalai/prod/db"  # Dhyan rakhna AWS mein yahi naam banana hai
    region_name = "eu-north-1"       # Tumhara AWS region

    # AWS Secrets Manager client banao
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(f"⚠️ AWS Secrets Manager Fetch Failed: {e}")
        return None

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# 1. Try to get DB URL from AWS Secrets Manager FIRST
db_url = None
aws_secrets = get_aws_secret()

if aws_secrets and "DATABASE_URL" in aws_secrets:
    db_url = aws_secrets["DATABASE_URL"]
    print("✅ Successfully loaded Database URL from AWS Secrets Manager!")

# 2. Safety fallback: If AWS fails or running locally, use .env or settings
if not db_url:
    print("⚠️ Falling back to local .env / settings for DATABASE_URL.")
    db_url = os.getenv("DATABASE_URL")

if not db_url:
    db_url = str(settings.DATABASE_URL)

# 3. FORCE THE ASYNC DRIVER MANUALLY TO BYPASS MACHINE MEMORY GLITCHES
if db_url and db_url.startswith("postgresql://"):
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