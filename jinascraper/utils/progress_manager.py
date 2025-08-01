"""Progress management system for enhanced CLI display."""

import time
import threading
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from .terminal_utils import TerminalUtils, colorize


@dataclass
class ProgressState:
    """State of a progress operation."""
    name: str
    current: int
    total: int
    start_time: float
    message: str = ""
    completed: bool = False
    success: bool = True
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total <= 0:
            return 0.0
        return min((self.current / self.total) * 100, 100.0)
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> float:
        """Estimate remaining time in seconds."""
        if self.current <= 0 or self.completed:
            return 0.0
        
        rate = self.current / self.elapsed_time
        if rate <= 0:
            return 0.0
        
        remaining_items = max(self.total - self.current, 0)
        return remaining_items / rate
    
    @property
    def rate(self) -> float:
        """Calculate processing rate (items per second)."""
        if self.elapsed_time <= 0:
            return 0.0
        return self.current / self.elapsed_time


class ProgressBar:
    """Individual progress bar with customizable appearance."""
    
    def __init__(self, name: str, total: int, width: int = 40, 
                 show_percentage: bool = True, show_rate: bool = True,
                 show_eta: bool = True, style: str = 'blocks'):
        """
        Initialize a progress bar.
        
        Args:
            name: Progress bar identifier
            total: Total number of items to process
            width: Width of the progress bar in characters
            show_percentage: Show percentage completion
            show_rate: Show processing rate
            show_eta: Show estimated time remaining
            style: Progress bar style ('blocks', 'ascii', 'dots')
        """
        self.state = ProgressState(name, 0, total, time.time())
        self.width = width
        self.show_percentage = show_percentage
        self.show_rate = show_rate
        self.show_eta = show_eta
        self.style = style
        
        # Style configurations
        self.styles = {
            'blocks': {
                'filled': '█',
                'empty': '░',
                'partial': ['▏', '▎', '▍', '▌', '▋', '▊', '▉']
            },
            'ascii': {
                'filled': '=',
                'empty': '-',
                'partial': ['>']
            },
            'dots': {
                'filled': '●',
                'empty': '○',
                'partial': ['◐', '◑', '◒', '◓']
            }
        }
    
    def update(self, current: int, message: str = "") -> None:
        """
        Update progress bar state.
        
        Args:
            current: Current progress value
            message: Optional status message
        """
        self.state.current = min(current, self.state.total)
        self.state.message = message
        
        if self.state.current >= self.state.total:
            self.state.completed = True
    
    def complete(self, success: bool = True, message: str = "") -> None:
        """
        Mark progress bar as completed.
        
        Args:
            success: Whether the operation was successful
            message: Final status message
        """
        self.state.current = self.state.total
        self.state.completed = True
        self.state.success = success
        if message:
            self.state.message = message
    
    def render(self, use_colors: bool = True) -> str:
        """
        Render the progress bar as a string.
        
        Args:
            use_colors: Whether to use colors in output
            
        Returns:
            Formatted progress bar string
        """
        # Calculate progress
        percentage = self.state.percentage
        filled_width = int((percentage / 100) * self.width)
        
        # Get style characters
        style_config = self.styles.get(self.style, self.styles['blocks'])
        filled_char = style_config['filled']
        empty_char = style_config['empty']
        
        # Build progress bar
        bar_filled = filled_char * filled_width
        bar_empty = empty_char * (self.width - filled_width)
        
        # Add partial character for sub-pixel precision
        if filled_width < self.width and self.style in ['blocks', 'dots']:
            partial_chars = style_config.get('partial', [])
            if partial_chars:
                remainder = ((percentage / 100) * self.width) - filled_width
                if remainder > 0:
                    partial_index = int(remainder * len(partial_chars))
                    if partial_index < len(partial_chars):
                        bar_empty = partial_chars[partial_index] + bar_empty[1:]
        
        # Color the progress bar
        if use_colors and TerminalUtils.supports_colors():
            if self.state.completed:
                if self.state.success:
                    bar_filled = colorize(bar_filled, 'green')
                else:
                    bar_filled = colorize(bar_filled, 'red')
            else:
                bar_filled = colorize(bar_filled, 'cyan')
            
            bar_empty = colorize(bar_empty, 'bright_black')
        
        progress_bar = f"[{bar_filled}{bar_empty}]"
        
        # Build info components
        info_parts = []
        
        if self.show_percentage:
            percentage_str = f"{percentage:5.1f}%"
            if use_colors and TerminalUtils.supports_colors():
                if self.state.completed:
                    color = 'green' if self.state.success else 'red'
                    percentage_str = colorize(percentage_str, color, bold=True)
                else:
                    percentage_str = colorize(percentage_str, 'cyan')
            info_parts.append(percentage_str)
        
        # Add status icon
        if self.state.completed:
            if self.state.success:
                icon = colorize('✅', 'green') if use_colors else '[OK]'
            else:
                icon = colorize('❌', 'red') if use_colors else '[FAIL]'
            info_parts.append(icon)
        elif self.state.current > 0:
            icon = colorize('⏳', 'yellow') if use_colors else '[...]'
            info_parts.append(icon)
        
        # Add rate information
        if self.show_rate and self.state.rate > 0:
            rate_str = f"{self.state.rate:.1f}/s"
            if use_colors:
                rate_str = colorize(rate_str, 'bright_blue')
            info_parts.append(rate_str)
        
        # Add ETA information
        if self.show_eta and not self.state.completed and self.state.estimated_remaining > 0:
            eta = self.state.estimated_remaining
            if eta < 60:
                eta_str = f"{eta:.0f}s"
            elif eta < 3600:
                eta_str = f"{eta/60:.1f}m"
            else:
                eta_str = f"{eta/3600:.1f}h"
            
            if use_colors:
                eta_str = colorize(f"ETA {eta_str}", 'bright_magenta')
            else:
                eta_str = f"ETA {eta_str}"
            info_parts.append(eta_str)
        
        # Add current/total counts
        count_str = f"{self.state.current}/{self.state.total}"
        if use_colors:
            count_str = colorize(count_str, 'bright_white')
        info_parts.append(count_str)
        
        # Combine all parts
        info_str = " ".join(info_parts)
        
        # Add message if present
        message_str = ""
        if self.state.message:
            message_str = f" {self.state.message}"
            if use_colors:
                message_str = colorize(message_str, 'bright_yellow')
        
        return f"{progress_bar} {info_str}{message_str}"


