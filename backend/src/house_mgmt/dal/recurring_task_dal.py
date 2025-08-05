"""
Recurring Task Data Access Layer with DynamoDB implementation
Following Best-practices.md: KeyConditionExpression (not scans), UTC timestamps, structured logging
Following technical design schema: PK = "RECURRING", SK = "TASK#uuid"
"""
import boto3
import os
from typing import List, Optional, Dict
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from house_mgmt.models.recurring_task import RecurringTaskCreate, RecurringTaskModel
from house_mgmt.utils.logging import log_info, log_error


class RecurringTaskDAL:
    """DAL for recurring task operations with DynamoDB persistence"""
    
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
            self._stored_tasks = {}
            log_info("Using in-memory storage fallback", error=str(e))
    
    def create_recurring_task(self, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """
        Create recurring task with DynamoDB persistence and UTC timestamps
        
        Args:
            task_data: Validated Pydantic recurring task creation data
            
        Returns:
            RecurringTaskModel with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If unexpected error occurs
        """
        try:
            import uuid
            
            # Generate UTC timestamps (Best-practices.md requirement)
            now = datetime.now(timezone.utc)
            task_id = str(uuid.uuid4())
            
            # Create DynamoDB item following technical design schema
            item = {
                'PK': 'RECURRING',
                'SK': f'TASK#{task_id}',
                'entity_type': 'recurring_task',
                'task_id': task_id,
                'task_name': task_data.task_name,
                'assigned_to': task_data.assigned_to,
                'frequency': task_data.frequency,
                'due': task_data.due,
                'overdue_when': task_data.overdue_when,
                'category': task_data.category,
                'status': task_data.status,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Store in DynamoDB or fallback to in-memory
            if self.use_dynamodb:
                self.table.put_item(Item=item)
                log_info(
                    "Recurring task stored in DynamoDB successfully",
                    task_id=task_id,
                    table_name=self.table_name
                )
            else:
                # Fall back to in-memory storage
                self._stored_tasks[task_id] = item
                log_info(
                    "Recurring task stored in memory (DynamoDB not available)",
                    task_id=task_id
                )
            
            # Create return model with proper datetime objects
            result = RecurringTaskModel(
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency,
                due=task_data.due,
                overdue_when=task_data.overdue_when,
                category=task_data.category,
                status=task_data.status,
                created_at=now,
                updated_at=now
            )
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Recurring task created successfully",
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency
            )
            
            return result
            
        except ValueError:
            # Re-raise validation errors (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create recurring task",
                error=str(e),
                table_name=self.table_name
            )
            raise RuntimeError("An error occurred while creating the recurring task")
    
    def get_recurring_task_by_id(self, task_id: str) -> Optional[RecurringTaskModel]:
        """
        Retrieve recurring task by ID using DynamoDB GetItem
        
        Args:
            task_id: Unique recurring task identifier
            
        Returns:
            RecurringTaskModel if found, None otherwise
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            # Use GetItem with exact key (Best-practices.md: KeyConditionExpression)
            if self.use_dynamodb:
                response = self.table.get_item(
                    Key={
                        'PK': 'RECURRING',
                        'SK': f'TASK#{task_id}'
                    }
                )
                
                if 'Item' in response:
                    item = response['Item']
                    # Convert DynamoDB item to Pydantic model
                    result = self._item_to_model(item)
                    log_info("Recurring task retrieved from DynamoDB successfully", task_id=task_id)
                    return result
                else:
                    log_info("Recurring task not found in DynamoDB", task_id=task_id)
                    return None
            else:
                # Fall back to in-memory storage
                item = self._stored_tasks.get(task_id)
                if item:
                    return self._item_to_model(item)
                return None
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve recurring task",
                error=str(e),
                task_id=task_id
            )
            raise RuntimeError("An error occurred while retrieving the recurring task")
    
    def get_all_recurring_tasks(self) -> List[RecurringTaskModel]:
        """
        Retrieve all recurring tasks using DynamoDB Query with KeyConditionExpression
        Following Best-practices.md: Use KeyConditionExpression (not scans)
        
        Returns:
            List of all recurring tasks (empty list if none exist)
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            # Use Query with KeyConditionExpression (Best-practices.md requirement)
            if self.use_dynamodb:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': 'RECURRING',
                        ':sk_prefix': 'TASK#'
                    }
                )
                
                # Convert items to Pydantic models
                results = []
                for item in response.get('Items', []):
                    model = self._item_to_model(item)
                    results.append(model)
                
                log_info(
                    "All recurring tasks retrieved from DynamoDB successfully",
                    count=len(results)
                )
                
                return results
            else:
                # Fall back to in-memory storage
                results = []
                for item in self._stored_tasks.values():
                    model = self._item_to_model(item)
                    results.append(model)
                return results
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve all recurring tasks",
                error=str(e)
            )
            raise RuntimeError("An error occurred while retrieving recurring tasks")
    
    def _item_to_model(self, item: dict) -> RecurringTaskModel:
        """
        Convert DynamoDB item to Pydantic model
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            RecurringTaskModel with proper datetime objects
        """
        # Parse ISO datetime strings back to datetime objects
        created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        
        return RecurringTaskModel(
            task_id=item['task_id'],
            task_name=item['task_name'],
            assigned_to=item['assigned_to'],
            frequency=item['frequency'],
            due=item['due'],
            overdue_when=item['overdue_when'],
            category=item['category'],
            status=item['status'],
            created_at=created_at,
            updated_at=updated_at
        )