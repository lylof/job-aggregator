"""Security utilities for input validation, data sanitization, and audit logging."""

import re
import hashlib
import secrets
import urllib.parse
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    event_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityAuditor:
    """Security auditing and logging system."""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.security_events: List[SecurityEvent] = []
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns: List[str] = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'union\s+select',  # SQL injection
            r'\.\./',  # Path traversal
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI XSS
        ]
    
    def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        self.security_events.append(event)
        
        # Maintain max events limit
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
        
        # Log to structured logger
        logger.warning(
            "Security event",
            event_type=event.event_type,
            severity=event.severity,
            description=event.description,
            url=event.url,
            metadata=event.metadata
        )
        
        # Auto-block on critical events
        if event.severity == "CRITICAL" and event.source_ip:
            self.block_ip(event.source_ip)
    
    def block_ip(self, ip_address: str) -> None:
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP address {ip_address} has been blocked")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked."""
        return ip_address in self.blocked_ips
    
    def detect_suspicious_content(self, content: str) -> List[str]:
        """Detect suspicious patterns in content."""
        detected_patterns = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event for event in self.security_events
            if event.timestamp > cutoff_time
        ]
        
        severity_counts = {}
        event_type_counts = {}
        
        for event in recent_events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        return {
            "total_events": len(recent_events),
            "severity_breakdown": severity_counts,
            "event_type_breakdown": event_type_counts,
            "blocked_ips_count": len(self.blocked_ips),
            "time_period_hours": hours
        }


class URLValidator:
    """URL validation and sanitization utilities."""
    
    ALLOWED_SCHEMES = {'http', 'https'}
    BLOCKED_DOMAINS = {
        'localhost', '127.0.0.1', '0.0.0.0',
        '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'  # Private IP ranges
    }
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate if URL is safe and well-formed."""
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in URLValidator.ALLOWED_SCHEMES:
                return False
            
            # Check if domain is blocked
            if parsed.netloc.lower() in URLValidator.BLOCKED_DOMAINS:
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'javascript:', r'data:', r'file:', r'ftp:',
                r'\.\./', r'%2e%2e%2f', r'%252e%252e%252f'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL by removing dangerous components."""
        try:
            parsed = urlparse(url)
            
            # Remove fragment and dangerous query parameters
            dangerous_params = {'javascript', 'script', 'eval', 'onload', 'onerror'}
            query_params = parse_qs(parsed.query)
            
            safe_params = {
                key: value for key, value in query_params.items()
                if key.lower() not in dangerous_params
            }
            
            # Reconstruct URL
            safe_query = urllib.parse.urlencode(safe_params, doseq=True)
            safe_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                safe_query,
                ''  # Remove fragment
            ))
            
            return safe_url
            
        except Exception:
            return url
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL safely."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None


class DataSanitizer:
    """Data sanitization utilities."""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Remove potentially dangerous HTML content."""
        # Remove script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous attributes
        dangerous_attrs = ['onload', 'onerror', 'onclick', 'onmouseover', 'onfocus', 'onblur']
        for attr in dangerous_attrs:
            content = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
        
        # Remove javascript: and data: URLs
        content = re.sub(r'javascript:[^"\'\\s]*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:text/html[^"\'\\s]*', '', content, flags=re.IGNORECASE)
        
        return content
    
    @staticmethod
    def sanitize_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize job data dictionary."""
        sanitized = {}
        
        for key, value in job_data.items():
            if isinstance(value, str):
                # Sanitize string values
                sanitized_value = DataSanitizer.sanitize_html(value)
                sanitized_value = DataSanitizer._remove_control_characters(sanitized_value)
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = DataSanitizer.sanitize_job_data(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    DataSanitizer.sanitize_html(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """Remove control characters from text."""
        # Remove control characters except newline, carriage return, and tab
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    @staticmethod
    def validate_job_data_structure(job_data: Dict[str, Any]) -> List[str]:
        """Validate job data structure and return list of issues."""
        issues = []
        
        # Required fields
        required_fields = ['title', 'company', 'source_url']
        for field in required_fields:
            if field not in job_data or not job_data[field]:
                issues.append(f"Missing required field: {field}")
        
        # URL validation
        if 'source_url' in job_data:
            if not URLValidator.is_valid_url(job_data['source_url']):
                issues.append("Invalid source URL")
        
        # String length limits
        string_limits = {
            'title': 200,
            'company': 100,
            'description': 10000,
            'location': 100
        }
        
        for field, max_length in string_limits.items():
            if field in job_data and isinstance(job_data[field], str):
                if len(job_data[field]) > max_length:
                    issues.append(f"Field {field} exceeds maximum length of {max_length}")
        
        return issues


class RateLimiter:
    """Rate limiting for API endpoints and operations."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for the given identifier."""
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.time_window)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        if identifier not in self.requests:
            return self.max_requests
        
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.time_window)
        
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        return max(0, self.max_requests - len(recent_requests))