class ProgressManager:
    """Manager for multiple progress bars with real-time updates."""
    
    def __init__(self, terminal_width: Optional[int] = None, 
                 update_interval: float = 0.1, use_colors: bool = True):
        """
        Initialize the progress manager.
        
        Args:
            terminal_width: Terminal width (auto-detected if None)
            update_interval: Update interval in seconds
            use_colors: Whether to use colors in output
        """
        if terminal_width is None:
            terminal_width, _ = TerminalUtils.get_terminal_size()
        
        self.terminal_width = terminal_width
        self.update_interval = update_interval
        self.use_colors = use_colors and TerminalUtils.supports_colors()
        
        self.progress_bars: Dict[str, ProgressBar] = {}
        self.display_order: List[str] = []
        self.last_render_lines = 0
        self.lock = threading.Lock()
        self.active = False
    
    def create_progress_bar(self, name: str, total: int, description: str = "",
                          width: Optional[int] = None, **kwargs) -> str:
        """
        Create a new progress bar.
        
        Args:
            name: Unique identifier for the progress bar
            total: Total number of items to process
            description: Human-readable description
            width: Progress bar width (calculated if None)
            **kwargs: Additional arguments for ProgressBar
            
        Returns:
            Progress bar identifier
        """
        with self.lock:
            if width is None:
                # Calculate width based on terminal size and other elements
                reserved_space = 50  # Space for percentage, counts, etc.
                width = max(20, self.terminal_width - reserved_space)
            
            progress_bar = ProgressBar(name, total, width, **kwargs)
            self.progress_bars[name] = progress_bar
            
            if name not in self.display_order:
                self.display_order.append(name)
            
            return name
    
    def update_progress_bar(self, name: str, current: int, message: str = "") -> None:
        """
        Update a progress bar.
        
        Args:
            name: Progress bar identifier
            current: Current progress value
            message: Optional status message
        """
        with self.lock:
            if name in self.progress_bars:
                self.progress_bars[name].update(current, message)
    
    def complete_progress_bar(self, name: str, success: bool = True, 
                            message: str = "") -> None:
        """
        Mark a progress bar as completed.
        
        Args:
            name: Progress bar identifier
            success: Whether the operation was successful
            message: Final status message
        """
        with self.lock:
            if name in self.progress_bars:
                self.progress_bars[name].complete(success, message)
    
    def remove_progress_bar(self, name: str) -> None:
        """
        Remove a progress bar.
        
        Args:
            name: Progress bar identifier
        """
        with self.lock:
            if name in self.progress_bars:
                del self.progress_bars[name]
            if name in self.display_order:
                self.display_order.remove(name)
    
    def render_all_bars(self, show_completed: bool = True) -> List[str]:
        """
        Render all progress bars.
        
        Args:
            show_completed: Whether to show completed progress bars
            
        Returns:
            List of rendered progress bar strings
        """
        with self.lock:
            lines = []
            
            for name in self.display_order:
                if name not in self.progress_bars:
                    continue
                
                progress_bar = self.progress_bars[name]
                
                # Skip completed bars if not showing them
                if not show_completed and progress_bar.state.completed:
                    continue
                
                # Render the progress bar
                bar_line = progress_bar.render(self.use_colors)
                
                # Add description/name prefix
                if name != progress_bar.state.name:
                    prefix = f"{name}: "
                    if self.use_colors:
                        prefix = colorize(prefix, 'bright_white', bold=True)
                    bar_line = prefix + bar_line
                
                lines.append(bar_line)
            
            return lines
    
    def display_bars(self, show_completed: bool = True) -> None:
        """
        Display all progress bars, updating in place.
        
        Args:
            show_completed: Whether to show completed progress bars
        """
        if not self.use_colors:
            # For terminals without color support, just print updates
            lines = self.render_all_bars(show_completed)
            for line in lines:
                print(line)
            return
        
        lines = self.render_all_bars(show_completed)
        
        # Clear previous lines
        if self.last_render_lines > 0:
            TerminalUtils.move_cursor_up(self.last_render_lines)
            for _ in range(self.last_render_lines):
                TerminalUtils.clear_line()
                print()
            TerminalUtils.move_cursor_up(self.last_render_lines)
        
        # Print new lines
        for line in lines:
            print(line)
        
        self.last_render_lines = len(lines)
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get summary statistics for all progress bars.
        
        Returns:
            Dictionary with summary statistics
        """
        with self.lock:
            total_bars = len(self.progress_bars)
            completed_bars = sum(1 for bar in self.progress_bars.values() 
                               if bar.state.completed)
            successful_bars = sum(1 for bar in self.progress_bars.values() 
                                if bar.state.completed and bar.state.success)
            
            total_items = sum(bar.state.total for bar in self.progress_bars.values())
            completed_items = sum(bar.state.current for bar in self.progress_bars.values())
            
            overall_percentage = (completed_items / max(total_items, 1)) * 100
            
            return {
                'total_bars': total_bars,
                'completed_bars': completed_bars,
                'successful_bars': successful_bars,
                'failed_bars': completed_bars - successful_bars,
                'total_items': total_items,
                'completed_items': completed_items,
                'overall_percentage': overall_percentage,
                'all_completed': completed_bars == total_bars,
                'all_successful': successful_bars == completed_bars == total_bars
            }
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all progress bars to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all completed, False if timeout
        """
        start_time = time.time()
        
        while True:
            summary = self.get_summary()
            if summary['all_completed']:
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(self.update_interval)
    
    def clear_display(self) -> None:
        """Clear the progress display."""
        if self.last_render_lines > 0 and self.use_colors:
            TerminalUtils.move_cursor_up(self.last_render_lines)
            for _ in range(self.last_render_lines):
                TerminalUtils.clear_line()
                print()
            TerminalUtils.move_cursor_up(self.last_render_lines)
            self.last_render_lines = 0


