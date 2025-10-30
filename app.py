"""
Main FastAPI application
"""
from fastapi import FastAPI
from api.middleware import setup_middleware
from api.error_handlers import setup_error_handlers
from api.routes import health

# Import V1 routes
from api.routes.v1 import token as token_v1
from api.routes.v1 import upload as upload_v1
from api.routes.v1 import analysis as analysis_v1

# Import V2 routes
from api.routes.v2 import upload as upload_v2
from api.routes.v2 import analysis as analysis_v2


def create_app() -> FastAPI:
    """
    Factory function untuk membuat instance FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Perfect Corp Skin Analysis API",
        description="""
        API untuk integrasi dengan YouCam AI Skin Analysis dari Perfect Corp.
        
        ## API Versions
        
        ### V1 (Legacy)
        - Token-based authentication
        - Direct file upload melalui server
        - Analysis task creation dan polling
        
        ### V2 (Recommended)
        - API Key authentication
        - Presigned URL upload (lebih cepat)
        - Improved error handling
        """,
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Register common routes
    app.include_router(health.router)
    
    # Register V1 routes
    app.include_router(token_v1.router)
    app.include_router(upload_v1.router)
    app.include_router(analysis_v1.router)
    
    # Register V2 routes
    app.include_router(upload_v2.router)
    app.include_router(analysis_v2.router)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    from config.settings import HOST, PORT
    
    uvicorn.run(
        "app:app",  # String module:app untuk enable reload
        host=HOST,
        port=PORT,
        reload=True  # Auto-reload saat ada perubahan kode
    )
