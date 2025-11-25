"""
Meals API Routes
Following Best-practices.md: API → Service → DAL separation, structured logging, error handling
Following existing patterns from family_member and daily_task routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
import re

from models.meal import MealModel, MealUpdate
from dal.meal_dal import MealDAL
from utils.logging import log_info, log_error

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("", response_model=List[MealModel])
async def get_meals(
    date_param: Optional[str] = Query(None, alias="date"),
    status: Optional[str] = Query(None, description="Filter by status: available, prepared, expired")
):
    """
    Get meals for a specific date or all meals
    
    Query Parameters:
        date: Optional date in YYYY-MM-DD format. If not provided, returns all meals
        status: Optional status filter (available, prepared, expired)
        
    Returns:
        List of meals for the specified date/status
        
    Raises:
        422: Invalid date format or status
        500: Internal server error
    """
    try:
        # Validate status if provided
        if status and status not in ['available', 'prepared', 'expired']:
            raise HTTPException(
                status_code=422,
                detail="Invalid status. Must be one of: available, prepared, expired"
            )
        
        # Validate date format if provided
        target_date = None
        if date_param:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_param.strip()):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid date format. Expected YYYY-MM-DD"
                )
            
            # Validate date is actually valid
            try:
                datetime.strptime(date_param.strip(), '%Y-%m-%d')
                target_date = date_param.strip()
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid date format. Expected YYYY-MM-DD"
                )
        
        log_info(
            "meals_get_started",
            target_date=target_date,
            status_filter=status,
            date_provided=date_param is not None
        )
        
        # Get meals
        meal_dal = MealDAL()
        
        if target_date:
            meals = meal_dal.get_meals_by_date(target_date)
            # Apply status filter if provided
            if status:
                meals = [meal for meal in meals if meal.status == status]
        else:
            meals = meal_dal.get_all_meals(status_filter=status)
        
        log_info(
            "meals_retrieved_successfully", 
            target_date=target_date,
            status_filter=status,
            meal_count=len(meals)
        )
        
        return meals
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to retrieve meals",
            error=str(e),
            target_date=target_date if 'target_date' in locals() else None,
            status_filter=status
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving meals"
        )


@router.get("/{meal_id}", response_model=MealModel)
async def get_meal_by_id(meal_id: str):
    """
    Get a specific meal by ID
    
    Path Parameters:
        meal_id: ID of the meal to retrieve
        
    Returns:
        Meal details
        
    Raises:
        404: Meal not found
        500: Internal server error
    """
    try:
        log_info("meal_get_by_id_started", meal_id=meal_id)
        
        meal_dal = MealDAL()
        meal = meal_dal.get_meal_by_id(meal_id)
        
        if not meal:
            log_info("meal_not_found", meal_id=meal_id)
            raise HTTPException(
                status_code=404,
                detail="Meal not found"
            )
        
        log_info(
            "meal_retrieved_successfully",
            meal_id=meal_id,
            meal_name=meal.meal_name
        )
        
        return meal
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to retrieve meal",
            error=str(e),
            meal_id=meal_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the meal"
        )


@router.put("/{meal_id}/status", response_model=MealModel)
async def update_meal_status(meal_id: str, meal_update: MealUpdate):
    """
    Update meal preparation status
    
    Path Parameters:
        meal_id: ID of the meal to update
        
    Body:
        MealUpdate with new status
        
    Returns:
        Updated meal with new status and timestamps
        
    Raises:
        404: Meal not found
        422: Invalid status
        500: Internal server error
    """
    try:
        log_info(
            "meal_status_update_started",
            meal_id=meal_id,
            new_status=meal_update.status
        )
        
        # Update meal status
        meal_dal = MealDAL()
        updated_meal = meal_dal.update_meal_status(meal_id, meal_update)
        
        if not updated_meal:
            log_info("meal_not_found_for_update", meal_id=meal_id)
            raise HTTPException(
                status_code=404,
                detail="Meal not found"
            )
        
        log_info(
            "meal_status_updated_successfully",
            meal_id=meal_id,
            meal_name=updated_meal.meal_name,
            new_status=meal_update.status,
            prepared_at=updated_meal.prepared_at.isoformat() if updated_meal.prepared_at else None
        )
        
        return updated_meal
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to update meal status",
            error=str(e),
            meal_id=meal_id,
            new_status=meal_update.status if meal_update else None
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the meal"
        )


@router.put("/{meal_id}/prepare", response_model=MealModel)
async def prepare_meal(meal_id: str):
    """
    Mark a meal as prepared (convenience endpoint)
    
    Path Parameters:
        meal_id: ID of the meal to mark as prepared
        
    Returns:
        Updated meal with prepared status and timestamp
        
    Raises:
        404: Meal not found
        500: Internal server error
    """
    try:
        log_info("meal_prepare_started", meal_id=meal_id)
        
        # Update meal status to prepared
        meal_update = MealUpdate(status="prepared")
        meal_dal = MealDAL()
        updated_meal = meal_dal.update_meal_status(meal_id, meal_update)
        
        if not updated_meal:
            log_info("meal_not_found_for_prepare", meal_id=meal_id)
            raise HTTPException(
                status_code=404,
                detail="Meal not found"
            )
        
        log_info(
            "meal_prepared_successfully",
            meal_id=meal_id,
            meal_name=updated_meal.meal_name,
            prepared_at=updated_meal.prepared_at.isoformat() if updated_meal.prepared_at else None
        )
        
        return updated_meal
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to prepare meal",
            error=str(e),
            meal_id=meal_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while preparing the meal"
        )


@router.put("/{meal_id}/unprepare", response_model=MealModel)
async def unprepare_meal(meal_id: str):
    """
    Mark a meal as available (unprepare)
    
    Path Parameters:
        meal_id: ID of the meal to mark as available
        
    Returns:
        Updated meal with available status
        
    Raises:
        404: Meal not found
        500: Internal server error
    """
    try:
        log_info("meal_unprepare_started", meal_id=meal_id)
        
        # Update meal status to available
        meal_update = MealUpdate(status="available")
        meal_dal = MealDAL()
        updated_meal = meal_dal.update_meal_status(meal_id, meal_update)
        
        if not updated_meal:
            log_info("meal_not_found_for_unprepare", meal_id=meal_id)
            raise HTTPException(
                status_code=404,
                detail="Meal not found"
            )
        
        log_info(
            "meal_unprepared_successfully",
            meal_id=meal_id,
            meal_name=updated_meal.meal_name
        )
        
        return updated_meal
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to unprepare meal",
            error=str(e),
            meal_id=meal_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while unpreparing the meal"
        )


@router.delete("/{meal_id}")
async def delete_meal(meal_id: str):
    """
    Delete a meal
    
    Path Parameters:
        meal_id: ID of the meal to delete
        
    Returns:
        Success message
        
    Raises:
        404: Meal not found
        500: Internal server error
    """
    try:
        log_info("meal_delete_started", meal_id=meal_id)
        
        meal_dal = MealDAL()
        success = meal_dal.delete_meal(meal_id)
        
        if not success:
            log_info("meal_not_found_for_delete", meal_id=meal_id)
            raise HTTPException(
                status_code=404,
                detail="Meal not found"
            )
        
        log_info("meal_deleted_successfully", meal_id=meal_id)
        
        return {"message": "Meal deleted successfully"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to delete meal",
            error=str(e),
            meal_id=meal_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the meal"
        )