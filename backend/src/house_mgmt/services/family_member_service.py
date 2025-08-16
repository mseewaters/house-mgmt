"""
Family Member Service Layer
Following Best-practices.md: API → Service → DAL separation
"""
from typing import List, Optional
from models.family_member import FamilyMemberCreate, FamilyMemberModel
from dal.family_member_dal import FamilyMemberDAL
from utils.logging import log_info, log_error


class FamilyMemberService:
    """
    Service layer for family member business logic
    
    Responsibilities:
    - Business rule validation
    - Coordinate between API and DAL layers
    - Handle service-level error scenarios
    - Logging business events
    """
    
    def __init__(self, dal: Optional[FamilyMemberDAL] = None) -> None:
        """
        Initialize service with DAL dependency injection
        
        Args:
            dal: Family member DAL instance (defaults to new instance)
        """
        self._dal = dal or FamilyMemberDAL()
    
    def create_family_member(self, family_member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """
        Create a new family member with business validation
        
        Args:
            family_member_data: Validated family member creation data
            
        Returns:
            Created family member with generated ID and timestamps
            
        Raises:
            ValueError: For business rule violations
            RuntimeError: For unexpected persistence errors
        """
        try:
            log_info(
                "family_member_service_create_started",
                name=family_member_data.name,
                member_type=family_member_data.member_type
            )
            
            # Business rule: Could add additional validations here
            # For example: Check for duplicate names, family size limits, etc.
            
            # Delegate to DAL
            result = self._dal.create_family_member(family_member_data)
            
            log_info(
                "family_member_service_create_completed",
                member_id=result.member_id,
                name=result.name
            )
            
            return result
            
        except ValueError as e:
            # Re-raise validation errors from DAL
            log_error(
                "family_member_service_create_validation_error",
                error=str(e),
                name=family_member_data.name
            )
            raise
            
        except Exception as e:
            # Handle and log unexpected errors
            log_error(
                "family_member_service_create_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                name=family_member_data.name
            )
            raise RuntimeError("Failed to create family member") from e
    
    def get_family_member_by_id(self, member_id: str) -> Optional[FamilyMemberModel]:
        """
        Retrieve family member by ID
        
        Args:
            member_id: Unique family member identifier
            
        Returns:
            Family member if found, None otherwise (caller handles 404)
            
        Raises:
            RuntimeError: For unexpected persistence errors only
        """
        try:
            log_info(
                "family_member_service_get_by_id_started",
                member_id=member_id
            )
            
            # Delegate to DAL - let it return None for not found
            result = self._dal.get_family_member_by_id(member_id)
            
            if result:
                log_info(
                    "family_member_service_get_by_id_found",
                    member_id=member_id,
                    name=result.name
                )
            else:
                log_info(
                    "family_member_service_get_by_id_not_found",
                    member_id=member_id
                )
            
            # Return None - let the API layer handle 404 response
            return result
            
        except Exception as e:
            # Handle and log unexpected errors only
            log_error(
                "family_member_service_get_by_id_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                member_id=member_id
            )
            raise RuntimeError("Failed to retrieve family member") from e
    
    def get_all_family_members(self) -> List[FamilyMemberModel]:
        """
        Retrieve all family members
        
        Returns:
            List of all family members (empty list if none exist)
            
        Raises:
            RuntimeError: For unexpected persistence errors
        """
        try:
            log_info("family_member_service_get_all_started")
            
            # Delegate to DAL
            results = self._dal.get_all_family_members()
            
            log_info(
                "family_member_service_get_all_completed",
                count=len(results)
            )
            
            return results
            
        except Exception as e:
            # Handle and log unexpected errors
            log_error(
                "family_member_service_get_all_unexpected_error",
                error=str(e),
                error_type=type(e).__name__
            )
            raise RuntimeError("Failed to retrieve family members") from e
        
    def update_family_member(self, member_id: str, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """
        Update an existing family member
        
        Args:
            member_id: UUID of the family member to update
            member_data: Validated family member update data
            
        Returns:
            Updated family member with new timestamps
            
        Raises:
            ValueError: If family member not found
            Exception: For database errors
        """
        try:
            log_info(
                "family_member_service_update_started",
                member_id=member_id,
                name=member_data.name,
                member_type=member_data.member_type
            )
            
            # Check if member exists first
            existing_member = self._dal.get_family_member_by_id(member_id)
            if existing_member is None:
                log_error("family_member_service_update_not_found", member_id=member_id)
                raise ValueError(f"Family member not found: {member_id}")
            
            # Update via DAL
            updated_member = self._dal.update_family_member(member_id, member_data)
            
            log_info(
                "family_member_service_update_success",
                member_id=updated_member.member_id,
                name=updated_member.name,
                updated_at=updated_member.updated_at.isoformat()
            )
            
            return updated_member
            
        except ValueError:
            # Re-raise validation errors (member not found)
            raise
        except Exception as e:
            log_error(
                "family_member_service_update_error",
                member_id=member_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def delete_family_member(self, member_id: str) -> None:
        """
        Delete a family member after checking for associated recurring tasks
        
        Args:
            member_id: UUID of the family member to delete
            
        Raises:
            ValueError: If family member not found or has associated tasks
            Exception: For database errors
        """
        try:
            log_info(
                "family_member_service_delete_started",
                member_id=member_id
            )
            
            # Check if member exists first
            existing_member = self._dal.get_family_member_by_id(member_id)
            if existing_member is None:
                log_error("family_member_service_delete_not_found", member_id=member_id)
                raise ValueError(f"Family member not found: {member_id}")
            
            # Check for associated recurring tasks
            from dal.recurring_task_dal import RecurringTaskDAL
            recurring_task_dal = RecurringTaskDAL(table_name=self._dal.table_name)
            
            log_info("checking_for_associated_tasks", member_id=member_id)  # ADD THIS LINE

            try:
                # Try to get tasks for this member
                member_tasks = recurring_task_dal.get_recurring_tasks_by_member(member_id)
                log_info("found_member_tasks", member_id=member_id, task_count=len(member_tasks))  # ADD THIS LINE

                if member_tasks:
                    log_error(
                        "family_member_service_delete_has_tasks",
                        member_id=member_id,
                        task_count=len(member_tasks)
                    )
                    raise ValueError(f"Cannot delete family member with {len(member_tasks)} associated tasks")
            except ValueError as e:
                if "not found" not in str(e).lower():
                    # Re-raise if it's not a "no tasks found" error
                    raise
                # If no tasks found, that's fine - continue with deletion
            
            # Delete via DAL
            self._dal.delete_family_member(member_id)
            
            log_info(
                "family_member_service_delete_success",
                member_id=member_id,
                name=existing_member.name
            )
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            log_error(
                "family_member_service_delete_error",
                member_id=member_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

        