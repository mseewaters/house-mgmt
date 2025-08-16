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
                    log_info("processing_found_item", member_id=member_id, item_keys=list(item.keys()))
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
        # Parse ISO datetime strings back to datetime objects (handle missing created_at)
        created_at_str = item.get('created_at', item.get('updated_at'))
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
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
    
    def update_family_member(self, member_id: str, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """
        Update an existing family member in DynamoDB or in-memory storage
        
        Args:
            member_id: UUID of the family member to update
            member_data: Validated family member update data
            
        Returns:
            Updated family member with new timestamps
            
        Raises:
            ValueError: If family member not found
            Exception: For database errors
        """
        if self.use_dynamodb:
            return self._update_family_member_dynamodb(member_id, member_data)
        else:
            return self._update_family_member_memory(member_id, member_data)


    def _update_family_member_dynamodb(self, member_id: str, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """Update family member in DynamoDB"""
        try:
            # First check if member exists
            existing_member = self.get_family_member_by_id(member_id)
            if existing_member is None:
                raise ValueError(f"Family member not found: {member_id}")
            
            # Prepare update data with new timestamp
            now = datetime.now(timezone.utc)
            
            # Build update expression dynamically based on provided fields
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            # Always update these fields
            update_expression_parts.append("#name = :name")
            update_expression_parts.append("#member_type = :member_type") 
            update_expression_parts.append("#status = :status")
            update_expression_parts.append("#updated_at = :updated_at")
            
            expression_attribute_names["#name"] = "name"
            expression_attribute_names["#member_type"] = "member_type"
            expression_attribute_names["#status"] = "status"
            expression_attribute_names["#updated_at"] = "updated_at"
            
            expression_attribute_values[":name"] = member_data.name
            expression_attribute_values[":member_type"] = member_data.member_type
            expression_attribute_values[":status"] = member_data.status
            expression_attribute_values[":updated_at"] = now.isoformat()
            
            # Build SET expression
            set_expression = "SET " + ", ".join(update_expression_parts)

            # Handle pet_type separately
            if member_data.member_type == "Pet" and member_data.pet_type:
                set_expression += ", #pet_type = :pet_type"
                expression_attribute_names["#pet_type"] = "pet_type"
                expression_attribute_values[":pet_type"] = member_data.pet_type
                update_expression = set_expression
            elif member_data.member_type == "Person":
                # Remove pet_type for Person members
                update_expression = set_expression + " REMOVE #pet_type"
                expression_attribute_names["#pet_type"] = "pet_type"
            else:
                update_expression = set_expression
            
            # Perform the update
            response = self.table.update_item(
                Key={
                    'PK': 'FAMILY',
                    'SK': f'MEMBER#{member_id}'
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            # Transform response to FamilyMemberModel
            updated_item = response['Attributes']
            return FamilyMemberModel(
                member_id=updated_item['member_id'],
                name=updated_item['name'],
                member_type=updated_item['member_type'],
                pet_type=updated_item.get('pet_type'),
                status=updated_item['status'],
                created_at=datetime.fromisoformat(updated_item['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(updated_item['updated_at'].replace('Z', '+00:00'))
            )
            
        except self.table.meta.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Family member not found: {member_id}")
            raise


    def _update_family_member_memory(self, member_id: str, member_data: FamilyMemberCreate) -> FamilyMemberModel:
        """Update family member in in-memory storage"""
        # Find existing member
        for i, member in enumerate(self.family_members):
            if member.member_id == member_id:
                # Update with new data and timestamp
                updated_member = FamilyMemberModel(
                    member_id=member_id,
                    name=member_data.name,
                    member_type=member_data.member_type,
                    pet_type=member_data.pet_type if member_data.member_type == "Pet" else None,
                    status=member_data.status,
                    created_at=member.created_at,  # Keep original created_at
                    updated_at=datetime.now(timezone.utc)
                )
                self.family_members[i] = updated_member
                return updated_member
        
        raise ValueError(f"Family member not found: {member_id}")


    def delete_family_member(self, member_id: str) -> None:
        """
        Delete a family member from DynamoDB or in-memory storage
        
        Args:
            member_id: UUID of the family member to delete
            
        Raises:
            ValueError: If family member not found
            Exception: For database errors
        """
        if self.use_dynamodb:
            self._delete_family_member_dynamodb(member_id)
        else:
            self._delete_family_member_memory(member_id)


    def _delete_family_member_dynamodb(self, member_id: str) -> None:
        """Delete family member from DynamoDB"""
        try:
            # First check if member exists
            self.get_family_member_by_id(member_id)
            
            # Delete the item
            self.table.delete_item(
                Key={
                    'PK': 'FAMILY',
                    'SK': f'MEMBER#{member_id}'
                }
            )
            
        except ValueError:
            # Member not found - re-raise
            raise


    def _delete_family_member_memory(self, member_id: str) -> None:
        """Delete family member from in-memory storage"""
        for i, member in enumerate(self.family_members):
            if member.member_id == member_id:
                del self.family_members[i]
                return
        
        raise ValueError(f"Family member not found: {member_id}")

