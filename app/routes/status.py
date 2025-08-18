from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import StatusResponse
from app.services.expense_rag import SimpleExpenseRAG
from app.core.utils import fetch_expense_data, fetch_user_specific_expense_data, validate_user_exists

router = APIRouter(tags=["status"])

# Global RAG instance (will be set during startup)
rag_instance: SimpleExpenseRAG = None


def set_rag_instance(rag: SimpleExpenseRAG):
    """Set the global RAG instance"""
    global rag_instance
    rag_instance = rag


@router.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint"""
    return StatusResponse(
        status="success",
        message="Teddy - Personal Finance Assistant API is running"
    )


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status and data summary"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        summary = rag_instance.get_data_summary()
        return StatusResponse(
            status="success",
            message="System is operational",
            data_summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/data-summary")
async def get_data_summary():
    """Get summary of available expense data"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        summary = rag_instance.get_data_summary()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting data summary: {str(e)}")


@router.get("/report/collection")
async def get_report_collection(userId: str = Query(..., description="User ID to fetch expense report for")):
    """Get expense report collection for a specific user - user_id in params"""
    if not userId or not userId.strip():
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty. Unable to fetch report data without a valid user ID."
        )
    
    try:
        # Validate user exists first
        is_valid_user, validated_user_id = validate_user_exists(userId.strip())
        
        if not is_valid_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to fetch report data. Invalid user_id: {userId}. User not found."
            )
        
        # Fetch user-specific expense data
        expense_data = fetch_user_specific_expense_data(validated_user_id)
        
        if not expense_data:
            return {
                "userId": validated_user_id,
                "report": "No expense data available",
                "status": "success",
                "message": "User validated but no expense data found",
                "debug_info": f"Attempted to fetch data for user_id: {validated_user_id}"
            }
        
        return {
            "userId": validated_user_id,
            "report": expense_data,
            "status": "success",
            "message": "Report collection retrieved successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to fetch report data. Error: {str(e)}"
        )


@router.get("/report/monthly")
async def get_monthly_report(userId: str = Query(..., description="User ID to fetch monthly expense report for")):
    """Get monthly expense report for a specific user - user_id in params"""
    if not userId or not userId.strip():
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty. Unable to fetch monthly report without a valid user ID."
        )
    
    try:
        # Validate user exists first
        is_valid_user, validated_user_id = validate_user_exists(userId.strip())
        
        if not is_valid_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to fetch monthly report. Invalid user_id: {userId}. User not found."
            )
        
        # Fetch user-specific expense data
        expense_data = fetch_user_specific_expense_data(validated_user_id)
        
        if not expense_data:
            return {
                "userId": validated_user_id,
                "monthlyReport": "No expense data available for this month",
                "status": "success",
                "message": "User validated but no monthly expense data found",
                "debug_info": f"Attempted to fetch data for user_id: {validated_user_id}"
            }
        
        # In a real implementation, you would filter the data for the current month
        # For now, returning all data with a monthly report structure
        return {
            "userId": validated_user_id,
            "monthlyReport": expense_data,
            "reportType": "monthly",
            "status": "success",
            "message": "Monthly report retrieved successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to fetch monthly report. Error: {str(e)}"
        )
