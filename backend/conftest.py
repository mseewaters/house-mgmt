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
    """Create a test client for the FastAPI app"""
    return TestClient(app)

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
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table_name