from fastapi import APIRouter

# Aggregator router for /cases - includes per-route routers
from app.api.routes.cases_get_user_cases import router as get_user_cases_router
from app.api.routes.cases_create_draft import router as create_draft_router
from app.api.routes.cases_extract_charges import router as extract_charges_router
from app.api.routes.cases_add_manual_charge import router as add_manual_charge_router
from app.api.routes.cases_finalize_charges import router as finalize_charges_router
from app.api.routes.cases_fetch_precedents import router as fetch_precedents_router
from app.api.routes.cases_get_precedents import router as get_precedents_router
from app.api.routes.cases_delete import router as delete_router
from app.api.routes.cases_get_details import router as get_details_router
from app.api.routes.delete_legal_section import router as delete_legal_section_router
from app.api.routes.cases_regenerate_summary import router as regenerate_summary_router
router = APIRouter(prefix="/cases", tags=["Legal Cases"])

# include child routers (they define their own handlers)
router.include_router(get_user_cases_router)
router.include_router(create_draft_router)
router.include_router(extract_charges_router)
router.include_router(add_manual_charge_router)
router.include_router(finalize_charges_router)
router.include_router(fetch_precedents_router)
router.include_router(get_precedents_router)
router.include_router(delete_router)
router.include_router(get_details_router)
router.include_router(delete_legal_section_router)
router.include_router(regenerate_summary_router)