# Timezone-aware datetime utilities
from datetime import datetime, timezone
from typing import Optional

def now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def to_utc_string(dt: datetime) -> str:
    """Convert datetime to UTC ISO string"""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

def from_utc_string(utc_string: str) -> datetime:
    """Parse UTC ISO string to datetime"""
    return datetime.fromisoformat(utc_string.replace('Z', '+00:00'))

def format_for_display(utc_dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format UTC datetime for display (still in UTC)"""
    return utc_dt.strftime(format_str) + " UTC"

# Example usage in FastAPI response models
from pydantic import BaseModel, Field

class TimestampedResponse(BaseModel):
    id: str
    created_at: datetime = Field(..., description="UTC timestamp")
    updated_at: Optional[datetime] = Field(None, description="UTC timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }