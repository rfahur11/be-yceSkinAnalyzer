"""
Error handlers untuk aplikasi FastAPI
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def setup_error_handlers(app: FastAPI):
    """
    Setup error handlers untuk aplikasi FastAPI.
    
    Args:
        app: Instance FastAPI
    """
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        """Handler untuk 404 Not Found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Endpoint yang Anda cari tidak ditemukan",
                "status_code": 404
            }
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        """Handler untuk 500 Internal Server errors."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "Terjadi kesalahan pada server",
                "status_code": 500
            }
        )
