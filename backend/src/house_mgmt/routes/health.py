"""
Health check and sample routes
"""
import os
from fastapi import APIRouter
from house_mgmt.utils.logging import log_info

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health_check():
    """Health check endpoint"""
    app_name = os.getenv("APP_NAME", "HouseManagement")
    stage = os.getenv("STAGE", "Prod")
    
    log_info("Health check requested", app=app_name, stage=stage)
    
    return {
        "status": "healthy",
        "app": app_name,
        "stage": stage,
        "message": "House Management API is running"
    }

@router.get("/hello/{name}")
def hello(name: str):
    """Sample parameterized endpoint"""
    app_name = os.getenv("APP_NAME", "HouseManagement")
    
    log_info("Hello endpoint called", name=name, app=app_name)
    
    return {"message": f"Hello, {name}!", "app": app_name}