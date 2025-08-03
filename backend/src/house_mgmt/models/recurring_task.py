"""
Recurring Task Pydantic models with enhanced security validation
Following Best-practices.md: All inputs validated with Pydantic models
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime
import re

class RecurringTaskCreate(BaseModel):
    """Model for creating recurring task with enhanced security validation"""
    task_name: str = Field(..., description="Recurring task name")
    assigned_to: str = Field(..., description="Family member UUID")
    frequency: Literal["Daily", "Weekly", "Monthly"] = Field(..., description="Task frequency")
    due: str = Field(..., description="When task is due")
    overdue_when: Literal["Immediate", "1 hour", "6 hours", "1 day", "3 days", "7 days"] = Field(..., description="When task becomes overdue")
    category: Literal["Medication", "Feeding", "Health", "Cleaning", "Other"] = Field(..., description="Task category")
    status: Literal["Active", "Inactive"] = Field(..., description="Task status")
    
    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v):
        """Validate task name with security considerations"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        
        # Security: Remove control characters and excessive whitespace
        sanitized = re.sub(r'\s+', ' ', v.strip())
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        if len(sanitized) > 30:
            raise ValueError("Task name must be 30 characters or less")
        if len(sanitized) == 0:
            raise ValueError("Task name cannot be empty after sanitization")
            
        # Security: Basic injection prevention
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in sanitized.lower() for pattern in suspicious_patterns):
            raise ValueError("Task name contains invalid content")
            
        return sanitized
    
    @field_validator('assigned_to')
    @classmethod
    def validate_assigned_to(cls, v):
        """Validate assigned_to with basic format check"""
        if not v or not v.strip():
            raise ValueError("assigned_to cannot be empty")
        
        # Security: Basic format validation (UUID-like or test format)
        sanitized = v.strip()
        if len(sanitized) < 5 or len(sanitized) > 50:
            raise ValueError("assigned_to has invalid length")
            
        # Allow UUID format or test format like "member-uuid-123"
        if not re.match(r'^[a-zA-Z0-9\-]+$', sanitized):
            raise ValueError("assigned_to contains invalid characters")
            
        return sanitized
    
    @field_validator('due')
    @classmethod
    def validate_due(cls, v):
        """Validate due field content"""
        if not v or not v.strip():
            raise ValueError("due cannot be empty")
            
        # Security: Limit due field content and sanitize
        sanitized = v.strip()[:20]  # Limit length
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        return sanitized

class RecurringTaskModel(BaseModel):
    """Complete recurring task model with timestamps"""
    task_id: str
    task_name: str
    assigned_to: str
    frequency: str
    due: str
    overdue_when: str
    category: str
    status: str
    created_at: datetime
    updated_at: datetime