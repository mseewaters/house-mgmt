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
from boto3.dynamodb.conditions import Key
from models.recurring_task import RecurringTaskCreate, RecurringTaskModel
from utils.logging import log_info, log_error


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
                'GSI1PK': f'MEMBER#{task_data.assigned_to}',  # ADD THIS LINE
                'GSI1SK': f'RECURRING#{task_id}',             # ADD THIS LINE
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
        # Parse ISO datetime strings back to datetime objects (handle missing created_at)
        created_at_str = item.get('created_at', item.get('updated_at'))
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
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
    
    def update_recurring_task(self, task_id: str, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """
        Update an existing recurring task in DynamoDB or in-memory storage
        
        Args:
            task_id: UUID of the recurring task to update
            task_data: Validated recurring task update data
            
        Returns:
            Updated recurring task with new timestamps
            
        Raises:
            ValueError: If recurring task not found
            Exception: For database errors
        """
        if self.use_dynamodb:
            return self._update_recurring_task_dynamodb(task_id, task_data)
        else:
            return self._update_recurring_task_memory(task_id, task_data)


    def _update_recurring_task_dynamodb(self, task_id: str, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """Update recurring task in DynamoDB"""
        try:
            # First check if task exists
            existing_task = self.get_recurring_task_by_id(task_id)
            if existing_task is None:
                raise ValueError(f"Recurring task not found: {task_id}")
            
            # Prepare update data with new timestamp
            now = datetime.now(timezone.utc)
            
            # Build update expression
            update_expression = """
                SET task_name = :task_name,
                    assigned_to = :assigned_to,
                    frequency = :frequency,
                    due = :due,
                    overdue_when = :overdue_when,
                    category = :category,
                    #status = :status,
                    updated_at = :updated_at
            """
            
            expression_attribute_names = {
                "#status": "status"  # 'status' is a reserved word in DynamoDB
            }
            
            expression_attribute_values = {
                ":task_name": task_data.task_name,
                ":assigned_to": task_data.assigned_to,
                ":frequency": task_data.frequency,
                ":due": task_data.due,
                ":overdue_when": task_data.overdue_when,
                ":category": task_data.category,
                ":status": task_data.status,
                ":updated_at": now.isoformat()
            }
            
            # Perform the update
            response = self.table.update_item(
                Key={
                    'PK': 'RECURRING',
                    'SK': f'TASK#{task_id}'
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            # Transform response to RecurringTaskModel
            updated_item = response['Attributes']
            return RecurringTaskModel(
                task_id=updated_item['task_id'],
                task_name=updated_item['task_name'],
                assigned_to=updated_item['assigned_to'],
                frequency=updated_item['frequency'],
                due=updated_item['due'],
                overdue_when=updated_item['overdue_when'],
                category=updated_item['category'],
                status=updated_item['status'],
                created_at=datetime.fromisoformat(updated_item['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(updated_item['updated_at'].replace('Z', '+00:00'))
            )
            
        except self.table.meta.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Recurring task not found: {task_id}")
            raise


    def _update_recurring_task_memory(self, task_id: str, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """Update recurring task in in-memory storage"""
        # Find existing task
        for i, task in enumerate(self.recurring_tasks):
            if task.task_id == task_id:
                # Update with new data and timestamp
                updated_task = RecurringTaskModel(
                    task_id=task_id,
                    task_name=task_data.task_name,
                    assigned_to=task_data.assigned_to,
                    frequency=task_data.frequency,
                    due=task_data.due,
                    overdue_when=task_data.overdue_when,
                    category=task_data.category,
                    status=task_data.status,
                    created_at=task.created_at,  # Keep original created_at
                    updated_at=datetime.now(timezone.utc)
                )
                self.recurring_tasks[i] = updated_task
                return updated_task
        
        raise ValueError(f"Recurring task not found: {task_id}")


    def delete_recurring_task(self, task_id: str) -> None:
        """
        Delete a recurring task from DynamoDB or in-memory storage
        
        Args:
            task_id: UUID of the recurring task to delete
            
        Raises:
            ValueError: If recurring task not found
            Exception: For database errors
        """
        if self.use_dynamodb:
            self._delete_recurring_task_dynamodb(task_id)
        else:
            self._delete_recurring_task_memory(task_id)


    def _delete_recurring_task_dynamodb(self, task_id: str) -> None:
        """Delete recurring task from DynamoDB"""
        try:
            # First check if task exists
            self.get_recurring_task_by_id(task_id)
            
            # Delete the item
            self.table.delete_item(
                Key={
                    'PK': 'RECURRING',
                    'SK': f'TASK#{task_id}'
                }
            )
            
        except ValueError:
            # Task not found - re-raise
            raise


    def _delete_recurring_task_memory(self, task_id: str) -> None:
        """Delete recurring task from in-memory storage"""
        for i, task in enumerate(self.recurring_tasks):
            if task.task_id == task_id:
                del self.recurring_tasks[i]
                return
        
        raise ValueError(f"Recurring task not found: {task_id}")


    def get_recurring_tasks_by_member(self, member_id: str) -> List[RecurringTaskModel]:
        """
        Get all recurring tasks assigned to a specific family member
        Used by family member deletion to check for associated tasks
        
        Args:
            member_id: UUID of the family member
            
        Returns:
            List of recurring tasks assigned to this member
            
        Raises:
            ValueError: If no tasks found (for business logic checks)
        """
        if self.use_dynamodb:
            return self._get_recurring_tasks_by_member_dynamodb(member_id)
        else:
            return self._get_recurring_tasks_by_member_memory(member_id)


    def _get_recurring_tasks_by_member_dynamodb(self, member_id: str) -> List[RecurringTaskModel]:
        """Get member's recurring tasks from DynamoDB using GSI"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f'MEMBER#{member_id}') & Key('GSI1SK').begins_with('RECURRING#')
            )
            
            tasks = []
            for item in response['Items']:
                task = RecurringTaskModel(
                    task_id=item['task_id'],
                    task_name=item['task_name'],
                    assigned_to=item['assigned_to'],
                    frequency=item['frequency'],
                    due=item['due'],
                    overdue_when=item['overdue_when'],
                    category=item['category'],
                    status=item['status'],
                    created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            raise Exception(f"Failed to query recurring tasks by member: {str(e)}")


    def _get_recurring_tasks_by_member_memory(self, member_id: str) -> List[RecurringTaskModel]:
        """Get member's recurring tasks from in-memory storage"""
        return [task for task in self.recurring_tasks if task.assigned_to == member_id]