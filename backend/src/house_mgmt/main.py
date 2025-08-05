import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from house_mgmt.middleware.correlation import CorrelationIDMiddleware
from house_mgmt.utils.logging import log_info, log_error

# Read environment variables (passed from SAM)
APP_NAME = os.getenv("APP_NAME", "HouseManagement")
STAGE = os.getenv("STAGE", "Prod")

# Initialize FastAPI app with security settings
app = FastAPI(
    title=f"{APP_NAME} API",
    description=f"A FastAPI backend deployed via AWS SAM (Stage: {STAGE})",
    version="1.0.0",
    # Security: Limit request body size to prevent DoS
    docs_url=None if STAGE == "Prod" else "/docs",  # Disable docs in production
    redoc_url=None if STAGE == "Prod" else "/redoc"  # Disable redoc in production
)

# Security: Add trusted host middleware for production only
if STAGE == "Prod":
    # In production, only allow requests from known hosts
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*.execute-api.us-east-1.amazonaws.com", "localhost", "testserver"]
    )

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Security: Global exception handler to prevent information disclosure
@app.exception_handler(Exception)
async def secure_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions securely"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Log full error details for developers
    log_error(
        "Unhandled exception occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        correlation_id=correlation_id
    )
    
    # Return generic error to users (security best practice)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "correlation_id": correlation_id
        }
    )

# Security: Request size validation middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limit request body size to prevent DoS attacks"""
    # Only check POST/PUT requests with bodies
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get('content-length')
        if content_length:
            content_length = int(content_length)
            # Limit to 1MB for API requests
            max_size = 1024 * 1024  # 1MB
            if content_length > max_size:
                log_error(
                    "Request too large",
                    content_length=content_length,
                    max_size=max_size,
                    path=request.url.path
                )
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
    
    response = await call_next(request)
    return response

# CORS is handled by API Gateway - see template.yaml

# Import routes
from house_mgmt.routes.health import router as health_router
from house_mgmt.routes.family_members import router as family_router
from house_mgmt.routes.recurring_tasks import router as recurring_tasks_router
from house_mgmt.routes.daily_tasks import router as daily_tasks_router
from house_mgmt.routes.weather import router as weather_router

# Register routes
app.include_router(health_router)
app.include_router(family_router)
app.include_router(recurring_tasks_router)
app.include_router(daily_tasks_router)
app.include_router(weather_router)

# Add test endpoint for correlation ID verification
@app.get("/api/test/correlation")
async def test_correlation(request: Request):
    """
    Test endpoint to verify correlation ID is available in request state
    
    Returns:
        Correlation ID from request state
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    log_info(
        "test_correlation_endpoint_called",
        correlation_id=correlation_id,
        available=correlation_id is not None
    )
    
    return {
        "correlation_id": correlation_id,
        "available": correlation_id is not None
    }

# Lambda handler
handler = Mangum(app)