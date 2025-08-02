# Secure error handling without information disclosure
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

def get_correlation_id() -> str:
    """Generate correlation ID for request tracing"""
    import uuid
    return str(uuid.uuid4())

@app.exception_handler(Exception)
async def secure_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions securely"""
    correlation_id = get_correlation_id()
    
    # Log full error details internally
    log_error("Internal error", 
              path=str(request.url.path),
              method=request.method,
              error=str(exc), 
              trace=traceback.format_exc(),
              correlation_id=correlation_id)
    
    # Return generic error to user
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error", 
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors (safe to return details)"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed", 
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )