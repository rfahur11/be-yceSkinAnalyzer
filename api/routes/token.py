"""
Route handlers untuk token management
"""
from fastapi import APIRouter
from services.token_manager import token_manager

router = APIRouter(prefix="/token", tags=["Token Management"])


@router.post("/get")
async def get_token():
    """
    Endpoint untuk mendapatkan access_token dari Perfect Corp API.
    
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
