"""Enhanced error display system for CLI interface."""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .terminal_utils import TerminalUtils, colorize, create_box


class ErrorType(Enum):
    """Types of errors that can occur."""
    TIMEOUT = "timeout"
    HTTP_ERROR = "http_error"
    CONNECTION_ERROR = "connection_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    CACHE_ERROR = "cache_error"
    API_ERROR = "api_error"
    UNKNOWN = "unknown"


class ErrorLevel(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_type: ErrorType
    level: ErrorLevel
    message: str
    source: str
    suggestions: List[str] = None
    technical_details: str = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class ErrorDisplayManager:
    """Manager for elegant error display and suggestions."""
    
    def __init__(self, use_colors: bool = True, terminal_width: Optional[int] = None):
        """
        Initialize the error display manager.
        
        Args:
            use_colors: Whether to use colors in error display
            terminal_width: Terminal width (auto-detected if None)
        """
        self.use_colors = use_colors and TerminalUtils.supports_colors()
        if terminal_width is None:
            terminal_width, _ = TerminalUtils.get_terminal_size()
        self.terminal_width = terminal_width
        
        # Error suggestion database
        self.error_suggestions = self._build_suggestion_database()
        
        # Error statistics
        self.error_counts = {error_type: 0 for error_type in ErrorType}
        self.recent_errors = []
    
    def show_error(self, error_info: ErrorInfo) -> str:
        """
        Display a formatted error with suggestions.
        
        Args:
            error_info: Error information
            
        Returns:
            Formatted error string
        """
        # Update statistics
        self.error_counts[error_info.error_type] += 1
        self.recent_errors.append(error_info)
        
        # Keep only recent errors
        if len(self.recent_errors) > 50:
            self.recent_errors = self.recent_errors[-50:]
        
        # Generate error display
        error_display = self._format_error_display(error_info)
        
        # Print immediately for critical errors
        if error_info.level in [ErrorLevel.CRITICAL, ErrorLevel.ERROR]:
            print(error_display)
        
        return error_display
    
    def show_cache_stats(self, cache_stats: Dict[str, Any]) -> str:
        """
        Display cache statistics with visual indicators.
        
        Args:
            cache_stats: Cache statistics dictionary
            
        Returns:
            Formatted cache stats string
        """
        lines = []
        
        # Header
        header = "💾 STATISTIQUES CACHE REDIS"
        if self.use_colors:
            header = colorize(header, 'bright_blue', bold=True)
        lines.append(header)
        
        # Hit rate with visual bar
        hit_rate = cache