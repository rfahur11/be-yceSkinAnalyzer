"""
Middleware configuration untuk FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import (
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS
)


def setup_middleware(app: FastAPI):
    """
    Setup middleware untuk aplikasi FastAPI.
    
    Args:
        app: Instance FastAPI
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )
