"""
Enhanced error handling system for JinaScraper CLI.

This module provides intelligent error handling with automatic suggestions,
visual error levels, and contextual help.
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .terminal_utils import TerminalUtils, colorize, create_box, create_separator


class ErrorLevel(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ErrorType(Enum):
    """Types of errors that can occur."""
    NETWORK_TIMEOUT = "network_timeout"
    HTTP_ERROR = "http_error"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    PARSING_ERROR = "parsing_error"
    CONFIGURATION = "configuration"
    CACHE_ERROR = "cache_error"
    DATABASE_ERROR = "database_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Information about an error."""
    error_type: ErrorType
    level: ErrorLevel
    message: str
    source: str
    timestamp: float
    context: Dict[str, Any] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.suggestions is None:
            self.suggestions = []


class ErrorSuggestionEngine:
    """Engine for generating automatic error suggestions."""
    
    def __init__(self):
        """Initialize the suggestion engine."""
        self.suggestion_rules = self._build_suggestion_rules()
    
    def _build_suggestion_rules(self) -> Dict[ErrorType, List[str]]:
        """Build the rules for automatic suggestions."""
        return {
            ErrorType.NETWORK_TIMEOUT: [
                "Vérifiez votre connexion internet",
                "Augmentez la valeur de timeout dans la configuration",
                "Réessayez dans quelques minutes",
                "Vérifiez si le site web est accessible depuis un navigateur"
            ],
            ErrorType.HTTP_ERROR: [
                "Vérifiez que l'URL est correcte et accessible",
                "Le site web peut être temporairement indisponible",
                "Vérifiez les paramètres de requête HTTP",
                "Contactez l'administrateur du site si le problème persiste"
            ],
            ErrorType.AUTHENTICATION: [
                "Vérifiez vos clés API dans le fichier .env",
                "Assurez-vous que les clés API sont valides et non expirées",
                "Vérifiez les permissions de votre compte API",
                "Régénérez les clés API si nécessaire"
            ],
            ErrorType.RATE_LIMIT: [
                "Attendez avant de relancer le scraping",
                "Réduisez la fréquence des requêtes",
                "Vérifiez les limites de votre plan API",
                "Considérez l'upgrade de votre plan API"
            ],
            ErrorType.PARSING_ERROR: [
                "Le format de la page web a peut-être changé",
                "Vérifiez les sélecteurs CSS dans la configuration",
                "Mettez à jour les patterns d'extraction",
                "Signalez le problème pour mise à jour"
            ],
            ErrorType.CONFIGURATION: [
                "Vérifiez le fichier de configuration",
                "Assurez-vous que tous les paramètres requis sont définis",
                "Consultez la documentation de configuration",
                "Utilisez les valeurs par défaut recommandées"
            ],
            ErrorType.CACHE_ERROR: [
                "Vérifiez que Redis est démarré et accessible",
                "Testez la connexion Redis manuellement",
                "Vérifiez la configuration REDIS_URL",
                "Le système basculera automatiquement sur FakeRedis"
            ],
            ErrorType.DATABASE_ERROR: [
                "Vérifiez la connexion à la base de données",
                "Assurez-vous que Supabase est accessible",
                "Vérifiez les credentials de base de données",
                "Consultez les logs de base de données"
            ],
            ErrorType.UNKNOWN: [
                "Consultez les logs détaillés pour plus d'informations",
                "Réessayez l'opération",
                "Contactez le support technique",
                "Signalez le problème avec les détails d'erreur"
            ]
        }
    
    def get_suggestions(self, error_type: ErrorType, context: Dict[str, Any] = None) -> List[str]:
        """
        Get suggestions for an error type.
        
        Args:
            error_type: Type of error
            context: Additional context
            
        Returns:
            List of suggestions
        """
        base_suggestions = self.suggestion_rules.get(error_type, self.suggestion_rules[ErrorType.UNKNOWN])
        
        # Add context-specific suggestions
        contextual_suggestions = self._get_contextual_suggestions(error_type, context or {})
        
        return base_suggestions + contextual_suggestions
    
    def _get_contextual_suggestions(self, error_type: ErrorType, context: Dict[str, Any]) -> List[str]:
        """Get context-specific suggestions."""
        suggestions = []
        
        if error_type == ErrorType.HTTP_ERROR:
            status_code = context.get('status_code')
            if status_code == 400:
                suggestions.append("Erreur 400: Vérifiez les paramètres de la requête")
            elif status_code == 401:
                suggestions.append("Erreur 401: Problème d'authentification")
            elif status_code == 403:
                suggestions.append("Erreur 403: Accès interdit - vérifiez les permissions")
            elif status_code == 404:
                suggestions.append("Erreur 404: URL non trouvée - vérifiez l'adresse")
            elif status_code == 429:
                suggestions.append("Erreur 429: Trop de requêtes - attendez avant de réessayer")
            elif status_code >= 500:
                suggestions.append(f"Erreur serveur {status_code}: Problème côté serveur")
        
        elif error_type == ErrorType.NETWORK_TIMEOUT:
            timeout_value = context.get('timeout')
            if timeout_value:
                suggestions.append(f"Timeout actuel: {timeout_value}s - considérez l'augmenter")
        
        return suggestions


