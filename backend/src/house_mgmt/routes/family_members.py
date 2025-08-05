"""
Family Member API routes
Following Best-practices.md: API → Service → DAL architecture
"""
from typing import List
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from house_mgmt.models.family_member import FamilyMemberCreate, FamilyMemberModel
from house_mgmt.services.family_member_service import FamilyMemberService
from house_mgmt.utils.logging import log_info, log_error

router = APIRouter(prefix="/api", tags=["family-members"])

# Initialize service
family_service = FamilyMemberService()


@router.post("/family-members", status_code=status.HTTP_201_CREATED)
async def create_family_member(
    request: Request,
    family_member_data: FamilyMemberCreate
) -> FamilyMemberModel:
    """
    Create a new family member
    
    Args:
        request: FastAPI request object (for correlation ID)
        family_member_data: Validated family member data
        
    Returns:
        Created family member with timestamps
        
    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "create_family_member_requested",
            name=family_member_data.name,
            member_type=family_member_data.member_type,
            correlation_id=correlation_id
        )
        
        # Create via service layer
        result = family_service.create_family_member(family_member_data)
        
        log_info(
            "create_family_member_success",
            member_id=result.member_id,
            name=result.name,
            correlation_id=correlation_id
        )
        
        return result
        
    except ValueError as e:
        # Business logic validation errors
        log_error(
            "create_family_member_validation_error",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
        
    except Exception as e:
        # Internal server errors
        log_error(
            "create_family_member_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the family member"
        )


@router.get("/family-members/{member_id}")
async def get_family_member(
    request: Request,
    member_id: str
) -> FamilyMemberModel:
    """
    Get family member by ID
    
    Args:
        request: FastAPI request object (for correlation ID)
        member_id: Family member UUID
        
    Returns:
        Family member data
        
    Raises:
        HTTPException: 404 if not found, 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "get_family_member_requested",
            member_id=member_id,
            correlation_id=correlation_id
        )
        
        # Retrieve via service layer
        result = family_service.get_family_member_by_id(member_id)
        
        if result is None:
            log_info(
                "get_family_member_not_found",
                member_id=member_id,
                correlation_id=correlation_id
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Family member not found"}
            )
        
        log_info(
            "get_family_member_success",
            member_id=member_id,
            name=result.name,
            correlation_id=correlation_id
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
        
    except Exception as e:
        # Internal server errors
        log_error(
            "get_family_member_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            member_id=member_id,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the family member"
        )


@router.get("/family-members")
async def get_all_family_members(request: Request) -> List[FamilyMemberModel]:
    """
    Get all family members
    
    Args:
        request: FastAPI request object (for correlation ID)
        
    Returns:
        List of all family members
        
    Raises:
        HTTPException: 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "get_all_family_members_requested",
            correlation_id=correlation_id
        )
        
        # Retrieve via service layer
        results = family_service.get_all_family_members()
        
        log_info(
            "get_all_family_members_success",
            count=len(results),
            correlation_id=correlation_id
        )
        
        return results
        
    except Exception as e:
        # Internal server errors
        log_error(
            "get_all_family_members_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving family members"
        )