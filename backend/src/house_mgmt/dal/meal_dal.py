"""
Meal Data Access Layer with DynamoDB implementation
Following Best-practices.md: KeyConditionExpression (not scans), UTC timestamps, structured logging
Following technical design schema: PK = "MEAL#date", SK = "MEAL#uuid"
"""
import boto3
import os
import uuid
from typing import List, Optional, Dict
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from models.meal import MealCreate, MealUpdate, MealModel
from utils.logging import log_info, log_error


class MealDAL:
    """DAL for meal operations with DynamoDB persistence"""
    
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
            # Fall back to in-memory storage - ALWAYS create fresh instance
            self.use_dynamodb = False
            self._stored_meals = {}  # Fresh dictionary for each DAL instance
            log_info("Using in-memory storage fallback", error=str(e))
    
    def create_meal(self, meal_data: MealCreate) -> MealModel:
        """
        Create meal with DynamoDB persistence and UTC timestamps
        
        Args:
            meal_data: Validated Pydantic meal creation data
            
        Returns:
            MealModel with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If unexpected error occurs
        """
        try:
            # Generate UTC timestamps (Best-practices.md requirement)
            now = datetime.now(timezone.utc)
            meal_id = str(uuid.uuid4())
            
            # Create DynamoDB item following technical design schema
            item = {
                'PK': f'MEAL#{meal_data.date_shipped}',
                'SK': f'MEAL#{meal_id}',
                'GSI1PK': f'MEAL#STATUS#{meal_data.status}',
                'GSI1SK': meal_data.date_shipped,
                'entity_type': 'meal',
                'meal_id': meal_id,
                'meal_name': meal_data.meal_name,
                'description': meal_data.description,
                'thumbnail_url': meal_data.thumbnail_url,
                'date_shipped': meal_data.date_shipped,
                'status': meal_data.status,
                'prepared_at': None,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Store in DynamoDB or fallback to in-memory
            if self.use_dynamodb:
                self.table.put_item(Item=item)
                log_info(
                    "Meal stored in DynamoDB successfully",
                    meal_id=meal_id,
                    table_name=self.table_name
                )
            else:
                # Fall back to in-memory storage
                self._stored_meals[meal_id] = item
                log_info(
                    "Meal stored in memory (DynamoDB not available)",
                    meal_id=meal_id
                )
            
            # Create return model with proper datetime objects
            result = MealModel(
                meal_id=meal_id,
                meal_name=meal_data.meal_name,
                description=meal_data.description,
                thumbnail_url=meal_data.thumbnail_url,
                date_shipped=meal_data.date_shipped,
                status=meal_data.status,
                prepared_at=None,
                created_at=now,
                updated_at=now
            )
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Meal created successfully",
                meal_id=meal_id,
                meal_name=meal_data.meal_name,
                date_shipped=meal_data.date_shipped
            )
            
            return result
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create meal",
                error=str(e),
                meal_name=meal_data.meal_name if meal_data else None
            )
            raise RuntimeError("An error occurred while creating the meal")
    
    def get_meal_by_id(self, meal_id: str) -> Optional[MealModel]:
        """
        Retrieve meal by ID
        
        Args:
            meal_id: Meal ID to retrieve
            
        Returns:
            MealModel if found, None otherwise
        """
        try:
            if self.use_dynamodb:
                # Need to scan since we don't know the date (PK)
                # This is not ideal but needed for get_by_id functionality
                response = self.table.scan(
                    FilterExpression='meal_id = :meal_id',
                    ExpressionAttributeValues={':meal_id': meal_id}
                )
                items = response.get('Items', [])
                if not items:
                    return None
                item = items[0]
            else:
                # In-memory storage
                item = self._stored_meals.get(meal_id)
                if not item:
                    return None
            
            # Convert to model
            return self._item_to_model(item)
            
        except Exception as e:
            log_error("Failed to retrieve meal", error=str(e), meal_id=meal_id)
            return None
    
    def get_meals_by_date(self, date: str) -> List[MealModel]:
        """
        Get all meals for a specific date using KeyConditionExpression
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of MealModel for the specified date
        """
        try:
            if self.use_dynamodb:
                # Use KeyConditionExpression following Best-practices.md
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                    ExpressionAttributeValues={
                        ':pk': f'MEAL#{date}',
                        ':sk': 'MEAL#'
                    }
                )
                items = response.get('Items', [])
            else:
                # In-memory storage - filter by PK to match DynamoDB behavior
                target_pk = f'MEAL#{date}'
                items = [
                    item for item in self._stored_meals.values()
                    if item.get('PK') == target_pk and item.get('SK', '').startswith('MEAL#')
                ]
                
                # Debug logging to see what we're filtering
                log_info(
                    "Filtering meals by date",
                    target_date=date,
                    target_pk=target_pk,
                    total_stored=len(self._stored_meals),
                    matching_items=len(items)
                )
            
            # Convert to models
            return [self._item_to_model(item) for item in items]
            
        except Exception as e:
            log_error("Failed to retrieve meals by date", error=str(e), date=date)
            return []
    
    def get_all_meals(self, status_filter: Optional[str] = None) -> List[MealModel]:
        """
        Get all meals, optionally filtered by status
        
        Args:
            status_filter: Optional status to filter by (available, prepared, expired)
            
        Returns:
            List of MealModel
        """
        try:
            if self.use_dynamodb:
                if status_filter:
                    # Use GSI to filter by status
                    response = self.table.query(
                        IndexName='GSI1',
                        KeyConditionExpression='GSI1PK = :gsi_pk',
                        ExpressionAttributeValues={
                            ':gsi_pk': f'MEAL#STATUS#{status_filter}'
                        }
                    )
                else:
                    # Scan all meals (not ideal but needed for get all functionality)
                    response = self.table.scan(
                        FilterExpression='entity_type = :entity_type',
                        ExpressionAttributeValues={':entity_type': 'meal'}
                    )
                items = response.get('Items', [])
            else:
                # In-memory storage
                items = [
                    item for item in self._stored_meals.values()
                    if item.get('entity_type') == 'meal' and 
                       (not status_filter or item.get('status') == status_filter)
                ]
            
            # Convert to models and sort by date_shipped (newest first)
            meals = [self._item_to_model(item) for item in items]
            meals.sort(key=lambda x: x.date_shipped, reverse=True)
            return meals
            
        except Exception as e:
            log_error("Failed to retrieve all meals", error=str(e), status_filter=status_filter)
            return []
    
    def update_meal_status(self, meal_id: str, meal_update: MealUpdate) -> Optional[MealModel]:
        """
        Update meal status and preparation timestamp
        
        Args:
            meal_id: Meal ID to update
            meal_update: MealUpdate with new status
            
        Returns:
            Updated MealModel if successful, None otherwise
        """
        try:
            # First get the current meal to know its PK
            current_meal = self.get_meal_by_id(meal_id)
            if not current_meal:
                return None
            
            now = datetime.now(timezone.utc)
            prepared_at = now if meal_update.status == 'prepared' else None
            
            if self.use_dynamodb:
                # Update in DynamoDB
                update_expression = "SET #status = :status, updated_at = :updated_at, prepared_at = :prepared_at, GSI1PK = :gsi_pk"
                expression_values = {
                    ':status': meal_update.status,
                    ':updated_at': now.isoformat(),
                    ':prepared_at': prepared_at.isoformat() if prepared_at else None,
                    ':gsi_pk': f'MEAL#STATUS#{meal_update.status}'
                }
                expression_names = {'#status': 'status'}
                
                response = self.table.update_item(
                    Key={
                        'PK': f'MEAL#{current_meal.date_shipped}',
                        'SK': f'MEAL#{meal_id}'
                    },
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ExpressionAttributeNames=expression_names,
                    ReturnValues='ALL_NEW'
                )
                updated_item = response['Attributes']
            else:
                # Update in-memory storage
                item = self._stored_meals[meal_id]
                item['status'] = meal_update.status
                item['updated_at'] = now.isoformat()
                item['prepared_at'] = prepared_at.isoformat() if prepared_at else None
                item['GSI1PK'] = f'MEAL#STATUS#{meal_update.status}'
                updated_item = item
            
            log_info(
                "Meal status updated",
                meal_id=meal_id,
                old_status=current_meal.status,
                new_status=meal_update.status
            )
            
            return self._item_to_model(updated_item)
            
        except Exception as e:
            log_error("Failed to update meal status", error=str(e), meal_id=meal_id)
            return None
    
    def delete_meal(self, meal_id: str) -> bool:
        """
        Delete meal by ID
        
        Args:
            meal_id: Meal ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First get the current meal to know its PK
            current_meal = self.get_meal_by_id(meal_id)
            if not current_meal:
                return False
            
            if self.use_dynamodb:
                # Delete from DynamoDB
                self.table.delete_item(
                    Key={
                        'PK': f'MEAL#{current_meal.date_shipped}',
                        'SK': f'MEAL#{meal_id}'
                    }
                )
            else:
                # Delete from in-memory storage
                del self._stored_meals[meal_id]
            
            log_info("Meal deleted successfully", meal_id=meal_id)
            return True
            
        except Exception as e:
            log_error("Failed to delete meal", error=str(e), meal_id=meal_id)
            return False
    
    def _item_to_model(self, item: Dict) -> MealModel:
        """Convert DynamoDB item to MealModel"""
        return MealModel(
            meal_id=item['meal_id'],
            meal_name=item['meal_name'],
            description=item['description'],
            thumbnail_url=item['thumbnail_url'],
            date_shipped=item['date_shipped'],
            status=item['status'],
            prepared_at=datetime.fromisoformat(item['prepared_at']) if item.get('prepared_at') else None,
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at'])
        )