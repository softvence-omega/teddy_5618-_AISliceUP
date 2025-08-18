from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import CreateHistoryRequest, HistoryResponse
from app.core.utils import validate_user_exists, fetch_chat_history, validate_and_send_to_history
from typing import Dict, Any

router = APIRouter(prefix="/history", tags=["history"])


@router.post("/create-history")
async def create_history(request: CreateHistoryRequest):
    """Create/save chat history - user_id in body"""
    
    # Validate all required fields
    if not request.userId or not request.userId.strip():
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty in request body."
        )
    
    if not request.human or not request.human.strip():
        raise HTTPException(
            status_code=400, 
            detail="Human message is required and cannot be empty."
        )
    
    if not request.assistant or not request.assistant.strip():
        raise HTTPException(
            status_code=400, 
            detail="Assistant message is required and cannot be empty."
        )
    
    try:
        # Validate user exists first
        is_valid_user, validated_user_id = validate_user_exists(request.userId.strip())
        
        if not is_valid_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to save chat history. Invalid user_id: {request.userId}. User not found."
            )
        
        # Save the chat history
        success = validate_and_send_to_history(
            request.human.strip(), 
            request.assistant.strip(), 
            validated_user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to save chat history to external service."
            )
        
        return {
            "userId": validated_user_id,
            "status": "success",
            "message": "Chat history saved successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to save chat history. Error: {str(e)}"
        )


@router.get("/get-history", response_model=HistoryResponse)
async def get_history(userId: str = Query(..., description="User ID to fetch chat history for")):
    """Get chat history for a specific user - user_id in params"""
    if not userId or not userId.strip() or userId == "" or userId == "string":
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty. Unable to fetch chat history without a valid user ID."
        )
    
    try:
        chat_history, is_valid_user = fetch_chat_history(userId.strip())
        
        if not is_valid_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to fetch chat history. Invalid user_id: {userId}. User not found."
            )
        
        return HistoryResponse(
            userId=userId.strip(),
            chat_history=chat_history,
            total_conversations=len(chat_history),
            status="success"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to fetch chat history. Error: {str(e)}"
        )


@router.get("/user-summary")
async def get_user_history_summary(userId: str = Query(..., description="User ID to get summary for")):
    """Get summary of user's chat history - user_id in params"""
    if not userId or not userId.strip():
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty."
        )
    
    try:
        # Validate user exists first
        is_valid_user, validated_user_id = validate_user_exists(userId.strip())
        
        if not is_valid_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Invalid user_id: {userId}. User not found."
            )
        
        chat_history, _ = fetch_chat_history(validated_user_id)
        
        return {
            "userId": validated_user_id,
            "total_conversations": len(chat_history),
            "has_history": len(chat_history) > 0,
            "status": "success"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting user summary: {str(e)}"
        )
