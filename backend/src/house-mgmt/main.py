import os
from fastapi import FastAPI
from mangum import Mangum

# Read environment variables (passed from SAM)
APP_NAME = os.getenv("APP_NAME", "MyPersonalApp")
STAGE = os.getenv("STAGE", "Prod")

# Initialize FastAPI app
app = FastAPI(
    title=f"{APP_NAME} API",
    description=f"A FastAPI backend deployed via AWS SAM (Stage: {STAGE})",
    version="1.0.0"
)

# CORS is handled by API Gateway - see template.yaml

# Import routes
from house-mgmt.routes.health import router as health_router

# Register routes
app.include_router(health_router)

# Lambda handler
handler = Mangum(app)
