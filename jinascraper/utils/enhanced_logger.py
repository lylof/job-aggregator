"""
Enhanced Logger for JinaScraper CLI
Provides beautiful, readable logging with emojis, colors, and structured output.
"""

import sys
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class LogLevel(Enum):
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2


class EnhancedLogger:
    """Enhanced logger with beautiful formatting and level control."""
    
    def __init__(self, level: LogLevel = LogLevel.NORMAL, use_colors: bool = True, show_urls: int = 3):
        self.level = level
        self.use_colors = use_colors
        self.show_urls = show_urls
        
        # Color codes
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'gray': '\033[90m',
        } if use_colors else {key: '' for key in ['reset', 'bold', 'green', 'red', 'yellow', 'blue', 'cyan', 'gray']}
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def _should_log(self, min_level: LogLevel) -> bool:
        """Check if message should be logged based on current level."""
        return self.level.value >= min_level.value
    
    def print_header(self, title: str, emoji: str = "🚀", min_level: LogLevel = LogLevel.NORMAL):
        """Print a main header with separator line."""
        if not self._should_log(min_level):
            return
            
        separator = "═" * 50
        header_text = f"{emoji} {title.upper()}"
        
        print(f"\n{self._colorize(separator, 'cyan')}")
        print(f"{self._colorize(header_text, 'bold')}")
        print(f"{self._colorize(separator, 'cyan')}")
    
    def print_section(self, title: str, emoji: str = "📍", min_level: LogLevel = LogLevel.NORMAL):
        """Print a section header."""
        if not self._should_log(min_level):
            return
            
        section_text = f"{emoji} {title}"
        print(f"\n{self._colorize(section_text, 'blue')}")
    
    def print_progress(self, current: int, total: int, item_name: str, min_level: LogLevel = LogLevel.NORMAL):
        """Print progress indicator."""
        if not self._should_log(min_level):
            return
            
        progress_text = f"📊 {item_name} {current}/{total}"
        print(f"{self._colorize(progress_text, 'cyan')}")
    
    def print_success(self, message: str, details: Optional[str] = None, min_level: LogLevel = LogLevel.NORMAL):
        """Print success message."""
        if not self._should_log(min_level):
            return
            
        success_text = f"✅ {message}"
        print(f"   {self._colorize(success_text, 'green')}")
        
        if details and self.level == LogLevel.VERBOSE:
            print(f"      {self._colorize(details, 'gray')}")
    
    def print_error(self, message: str, error_details: Optional[str] = None, min_level: LogLevel = LogLevel.NORMAL):
        """Print error message."""
        if not self._should_log(min_level):
            return
            
        error_text = f"❌ {message}"
        print(f"   {self._colorize(error_text, 'red')}")
        
        if error_details:
            print(f"   🚨 {self._colorize(f'Erreur: {error_details}', 'yellow')}")
    
    def print_warning(self, message: str, min_level: LogLevel = LogLevel.NORMAL):
        """Print warning message."""
        if not self._should_log(min_level):
            return
            
        warning_text = f"⚠️  {message}"
        print(f"   {self._colorize(warning_text, 'yellow')}")
    
    def print_info(self, message: str, min_level: LogLevel = LogLevel.VERBOSE):
        """Print info message (verbose only by default)."""
        if not self._should_log(min_level):
            return
            
        info_text = f"ℹ️  {message}"
        print(f"   {self._colorize(info_text, 'gray')}")
    
    def print_sample_urls(self, urls: List[str], title: str = "Exemples", min_level: LogLevel = LogLevel.NORMAL):
        """Print sample URLs with truncation."""
        if not self._should_log(min_level) or not urls:
            return
        
        sample_count = min(len(urls), self.show_urls)
        
        print(f"   📝 {self._colorize(f'{title}:', 'blue')}")
        for i, url in enumerate(urls[:sample_count]):
            # Truncate long URLs
            display_url = url if len(url) <= 80 else f"{url[:77]}..."
            print(f"      • {self._colorize(display_url, 'gray')}")
        
        if len(urls) > sample_count:
            remaining = len(urls) - sample_count
            print(f"      {self._colorize(f'... et {remaining} autres', 'gray')}")
    
    def print_batch_start(self, batch_num: int, total_batches: int, batch_size: int, min_level: LogLevel = LogLevel.NORMAL):
        """Print batch processing start."""
        if not self._should_log(min_level):
            return
            
        batch_text = f"📊 Batch {batch_num}/{total_batches} ({batch_size} jobs à traiter)"
        print(f"\n{self._colorize(batch_text, 'cyan')}")
    
    def print_job_processing(self, job_num: int, total_jobs: int, url: str, min_level: LogLevel = LogLevel.NORMAL):
        """Print individual job processing."""
        if not self._should_log(min_level):
            return
            
        # Truncate URL for display
        display_url = url if len(url) <= 70 else f"{url[:67]}..."
        job_text = f"🔄 [{job_num}/{total_jobs}] {display_url}"
        print(f"{self._colorize(job_text, 'blue')}")
    
    def print_service_result(self, service_name: str, success: bool, duration: Optional[float] = None, 
                           error: Optional[str] = None, min_level: LogLevel = LogLevel.NORMAL):
        """Print service execution result."""
        if not self._should_log(min_level):
            return
            
        duration_text = f" ({duration:.1f}s)" if duration else ""
        
        if success:
            result_text = f"✅ {service_name}: OK{duration_text}"
            print(f"   {self._colorize(result_text, 'green')}")
        else:
            result_text = f"❌ {service_name}: Échec{duration_text}"
            print(f"   {self._colorize(result_text, 'red')}")
            if error:
                print(f"   🚨 {self._colorize(f'Erreur: {error}', 'yellow')}")
    
    def print_stage_summary(self, stage_name: str, success_count: int, total_count: int, 
                          duration: float, min_level: LogLevel = LogLevel.NORMAL):
        """Print stage completion summary."""
        if not self._should_log(min_level):
            return
            
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n{self._colorize('─' * 50, 'gray')}")
        print(f"📈 {self._colorize(f'Résumé {stage_name}:', 'bold')}")
        print(f"   • Succès: {self._colorize(f'{success_count}/{total_count}', 'green')} ({success_rate:.1f}%)")
        print(f"   • Durée: {self._colorize(f'{duration:.1f}s', 'blue')}")
        
        if success_count < total_count:
            failed_count = total_count - success_count
            print(f"   • Échecs: {self._colorize(str(failed_count), 'red')}")
    
    def print_configuration(self, config: Dict[str, Any], min_level: LogLevel = LogLevel.NORMAL):
        """Print configuration details."""
        if not self._should_log(min_level):
            return
            
        print(f"📋 {self._colorize('Configuration:', 'bold')}")
        for key, value in config.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value) if value else "Aucune"
            else:
                value_str = str(value)
            print(f"   • {key}: {self._colorize(value_str, 'blue')}")
    
    def print_final_report(self, success: bool, jobs_processed: int, sources_processed: int, 
                         duration: float, errors: List[str] = None, min_level: LogLevel = LogLevel.NORMAL):
        """Print final execution report."""
        if not self._should_log(min_level):
            return
            
        status_emoji = "✅" if success else "❌"
        status_text = "SUCCÈS" if success else "ÉCHEC"
        status_color = "green" if success else "red"
        
        print(f"\n{self._colorize('═' * 60, 'cyan')}")
        print(f"{status_emoji} {self._colorize(f'JINASCRAPER - {status_text}', status_color)}")
        print(f"{self._colorize('═' * 60, 'cyan')}")
        
        print(f"📊 Jobs traités: {self._colorize(str(jobs_processed), 'blue')}")
        print(f"🌐 Sources traitées: {self._colorize(str(sources_processed), 'blue')}")
        print(f"⏱️  Durée totale: {self._colorize(f'{duration:.1f}s', 'blue')}")
        
        if errors and self.level != LogLevel.QUIET:
            print(f"\n❌ {self._colorize(f'Erreurs ({len(errors)}):', 'red')}")
            for error in errors[:5]:  # Limit to 5 errors
                print(f"   - {self._colorize(error, 'yellow')}")
            if len(errors) > 5:
                print(f"   {self._colorize(f'... et {len(errors) - 5} autres erreurs', 'gray')}")


def create_logger(verbose: bool = False, quiet: bool = False, use_colors: bool = True, show_urls: int = 3) -> EnhancedLogger:
    """Factory function to create logger with appropriate level."""
    if quiet:
        level = LogLevel.QUIET
    elif verbose:
        level = LogLevel.VERBOSE
    else:
        level = LogLevel.NORMAL
    
    return EnhancedLogger(level=level, use_colors=use_colors, show_urls=show_urls)