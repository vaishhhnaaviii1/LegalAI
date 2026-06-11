from fastapi import HTTPException, status

# Centralized error messages and helper functions
USER_NOT_FOUND = "User not found"
CASE_NOT_FOUND = "Case not found"
SERVER_ERROR_PREFIX = "Server Error"
INVALID_PAYLOAD = (
    "Invalid payload: At least one of 'approved_id' or 'rejected_data' "
    "must be present and contain items."
)


def user_not_found_exc() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)


def case_not_found_exc() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CASE_NOT_FOUND)


def server_error_exc(exc: Exception | str | None = None) -> HTTPException:
    msg = f"{SERVER_ERROR_PREFIX}: {str(exc)}" if exc else SERVER_ERROR_PREFIX
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)


def invalid_payload_message() -> str:
    return INVALID_PAYLOAD


def invalid_payload_exc(detail: str | None = None) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail or INVALID_PAYLOAD)
