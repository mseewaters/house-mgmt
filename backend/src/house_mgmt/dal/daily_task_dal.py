"""
Daily Task Data Access Layer with DynamoDB implementation
Following Best-practices.md: KeyConditionExpression (not scans), UTC timestamps, structured logging
Following technical design schema: PK = "DAILY#date", SK = "TASK#uuid"
"""
import boto3
import os
from typing import List, Optional, Dict
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from house_mgmt.models.daily_task import DailyTaskCreate, DailyTaskModel
from house_mgmt.utils.logging import log_info, log_error


class DailyTaskDAL:
    """DAL for daily task operations with DynamoDB persistence"""
    
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
            self._stored_tasks = {}  # Fresh dictionary for each DAL instance
            log_info("Using in-memory storage fallback", error=str(e))
    
    def create_daily_task(self, task_data: DailyTaskCreate) -> DailyTaskModel:
        """
        Create daily task with DynamoDB persistence and UTC timestamps
        
        Args:
            task_data: Validated Pydantic daily task creation data
            
        Returns:
            DailyTaskModel with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If unexpected error occurs
        """
        try:
            import uuid
            
            # Generate UTC timestamps (Best-practices.md requirement)
            now = datetime.now(timezone.utc)
            task_id = str(uuid.uuid4())
            
            # Calculate overdue and clear timestamps based on overdue_when
            overdue_delta_hours = {
                "Immediate": 0,
                "1 hour": 1,
                "6 hours": 6, 
                "1 day": 24,
                "3 days": 72,
                "7 days": 168
            }
            
            from datetime import timedelta
            overdue_hours = overdue_delta_hours.get(task_data.overdue_when, 1)
            overdue_at = now + timedelta(hours=overdue_hours)
            clear_at = now + timedelta(days=1)  # Clear next day by default
            
            # Create DynamoDB item following technical design schema
            item = {
                'PK': f'DAILY#{task_data.date}',
                'SK': f'TASK#{task_id}',
                'GSI1PK': f'MEMBER#{task_data.assigned_to}',
                'GSI1SK': f'DAILY#{task_data.date}',
                'entity_type': 'daily_task',
                'task_id': task_id,
                'task_name': task_data.task_name,
                'assigned_to': task_data.assigned_to,
                'recurring_task_id': task_data.recurring_task_id,
                'date': task_data.date,
                'due_time': task_data.due_time,
                'status': task_data.status,
                'category': task_data.category,
                'overdue_when': task_data.overdue_when,
                'completed_at': None,
                'generated_at': now.isoformat(),
                'overdue_at': overdue_at.isoformat(),
                'clear_at': clear_at.isoformat(),
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Store in DynamoDB or fallback to in-memory
            if self.use_dynamodb:
                self.table.put_item(Item=item)
                log_info(
                    "Daily task stored in DynamoDB successfully",
                    task_id=task_id,
                    table_name=self.table_name
                )
            else:
                # Fall back to in-memory storage
                self._stored_tasks[task_id] = item
                log_info(
                    "Daily task stored in memory (DynamoDB not available)",
                    task_id=task_id
                )
            
            # Create return model with proper datetime objects
            result = DailyTaskModel(
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                recurring_task_id=task_data.recurring_task_id,
                date=task_data.date,
                due_time=task_data.due_time,
                status=task_data.status,
                category=task_data.category,
                overdue_when=task_data.overdue_when,
                completed_at=None,
                generated_at=now,
                overdue_at=overdue_at,
                clear_at=clear_at,
                created_at=now,
                updated_at=now
            )
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Daily task created successfully",
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                date=task_data.date
            )
            
            return result
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create daily task",
                error=str(e),
                task_name=task_data.task_name if task_data else None
            )
            raise RuntimeError("An error occurred while creating the daily task")
    
    def get_daily_task_by_id(self, task_id: str) -> Optional[DailyTaskModel]:
        """
        Retrieve daily task by ID
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            DailyTaskModel if found, None otherwise
        """
        try:
            if self.use_dynamodb:
                # Need to scan since we don't know the date (PK)
                # This is not ideal but needed for get_by_id functionality
                response = self.table.scan(
                    FilterExpression='task_id = :task_id',
                    ExpressionAttributeValues={':task_id': task_id}
                )
                items = response.get('Items', [])
                if not items:
                    return None
                item = items[0]
            else:
                # In-memory storage
                item = self._stored_tasks.get(task_id)
                if not item:
                    return None
            
            # Convert to model
            return self._item_to_model(item)
            
        except Exception as e:
            log_error("Failed to retrieve daily task", error=str(e), task_id=task_id)
            return None
    
    def get_daily_tasks_by_date(self, date: str) -> List[DailyTaskModel]:
        """
        Get all daily tasks for a specific date using KeyConditionExpression
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of DailyTaskModel for the specified date
        """
        try:
            if self.use_dynamodb:
                # Use KeyConditionExpression following Best-practices.md
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                    ExpressionAttributeValues={
                        ':pk': f'DAILY#{date}',
                        ':sk': 'TASK#'
                    }
                )
                items = response.get('Items', [])
            else:
                # In-memory storage - filter by PK to match DynamoDB behavior
                target_pk = f'DAILY#{date}'
                items = [
                    item for item in self._stored_tasks.values()
                    if item.get('PK') == target_pk and item.get('SK', '').startswith('TASK#')
                ]
                
                # Debug logging to see what we're filtering
                log_info(
                    "Filtering daily tasks by date",
                    target_date=date,
                    target_pk=target_pk,
                    total_stored=len(self._stored_tasks),
                    matching_items=len(items),
                    all_pks=[item.get('PK') for item in self._stored_tasks.values()]
                )
            
            # Convert to models
            return [self._item_to_model(item) for item in items]
            
        except Exception as e:
            log_error("Failed to retrieve daily tasks by date", error=str(e), date=date)
            return []
    
    def update_daily_task_status(self, task_id: str, status: str, completed_at: Optional[datetime] = None) -> Optional[DailyTaskModel]:
        """
        Update daily task status and completion timestamp
        
        Args:
            task_id: Task ID to update
            status: New status
            completed_at: Completion timestamp (if status is Completed)
            
        Returns:
            Updated DailyTaskModel if successful, None otherwise
        """
        try:
            # First get the current task to know its PK
            current_task = self.get_daily_task_by_id(task_id)
            if not current_task:
                return None
            
            now = datetime.now(timezone.utc)
            
            if self.use_dynamodb:
                # Update in DynamoDB
                update_expression = "SET #status = :status, updated_at = :updated_at"
                expression_values = {
                    ':status': status,
                    ':updated_at': now.isoformat()
                }
                expression_names = {'#status': 'status'}
                
                if completed_at:
                    update_expression += ", completed_at = :completed_at"
                    expression_values[':completed_at'] = completed_at.isoformat()
                
                response = self.table.update_item(
                    Key={
                        'PK': f'DAILY#{current_task.date}',
                        'SK': f'TASK#{task_id}'
                    },
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ExpressionAttributeNames=expression_names,
                    ReturnValues='ALL_NEW'
                )
                updated_item = response['Attributes']
            else:
                # Update in-memory storage
                item = self._stored_tasks[task_id]
                item['status'] = status
                item['updated_at'] = now.isoformat()
                if completed_at:
                    item['completed_at'] = completed_at.isoformat()
                updated_item = item
            
            return self._item_to_model(updated_item)
            
        except Exception as e:
            log_error("Failed to update daily task status", error=str(e), task_id=task_id)
            return None
    
    def _item_to_model(self, item: Dict) -> DailyTaskModel:
        """Convert DynamoDB item to DailyTaskModel"""
        from datetime import datetime
        
        return DailyTaskModel(
            task_id=item['task_id'],
            task_name=item['task_name'],
            assigned_to=item['assigned_to'],
            recurring_task_id=item['recurring_task_id'],
            date=item['date'],
            due_time=item['due_time'],
            status=item['status'],
            category=item['category'],
            overdue_when=item['overdue_when'],
            completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None,
            generated_at=datetime.fromisoformat(item['generated_at']),
            overdue_at=datetime.fromisoformat(item['overdue_at']),
            clear_at=datetime.fromisoformat(item['clear_at']),
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at'])
        )