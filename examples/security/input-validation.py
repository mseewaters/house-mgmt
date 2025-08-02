# Input validation with Pydantic
from pydantic import BaseModel, Field, validator
from typing import Optional

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    email: str = Field(..., regex="^[^@]+@[^@]+\.[^@]+$")
    
    @validator('username')
    def username_must_be_safe(cls, v):
        if any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError('Username contains unsafe characters')
        return v

class UpdateUserRequest(BaseModel):
    email: Optional[str] = Field(None, regex="^[^@]+@[^@]+\.[^@]+$")
    bio: Optional[str] = Field(None, max_length=500)
    
    @validator('bio')
    def sanitize_bio(cls, v):
        if v and any(char in v for char in ['<script', '<iframe', 'javascript:']):
            raise ValueError('Bio contains unsafe content')
        return v