class ErrorFormatter:
    """Formatter for displaying errors with visual appeal."""
    
    def __init__(self, use_colors: bool = True, terminal_width: Optional[int] = None):
        """
        Initialize the error formatter.
        
        Args:
            use_colors: Whether to use colors
            terminal_width: Terminal width
        """
        self.use_colors = use_colors and TerminalUtils.supports_colors()
        if terminal_width is None:
            terminal_width, _ = TerminalUtils.get_terminal_size()
        self.terminal_width = terminal_width
    
    def format_error(self, error_info: ErrorInfo) -> str:
        """
        Format an error for display.
        
        Args:
            error_info: Error information
            
        Returns:
            Formatted error string
        """
        lines = []
        
        # Error header with icon and level
        icon, color = self._get_error_display_config(error_info.level)
        
        header = f"{icon} {error_info.level.value.upper()}"
        if self.use_colors:
            header = colorize(header, color, bold=True)
        
        lines.append(header)
        
        # Error message
        message_line = f"Message: {error_info.message}"
        if self.use_colors:
            message_line = colorize(message_line, color)
        lines.append(message_line)
        
        # Source information
        source_line = f"Source: {error_info.source}"
        if self.use_colors:
            source_line = colorize(source_line, 'bright_black')
        lines.append(source_line)
        
        # Timestamp
        time_str = time.strftime("%H:%M:%S", time.localtime(error_info.timestamp))
        timestamp_line = f"Heure: {time_str}"
        if self.use_colors:
            timestamp_line = colorize(timestamp_line, 'bright_black')
        lines.append(timestamp_line)
        
        # Context information if available
        if error_info.context:
            lines.append("")
            context_header = "Contexte:"
            if self.use_colors:
                context_header = colorize(context_header, 'bright_white', bold=True)
            lines.append(context_header)
            
            for key, value in error_info.context.items():
                context_line = f"  {key}: {value}"
                if self.use_colors:
                    context_line = colorize(context_line, 'cyan')
                lines.append(context_line)
        
        return "\\n".join(lines)
    
    def format_suggestions(self, suggestions: List[str]) -> str:
        """
        Format suggestions for display.
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Formatted suggestions string
        """
        if not suggestions:
            return ""
        
        lines = []
        
        # Suggestions header
        header = "💡 Suggestions:"
        if self.use_colors:
            header = colorize(header, 'bright_yellow', bold=True)
        lines.append(header)
        
        # Individual suggestions
        for i, suggestion in enumerate(suggestions, 1):
            suggestion_line = f"  {i}. {suggestion}"
            if self.use_colors:
                suggestion_line = colorize(suggestion_line, 'yellow')
            lines.append(suggestion_line)
        
        return "\\n".join(lines)
    
    def format_error_summary(self, errors: List[ErrorInfo]) -> str:
        """
        Format a summary of multiple errors.
        
        Args:
            errors: List of errors
            
        Returns:
            Formatted error summary
        """
        if not errors:
            return ""
        
        lines = []
        
        # Summary header
        header = f"🚨 RÉSUMÉ DES ERREURS ({len(errors)})"
        if self.use_colors:
            header = colorize(header, 'red', bold=True)
        lines.append(header)
        lines.append(TerminalUtils.create_separator(width=50, style='simple'))
        lines.append("")
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            error_type = error.error_type
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Display each group
        for error_type, error_list in error_groups.items():
            group_header = f"🔴 {error_type.value.upper().replace('_', ' ')} ({len(error_list)})"
            if self.use_colors:
                group_header = colorize(group_header, 'red', bold=True)
            lines.append(group_header)
            
            for error in error_list:
                error_line = f"  • {error.source}: {error.message}"
                if self.use_colors:
                    error_line = colorize(error_line, 'bright_red')
                lines.append(error_line)
            
            lines.append("")
        
        return "\\n".join(lines)
    
    def _get_error_display_config(self, level: ErrorLevel) -> Tuple[str, str]:
        """Get display configuration for error level."""
        config = {
            ErrorLevel.CRITICAL: ("🚨", "red"),
            ErrorLevel.WARNING: ("⚠️", "yellow"),
            ErrorLevel.INFO: ("ℹ️", "cyan"),
            ErrorLevel.SUCCESS: ("✅", "green")
        }
        return config.get(level, ("❓", "white"))


