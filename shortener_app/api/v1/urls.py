from fastapi import APIRouter, Depends, HTTPException, status
from shortener_app.schemas.url import URLCreate, URLResponse, URLStats
from shortener_app.services.url_service import URLService
from shortener_app.dependencies import get_url_service

router = APIRouter(prefix="/urls", tags=["urls"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_data: URLCreate,
    url_service: URLService = Depends(get_url_service)
):
    """Create a new short URL (async for cache I/O)"""
    return await url_service.create_short_url(url_data.long_url)


@router.get("/{short_code}", response_model=URLResponse)
async def get_url_info(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """Get information about a short URL (async for interface consistency)"""
    url = await url_service.get_url_by_short_code(short_code)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    return url


@router.get("/{short_code}/stats", response_model=URLStats)
async def get_url_stats(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """Get statistics for a short URL (async for interface consistency)"""
    stats = await url_service.get_url_stats(short_code)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    return stats


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """Delete a short URL (async for cache invalidation)"""
    success = await url_service.delete_url(short_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
