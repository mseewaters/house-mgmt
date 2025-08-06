"""
Family Member DAL with DynamoDB implementation
Following Best-practices.md: KeyConditionExpression (not scans), UTC timestamps, structured logging
"""
import boto3
import os
from typing import Optional, List
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from models.family_member import FamilyMemberCreate, FamilyMemberModel
from utils.logging import log_info, log_error


class FamilyMemberDAL:
    """DAL class with DynamoDB persistence and structured logging"""
    
    def __init__(self, table_name: str = None) -> None:
        """
        Initialize DAL with DynamoDB table
        
        Args:
            table_name: DynamoDB table name. If None, uses environment variable
        """
        self.table_name = table_name or os.getenv('DYNAMODB_TABLE', 'house-mgmt-dev')
        
        # Initialize DynamoDB resource
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self.table = self.dynamodb.Table(self.table_name)
            # Test if table exists
            self.table.table_status
            self.use_dynamodb = True
            log_info("DynamoDB connection established", table_name=self.table_name)
        except Exception as e:
            # Fall back to in-memory storage
            self.use_dynamodb = False
            self._stored_members = {}
            log_info("Using in-memory storage fallback", error=str(e))
    
    def create_family_member(self, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """
        Create family member with DynamoDB persistence and UTC timestamps
        
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
            
            # Create DynamoDB item following technical design schema
            item = {
                'PK': 'FAMILY',
                'SK': f'MEMBER#{member_id}',
                'entity_type': 'family_member',
                'member_id': member_id,
                'name': member_data.name,
                'member_type': member_data.member_type,
                'pet_type': member_data.pet_type,  # Will be None for Person
                'status': member_data.status,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Store in DynamoDB
            if self.use_dynamodb:
                self.table.put_item(Item=item)
                log_info(
                    "Family member stored in DynamoDB successfully",
                    member_id=member_id,
                    table_name=self.table_name
                )
            else:
                # Fall back to in-memory storage
                self._stored_members[member_id] = item
                log_info(
                    "Family member stored in memory (DynamoDB not available)",
                    member_id=member_id
                )
            
            # Create return model with proper datetime objects
            result = FamilyMemberModel(
                member_id=member_id,
                name=member_data.name,
                member_type=member_data.member_type,
                pet_type=member_data.pet_type,
                status=member_data.status,
                created_at=now,
                updated_at=now
            )
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Family member created successfully",
                member_id=member_id,
                name=member_data.name,
                member_type=member_data.member_type
            )
            
            return result
            
        except ValueError:
            # Re-raise validation errors from Pydantic (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create family member",
                error=str(e),
                table_name=self.table_name
            )
            raise RuntimeError("An error occurred while creating the family member")
    
    def get_family_member_by_id(self, member_id: str) -> Optional[FamilyMemberModel]:
        """
        Retrieve family member by ID using DynamoDB GetItem
        
        Args:
            member_id: Unique family member identifier
            
        Returns:
            FamilyMemberModel if found, None otherwise
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            # Use GetItem with exact key (Best-practices.md: KeyConditionExpression)
            if self.use_dynamodb:
                response = self.table.get_item(
                    Key={
                        'PK': 'FAMILY',
                        'SK': f'MEMBER#{member_id}'
                    }
                )
                
                if 'Item' in response:
                    item = response['Item']
                    # Convert DynamoDB item to Pydantic model
                    result = self._item_to_model(item)
                    log_info("Family member retrieved from DynamoDB successfully", member_id=member_id)
                    return result
                else:
                    log_info("Family member not found in DynamoDB", member_id=member_id)
                    return None
            else:
                # Fall back to in-memory storage
                item = self._stored_members.get(member_id)
                if item:
                    return self._item_to_model(item)
                return None
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve family member",
                error=str(e),
                member_id=member_id
            )
            raise RuntimeError("An error occurred while retrieving the family member")
    
    def get_all_family_members(self) -> List[FamilyMemberModel]:
        """
        Retrieve all family members using DynamoDB Query with KeyConditionExpression
        Following Best-practices.md: Use KeyConditionExpression (not scans)
        
        Returns:
            List of all family members (empty list if none exist)
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            # Use Query with KeyConditionExpression (Best-practices.md requirement)
            if self.use_dynamodb:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': 'FAMILY',
                        ':sk_prefix': 'MEMBER#'
                    }
                )
                
                # Convert items to Pydantic models
                results = []
                for item in response.get('Items', []):
                    model = self._item_to_model(item)
                    results.append(model)
                
                log_info(
                    "All family members retrieved from DynamoDB successfully",
                    count=len(results)
                )
                
                return results
            else:
                # Fall back to in-memory storage
                results = []
                for item in self._stored_members.values():
                    model = self._item_to_model(item)
                    results.append(model)
                return results
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve all family members",
                error=str(e)
            )
            raise RuntimeError("An error occurred while retrieving family members")
    
    def _item_to_model(self, item: dict) -> FamilyMemberModel:
        """
        Convert DynamoDB item to Pydantic model
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            FamilyMemberModel with proper datetime objects
        """
        # Parse ISO datetime strings back to datetime objects
        created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        
        return FamilyMemberModel(
            member_id=item['member_id'],
            name=item['name'],
            member_type=item['member_type'],
            pet_type=item.get('pet_type'),  # May be None
            status=item['status'],
            created_at=created_at,
            updated_at=updated_at
        )