# Convenience functions
def create_simple_progress_bar(name: str, total: int, width: int = 40) -> ProgressBar:
    """Create a simple progress bar for standalone use."""
    return ProgressBar(name, total, width)

def demo_progress_bars():
    """Demonstrate progress bar functionality."""
    manager = ProgressManager()
    
    # Create multiple progress bars
    manager.create_progress_bar("download", 100, "Downloading files")
    manager.create_progress_bar("process", 50, "Processing data")
    manager.create_progress_bar("upload", 25, "Uploading results")
    
    # Simulate progress
    import random
    for i in range(100):
        # Update download
        if i < 80:
            manager.update_progress_bar("download", i + 1, f"File {i+1}/100")
        
        # Update process
        if i < 50:
            manager.update_progress_bar("process", i + 1, f"Item {i+1}/50")
        
        # Update upload
        if i < 25:
            manager.update_progress_bar("upload", i + 1, f"Chunk {i+1}/25")
        
        # Display updates
        manager.display_bars()
        time.sleep(0.05)
    
    # Complete all bars
    manager.complete_progress_bar("download", True, "Download complete")
    manager.complete_progress_bar("process", True, "Processing complete")
    manager.complete_progress_bar("upload", True, "Upload complete")
    
    # Final display
    manager.display_bars()
    print("\nAll operations completed!")
    
    return manager.get_summary()