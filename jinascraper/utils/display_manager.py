"""Main display manager for enhanced CLI interface."""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .terminal_utils import TerminalUtils, colorize, create_box, create_separator
from .progress_manager import ProgressManager, ProgressBar
from .report_generator import ReportGenerator, ReportData


@dataclass
class DisplayConfig:
    """Configuration for display manager."""
    use_colors: bool = True
    show_progress: bool = True
    show_metrics: bool = True
    refresh_rate: float = 0.1  # seconds
    terminal_width: Optional[int] = None
    terminal_height: Optional[int] = None
    compact_mode: bool = False
    quiet_mode: bool = False
    verbose_mode: bool = False


@dataclass
class DisplayState:
    """Current state of the display."""
    current_stage: str = ""
    stage_description: str = ""
    sources_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    global_metrics: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)


class DisplayManager:
    """Main display manager for enhanced CLI interface."""
    
    def __init__(self, config: Optional[DisplayConfig] = None):
        """
        Initialize the display manager.
        
        Args:
            config: Display configuration
        """
        self.config = config or DisplayConfig()
        self.state = DisplayState()
        
        # Initialize components
        self.terminal = TerminalUtils()
        self.progress_manager = ProgressManager(
            use_colors=self.config.use_colors,
            terminal_width=self.config.terminal_width
        )
        self.report_generator = ReportGenerator(
            use_colors=self.config.use_colors,
            terminal_width=self.config.terminal_width
        )
        
        # Auto-detect terminal size if not provided
        if self.config.terminal_width is None or self.config.terminal_height is None:
            width, height = self.terminal.get_terminal_size()
            self.config.terminal_width = width
            self.config.terminal_height = height
        
        # Display control
        self._display_active = False
        self._refresh_task = None
        self._last_lines_count = 0
        
    async def start_display(self):
        """Start the display manager."""
        if self._display_active:
            return
            
        self._display_active = True
        
        # Show startup header
        if not self.config.quiet_mode:
            await self._show_startup_header()
        
        # Start refresh task if progress is enabled
        if self.config.show_progress and not self.config.quiet_mode:
            self._refresh_task = asyncio.create_task(self._refresh_loop())
    
    async def stop_display(self):
        """Stop the display manager."""
        self._display_active = False
        
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
    
    @asynccontextmanager
    async def display_context(self):
        """Context manager for display lifecycle."""
        await self.start_display()
        try:
            yield self
        finally:
            await self.stop_display()
    
    def set_stage(self, stage: str, description: str = ""):
        """
        Set the current processing stage.
        
        Args:
            stage: Stage name
            description: Stage description
        """
        self.state.current_stage = stage
        self.state.stage_description = description
        self.state.last_update = time.time()
        
        if not self.config.quiet_mode:
            stage_msg = f"🔍 {stage.upper()}"
            if description:
                stage_msg += f" - {description.upper()}"
            
            if self.config.use_colors:
                stage_msg = colorize(stage_msg, 'bright_blue', bold=True)
            
            print(f"\n{stage_msg}")
            print(TerminalUtils.create_separator(width=self.config.terminal_width, style='thick'))
    
    def update_source_progress(self, source_name: str, progress: int, total: int, 
                             status: str = "running", **kwargs):
        """
        Update progress for a specific source.
        
        Args:
            source_name: Name of the source
            progress: Current progress
            total: Total items
            status: Current status
            **kwargs: Additional metadata
        """
        self.state.sources_progress[source_name] = {
            'progress': progress,
            'total': total,
            'status': status,
            'last_update': time.time(),
            **kwargs
        }
        self.state.last_update = time.time()
    
    def update_global_metrics(self, metrics: Dict[str, Any]):
        """
        Update global metrics.
        
        Args:
            metrics: Metrics dictionary
        """
        self.state.global_metrics.update(metrics)
        self.state.last_update = time.time()
    
    def add_message(self, message: str, level: str = "info", source: str = "system"):
        """
        Add a message to the display.
        
        Args:
            message: Message text
            level: Message level (info, warning, error)
            source: Message source
        """
        msg_data = {
            'message': message,
            'level': level,
            'source': source,
            'timestamp': time.time()
        }
        
        self.state.messages.append(msg_data)
        
        # Also add to appropriate category
        if level == "error":
            self.state.errors.append(msg_data)
        elif level == "warning":
            self.state.warnings.append(msg_data)
        
        # Keep only recent messages
        max_messages = 100
        if len(self.state.messages) > max_messages:
            self.state.messages = self.state.messages[-max_messages:]
        
        self.state.last_update = time.time()
        
        # Immediate display for important messages
        if level in ["error", "warning"] and not self.config.quiet_mode:
            self._display_immediate_message(msg_data)
    
    def show_final_report(self, results: ReportData) -> str:
        """
        Show the final report.
        
        Args:
            results: Report data
            
        Returns:
            Generated report string
        """
        if self.config.quiet_mode:
            return ""
        
        # Clear current display
        self._clear_display()
        
        # Generate and show report
        report = self.report_generator.generate_final_report(results)
        print(report)
        
        return report
    
    def show_error_summary(self, errors: List[Dict[str, Any]]) -> str:
        """
        Show error summary.
        
        Args:
            errors: List of errors
            
        Returns:
            Generated error report
        """
        if not errors or self.config.quiet_mode:
            return ""
        
        report = self.report_generator.generate_error_report(errors)
        print(f"\n{report}")
        
        return report
    
    def create_progress_bar(self, bar_id: str, total: int, description: str = "",
                          style: str = "modern") -> ProgressBar:
        """
        Create a new progress bar.
        
        Args:
            bar_id: Unique identifier for the bar
            total: Total items
            description: Bar description
            style: Progress bar style
            
        Returns:
            Progress bar instance
        """
        return self.progress_manager.create_progress_bar(
            bar_id=bar_id,
            total=total,
            description=description,
            style=style
        )
    
    def update_progress_bar(self, bar_id: str, progress: int, **kwargs):
        """
        Update a progress bar.
        
        Args:
            bar_id: Bar identifier
            progress: Current progress
            **kwargs: Additional parameters
        """
        self.progress_manager.update_progress(bar_id, progress, **kwargs)
    
    def remove_progress_bar(self, bar_id: str):
        """
        Remove a progress bar.
        
        Args:
            bar_id: Bar identifier
        """
        self.progress_manager.remove_progress_bar(bar_id)
    
    async def _show_startup_header(self):
        """Show the startup header."""
        # Get system configuration
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
    
    async def _refresh_loop(self):
        """Main refresh loop for dynamic display."""
        try:
            while self._display_active:
                if self.state.sources_progress and not self.config.compact_mode:
                    await self._refresh_display()
                
                await asyncio.sleep(self.config.refresh_rate)
        except asyncio.CancelledError:
            pass
    
    async def _refresh_display(self):
        """Refresh the current display."""
        if self.config.quiet_mode:
            return
        
        # Clear previous display
        self._clear_display()
        
        # Show current stage progress
        if self.state.current_stage and self.state.sources_progress:
            progress_lines = self._generate_progress_display()
            print(progress_lines)
            
            # Count lines for next clear
            self._last_lines_count = len(progress_lines.split('\n'))
    
    def _generate_progress_display(self) -> str:
        """Generate the current progress display."""
        lines = []
        
        # Stage header (if not already shown)
        current_time = time.time()
        elapsed = current_time - self.state.start_time
        
        if elapsed > 1:  # Only show after 1 second
            # Progress for each source
            for source_name, progress_data in self.state.sources_progress.items():
                line = self._format_source_progress_line(source_name, progress_data)
                lines.append(line)
            
            # Summary line
            if self.state.global_metrics:
                summary_line = self._format_summary_line()
                lines.append("")
                lines.append(summary_line)
        
        return '\n'.join(lines)
    
    def _format_source_progress_line(self, source_name: str, progress_data: Dict[str, Any]) -> str:
        """Format a single source progress line."""
        progress = progress_data.get('progress', 0)
        total = progress_data.get('total', 100)
        status = progress_data.get('status', 'running')
        urls_found = progress_data.get('urls_found', 0)
        
        # Create progress bar
        bar_width = 32
        if total > 0:
            filled = int((progress / total) * bar_width)
        else:
            filled = 0
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Status icon and message
        if status == 'completed':
            if urls_found > 0:
                icon = "✅"
                message = f"{urls_found} URLs trouvées"
                color = 'green'
            else:
                icon = "⚠️"
                message = "Aucune URL trouvée"
                color = 'yellow'
        elif status == 'error':
            icon = "❌"
            message = progress_data.get('error_message', 'Erreur')
            color = 'red'
        elif status == 'timeout':
            icon = "⚠️"
            message = "Timeout détecté"
            color = 'yellow'
        else:
            icon = "⏳"
            message = f"{urls_found} URLs trouvées..."
            color = 'cyan'
        
        # Format line
        percentage = (progress / max(total, 1)) * 100
        
        if self.config.use_colors:
            name_colored = colorize(f"📡 {source_name:<15}", 'bright_white')
            bar_colored = colorize(bar, color)
            percentage_colored = colorize(f"{percentage:3.0f}%", color)
            status_colored = colorize(f"{icon} {message}", color)
            return f"{name_colored} [{bar_colored}] {percentage_colored} {status_colored}"
        else:
            return f"📡 {source_name:<15} [{bar}] {percentage:3.0f}% {icon} {message}"
    
    def _format_summary_line(self) -> str:
        """Format the summary line."""
        cache_hits = self.state.global_metrics.get('cache_hits', 0)
        api_savings = self.state.global_metrics.get('api_savings', 0)
        elapsed_time = time.time() - self.state.start_time
        
        # Format time
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.0f}s"
        else:
            time_str = f"{elapsed_time/60:.1f}m"
        
        summary_text = f"💾 Cache: {cache_hits} URLs déjà vues"
        if api_savings > 0:
            summary_text += f" (économie de {api_savings} appels API)"
        summary_text += f" | ⏱️ Temps écoulé: {time_str}"
        
        if self.config.use_colors:
            return colorize(summary_text, 'bright_magenta')
        return summary_text
    
    def _clear_display(self):
        """Clear the current display."""
        if self._last_lines_count > 0:
            # Move cursor up and clear lines
            for _ in range(self._last_lines_count):
                print('\033[1A\033[2K', end='')  # Move up and clear line
            self._last_lines_count = 0
    
    def _display_immediate_message(self, msg_data: Dict[str, Any]):
        """Display an immediate message."""
        level = msg_data['level']
        message = msg_data['message']
        source = msg_data['source']
        
        if level == "error":
            icon = "❌"
            color = 'red'
        elif level == "warning":
            icon = "⚠️"
            color = 'yellow'
        else:
            icon = "ℹ️"
            color = 'cyan'
        
        formatted_msg = f"{icon} {source}: {message}"
        
        if self.config.use_colors:
            formatted_msg = colorize(formatted_msg, color)
        
        print(formatted_msg)
    
    def get_display_stats(self) -> Dict[str, Any]:
        """Get current display statistics."""
        return {
            'active': self._display_active,
            'current_stage': self.state.current_stage,
            'sources_count': len(self.state.sources_progress),
            'messages_count': len(self.state.messages),
            'errors_count': len(self.state.errors),
            'warnings_count': len(self.state.warnings),
            'uptime': time.time() - self.state.start_time,
            'last_update': self.state.last_update
        }


