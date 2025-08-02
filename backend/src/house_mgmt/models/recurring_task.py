"""
Recurring Task Pydantic models
Following Best-practices.md: All inputs validated with Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class RecurringTaskCreate(BaseModel):
    """Model for creating recurring task"""
    task_name: str
    assigned_to: str
    frequency: Literal["Daily", "Weekly", "Monthly"]
    due: str
    overdue_when: Literal["Immediate", "1 hour", "6 hours", "1 day", "3 days", "7 days"]
    category: Literal["Medication", "Feeding", "Health", "Cleaning", "Other"]
    status: Literal["Active", "Inactive"]

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