class SecretManager:
    """Secure handling of API keys and secrets."""
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Create a hash of an API key for logging/storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionaries for logging."""
        sensitive_keys = {
            'api_key', 'password', 'token', 'secret', 'key',
            'authorization', 'auth', 'credential'
        }
        
        masked_data = {}
        for key, value in data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    masked_data[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
                else:
                    masked_data[key] = '***'
            elif isinstance(value, dict):
                masked_data[key] = SecretManager.mask_sensitive_data(value)
            else:
                masked_data[key] = value
        
        return masked_data
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)


# Global instances
security_auditor = SecurityAuditor()
url_validator = URLValidator()
data_sanitizer = DataSanitizer()
rate_limiter = RateLimiter()


# Decorators for security
def validate_url_input(func):
    """Decorator to validate URL inputs."""
    def wrapper(*args, **kwargs):
        # Check for URL arguments
        for arg in args:
            if isinstance(arg, str) and (arg.startswith('http://') or arg.startswith('https://')):
                if not url_validator.is_valid_url(arg):
                    security_auditor.log_security_event(SecurityEvent(
                        event_type="INVALID_URL",
                        severity="MEDIUM",
                        description=f"Invalid URL detected: {arg}",
                        url=arg
                    ))
                    raise ValueError(f"Invalid URL: {arg}")
        
        # Check URL parameters in kwargs
        for key, value in kwargs.items():
            if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                if not url_validator.is_valid_url(value):
                    security_auditor.log_security_event(SecurityEvent(
                        event_type="INVALID_URL",
                        severity="MEDIUM",
                        description=f"Invalid URL in parameter {key}: {value}",
                        url=value
                    ))
                    raise ValueError(f"Invalid URL in parameter {key}: {value}")
        
        return func(*args, **kwargs)
    return wrapper


def rate_limited(max_requests: int = 100, time_window: int = 3600):
    """Decorator for rate limiting function calls."""
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Use function name as identifier (could be enhanced with user/IP)
            identifier = func.__name__
            
            if not limiter.is_allowed(identifier):
                security_auditor.log_security_event(SecurityEvent(
                    event_type="RATE_LIMIT_EXCEEDED",
                    severity="MEDIUM",
                    description=f"Rate limit exceeded for function {func.__name__}",
                    metadata={"function": func.__name__, "max_requests": max_requests}
                ))
                raise Exception(f"Rate limit exceeded for {func.__name__}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_security_event(event_type: str, severity: str = "LOW"):
    """Decorator to audit function calls as security events."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                security_auditor.log_security_event(SecurityEvent(
                    event_type=event_type,
                    severity=severity,
                    description=f"Function {func.__name__} executed successfully",
                    metadata={"function": func.__name__, "success": True}
                ))
                return result
            except Exception as e:
                security_auditor.log_security_event(SecurityEvent(
                    event_type=event_type,
                    severity="HIGH",
                    description=f"Function {func.__name__} failed: {str(e)}",
                    metadata={"function": func.__name__, "success": False, "error": str(e)}
                ))
                raise
        return wrapper
    return decorator