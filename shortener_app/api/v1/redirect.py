from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from shortener_app.database.connection import get_db
from shortener_app.services.url_service import URLService

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
def redirect_to_long_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Redirect to the original URL"""
    url_service = URLService(db)
    long_url = url_service.redirect_url(short_code)
    
    if not long_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found or inactive"
        )
    
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)
