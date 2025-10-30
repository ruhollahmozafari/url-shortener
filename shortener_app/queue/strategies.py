"""
Queue strategies using Strategy Pattern.
Allows switching between different queue backends (Redis Streams, In-Memory).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from collections import deque
import asyncio
from .models import HitEvent


class QueueStrategy(ABC):
    """
    Abstract base class for queue strategies.
    
    This is the Strategy Pattern interface - allows multiple queue implementations
    without changing the service/worker code.
    
    Similar to Celery's broker abstraction.
    """
    
    @abstractmethod
    async def publish(self, queue_name: str, message: HitEvent) -> bool:
        """
        Publish a message to the queue.
        
        Args:
            queue_name: Name of the queue
            message: HitEvent to publish
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def consume(
        self, 
        queue_name: str, 
        batch_size: int = 1,
        block_time: int = 1000
    ) -> List[HitEvent]:
        """
        Consume messages from the queue.
        
        Args:
            queue_name: Name of the queue
            batch_size: Maximum number of messages to retrieve
            block_time: Time to wait for messages (milliseconds)
            
        Returns:
            List of HitEvent messages
        """
        pass
    
    @abstractmethod
    async def ack(self, queue_name: str, message_ids: List[str]) -> bool:
        """
        Acknowledge messages (mark as processed).
        
        Args:
            queue_name: Name of the queue
            message_ids: List of message IDs to acknowledge
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get the number of pending messages in queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Number of pending messages
        """
        pass
    
    async def consume_batch(self, queue_name: str, batch_size: int = 100, block_time: int = 1000) -> List[HitEvent]:
        """
        Consume a batch of messages (alias for consume with larger default batch size).
        
        Args:
            queue_name: Name of the queue
            batch_size: Number of messages to consume (default: 100)
            block_time: Time to wait for messages (milliseconds)
            
        Returns:
            List of HitEvent messages
        """
        return await self.consume(queue_name, batch_size, block_time)


