"""Jina Client for communication with Jina AI Reader API."""

import asyncio
import time
from jinascraper.utils.type_helpers import Dict, Any, Optional, List
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from jinascraper.config import config


logger = structlog.get_logger(__name__)


class JinaClientError(Exception):
    """Base exception for Jina Client errors."""
    pass


class JinaAPIError(JinaClientError):
    """Exception for Jina API-related errors."""
    pass


class JinaClient:
    """Client for communicating with Jina AI Reader API."""
    
    def __init__(self):
        self.api_key = config.jina_api_key
        self.base_url = config.jina_base_url
        self.timeout = config.timeout_seconds
        self.max_concurrent = config.max_concurrent_requests
        self.delay = config.request_delay_seconds
        
        # Jina API rate limiting: 5000 RPM = ~83 requests per second
        # We'll be more conservative: 60 requests per minute = 1 per second
        self.rate_limit_rpm = 60
        self.rate_limit_delay = 60.0 / self.rate_limit_rpm  # 1 second between requests
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "JinaJobScraper/1.0.0",
                "Accept": "application/json",
            },
            limits=httpx.Limits(max_connections=self.max_concurrent)
        )
        
        # Rate limiting semaphore and timing
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to respect Jina API limits (5000 RPM)."""
        async with self._request_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                logger.debug("Rate limiting: sleeping", sleep_seconds=sleep_time)
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError, JinaAPIError)),
        reraise=True
    )
    async def make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a rate-limited request to Jina Reader API.
        
        Args:
            url: Target URL to extract content from
            params: Optional parameters for the request
            
        Returns:
            Dictionary containing the response data
        """
        async with self._semaphore:
            # Enforce rate limiting
            await self._enforce_rate_limit()
            
            start_time = time.time()
            
            try:
                # For Jina Reader API, we construct the URL differently
                # Format: https://r.jina.ai/{target_url}
                jina_url = f"{self.base_url.rstrip('/')}/{url}"
                
                # Prepare headers for the request
                headers = {}
                
                # SOLUTION: Use X-Respond-With header to bypass readability filtering
                # This ensures we get complete content instead of truncated content
                if params and params.get("return_format") == "markdown":
                    headers["X-Respond-With"] = "markdown"
                    # Remove return_format from params since we're using header instead
                    params = {k: v for k, v in params.items() if k != "return_format"}
                
                # Handle CSS selectors as headers instead of parameters
                if params:
                    # Convert target_selector to X-Target-Selector header
                    if "target_selector" in params:
                        headers["X-Target-Selector"] = params["target_selector"]
                        params = {k: v for k, v in params.items() if k != "target_selector"}
                    
                    # Convert remove_selector to X-Remove-Selector header  
                    if "remove_selector" in params:
                        headers["X-Remove-Selector"] = params["remove_selector"]
                        params = {k: v for k, v in params.items() if k != "remove_selector"}
                    
                    # Convert css_selector_excluding to X-CSS-Selector-Excluding header
                    if "css_selector_excluding" in params:
                        headers["X-CSS-Selector-Excluding"] = params["css_selector_excluding"]
                        params = {k: v for k, v in params.items() if k != "css_selector_excluding"}
                    
                    # Handle legacy css_selector_only
                    if "css_selector_only" in params:
                        headers["X-Target-Selector"] = params["css_selector_only"]
                        params = {k: v for k, v in params.items() if k != "css_selector_only"}
                
                logger.info("Making Jina Reader request", url=jina_url, params=params, headers=headers)
                
                response = await self.client.get(jina_url, params=params or {}, headers=headers)
                response.raise_for_status()
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # Jina Reader API returns JSON with content in data.content
                response_json = response.json()
                
                if "data" in response_json and "content" in response_json["data"]:
                    content = response_json["data"]["content"]
                    title = response_json["data"].get("title", "")
                    description = response_json["data"].get("description", "")
                else:
                    # Fallback to plain text if JSON structure is different
                    content = response.text
                    title = ""
                    description = ""
                
                data = {
                    "content": content,
                    "title": title,
                    "description": description,
                    "url": url,
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time,
                    "raw_response": response_json if "data" in response_json else None
                }
                
                logger.info(
                    "Jina Reader request successful",
                    url=jina_url,
                    status_code=response.status_code,
                    processing_time_ms=processing_time,
                    content_length=len(content)
                )
                
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Jina Reader HTTP error",
                    url=jina_url,
                    status_code=e.response.status_code,
                    error=str(e)
                )
                raise JinaAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            
            except httpx.RequestError as e:
                logger.error("Jina Reader request error", url=jina_url, error=str(e))
                raise JinaAPIError(f"Request failed: {str(e)}")
    
    async def test_rate_limiting(self, test_urls: List[str]) -> Dict[str, Any]:
        """
        Test rate limiting and error handling with multiple requests.
        
        Args:
            test_urls: List of URLs to test with
            
        Returns:
            Dictionary with test results and timing information
        """
        logger.info("Testing rate limiting and error handling", url_count=len(test_urls))
        
        start_time = time.time()
        results = []
        errors = []
        
        for i, url in enumerate(test_urls):
            try:
                request_start = time.time()
                response = await self.make_request(url)
                request_time = time.time() - request_start
                
                results.append({
                    "url": url,
                    "success": True,
                    "request_time": request_time,
                    "content_length": len(response.get("content", ""))
                })
                
                logger.info(
                    "Rate limit test request completed",
                    request_number=i+1,
                    url=url,
                    request_time_ms=int(request_time * 1000)
                )
                
            except Exception as e:
                error_info = {
                    "url": url,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                errors.append(error_info)
                
                logger.error(
                    "Rate limit test request failed",
                    request_number=i+1,
                    url=url,
                    error=str(e)
                )
        
        total_time = time.time() - start_time
        
        test_results = {
            "total_requests": len(test_urls),
            "successful_requests": len(results),
            "failed_requests": len(errors),
            "total_time_seconds": total_time,
            "average_time_per_request": total_time / len(test_urls) if test_urls else 0,
            "requests_per_minute": (len(test_urls) / total_time) * 60 if total_time > 0 else 0,
            "success_rate": len(results) / len(test_urls) if test_urls else 0,
            "results": results,
            "errors": errors
        }
        
        logger.info(
            "Rate limiting test completed",
            total_requests=test_results["total_requests"],
            successful=test_results["successful_requests"],
            failed=test_results["failed_requests"],
            total_time=f"{total_time:.2f}s",
            rpm=f"{test_results['requests_per_minute']:.1f}",
            success_rate=f"{test_results['success_rate']:.1%}"
        )
        
        return test_results