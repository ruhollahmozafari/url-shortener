from fastapi import FastAPI
from shortener_app.config import settings
from shortener_app.database.connection import engine, Base
from shortener_app.api.v1 import urls, redirect

# Import models to ensure they're registered with Base
from shortener_app.models import URL

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A URL shortener service built with FastAPI",
    debug=settings.debug
)

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.environment}




######## Include routers
app.include_router(urls.router, prefix="/api/v1")
app.include_router(redirect.router)


