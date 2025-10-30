from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
from shortener_app.services.url_service import URLService
from shortener_app.queue.models import HitEvent
from shortener_app.dependencies import get_url_service, get_queue
from shortener_app.queue.strategies import QueueStrategy
from shortener_app.config import settings

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
async def redirect_to_long_url(
    short_code: str,
    request: Request,
    url_service: URLService = Depends(get_url_service),
    queue: QueueStrategy = Depends(get_queue)
):
    """
    Redirect to the original URL.
    
    Flow (optimized for performance):
    1. Get long_url from cache (ASYNC I/O - ~0.1ms)
    2. Publish hit event to queue (ASYNC I/O - ~0.1ms)
    3. Redirect immediately (total ~0.2ms)
    
    Hit tracking is processed asynchronously by worker,
    so it doesn't slow down the redirect!
    
    Note: This is async for cache.get() and queue.publish() (both I/O operations).
    DB query is sync but only happens on cache miss (rare).
    """
    # Step 1: Get long URL using cache-aside pattern (ASYNC)
    long_url = await url_service.get_long_url_for_redirect(short_code)
    
    if not long_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found or inactive"
        )
    
    # Step 2: Publish hit event to queue (async, non-blocking)
    # Worker will process this and update database
    hit_event = HitEvent(
        short_code=short_code,
        timestamp=datetime.now(timezone.utc),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )
    
    # Publish to queue (doesn't block - fire and forget)
    await queue.publish(settings.queue_name, hit_event)
    
    # Step 3: Redirect immediately (user doesn't wait for DB write!)
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)