# Convenience functions for common display patterns
async def create_display_session(config: Optional[DisplayConfig] = None) -> DisplayManager:
    """
    Create and start a display session.
    
    Args:
        config: Display configuration
        
    Returns:
        Started display manager
    """
    manager = DisplayManager(config)
    await manager.start_display()
    return manager


def create_simple_display(use_colors: bool = True, quiet: bool = False) -> DisplayManager:
    """
    Create a simple display manager.
    
    Args:
        use_colors: Whether to use colors
        quiet: Whether to use quiet mode
        
    Returns:
        Display manager
    """
    config = DisplayConfig(
        use_colors=use_colors,
        quiet_mode=quiet,
        show_progress=not quiet
    )
    return DisplayManager(config)


def create_verbose_display(use_colors: bool = True) -> DisplayManager:
    """
    Create a verbose display manager.
    
    Args:
        use_colors: Whether to use colors
        
    Returns:
        Display manager
    """
    config = DisplayConfig(
        use_colors=use_colors,
        verbose_mode=True,
        show_progress=True,
        show_metrics=True,
        refresh_rate=0.05  # Faster refresh for verbose mode
    )
    return DisplayManager(config)


def create_compact_display(use_colors: bool = True) -> DisplayManager:
    """
    Create a compact display manager.
    
    Args:
        use_colors: Whether to use colors
        
    Returns:
        Display manager
    """
    config = DisplayConfig(
        use_colors=use_colors,
        compact_mode=True,
        show_progress=True,
        refresh_rate=0.2  # Slower refresh for compact mode
    )
    return DisplayManager(config)