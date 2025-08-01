"""Terminal utilities for enhanced CLI display."""

import os
import sys
import shutil
from typing import Tuple, Optional
import platform


class TerminalUtils:
    """Utilities for terminal management and display control."""
    
    # ANSI Color Codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'underline': '\033[4m',
        
        # Foreground colors
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        
        # Bright foreground colors
        'bright_black': '\033[90m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
        
        # Background colors
        'bg_black': '\033[40m',
        'bg_red': '\033[41m',
        'bg_green': '\033[42m',
        'bg_yellow': '\033[43m',
        'bg_blue': '\033[44m',
        'bg_magenta': '\033[45m',
        'bg_cyan': '\033[46m',
        'bg_white': '\033[47m',
    }
    
    # ANSI Control Codes
    CONTROLS = {
        'clear_line': '\033[2K',
        'clear_screen': '\033[2J',
        'cursor_home': '\033[H',
        'cursor_up': '\033[{}A',
        'cursor_down': '\033[{}B',
        'cursor_right': '\033[{}C',
        'cursor_left': '\033[{}D',
        'save_cursor': '\033[s',
        'restore_cursor': '\033[u',
        'hide_cursor': '\033[?25l',
        'show_cursor': '\033[?25h',
    }
    
    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        """
        Get the current terminal size.
        
        Returns:
            Tuple of (width, height) in characters
        """
        try:
            # Try to get terminal size using shutil (Python 3.3+)
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except (AttributeError, OSError):
            try:
                # Fallback for older Python versions or special cases
                import struct
                import fcntl
                import termios
                
                # Get terminal size using ioctl
                h, w, hp, wp = struct.unpack('HHHH',
                    fcntl.ioctl(0, termios.TIOCGWINSZ,
                    struct.pack('HHHH', 0, 0, 0, 0)))
                return w, h
            except (ImportError, OSError):
                # Final fallback - return default size
                return 80, 24
    
    @staticmethod
    def supports_colors() -> bool:
        """
        Check if the terminal supports ANSI colors.
        
        Returns:
            True if colors are supported, False otherwise
        """
        # Check if we're in a known color-supporting environment
        if hasattr(sys.stdout, 'isatty') and not sys.stdout.isatty():
            return False
        
        # Check environment variables
        term = os.environ.get('TERM', '').lower()
        colorterm = os.environ.get('COLORTERM', '').lower()
        
        # Known color-supporting terminals
        color_terms = [
            'xterm', 'xterm-color', 'xterm-256color',
            'screen', 'screen-256color',
            'tmux', 'tmux-256color',
            'rxvt', 'ansi', 'cygwin'
        ]
        
        # Check for color support indicators
        if any(ct in term for ct in color_terms):
            return True
        
        if colorterm in ['truecolor', '24bit']:
            return True
        
        # Windows-specific checks
        if platform.system() == 'Windows':
            # Windows 10 version 1607+ supports ANSI colors
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                winreg.CloseKey(key)
                return int(build) >= 14393
            except (ImportError, OSError, ValueError):
                # Check if we're in Windows Terminal or similar
                return 'WT_SESSION' in os.environ or 'TERM_PROGRAM' in os.environ
        
        # Default to True for Unix-like systems
        return platform.system() != 'Windows'
    
    @staticmethod
    def clear_line() -> None:
        """Clear the current line."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['clear_line'], end='', flush=True)
    
    @staticmethod
    def move_cursor_up(lines: int = 1) -> None:
        """
        Move cursor up by specified number of lines.
        
        Args:
            lines: Number of lines to move up
        """
        if TerminalUtils.supports_colors() and lines > 0:
            print(TerminalUtils.CONTROLS['cursor_up'].format(lines), end='', flush=True)
    
    @staticmethod
    def move_cursor_down(lines: int = 1) -> None:
        """
        Move cursor down by specified number of lines.
        
        Args:
            lines: Number of lines to move down
        """
        if TerminalUtils.supports_colors() and lines > 0:
            print(TerminalUtils.CONTROLS['cursor_down'].format(lines), end='', flush=True)
    
    @staticmethod
    def move_cursor_left(columns: int = 1) -> None:
        """
        Move cursor left by specified number of columns.
        
        Args:
            columns: Number of columns to move left
        """
        if TerminalUtils.supports_colors() and columns > 0:
            print(TerminalUtils.CONTROLS['cursor_left'].format(columns), end='', flush=True)
    
    @staticmethod
    def move_cursor_right(columns: int = 1) -> None:
        """
        Move cursor right by specified number of columns.
        
        Args:
            columns: Number of columns to move right
        """
        if TerminalUtils.supports_colors() and columns > 0:
            print(TerminalUtils.CONTROLS['cursor_right'].format(columns), end='', flush=True)
    
    @staticmethod
    def hide_cursor() -> None:
        """Hide the terminal cursor."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['hide_cursor'], end='', flush=True)
    
    @staticmethod
    def show_cursor() -> None:
        """Show the terminal cursor."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['show_cursor'], end='', flush=True)
    
    @staticmethod
    def save_cursor_position() -> None:
        """Save the current cursor position."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['save_cursor'], end='', flush=True)
    
    @staticmethod
    def restore_cursor_position() -> None:
        """Restore the saved cursor position."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['restore_cursor'], end='', flush=True)
    
    @staticmethod
    def clear_screen() -> None:
        """Clear the entire screen."""
        if TerminalUtils.supports_colors():
            print(TerminalUtils.CONTROLS['clear_screen'], end='', flush=True)
            print(TerminalUtils.CONTROLS['cursor_home'], end='', flush=True)
        else:
            # Fallback for systems without ANSI support
            os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    @staticmethod
    def colorize(text: str, color: str, background: Optional[str] = None, 
                 bold: bool = False, underline: bool = False) -> str:
        """
        Apply color and formatting to text.
        
        Args:
            text: Text to colorize
            color: Foreground color name
            background: Background color name (optional)
            bold: Apply bold formatting
            underline: Apply underline formatting
            
        Returns:
            Formatted text string
        """
        if not TerminalUtils.supports_colors():
            return text
        
        # Build format string
        format_codes = []
        
        if bold:
            format_codes.append(TerminalUtils.COLORS['bold'])
        
        if underline:
            format_codes.append(TerminalUtils.COLORS['underline'])
        
        if color in TerminalUtils.COLORS:
            format_codes.append(TerminalUtils.COLORS[color])
        
        if background and f'bg_{background}' in TerminalUtils.COLORS:
            format_codes.append(TerminalUtils.COLORS[f'bg_{background}'])
        
        if not format_codes:
            return text
        
        # Apply formatting
        format_start = ''.join(format_codes)
        format_end = TerminalUtils.COLORS['reset']
        
        return f"{format_start}{text}{format_end}"
    
    @staticmethod
    def create_box(text: str, width: Optional[int] = None, 
                   style: str = 'single', padding: int = 1) -> str:
        """
        Create a text box with borders.
        
        Args:
            text: Text to put in the box
            width: Box width (auto-calculated if None)
            style: Border style ('single', 'double', 'rounded')
            padding: Internal padding
            
        Returns:
            Formatted box as string
        """
        # Box drawing characters
        box_chars = {
            'single': {
                'top_left': '┌', 'top_right': '┐',
                'bottom_left': '└', 'bottom_right': '┘',
                'horizontal': '─', 'vertical': '│'
            },
            'double': {
                'top_left': '╔', 'top_right': '╗',
                'bottom_left': '╚', 'bottom_right': '╝',
                'horizontal': '═', 'vertical': '║'
            },
            'rounded': {
                'top_left': '╭', 'top_right': '╮',
                'bottom_left': '╰', 'bottom_right': '╯',
                'horizontal': '─', 'vertical': '│'
            }
        }
        
        chars = box_chars.get(style, box_chars['single'])
        
        # Split text into lines
        lines = text.split('\n')
        
        # Calculate width
        if width is None:
            width = max(len(line) for line in lines) + 2 * padding + 2
        
        content_width = width - 2 * padding - 2
        
        # Build box
        result = []
        
        # Top border
        result.append(chars['top_left'] + chars['horizontal'] * (width - 2) + chars['top_right'])
        
        # Empty padding lines at top
        for _ in range(padding):
            result.append(chars['vertical'] + ' ' * (width - 2) + chars['vertical'])
        
        # Content lines
        for line in lines:
            # Truncate or pad line to fit
            if len(line) > content_width:
                line = line[:content_width - 3] + '...'
            else:
                line = line.ljust(content_width)
            
            result.append(chars['vertical'] + ' ' * padding + line + ' ' * padding + chars['vertical'])
        
        # Empty padding lines at bottom
        for _ in range(padding):
            result.append(chars['vertical'] + ' ' * (width - 2) + chars['vertical'])
        
        # Bottom border
        result.append(chars['bottom_left'] + chars['horizontal'] * (width - 2) + chars['bottom_right'])
        
        return '\n'.join(result)
    
    @staticmethod
    def create_separator(width: Optional[int] = None, char: str = '─', 
                        style: str = 'simple') -> str:
        """
        Create a horizontal separator line.
        
        Args:
            width: Separator width (terminal width if None)
            char: Character to use for separator
            style: Separator style ('simple', 'thick', 'double')
            
        Returns:
            Separator string
        """
        if width is None:
            width, _ = TerminalUtils.get_terminal_size()
        
        # Style-specific characters
        style_chars = {
            'simple': '─',
            'thick': '━',
            'double': '═'
        }
        
        char = style_chars.get(style, char)
        return char * width
    
    @staticmethod
    def truncate_text(text: str, max_width: int, suffix: str = '...') -> str:
        """
        Truncate text to fit within specified width.
        
        Args:
            text: Text to truncate
            max_width: Maximum width
            suffix: Suffix to add when truncating
            
        Returns:
            Truncated text
        """
        if len(text) <= max_width:
            return text
        
        if max_width <= len(suffix):
            return suffix[:max_width]
        
        return text[:max_width - len(suffix)] + suffix
    
    @staticmethod
    def center_text(text: str, width: Optional[int] = None) -> str:
        """
        Center text within specified width.
        
        Args:
            text: Text to center
            width: Width to center within (terminal width if None)
            
        Returns:
            Centered text
        """
        if width is None:
            width, _ = TerminalUtils.get_terminal_size()
        
        if len(text) >= width:
            return text
        
        padding = (width - len(text)) // 2
        return ' ' * padding + text
    
    @staticmethod
    def get_platform_info() -> dict:
        """
        Get platform-specific information for terminal handling.
        
        Returns:
            Dictionary with platform information
        """
        return {
            'system': platform.system(),
            'platform': platform.platform(),
            'terminal': os.environ.get('TERM', 'unknown'),
            'colorterm': os.environ.get('COLORTERM', 'unknown'),
            'supports_colors': TerminalUtils.supports_colors(),
            'terminal_size': TerminalUtils.get_terminal_size(),
            'is_windows': platform.system() == 'Windows',
            'is_unix': platform.system() in ['Linux', 'Darwin'],
        }


# Convenience functions for common operations
def colorize(text: str, color: str, **kwargs) -> str:
    """Convenience function for colorizing text."""
    return TerminalUtils.colorize(text, color, **kwargs)

def create_box(text: str, **kwargs) -> str:
    """Convenience function for creating text boxes."""
    return TerminalUtils.create_box(text, **kwargs)

def create_separator(**kwargs) -> str:
    """Convenience function for creating separators."""
    return TerminalUtils.create_separator(**kwargs)

def get_terminal_size() -> Tuple[int, int]:
    """Convenience function for getting terminal size."""
    return TerminalUtils.get_terminal_size()

def supports_colors() -> bool:
    """Convenience function for checking color support."""
    return TerminalUtils.supports_colors()