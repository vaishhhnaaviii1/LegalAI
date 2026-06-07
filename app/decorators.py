# app/utils/decorators.py
import httpx
from groq import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# The universal retry policy for all 3rd-party external API calls
with_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    # Attempt 1 fails. It waits 2 seconds (the min), then tries again.

    #  Attempt 2 fails. It waits 4 seconds, then tries again.

    #  Attempt 3 fails. It stops. (The max=8 ensures that if you ever increase the retry limit, it never waits longer than 8 seconds per pause).

    # Catch both HTTP network failures and Groq-specific API errors
    retry=retry_if_exception_type((httpx.RequestError, APIError, ConnectionError)),
    reraise=True #Without this, Tenacity would just silently swallow the error and return None. By re-raising it, your FastAPI try/except block (which we built in Phase 3) will catch it and properly return a clean 500 Server Error to the React frontend so the user knows what happened.
)