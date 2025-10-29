from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shortener_app.database.connection import get_db
from shortener_app.schemas.url import URLCreate, URLResponse, URLStats
from shortener_app.models.url import URL
from shortener_app.services.url_service import URLService

router = APIRouter(prefix="/urls", tags=["urls"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(
    url_data: URLCreate,
    db: Session = Depends(get_db)
):
    """Create a new short URL"""
    url_service = URLService(db)
    return url_service.create_short_url(url_data.long_url)


@router.get("/{short_code}", response_model=URLResponse)
def get_url_info(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Get information about a short URL"""
    url_service = URLService(db)
    url = url_service.get_url_by_short_code(short_code)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    return url


@router.get("/{short_code}/stats", response_model=URLStats)
def get_url_stats(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a short URL"""
    url_service = URLService(db)
    stats = url_service.get_url_stats(short_code)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    return stats


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Delete a short URL"""
    url_service = URLService(db)
    success = url_service.delete_url(short_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
