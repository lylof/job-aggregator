"""Performance optimization and monitoring utilities."""

import asyncio
import time
import functools
import statistics
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation_name: str
    execution_time: float
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.active_operations: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        self.active_operations[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[PerformanceMetrics]:
        """End tracking an operation and record metrics."""
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return None
        
        start_time = self.active_operations.pop(operation_id)
        execution_time = time.time() - start_time
        
        operation_name = operation_id.split('_')[0]
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            metadata=metadata or {}
        )
        
        self.metrics_history[operation_name].append(metrics)
        return metrics
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        if operation_name not in self.metrics_history:
            return {}
        
        metrics = list(self.metrics_history[operation_name])
        if not metrics:
            return {}
        
        execution_times = [m.execution_time for m in metrics]
        
        return {
            "operation_name": operation_name,
            "total_executions": len(metrics),
            "avg_execution_time": statistics.mean(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "median_execution_time": statistics.median(execution_times),
            "std_dev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "last_execution": metrics[-1].timestamp.isoformat(),
            "total_time": sum(execution_times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tracked operations."""
        return {
            operation_name: self.get_operation_stats(operation_name)
            for operation_name in self.metrics_history.keys()
        }
    
    def get_slow_operations(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Get operations that are slower than threshold."""
        slow_ops = []
        
        for operation_name in self.metrics_history.keys():
            stats = self.get_operation_stats(operation_name)
            if stats.get("avg_execution_time", 0) > threshold_seconds:
                slow_ops.append(stats)
        
        return sorted(slow_ops, key=lambda x: x["avg_execution_time"], reverse=True)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def performance_tracked(operation_name: Optional[str] = None):
    """Decorator to track performance of functions."""
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_id = performance_monitor.start_operation(operation_name)
                try:
                    result = await func(*args, **kwargs)
                    performance_monitor.end_operation(operation_id, {"success": True})
                    return result
                except Exception as e:
                    performance_monitor.end_operation(operation_id, {"success": False, "error": str(e)})
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                operation_id = performance_monitor.start_operation(operation_name)
                try:
                    result = func(*args, **kwargs)
                    performance_monitor.end_operation(operation_id, {"success": True})
                    return result
                except Exception as e:
                    performance_monitor.end_operation(operation_id, {"success": False, "error": str(e)})
                    raise
            return sync_wrapper
    return decorator


class BatchProcessor:
    """Efficient batch processing with configurable concurrency and rate limiting."""
    
    def __init__(
        self,
        max_concurrent: int = 10,
        batch_size: int = 50,
        rate_limit_delay: float = 0.1,
        retry_attempts: int = 3
    ):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.retry_attempts = retry_attempts
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        items: List[Any],
        processor_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[Any]:
        """
        Process items in batches with concurrency control.
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processed results
        """
        results = []
        total_items = len(items)
        processed_count = 0
        
        # Split items into batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} items)")
            
            # Process batch items concurrently
            batch_tasks = []
            for item in batch:
                task = self._process_item_with_retry(processor_func, item)
                batch_tasks.append(task)
            
            # Execute batch with concurrency control
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results and handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {str(result)}")
                    results.append(None)
                else:
                    results.append(result)
                
                processed_count += 1
                
                # Call progress callback if provided
                if progress_callback:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(processed_count, total_items)
                    else:
                        progress_callback(processed_count, total_items)
            
            # Rate limiting between batches
            if batch_idx < len(batches) - 1:  # Don't delay after last batch
                await asyncio.sleep(self.rate_limit_delay)
        
        return results
    
    async def _process_item_with_retry(self, processor_func: Callable, item: Any) -> Any:
        """Process a single item with retry logic and concurrency control."""
        async with self.semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    return await processor_func(item)
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        logger.error(f"Failed to process item after {self.retry_attempts} attempts: {str(e)}")
                        raise
                    else:
                        wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                        await asyncio.sleep(wait_time)


# Global batch processor instance
batch_processor = BatchProcessor()


class CacheOptimizer:
    """Intelligent caching with LRU eviction and hit rate optimization."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: deque = deque()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU tracking."""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check TTL
            if time.time() - entry['timestamp'] > self.ttl_seconds:
                self._evict(key)
                self.miss_count += 1
                return None
            
            # Update access order for LRU
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            self.hit_count += 1
            return entry['value']
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction."""
        # Evict if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        # Add/update entry
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _evict(self, key: str) -> None:
        """Evict a specific key."""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if self.access_order:
            lru_key = self.access_order.popleft()
            if lru_key in self.cache:
                del self.cache[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "utilization": len(self.cache) / self.max_size
        }
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count of cleared items."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self._evict(key)
        
        return len(expired_keys)


class MemoryOptimizer:
    """Memory usage optimization utilities."""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage statistics."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available
            }
        except ImportError:
            logger.warning("psutil not available, memory monitoring disabled")
            return {}
    
    @staticmethod
    def optimize_large_list(items: List[Any], chunk_size: int = 1000) -> AsyncGenerator[List[Any], None]:
        """Process large lists in chunks to optimize memory usage."""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    @staticmethod
    def cleanup_large_objects(*objects) -> None:
        """Explicitly cleanup large objects to free memory."""
        import gc
        for obj in objects:
            del obj
        gc.collect()


# Performance optimization utilities
def optimize_async_operations(max_concurrent: int = 10):
    """Decorator to optimize async operations with concurrency control."""
    def decorator(func):
        semaphore = asyncio.Semaphore(max_concurrent)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 3600, max_size: int = 100):
    """Decorator to cache function results."""
    cache = CacheOptimizer(max_size=max_size, ttl_seconds=ttl_seconds)
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator