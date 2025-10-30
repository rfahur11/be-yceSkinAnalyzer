"""
Route handlers untuk health check
"""
from fastapi import APIRouter
from services.token_manager import token_manager

router = APIRouter(tags=["Health Check"])


@router.get("/")
async def root():
    """Root endpoint untuk health check."""
    return {
        "message": "Perfect Corp Skin Analysis API",
        "status": "running",
        "token_status": "valid" if token_manager.has_token() else "no token"
    }


@router.get("/health")
async def health_check():
    """Endpoint untuk mengecek kesehatan aplikasi."""
    return {
        "status": "healthy",
        "service": "Perfect Corp Skin Analysis API",
        "version": "1.0.0"
    }