class RedisStreamQueue(QueueStrategy):
    """
    Redis Streams implementation for message queue.
    
    Redis Streams is perfect for this use case:
    - Persistent (messages survive restarts)
    - Consumer groups (multiple workers)
    - Atomic operations
    - Built into Redis (no extra infrastructure)
    
    How it works:
    1. Producer publishes messages using XADD
    2. Consumer reads messages using XREADGROUP
    3. Consumer acknowledges messages using XACK
    4. Unacknowledged messages can be reclaimed
    
    Production-ready for high-volume URL shorteners.
    """
    
    def __init__(self, redis_client, consumer_group: str = "url_workers"):
        """
        Initialize Redis Streams queue.
        
        Args:
            redis_client: Redis client instance
            consumer_group: Name of consumer group for workers
        """
        self.redis = redis_client
        self.consumer_group = consumer_group
        self._initialized_streams = set()
    
    async def _ensure_stream_exists(self, queue_name: str):
        """
        Ensure stream and consumer group exist.
        Creates them if they don't exist.
        """
        if queue_name in self._initialized_streams:
            return
        
        try:
            # Try to create consumer group
            # If stream doesn't exist, this creates it with MKSTREAM
            self.redis.xgroup_create(
                name=queue_name,
                groupname=self.consumer_group,
                id='0',
                mkstream=True
            )
            print(f"✅ Created Redis stream: {queue_name}")
        except Exception as e:
            # Group might already exist, that's OK
            if "BUSYGROUP" not in str(e):
                print(f"⚠️  Stream creation warning: {e}")
        
        self._initialized_streams.add(queue_name)
    
    async def publish(self, queue_name: str, message: HitEvent) -> bool:
        """
        Publish message to Redis Stream.
        
        Uses XADD command to append message to stream.
        """
        try:
            await self._ensure_stream_exists(queue_name)
            
            # Convert HitEvent to dict and then to JSON
            message_data = {
                'data': message.model_dump_json()
            }
            
            # Add to stream (XADD command)
            message_id = self.redis.xadd(queue_name, message_data)
            return True
            
        except Exception as e:
            print(f"❌ Redis publish error: {e}")
            return False
    
    async def consume(
        self,
        queue_name: str,
        batch_size: int = 1,
        block_time: int = 1000
    ) -> List[HitEvent]:
        """
        Consume messages from Redis Stream.
        
        Uses XREADGROUP to read messages for this consumer group.
        Messages are not removed until acknowledged.
        """
        try:
            await self._ensure_stream_exists(queue_name)
            
            # Read from stream using consumer group
            # '>' means "messages never delivered to other consumers"
            import socket
            consumer_name = f"worker-{socket.gethostname()}-{id(self)}"
            
            messages = self.redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=consumer_name,  # Dynamic consumer name per worker instance
                streams={queue_name: '>'},
                count=batch_size,
                block=block_time
            )
            
            if not messages:
                return []
            
            # Parse messages
            events = []
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        # Parse JSON data
                        data = json.loads(message_data[b'data'].decode('utf-8'))
                        event = HitEvent(**data)
                        
                        # Store message ID for acknowledgment
                        event.message_id = message_id.decode('utf-8')
                        events.append(event)
                    except Exception as e:
                        print(f"⚠️  Failed to parse message {message_id}: {e}")
            
            return events
            
        except Exception as e:
            print(f"❌ Redis consume error: {e}")
            return []
    
    async def ack(self, queue_name: str, message_ids: List[str]) -> bool:
        """
        Acknowledge messages (remove from pending list).
        
        Uses XACK command to mark messages as processed.
        """
        try:
            if not message_ids:
                return True
            
            # Acknowledge messages
            self.redis.xack(queue_name, self.consumer_group, *message_ids)
            return True
            
        except Exception as e:
            print(f"❌ Redis ack error: {e}")
            return False
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get approximate queue length"""
        try:
            info = self.redis.xinfo_stream(queue_name)
            return info['length']
        except Exception:
            return 0


class InMemoryQueue(QueueStrategy):
    """
    In-memory queue implementation using Python deque.
    
    Pros:
    - Simple (no external dependencies)
    - Fast (no network overhead)
    - Good for development and testing
    
    Cons:
    - Not persistent (lost on restart)
    - Not distributed (each process has its own queue)
    - No consumer groups
    
    Used in development/testing environments.
    """
    
    def __init__(self):
        """Initialize in-memory queues"""
        self._queues: Dict[str, deque] = {}
    
    def _get_queue(self, queue_name: str) -> deque:
        """Get or create queue"""
        if queue_name not in self._queues:
            self._queues[queue_name] = deque()
        return self._queues[queue_name]
    
    async def publish(self, queue_name: str, message: HitEvent) -> bool:
        """Add message to in-memory queue"""
        try:
            queue = self._get_queue(queue_name)
            queue.append(message)
            return True
        except Exception as e:
            print(f"❌ In-memory publish error: {e}")
            return False
    
    async def consume(
        self,
        queue_name: str,
        batch_size: int = 1,
        block_time: int = 1000
    ) -> List[HitEvent]:
        """
        Consume messages from in-memory queue.
        
        Note: block_time is ignored (no blocking in this simple implementation)
        """
        try:
            queue = self._get_queue(queue_name)
            messages = []
            
            for _ in range(min(batch_size, len(queue))):
                if queue:
                    messages.append(queue.popleft())
            
            return messages
            
        except Exception as e:
            print(f"❌ In-memory consume error: {e}")
            return []
    
    async def ack(self, queue_name: str, message_ids: List[str]) -> bool:
        """
        Acknowledge messages.
        
        Note: In-memory queue doesn't need acknowledgment
        (messages are removed on consume)
        """
        return True
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        queue = self._get_queue(queue_name)
        return len(queue)

