"""
Correlation ID middleware for request tracing
Following Best-practices.md: Structured JSON logging with correlation IDs
"""
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from house_mgmt.utils.logging import set_correlation_id, log_info

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests for tracing
    
    Features:
    - Generates unique correlation ID for each request
    - Preserves custom correlation ID if provided in request headers
    - Adds correlation ID to response headers
    - Makes correlation ID available in request state
    - Integrates with structured logging
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add correlation ID
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state for access by route handlers
        request.state.correlation_id = correlation_id
        
        # Set for structured logging context
        set_correlation_id(correlation_id)
        
        # Log request start
        log_info(
            "request_started",
            method=request.method,
            url=str(request.url),
            correlation_id=correlation_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Log successful response
            log_info(
                "request_completed",
                status_code=response.status_code,
                correlation_id=correlation_id
            )
            
            return response
            
        except Exception as e:
            # Log error with correlation ID
            log_info(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id
            )
            raise