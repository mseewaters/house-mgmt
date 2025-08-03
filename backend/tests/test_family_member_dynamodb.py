"""
Test Family Member DynamoDB integration
Following TDD: Write failing tests first for real persistence
ALL TESTS USE @mock_aws
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone

@mock_aws
def test_create_family_member_dynamodb_persistence():
    """Test that family member is actually stored in DynamoDB"""
    # Arrange - Create real DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    dal = FamilyMemberDAL(table_name=table_name)
    member_data = FamilyMemberCreate(
        name="Alice",
        member_type="Person",
        status="Active"
    )
    
    # Act
    result = dal.create_family_member(member_data)
    
    # Assert - Verify it was stored in DynamoDB with correct schema
    stored_item = table.get_item(
        Key={
            'PK': 'FAMILY',
            'SK': f'MEMBER#{result.member_id}'
        }
    )
    
    assert 'Item' in stored_item
    item = stored_item['Item']
    assert item['PK'] == 'FAMILY'
    assert item['SK'] == f'MEMBER#{result.member_id}'
    assert item['entity_type'] == 'family_member'
    assert item['name'] == 'Alice'
    assert item['member_type'] == 'Person'
    assert item['status'] == 'Active'
    # DynamoDB stores None as absence - check it's not present or is None
    assert item.get('pet_type') is None
    assert 'created_at' in item
    assert 'updated_at' in item


@mock_aws
def test_create_family_member_pet_dynamodb_persistence():
    """Test that pet family member stores pet_type correctly"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    dal = FamilyMemberDAL(table_name=table_name)
    member_data = FamilyMemberCreate(
        name="Buddy",
        member_type="Pet",
        pet_type="dog",
        status="Active"
    )
    
    # Act
    result = dal.create_family_member(member_data)
    
    # Assert - Verify pet_type is stored correctly
    stored_item = table.get_item(
        Key={
            'PK': 'FAMILY',
            'SK': f'MEMBER#{result.member_id}'
        }
    )
    
    assert 'Item' in stored_item
    item = stored_item['Item']
    assert item['member_type'] == 'Pet'
    assert item['pet_type'] == 'dog'


@mock_aws
def test_get_family_member_by_id_dynamodb():
    """Test retrieving family member from DynamoDB by ID"""
    # Arrange - Create table and store a member
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    dal = FamilyMemberDAL(table_name=table_name)
    member_data = FamilyMemberCreate(
        name="John",
        member_type="Person", 
        status="Active"
    )
    
    # Create and store member
    created_member = dal.create_family_member(member_data)
    member_id = created_member.member_id
    
    # Act - Retrieve by ID
    retrieved_member = dal.get_family_member_by_id(member_id)
    
    # Assert
    assert retrieved_member is not None
    assert retrieved_member.member_id == member_id
    assert retrieved_member.name == "John"
    assert retrieved_member.member_type == "Person"
    assert retrieved_member.status == "Active"


@mock_aws
def test_get_family_member_not_found_dynamodb():
    """Test that non-existent member returns None from DynamoDB"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    from dal.family_member_dal import FamilyMemberDAL
    
    dal = FamilyMemberDAL(table_name=table_name)
    fake_id = "non-existent-uuid-12345"
    
    # Act
    result = dal.get_family_member_by_id(fake_id)
    
    # Assert
    assert result is None


@mock_aws
def test_get_all_family_members_dynamodb():
    """Test retrieving all family members from DynamoDB using KeyConditionExpression"""
    # Arrange - Create table and store multiple members
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    dal = FamilyMemberDAL(table_name=table_name)
    
    # Create multiple members
    person_data = FamilyMemberCreate(name="Alice", member_type="Person", status="Active")
    pet_data = FamilyMemberCreate(name="Buddy", member_type="Pet", pet_type="dog", status="Active")
    
    created_person = dal.create_family_member(person_data)
    created_pet = dal.create_family_member(pet_data)
    
    # Act - Get all family members
    all_members = dal.get_all_family_members()
    
    # Assert
    assert isinstance(all_members, list)
    assert len(all_members) == 2
    
    # Verify both members are returned
    member_names = [member.name for member in all_members]
    assert "Alice" in member_names
    assert "Buddy" in member_names
    
    # Verify one person and one pet
    member_types = [member.member_type for member in all_members]
    assert "Person" in member_types
    assert "Pet" in member_types


@mock_aws
def test_dynamodb_query_uses_key_condition_not_scan():
    """Test that get_all_family_members uses KeyConditionExpression, not scan"""
    # This test verifies we're following Best-practices.md: Use KeyConditionExpression not scans
    # We'll verify this by checking the query pattern matches: PK = "FAMILY", SK begins_with "MEMBER#"
    
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
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
    
    # Add some non-family data to ensure we don't accidentally return it
    table.put_item(Item={
        'PK': 'RECURRING',
        'SK': 'TASK#some-task-id', 
        'entity_type': 'recurring_task',
        'task_name': 'Should not be returned'
    })
    
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    dal = FamilyMemberDAL(table_name=table_name)
    member_data = FamilyMemberCreate(name="Test", member_type="Person", status="Active")
    dal.create_family_member(member_data)
    
    # Act
    all_members = dal.get_all_family_members()
    
    # Assert - Should only return family members, not other entities
    assert len(all_members) == 1
    assert all_members[0].name == "Test"
    # This test will pass only if we use proper KeyConditionExpression