# Automatic request logging middleware
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    log_info("HTTP request", 
             method=request.method, 
             path=request.url.path, 
             status=response.status_code, 
             duration_ms=duration)
    return response