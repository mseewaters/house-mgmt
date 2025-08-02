# Error logging with stack traces
import traceback
from fastapi import Request

@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
    log_error("Unhandled exception", 
              path=request.url.path, 
              error=str(exc), 
              trace=traceback.format_exc())
    raise exc