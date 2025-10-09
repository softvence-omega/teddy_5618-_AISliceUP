import asyncio
import requests
from app.services.message import generate_llm_summary
from fastapi import APIRouter, HTTPException, Query
from typing import List

router = APIRouter(prefix="/message", tags=["group_message"])

@router.post("/summary", response_model=List[str])
async def get_group_summary(user_id: str = Query(..., description="The user's unique identifier", min_length=1)):
    """Generate a concise summary of group expenses for the user"""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required and cannot be empty")
    
    try:
        # Wrap synchronous fetch in a thread
        summaries = await asyncio.to_thread(generate_llm_summary, user_id.strip())
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
