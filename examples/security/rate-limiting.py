# Rate limiting implementation
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.post("/api/login")
@limiter.limit("5/minute")  # 5 attempts per minute per IP
async def login(request: Request, credentials: LoginRequest):
    # Login logic here
    pass

@app.post("/api/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(request: Request, user_data: CreateUserRequest):
    # Registration logic here
    pass

@app.get("/api/users")
@limiter.limit("100/minute")  # Higher limit for read operations
async def get_users(request: Request):
    # Get users logic here
    pass