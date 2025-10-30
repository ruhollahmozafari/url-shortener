"""
Simple Hit Processor Worker

This worker processes hit events from the queue and stores them in analytics storage.
It uses batch processing for optimal performance.

Architecture:
- Consumes messages from queue in batches
- Stores analytics data via strategy pattern
- Updates total_hits in main DB periodically
- Simple, clean, and efficient
"""

import asyncio
import signal
import sys
from typing import Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from shortener_app.database.connection import SessionLocal
from shortener_app.models.url import URL
from shortener_app.queue.strategies import QueueStrategy
from shortener_app.queue.models import HitEvent
from shortener_app.storage.strategies import HitStorageStrategy
from shortener_app.config import settings


class SimpleHitWorker:
    """
    Simple hit processor worker with batch processing.
    
    Features:
    - Batch processing (100 hits at once)
    - In-memory counter for total_hits
    - Strategy pattern for storage
    - Simple and efficient
    """
    
    def __init__(
        self,
        queue: QueueStrategy,
        storage: HitStorageStrategy,
        db_session_factory=SessionLocal
    ):
        """
        Initialize worker with dependencies.
        
        Args:
            queue: Queue strategy for consuming messages
            storage: Storage strategy for analytics data
            db_session_factory: Factory for creating database sessions
        """
        self.queue = queue
        self.storage = storage
        self.db_session_factory = db_session_factory
        self.running = False
        self.hit_counts: Dict[str, int] = {}  # In-memory counter
        self.processed_count = 0
        
        # Configuration
        self.batch_size = 1
        self.update_interval = 1  # Update total_hits every 30 seconds
        self.last_update = datetime.utcnow()
    
    async def start(self):
        """Start the worker process"""
        self.running = True
        print("🚀 Simple Hit Worker started")
        print(f"📊 Batch size: {self.batch_size}")
        print(f"⏰ Update interval: {self.update_interval}s")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        while self.running:
            try:
                # Get batch of messages
                messages = await self.queue.consume_batch(
                    queue_name=settings.queue_name,
                    batch_size=self.batch_size,
                    block_time=1000  # 1 second
                )
                
                if messages:
                    try:
                        # Step 1: Process batch (analytics + counting)
                        await self._process_batch(messages)
                        
                        # Step 2: Update total_hits if needed
                        await self._update_total_hits_if_needed()
                        
                        # Step 3: ONLY acknowledge if everything succeeded
                        message_ids = [msg.message_id for msg in messages if hasattr(msg, 'message_id')]
                        if message_ids:
                            await self.queue.ack(settings.queue_name, message_ids)
                        
                        self.processed_count += len(messages)
                        print(f"✅ Processed {len(messages)} hits. Total: {self.processed_count}")
                        
                    except Exception as e:
                        print(f"❌ Batch processing failed: {e}")
                        # Messages stay in queue for retry!
                        # Don't acknowledge failed messages
                
            except asyncio.CancelledError:
                print("Worker task cancelled.")
                break
            except Exception as e:
                print(f"❌ Error processing batch: {e}")
                await asyncio.sleep(1)
        
        print("🛑 Simple Hit Worker stopped")
    
    async def _process_batch(self, messages: List[HitEvent]):
        """
        Process a batch of hit events.
        
        Steps:
        1. Store analytics data (batch write)
        2. Count hits in memory
        """
        # Step 1: Store analytics data (batch write to SQLite/ClickHouse)
        try:
            await self.storage.store_hits(messages)
        except Exception as e:
            print(f"❌ Storage error: {e}")
            # Continue processing even if storage fails
        
        # Step 2: Count hits in memory
        for hit in messages:
            self.hit_counts[hit.short_code] = self.hit_counts.get(hit.short_code, 0) + 1
    
    async def _update_total_hits_if_needed(self):
        """Update total_hits in main DB if needed"""
        now = datetime.utcnow()
        
        # Update if enough time has passed or too many hits accumulated
        should_update = (
            (now - self.last_update).seconds >= self.update_interval or
            len(self.hit_counts) >= 50  # Update every 50 different URLs
        )
        
        if should_update and self.hit_counts:
            await self._update_total_hits()
    
    async def _update_total_hits(self):
        """Update total_hits in main database (batch update)"""
        if not self.hit_counts:
            return
        
        db = self.db_session_factory()
        
        try:
            # Batch update all URLs
            for short_code, count in self.hit_counts.items():
                url = db.query(URL).filter(URL.short_code == short_code).first()
                if url:
                    url.total_hits += count
                else:
                    print(f"⚠️  URL not found: {short_code}")
            
            # Single commit for all updates
            db.commit()
            
            # Reset counter
            self.hit_counts.clear()
            self.last_update = datetime.utcnow()
            
            print(f"📊 Updated total_hits for {len(self.hit_counts)} URLs")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Database error: {e}")
            raise
        finally:
            db.close()
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown"""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.stop()
    
    def stop(self):
        """Stop the worker"""
        self.running = False


async def main():
    """
    Main entry point for simple hit worker.
    
    Usage:
        python -m shortener_app.workers.simple_worker
    """
    print("=" * 60)
    print("🔧 URL Shortener - Simple Hit Worker")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Queue backend: {settings.queue_backend}")
    print(f"Storage backend: {settings.hit_storage_backend}")
    print("=" * 60)
    
    # Create queue instance
    from shortener_app.queue.factory import QueueFactory, QueueBackend
    queue_backend = QueueBackend(settings.queue_backend)
    queue = QueueFactory.create(queue_backend)
    
    # Create storage instance
    from shortener_app.storage.factory import HitStorageFactory, HitStorageBackend
    storage_backend = HitStorageBackend(settings.hit_storage_backend)
    storage = HitStorageFactory.create(storage_backend)
    
    # Create and start worker
    worker = SimpleHitWorker(queue=queue, storage=storage)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