class EnhancedErrorHandler:
    """Enhanced error handler with intelligent suggestions and visual display."""
    
    def __init__(self, use_colors: bool = True, terminal_width: Optional[int] = None):
        """
        Initialize the enhanced error handler.
        
        Args:
            use_colors: Whether to use colors
            terminal_width: Terminal width
        """
        self.suggestion_engine = ErrorSuggestionEngine()
        self.formatter = ErrorFormatter(use_colors, terminal_width)
        self.error_history: List[ErrorInfo] = []
        self.use_colors = use_colors
    
    def detect_error_type(self, error_message: str, context: Dict[str, Any] = None) -> ErrorType:
        """
        Automatically detect error type from message and context.
        
        Args:
            error_message: Error message
            context: Additional context
            
        Returns:
            Detected error type
        """
        message_lower = error_message.lower()
        context = context or {}
        
        # Network-related errors
        if any(keyword in message_lower for keyword in ['timeout', 'connection', 'network']):
            return ErrorType.NETWORK_TIMEOUT
        
        # HTTP errors
        if any(keyword in message_lower for keyword in ['http', 'status', 'response']):
            return ErrorType.HTTP_ERROR
        
        # Authentication errors
        if any(keyword in message_lower for keyword in ['auth', 'api key', 'unauthorized', '401']):
            return ErrorType.AUTHENTICATION
        
        # Rate limiting
        if any(keyword in message_lower for keyword in ['rate limit', 'too many', '429']):
            return ErrorType.RATE_LIMIT
        
        # Parsing errors
        if any(keyword in message_lower for keyword in ['parse', 'selector', 'extract', 'format']):
            return ErrorType.PARSING_ERROR
        
        # Configuration errors
        if any(keyword in message_lower for keyword in ['config', 'setting', 'parameter']):
            return ErrorType.CONFIGURATION
        
        # Cache errors
        if any(keyword in message_lower for keyword in ['redis', 'cache']):
            return ErrorType.CACHE_ERROR
        
        # Database errors
        if any(keyword in message_lower for keyword in ['database', 'supabase', 'sql']):
            return ErrorType.DATABASE_ERROR
        
        # Check context for more clues
        if 'status_code' in context:
            return ErrorType.HTTP_ERROR
        
        return ErrorType.UNKNOWN
    
    def handle_error(self, message: str, source: str = "system", 
                    level: ErrorLevel = ErrorLevel.CRITICAL,
                    context: Dict[str, Any] = None,
                    show_suggestions: bool = True) -> ErrorInfo:
        """
        Handle an error with automatic type detection and suggestions.
        
        Args:
            message: Error message
            source: Error source
            level: Error level
            context: Additional context
            show_suggestions: Whether to show suggestions
            
        Returns:
            ErrorInfo object
        """
        # Detect error type
        error_type = self.detect_error_type(message, context)
        
        # Get suggestions
        suggestions = []
        if show_suggestions:
            suggestions = self.suggestion_engine.get_suggestions(error_type, context)
        
        # Create error info
        error_info = ErrorInfo(
            error_type=error_type,
            level=level,
            message=message,
            source=source,
            timestamp=time.time(),
            context=context,
            suggestions=suggestions
        )
        
        # Add to history
        self.error_history.append(error_info)
        
        # Display error
        self.display_error(error_info)
        
        return error_info
    
    def display_error(self, error_info: ErrorInfo):
        """
        Display an error with formatting and suggestions.
        
        Args:
            error_info: Error information
        """
        # Format and display error
        error_display = self.formatter.format_error(error_info)
        print(f"\\n{error_display}")
        
        # Display suggestions if available
        if error_info.suggestions:
            suggestions_display = self.formatter.format_suggestions(error_info.suggestions)
            print(f"\\n{suggestions_display}")
        
        print()  # Add spacing
    
    def show_error_summary(self) -> str:
        """
        Show a summary of all errors encountered.
        
        Returns:
            Formatted error summary
        """
        if not self.error_history:
            return "Aucune erreur enregistrée."
        
        summary = self.formatter.format_error_summary(self.error_history)
        print(summary)
        return summary
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get statistics about errors encountered.
        
        Returns:
            Error statistics
        """
        if not self.error_history:
            return {'total_errors': 0}
        
        # Count by type
        type_counts = {}
        level_counts = {}
        source_counts = {}
        
        for error in self.error_history:
            # Count by type
            error_type = error.error_type.value
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
            
            # Count by level
            level = error.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
            
            # Count by source
            source = error.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'by_type': type_counts,
            'by_level': level_counts,
            'by_source': source_counts,
            'most_recent': self.error_history[-1].timestamp if self.error_history else None
        }
    
    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()


# Convenience functions
def create_error_handler(use_colors: bool = True) -> EnhancedErrorHandler:
    """
    Create an enhanced error handler.
    
    Args:
        use_colors: Whether to use colors
        
    Returns:
        EnhancedErrorHandler instance
    """
    return EnhancedErrorHandler(use_colors=use_colors)


def handle_quick_error(message: str, source: str = "system", 
                      level: ErrorLevel = ErrorLevel.CRITICAL,
                      use_colors: bool = True) -> ErrorInfo:
    """
    Quick error handling function.
    
    Args:
        message: Error message
        source: Error source
        level: Error level
        use_colors: Whether to use colors
        
    Returns:
        ErrorInfo object
    """
    handler = create_error_handler(use_colors)
    return handler.handle_error(message, source, level)