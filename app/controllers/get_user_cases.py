import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import user_not_found_exc, server_error_exc


async def get_user_cases_controller(
    user_id: UUID, search: str | None, skip: int, limit: int, db: AsyncSession
):
    try:
        # LOGIC STEP 1: Verify the user actually exists
        user = await crud.user.get(
            db, id=user_id
        )  # TODO: will be authorised by the authentication Decorator
        if not user:
            raise user_not_found_exc()

        # LOGIC STEP 2: Fetch the paginated cases
        cases = await crud.legal_case.get_multi_by_user(
            db=db, user_id=user_id, skip=skip, limit=limit, search=search
        )
        return cases
    except Exception as e:
        print("🚨 FETCH ERROR 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
