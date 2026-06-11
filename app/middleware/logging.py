import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class APILoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log the incoming request
        logger.info(f"➡️ Incoming Request: {request.method} {request.url.path}")
        
        try:
            # Pass the request to the actual route
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log the successful response
            logger.info(
                f"⬅️ Response: {request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Time: {process_time:.4f}s"
            )
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            # Log any unhandled server crashes
            logger.error(
                f"❌ SERVER CRASH: {request.method} {request.url.path} "
                f"- Time: {process_time:.4f}s - Error: {str(e)}", 
                exc_info=True
            )
            raise