"""
Meal Pydantic models with enhanced security validation
Following Best-practices.md: All inputs validated with Pydantic models
Following technical design schema for meal data from email parsing
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re


class MealCreate(BaseModel):
    """Model for creating meal instance with validation"""
    meal_name: str = Field(..., description="Meal name from email")
    description: str = Field(..., description="Meal description")
    thumbnail_url: str = Field(..., description="Image URL for meal thumbnail")
    date_shipped: str = Field(..., description="Date meal was shipped (YYYY-MM-DD)")
    status: Literal["available", "prepared", "expired"] = Field(default="available", description="Meal preparation status")
    
    @field_validator('meal_name')
    @classmethod
    def validate_meal_name(cls, v):
        """Validate meal name with security considerations"""
        if not v or not v.strip():
            raise ValueError("Meal name cannot be empty")
        
        # Security: Remove control characters and excessive whitespace
        sanitized = re.sub(r'\s+', ' ', v.strip())
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        if len(sanitized) > 100:
            raise ValueError("Meal name must be 100 characters or less")
        if len(sanitized) == 0:
            raise ValueError("Meal name cannot be empty after sanitization")
            
        # Security: Basic injection prevention
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in sanitized.lower() for pattern in suspicious_patterns):
            raise ValueError("Meal name contains invalid content")
            
        return sanitized
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate meal description with security considerations"""
        if not v:
            v = ""
        
        # Security: Remove control characters and excessive whitespace
        sanitized = re.sub(r'\s+', ' ', v.strip())
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        if len(sanitized) > 200:
            raise ValueError("Meal description must be 200 characters or less")
            
        # Security: Basic injection prevention
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in sanitized.lower() for pattern in suspicious_patterns):
            raise ValueError("Meal description contains invalid content")
            
        return sanitized
    
    @field_validator('thumbnail_url')
    @classmethod
    def validate_thumbnail_url(cls, v):
        """Validate thumbnail URL format and security"""
        if not v or not v.strip():
            raise ValueError("Thumbnail URL cannot be empty")
        
        sanitized = v.strip()
        
        # Basic URL format validation
        if not re.match(r'^https?://', sanitized.lower()):
            raise ValueError("Thumbnail URL must start with http:// or https://")
        
        if len(sanitized) > 500:
            raise ValueError("Thumbnail URL must be 500 characters or less")
        
        # Security: Allow only specific domains for thumbnail URLs
        allowed_domains = ['asset.homechef.com', 'image.e.homechef.com']
        domain_found = False
        for domain in allowed_domains:
            if domain in sanitized.lower():
                domain_found = True
                break
        
        if not domain_found:
            raise ValueError(f"Thumbnail URL must be from allowed domains: {', '.join(allowed_domains)}")
            
        return sanitized
    
    @field_validator('date_shipped')
    @classmethod
    def validate_date_shipped(cls, v):
        """Validate date format (YYYY-MM-DD)"""
        if not v or not v.strip():
            raise ValueError("Date shipped cannot be empty")
        
        # Basic date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v.strip()):
            raise ValueError("Date shipped must be in YYYY-MM-DD format")
            
        return v.strip()


class MealUpdate(BaseModel):
    """Model for updating meal status"""
    status: Literal["available", "prepared", "expired"] = Field(..., description="Meal preparation status")


class MealModel(BaseModel):
    """Complete meal model with UTC timestamps following technical design schema"""
    meal_id: str
    meal_name: str
    description: str
    thumbnail_url: str
    date_shipped: str
    status: str
    prepared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime