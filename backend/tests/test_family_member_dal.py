"""
TDD: Family Member DAL Tests - Complete Coverage
Following TDD: Red → Green → Refactor
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone

@mock_aws
def test_create_family_member_person_success(mock_dynamodb_table):
    """Test creating a person family member successfully"""
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    # Arrange
    dal = FamilyMemberDAL(table_name=mock_dynamodb_table)
    member_data = FamilyMemberCreate(
        name="Sarah",
        member_type="Person",
        status="Active"
    )
    
    # Act
    result = dal.create_family_member(member_data)
    
    # Assert
    assert result.member_id is not None
    assert result.name == "Sarah"
    assert result.member_type == "Person"
    assert result.status == "Active"


@mock_aws
def test_create_family_member_pet_success(mock_dynamodb_table):
    """Test creating a pet family member successfully"""
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    # Arrange
    dal = FamilyMemberDAL(table_name=mock_dynamodb_table)
    member_data = FamilyMemberCreate(
        name="Fluffy",
        member_type="Pet",
        pet_type="cat",
        status="Active"
    )
    
    # Act
    result = dal.create_family_member(member_data)
    
    # Assert
    assert result.member_id is not None
    assert result.name == "Fluffy"
    assert result.member_type == "Pet"
    assert result.pet_type == "cat"
    assert result.status == "Active"


@mock_aws
def test_create_and_retrieve_family_member():
    """Test creating a family member and retrieving it from DynamoDB"""
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    # Setup mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='house-mgmt-test',
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
    
    # Arrange
    dal = FamilyMemberDAL(table_name='house-mgmt-test')
    member_data = FamilyMemberCreate(
        name="Mike",
        member_type="Person",
        status="Active"
    )
    
    # Act
    created_member = dal.create_family_member(member_data)
    retrieved_member = dal.get_family_member_by_id(created_member.member_id)
    
    # Assert
    assert retrieved_member is not None
    assert retrieved_member.member_id == created_member.member_id
    assert retrieved_member.name == "Mike"
    assert retrieved_member.member_type == "Person"
    assert retrieved_member.status == "Active"


@mock_aws
def test_family_member_has_utc_timestamps(mock_dynamodb_table):
    """Test that family members have proper UTC timestamps (Best-practices.md requirement)"""
    from dal.family_member_dal import FamilyMemberDAL
    from models.family_member import FamilyMemberCreate
    
    # Arrange
    dal = FamilyMemberDAL(table_name=mock_dynamodb_table)
    member_data = FamilyMemberCreate(
        name="Sarah",
        member_type="Person",
        status="Active"
    )
    before_creation = datetime.now(timezone.utc)
    
    # Act
    result = dal.create_family_member(member_data)
    
    # Assert - should have UTC timestamps
    assert hasattr(result, 'created_at'), "Family member should have created_at timestamp"
    assert hasattr(result, 'updated_at'), "Family member should have updated_at timestamp"
    assert result.created_at.tzinfo == timezone.utc, "created_at must be timezone-aware UTC"
    assert result.updated_at.tzinfo == timezone.utc, "updated_at must be timezone-aware UTC"
    assert result.created_at >= before_creation, "created_at should be recent"
    assert result.updated_at >= before_creation, "updated_at should be recent"


# NON-HAPPY PATH TESTS

@mock_aws
def test_get_family_member_not_found(mock_dynamodb_table):
    """Test retrieving non-existent family member returns None"""
    from dal.family_member_dal import FamilyMemberDAL
    
    # Arrange
    dal = FamilyMemberDAL(table_name=mock_dynamodb_table)
    fake_id = "non-existent-id"
    
    # Act
    result = dal.get_family_member_by_id(fake_id)
    
    # Assert
    assert result is None


def test_create_family_member_empty_name_validation():
    """Test validation error when name is empty"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="",
            member_type="Person",
            status="Active"
        )
    
    assert "name cannot be empty" in str(exc_info.value).lower()


def test_create_family_member_name_too_long_validation():
    """Test validation error when name exceeds 15 characters"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="ThisNameIsTooLongForValidation",  # >15 chars
            member_type="Person",
            status="Active"
        )
    
    assert "15 characters" in str(exc_info.value)


def test_create_pet_without_pet_type_validation():
    """Test validation error when Pet type missing pet_type"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="Buddy",
            member_type="Pet",
            status="Active"
            # Missing pet_type - should cause validation error
        )
    
    assert "pet_type is required when member_type is Pet" in str(exc_info.value)


def test_create_person_with_pet_type_validation():
    """Test validation error when Person has pet_type"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="Sarah",
            member_type="Person",
            pet_type="dog",  # Should not be provided for Person
            status="Active"
        )
    
    assert "pet_type should not be provided when member_type is Person" in str(exc_info.value)


def test_invalid_member_type_validation():
    """Test validation error for invalid member_type"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="Test",
            member_type="Robot",  # Invalid type
            status="Active"
        )
    
    # Should mention valid options
    error_str = str(exc_info.value)
    assert "Person" in error_str or "Pet" in error_str


def test_invalid_status_validation():
    """Test validation error for invalid status"""
    from models.family_member import FamilyMemberCreate
    from pydantic import ValidationError
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        FamilyMemberCreate(
            name="Test",
            member_type="Person",
            status="Maybe"  # Invalid status
        )
    
    # Should mention valid options
    error_str = str(exc_info.value)
    assert "Active" in error_str or "Inactive" in error_str