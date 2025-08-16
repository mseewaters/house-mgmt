"""
Pytest configuration and fixtures for backend
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'house_mgmt'))

import pytest
import boto3
from moto import mock_aws
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app with mocked database"""
    import os
    
    # Set test environment variable BEFORE importing anything
    original_table = os.environ.get('DYNAMODB_TABLE')
    os.environ['DYNAMODB_TABLE'] = 'house-mgmt-test'
    
    # Clear module cache to force re-initialization with test environment
    import sys
    modules_to_clear = [
        'dal.family_member_dal',
        'dal.recurring_task_dal', 
        'dal.daily_task_dal',
        'services.family_member_service',
        'services.recurring_task_service',
        'routes.family_members',
        'routes.recurring_tasks',
        'routes.daily_tasks'
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    with mock_aws():
        # Create test table for route tests with same schema as production
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='house-mgmt-test',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Force re-import of the main app with new environment
        if 'main' in sys.modules:
            del sys.modules['main']
        from main import app as test_app
        
        client = TestClient(test_app)
        yield client
    
    # Restore original environment
    if original_table:
        os.environ['DYNAMODB_TABLE'] = original_table
    else:
        os.environ.pop('DYNAMODB_TABLE', None)

@pytest.fixture
def mock_dynamodb_table():
    """Create a mocked DynamoDB table for testing"""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table_name = 'house-mgmt-test'
        
        # Create test table with same schema as production
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table_name