"""
Family Member DAL with UTC timestamp support
Following Best-practices.md: Store in UTC timezone
"""
from typing import Optional
from datetime import datetime, timezone
from models.family_member import FamilyMemberCreate, FamilyMemberModel

class FamilyMemberDAL:
    """DAL class with UTC timestamp support"""
    
    def __init__(self, table_name: str = None):
        """Initialize DAL with optional table name"""
        self.table_name = table_name or 'house-mgmt-dev'
        self._stored_members = {}  # In-memory storage for now
    
    def create_family_member(self, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """Create family member with proper UTC timestamps"""
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
        
        return member
    
    def get_family_member_by_id(self, member_id: str) -> Optional[FamilyMemberModel]:
        """Retrieve family member by ID"""
        return self._stored_members.get(member_id)