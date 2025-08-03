"""
Recurring Task Pydantic models with validation
Following Best-practices.md: All inputs validated with Pydantic models
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime

class RecurringTaskCreate(BaseModel):
    """Model for creating recurring task with validation"""
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
        """Validate task name is not empty and within length limit"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        if len(v.strip()) > 30:
            raise ValueError("Task name must be 30 characters or less")
        return v.strip()
    
    @field_validator('assigned_to')
    @classmethod
    def validate_assigned_to(cls, v):
        """Validate assigned_to is not empty"""
        if not v or not v.strip():
            raise ValueError("assigned_to cannot be empty")
        return v.strip()

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