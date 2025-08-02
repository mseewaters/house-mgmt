# Secure JWT token handling
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

def create_jwt_token(user_id: str, secret: str) -> str:
    """Create a secure JWT token with proper expiration"""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iss": "your-app-name"
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_jwt_token(token: str, secret: str) -> dict:
    """Verify JWT token with proper validation"""
    try:
        payload = jwt.decode(
            token, secret, 
            algorithms=["HS256"],
            options={"verify_exp": True, "verify_iss": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

def extract_token_from_header(authorization: str) -> str:
    """Extract Bearer token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    return authorization.split(" ")[1]