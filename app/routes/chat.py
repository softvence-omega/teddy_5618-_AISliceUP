from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import ChatRequest, ChatResponse
from app.services.expense_rag import SimpleExpenseRAG
from app.core.utils import validate_and_send_to_history, fetch_chat_history, fetch_user_specific_expense_data
from typing import List, Dict, Any

router = APIRouter(prefix="/chat", tags=["chat"])

# Global RAG instance (will be set during startup)
rag_instance: SimpleExpenseRAG = None


def set_rag_instance(rag: SimpleExpenseRAG):
    """Set the global RAG instance"""
    global rag_instance
    rag_instance = rag


@router.post("/", response_model=ChatResponse)
async def chat_with_teddy(request: ChatRequest):
    """Chat with Teddy, the personal finance assistant"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Validate message
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400, 
            detail="Message is required and cannot be empty"
        )
    
    # Validate user_id - this is critical for chat history collection
    if not request.user_id or not request.user_id.strip():
        raise HTTPException(
            status_code=400, 
            detail="User ID is required and cannot be empty. Chat history cannot be collected without a valid user ID."
        )
    
    try:
        # Create a fresh RAG instance for this specific user request to avoid cross-user contamination
        from app.services.expense_rag import SimpleExpenseRAG
        from app.core.config import API_BASE_URL, OPENAI_API_KEY
        
        # Create a new RAG instance for this user session
        user_rag_instance = SimpleExpenseRAG(API_BASE_URL, OPENAI_API_KEY)
        
        # Load user-specific expense data for this conversation
        user_expense_data = fetch_user_specific_expense_data(request.user_id.strip())
        if user_expense_data:
            # Set user-specific data for this conversation
            user_rag_instance.set_expense_data(user_expense_data)
            print(f"Loaded expense data for user: {request.user_id.strip()}")
        else:
            print(f"No expense data found for user: {request.user_id.strip()}")
            # Don't set any expense data, let the RAG system work with empty data
            user_rag_instance.set_expense_data(None)
        
        # Get response from RAG system - this will validate user_id existence and load user-specific chat history
        assistant_response, validated_user_id = user_rag_instance.chat(request.message.strip(), request.user_id.strip())
        
        if not assistant_response:
            raise HTTPException(status_code=500, detail="No response from assistant")
        
        # Only save to history if we have a validated user_id and it's not a greeting
        if validated_user_id and not any(greeting in request.message.lower() for greeting in ['hi', 'hello', 'hey']):
            success = validate_and_send_to_history(request.message.strip(), assistant_response, validated_user_id)
            if not success:
                print(f"Warning: Failed to save chat history for user {validated_user_id}")
        
        return ChatResponse(
            response=assistant_response,
            status="success"
        )
        
    except ValueError as e:
        # Handle invalid user_id errors and other validation errors
        error_msg = str(e)
        if "Invalid user_id" in error_msg or "User not found" in error_msg:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to fetch chat data. {error_msg}"
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

