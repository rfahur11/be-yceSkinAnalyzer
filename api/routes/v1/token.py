"""
Route handlers untuk token management - API v1
"""
from fastapi import APIRouter
from services.token_manager import token_manager

router = APIRouter(prefix="/v1/token", tags=["V1 - Token Management"])


@router.post("/get")
async def get_token():
    """
    Endpoint untuk mendapatkan access_token dari Perfect Corp API v1.0.
    
    Returns:
        Dict berisi access_token dan message
    """
    access_token = await token_manager.get_token()
    
    return {
        "access_token": access_token,
        "message": "Token berhasil didapatkan"
    }


@router.get("/status")
async def token_status():
    """
    Endpoint untuk mengecek status token saat ini.
    
    Returns:
        Dict berisi informasi status token
    """
    return token_manager.get_status()
