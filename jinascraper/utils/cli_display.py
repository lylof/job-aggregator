"""
CLI Display - Wrapper class for enhanced CLI interface.

This module provides a simplified interface that matches the original
task specification while using our DisplayManager internally.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .display_manager import DisplayManager, DisplayConfig as DisplayManagerConfig
from .report_generator import ReportGenerator, ReportData
from .terminal_utils import TerminalUtils, colorize
from .error_handler import EnhancedErrorHandler, ErrorLevel, ErrorType


@dataclass
class DisplayConfig:
    """Configuration for CLI display."""
    use_colors: bool = True
    verbose: bool = False
    quiet: bool = False
    compact: bool = False
    terminal_width: Optional[int] = None


class CLIDisplay:
    """
    Main CLI display class that orchestrates visual components.
    
    This class provides the interface specified in the original task
    while using our DisplayManager internally for the actual rendering.
    """
    
    def __init__(self, config: Optional[DisplayConfig] = None):
        """
        Initialize the CLI display.
        
        Args:
            config: Display configuration
        """
        self.config = config or DisplayConfig()
        
        # Create internal display manager
        display_manager_config = DisplayManagerConfig(
            use_colors=self.config.use_colors,
            show_progress=not self.config.quiet,
            show_metrics=True,
            quiet_mode=self.config.quiet,
            verbose_mode=self.config.verbose,
            compact_mode=self.config.compact,
            terminal_width=self.config.terminal_width
        )
        
        self.display_manager = DisplayManager(display_manager_config)
        self.report_generator = ReportGenerator(
            use_colors=self.config.use_colors,
            terminal_width=self.config.terminal_width
        )
        self.error_handler = EnhancedErrorHandler(
            use_colors=self.config.use_colors,
            terminal_width=self.config.terminal_width
        )
        
        self._active = False
    
    async def start(self):
        """Start the CLI display."""
        if not self._active:
            await self.display_manager.start_display()
            self._active = True
    
    async def stop(self):
        """Stop the CLI display."""
        if self._active:
            await self.display_manager.stop_display()
            self._active = False
    
    def show_startup_header(self):
        """Show the startup header with JinaScraper logo."""
        if self.config.quiet:
            return
        
        # Generate startup report
        config_data = {
            'sources': [
                {'name': 'Emploi.tg', 'active': True, 'description': 'Source gouvernementale principale'},
                {'name': 'ANPE Togo', 'active': True, 'description': 'Agence nationale pour l\'emploi'},
                {'name': 'EmploiTogo.info', 'active': True, 'description': 'Plateforme privée d\'emploi'},
                {'name': 'YOP L-FRII', 'active': True, 'description': 'Réseau social professionnel'},
                {'name': 'LinkedIn Togo', 'active': False, 'description': 'Timeouts fréquents'},
                {'name': 'Indeed Togo', 'active': False, 'description': 'HTTP 400 - Temporairement indisponible'}
            ],
            'cache_status': 'connected',
            'ai_services': 'operational'
        }
        
        header = self.report_generator.generate_startup_report(config_data)
        print(header)
        print()
    
    def show_configuration_summary(self, config: Dict[str, Any]):
        """
        Show configuration summary with table of sources and their status.
        
        Args:
            config: Configuration dictionary
        """
        if self.config.quiet:
            return
        
        # Extract sources information
        sources = config.get('sources', [])
        if sources:
            table_data = []
            for source in sources:
                status_icon = "✅" if source.get('active', True) else "❌"
                status_text = "Actif" if source.get('active', True) else "Inactif"
                
                if self.config.use_colors:
                    if source.get('active', True):
                        status_display = colorize(f"{status_icon} {status_text}", 'green')
                    else:
                        status_display = colorize(f"{status_icon} {status_text}", 'red')
                else:
                    status_display = f"{status_icon} {status_text}"
                
                table_data.append({
                    'Source': source.get('name', 'Unknown'),
                    'Statut': status_display,
                    'Description': source.get('description', 'N/A')
                })
            
            title = "📊 Configuration des Sources:"
            if self.config.use_colors:
                title = colorize(title, 'bright_blue', bold=True)
            
            print(title)
            table = self.report_generator.create_status_table(table_data)
            print(table)
            print()
    
    def show_stage_header(self, stage: str, description: str = ""):
        """
        Show stage header with visual separators.
        
        Args:
            stage: Stage name (e.g., "Stage 1", "Stage 2")
            description: Stage description
        """
        self.display_manager.set_stage(stage, description)
    
    def update_progress(self, source_name: str, progress: int, total: int, 
                       status: str = "running", **kwargs):
        """
        Update progress for a specific source with real-time display.
        
        Args:
            source_name: Name of the source
            progress: Current progress
            total: Total items
            status: Current status
            **kwargs: Additional metadata
        """
        self.display_manager.update_source_progress(
            source_name=source_name,
            progress=progress,
            total=total,
            status=status,
            **kwargs
        )
    
    def show_error(self, error_type: str, message: str, source: str = "system", 
                   suggestions: List[str] = None, context: Dict[str, Any] = None):
        """
        Show formatted error with automatic suggestions using enhanced error handler.
        
        Args:
            error_type: Type of error (critical, warning, info, success)
            message: Error message
            source: Error source
            suggestions: List of suggestions (optional, auto-generated if None)
            context: Additional context for error
        """
        if self.config.quiet and error_type not in ['critical']:
            return
        
        # Map error types to error levels
        level_map = {
            'critical': ErrorLevel.CRITICAL,
            'warning': ErrorLevel.WARNING,
            'info': ErrorLevel.INFO,
            'success': ErrorLevel.SUCCESS
        }
        
        level = level_map.get(error_type, ErrorLevel.CRITICAL)
        
        # Use enhanced error handler
        error_info = self.error_handler.handle_error(
            message=message,
            source=source,
            level=level,
            context=context,
            show_suggestions=suggestions is None  # Auto-generate if not provided
        )
        
        # If custom suggestions provided, show them instead
        if suggestions and not self.config.quiet:
            print()
            suggestion_title = "💡 Suggestions personnalisées:"
            if self.config.use_colors:
                suggestion_title = colorize(suggestion_title, 'yellow', bold=True)
            print(suggestion_title)
            
            for suggestion in suggestions:
                suggestion_line = f"  • {suggestion}"
                if self.config.use_colors:
                    suggestion_line = colorize(suggestion_line, 'yellow')
                print(suggestion_line)
            print()
        
        return error_info
    
    def show_cache_stats(self, stats: Dict[str, Any]):
        """
        Show Redis cache statistics with visual indicators.
        
        Args:
            stats: Cache statistics dictionary
        """
        if self.config.quiet:
            return
        
        hit_rate = stats.get('hit_rate', 0.0)
        total_keys = stats.get('total_keys', 0)
        memory_usage = stats.get('memory_usage', 0)
        
        # Create cache report
        lines = []
        
        title = "💾 STATISTIQUES CACHE REDIS"
        if self.config.use_colors:
            title = colorize(title, 'bright_blue', bold=True)
        lines.append(title)
        
        # Hit rate bar
        bar_width = 40
        filled = int(hit_rate * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        if self.config.use_colors:
            if hit_rate >= 0.8:
                bar = colorize(bar, 'green')
            elif hit_rate >= 0.5:
                bar = colorize(bar, 'yellow')
            else:
                bar = colorize(bar, 'red')
        
        hit_rate_line = f"Hit Rate: [{bar}] {hit_rate*100:.0f}%"
        lines.append(hit_rate_line)
        
        # Additional stats
        stats_line = f"Clés totales: {total_keys} | Mémoire: {memory_usage}MB"
        if self.config.use_colors:
            stats_line = colorize(stats_line, 'cyan')
        lines.append(stats_line)
        
        print("\\n".join(lines))
        print()
    
    def show_notification(self, notification_type: str, message: str, 
                         context: Dict[str, Any] = None):
        """
        Show non-intrusive notification.
        
        Args:
            notification_type: Type of notification
            message: Notification message
            context: Additional context
        """
        if self.config.quiet:
            return
        
        # Map notification types to icons and colors
        type_config = {
            'success': ('🎉', 'green'),
            'info': ('ℹ️', 'cyan'),
            'warning': ('⚠️', 'yellow'),
            'error': ('❌', 'red'),
            'cache': ('💾', 'blue'),
            'discovery': ('🔍', 'magenta')
        }
        
        icon, color = type_config.get(notification_type, ('📢', 'white'))
        
        notification_line = f"{icon} {message}"
        if self.config.use_colors:
            notification_line = colorize(notification_line, color)
        
        print(notification_line)
    
    def generate_final_report(self, results: Dict[str, Any]) -> str:
        """
        Generate and display the final comprehensive report.
        
        Args:
            results: Results dictionary
            
        Returns:
            Generated report string
        """
        # Convert results to ReportData format
        report_data = ReportData(
            total_sources=results.get('total_sources', 6),
            successful_sources=results.get('successful_sources', 4),
            total_urls_found=results.get('total_urls_found', 0),
            total_jobs_processed=results.get('jobs_processed', 0),
            cache_hit_rate=results.get('cache_hit_rate', 0.0),
            processing_time=results.get('processing_time', 0.0),
            errors=results.get('errors', []),
            warnings=results.get('warnings', []),
            performance_metrics=results.get('performance_metrics', {}),
            source_details=results.get('source_details', [])
        )
        
        return self.display_manager.show_final_report(report_data)
    
    def show_error_summary(self) -> str:
        """
        Show a summary of all errors encountered.
        
        Returns:
            Formatted error summary
        """
        return self.error_handler.show_error_summary()
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Error statistics dictionary
        """
        return self.error_handler.get_error_stats()
    
    def clear_errors(self):
        """Clear the error history."""
        self.error_handler.clear_error_history()
    
    def get_display_stats(self) -> Dict[str, Any]:
        """
        Get current display statistics including errors.
        
        Returns:
            Display statistics dictionary
        """
        display_stats = self.display_manager.get_display_stats()
        error_stats = self.error_handler.get_error_stats()
        
        # Combine stats
        combined_stats = {
            **display_stats,
            'error_stats': error_stats
        }
        
        return combined_stats


# Convenience functions
def create_cli_display(use_colors: bool = True, verbose: bool = False, 
                      quiet: bool = False, compact: bool = False) -> CLIDisplay:
    """
    Create a CLI display instance with the specified configuration.
    
    Args:
        use_colors: Whether to use colors
        verbose: Verbose mode
        quiet: Quiet mode
        compact: Compact mode
        
    Returns:
        CLIDisplay instance
    """
    config = DisplayConfig(
        use_colors=use_colors,
        verbose=verbose,
        quiet=quiet,
        compact=compact
    )
    return CLIDisplay(config)


def create_default_cli_display() -> CLIDisplay:
    """
    Create a CLI display with default settings.
    
    Returns:
        CLIDisplay instance with default configuration
    """
    return create_cli_display()