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