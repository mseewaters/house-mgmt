"""
Family Member DAL with Best-practices.md compliance
Following Best-practices.md: Type hints, docstrings, structured logging, error handling
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from models.family_member import FamilyMemberCreate, FamilyMemberModel
from utils.logging import log_info, log_error


class FamilyMemberDAL:
    """DAL class with UTC timestamp support and structured logging"""
    
    def __init__(self, table_name: str = None) -> None:
        """
        Initialize DAL with optional table name
        
        Args:
            table_name: DynamoDB table name. If None, uses default
        """
        self.table_name = table_name or 'house-mgmt-dev'
        self._stored_members: Dict[str, FamilyMemberModel] = {}
    
    def create_family_member(self, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """
        Create family member with proper UTC timestamps and validation
        
        Args:
            member_data: Validated family member creation data
            
        Returns:
            FamilyMemberModel: Created family member with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If unexpected error occurs
        """
        try:
            import uuid
            
            # Generate UTC timestamps (Best-practices.md requirement)
            now = datetime.now(timezone.utc)
            member_id = str(uuid.uuid4())
            
            # Create member with UTC timestamps
            member = FamilyMemberModel(
                member_id=member_id,
                name=member_data.name,
                member_type=member_data.member_type,
                pet_type=member_data.pet_type,
                status=member_data.status,
                created_at=now,
                updated_at=now
            )
            
            # Store in memory for retrieval
            self._stored_members[member_id] = member
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Family member created successfully",
                member_id=member_id,
                name=member_data.name,
                member_type=member_data.member_type
            )
            
            return member
            
        except ValueError:
            # Re-raise validation errors from Pydantic (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create family member",
                error=str(e),
                member_data=member_data.dict() if hasattr(member_data, 'dict') else str(member_data)
            )
            raise RuntimeError("An error occurred while creating the family member")
    
    def get_family_member_by_id(self, member_id: str) -> Optional[FamilyMemberModel]:
        """
        Retrieve family member by ID with structured logging
        
        Args:
            member_id: Unique family member identifier
            
        Returns:
            FamilyMemberModel if found, None otherwise
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            result = self._stored_members.get(member_id)
            
            # Structured logging
            if result:
                log_info("Family member retrieved successfully", member_id=member_id)
            else:
                log_info("Family member not found", member_id=member_id)
            
            return result
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve family member",
                error=str(e),
                member_id=member_id
            )
            raise RuntimeError("An error occurred while retrieving the family member")