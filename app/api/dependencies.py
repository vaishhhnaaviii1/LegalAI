from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.services.legal_service import LegalAnalysisService
from app.services.kanoon_service import KanoonService


@lru_cache()
def get_legal_service() -> LegalAnalysisService:
    """Dependency provider for the AI legal service."""
    return LegalAnalysisService()


@lru_cache()
def get_kanoon_service() -> KanoonService:
    """Dependency provider for the Kanoon API service."""
    return KanoonService()


# Expose the shared DB session dependency here for consistency in route imports.
get_db_session = get_session
