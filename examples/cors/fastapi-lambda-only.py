# FastAPI CORS - Complete Lambda implementation
# Use this approach when you want Lambda to handle ALL CORS
# Remove CORS section from template.yaml when using this

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Environment-based CORS configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production: Specific domain with credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],  # Your production domain
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["X-Correlation-ID"]  # Custom headers to expose
    )
elif ENVIRONMENT == "development":
    # Development: Local origins with credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # React/Next.js default
            "http://localhost:5173",   # Vite default
            "http://localhost:8080",   # Vue CLI default
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["X-Correlation-ID"]
    )
else:
    # Open/testing: No credentials, all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"]
    )

@app.get("/api/test")
def test():
    return {"message": "FastAPI handles CORS", "environment": ENVIRONMENT}

# Your template.yaml should NOT have CORS section:
# Globals:
#   Api:
#     # DO NOT ADD CORS HERE when using FastAPI CORS
#     pass