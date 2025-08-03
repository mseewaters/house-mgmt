import os
from fastapi import FastAPI, Request
from mangum import Mangum
from middleware.correlation import CorrelationIDMiddleware
from utils.logging import log_info

# Read environment variables (passed from SAM)
APP_NAME = os.getenv("APP_NAME", "HouseManagement")
STAGE = os.getenv("STAGE", "Prod")

# Initialize FastAPI app
app = FastAPI(
    title=f"{APP_NAME} API",
    description=f"A FastAPI backend deployed via AWS SAM (Stage: {STAGE})",
    version="1.0.0"
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# CORS is handled by API Gateway - see template.yaml

# Import routes
from routes.health import router as health_router
from routes.family_members import router as family_router
from routes.recurring_tasks import router as recurring_tasks_router

# Register routes
app.include_router(health_router)
app.include_router(family_router)
app.include_router(recurring_tasks_router)

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