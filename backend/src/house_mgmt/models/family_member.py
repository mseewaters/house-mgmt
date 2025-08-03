"""
Family Member model with enhanced security validation
Following Best-practices.md: All inputs validated with Pydantic models
Using Pydantic V2 syntax with security enhancements
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime, timezone
import re

class FamilyMemberCreate(BaseModel):
    """Model for creating family member with enhanced security validation"""
    name: str = Field(..., description="Family member name")
    member_type: Literal["Person", "Pet"] = Field(..., description="Type of family member")
    pet_type: Optional[Literal["dog", "cat", "other"]] = Field(None, description="Pet type if member_type is Pet")
    status: Literal["Active", "Inactive"] = Field(..., description="Member status")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name with security considerations"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        # Security: Remove control characters and excessive whitespace
        sanitized = re.sub(r'\s+', ' ', v.strip())
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        if len(sanitized) > 15:
            raise ValueError("Name must be 15 characters or less")
        if len(sanitized) == 0:
            raise ValueError("Name cannot be empty after sanitization")
            
        # Security: Basic injection prevention
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in sanitized.lower() for pattern in suspicious_patterns):
            raise ValueError("Name contains invalid content")
            
        # Security: Only allow alphanumeric, spaces, hyphens, apostrophes (common for names)
        if not re.match(r"^[a-zA-Z0-9\s\-']+$", sanitized):
            raise ValueError("Name contains invalid characters")
            
        return sanitized
    
    @model_validator(mode='after')
    def validate_pet_type(self):
        """Validate pet_type is provided when member_type is Pet"""
        if self.member_type == 'Pet' and not self.pet_type:
            raise ValueError("pet_type is required when member_type is Pet")
        if self.member_type == 'Person' and self.pet_type:
            raise ValueError("pet_type should not be provided when member_type is Person")
        return self

class FamilyMemberModel(BaseModel):
    """Complete family member model with UTC timestamps"""
    member_id: str
    name: str
    member_type: str
    pet_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime