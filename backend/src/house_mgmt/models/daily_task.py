"""
Daily Task Pydantic models with enhanced security validation
Following Best-practices.md: All inputs validated with Pydantic models
Following technical design schema for daily task instances
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re


class DailyTaskCreate(BaseModel):
    """Model for creating daily task instance with validation"""
    task_name: str = Field(..., description="Daily task name")
    assigned_to: str = Field(..., description="Family member UUID")
    recurring_task_id: str = Field(..., description="Source recurring task UUID")
    date: str = Field(..., description="Task date (YYYY-MM-DD)")
    due_time: Literal["Morning", "Evening"] = Field(..., description="When task is due")
    status: Literal["Pending", "Completed", "Overdue", "Cleared", "Skipped"] = Field(..., description="Task status")
    category: Literal["Medication", "Feeding", "Health", "Cleaning", "Other"] = Field(..., description="Task category")
    overdue_when: Literal["Immediate", "1 hour", "6 hours", "1 day", "3 days", "7 days"] = Field(..., description="When task becomes overdue")
    
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
    
    @field_validator('assigned_to', 'recurring_task_id')
    @classmethod
    def validate_uuid_fields(cls, v):
        """Validate UUID format for assigned_to and recurring_task_id"""
        if not v or not v.strip():
            raise ValueError("UUID field cannot be empty")
        
        # Basic UUID format validation (loose check for flexibility)
        sanitized = v.strip()
        if len(sanitized) < 10 or len(sanitized) > 50:
            raise ValueError("Invalid UUID format")
            
        return sanitized
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format (YYYY-MM-DD)"""
        if not v or not v.strip():
            raise ValueError("Date cannot be empty")
        
        # Basic date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v.strip()):
            raise ValueError("Date must be in YYYY-MM-DD format")
            
        return v.strip()


class DailyTaskModel(BaseModel):
    """Complete daily task model with UTC timestamps following technical design schema"""
    task_id: str
    task_name: str
    assigned_to: str
    recurring_task_id: str
    date: str
    due_time: str
    status: str
    category: str
    overdue_when: str
    completed_at: Optional[datetime] = None
    generated_at: datetime
    overdue_at: datetime
    clear_at: datetime
    created_at: datetime
    updated_at: datetime