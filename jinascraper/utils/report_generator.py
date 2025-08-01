"""Visual report generator for enhanced CLI display."""
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .terminal_utils import TerminalUtils, colorize, create_box, create_separator


@dataclass
class ReportData:
    """Data structure for report generation."""
    total_sources: int
    successful_sources: int
    total_urls_found: int
    total_jobs_processed: int
    cache_hit_rate: float
    processing_time: float
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    source_details: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.source_details is None:
            self.source_details = []


class ReportGenerator:
    """Generator for visual reports and professional summaries."""
    
    def __init__(self, use_colors: bool = True, terminal_width: Optional[int] = None):
        """
        Initialize the report generator.
        
        Args:
            use_colors: Whether to use colors in reports
            terminal_width: Terminal width (auto-detected if None)
        """
        self.use_colors = use_colors and TerminalUtils.supports_colors()
        if terminal_width is None:
            terminal_width, _ = TerminalUtils.get_terminal_size()
        self.terminal_width = terminal_width

    def generate_startup_report(self, config: Dict[str, Any]) -> str:
        """
        Generate the startup report with header and configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Formatted startup report
        """
        lines = []
        
        # ASCII Header
        header_lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║                            🔍 JINASCRAPER v2.0                              ║",
            "║                     Agrégateur d'Emplois IA pour le Togo                    ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝"
        ]
        
        for line in header_lines:
            if self.use_colors:
                lines.append(colorize(line, 'cyan', bold=True))
            else:
                lines.append(line)
        
        lines.append("")
        
        # Initialization message
        init_msg = "🚀 Initialisation du système..."
        if self.use_colors:
            init_msg = colorize(init_msg, 'bright_yellow', bold=True)
        lines.append(init_msg)
        lines.append("")
        
        # Configuration summary
        if 'sources' in config:
            lines.append(self._generate_sources_table(config['sources']))
        
        # System status
        lines.append(self._generate_system_status(config))
        
        return "\\n".join(lines)

    def generate_final_report(self, results: ReportData) -> str:
        """
        Generate the final professional report.
        
        Args:
            results: Report data
            
        Returns:
            Formatted final report
        """
        lines = []
        
        # Report header
        header_lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║                          📊 RAPPORT DE SCRAPING                             ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝"
        ]
        
        for line in header_lines:
            if self.use_colors:
                lines.append(colorize(line, 'green', bold=True))
            else:
                lines.append(line)
        
        lines.append("")
        
        # Executive summary
        lines.append(self._generate_executive_summary(results))
        lines.append("")
        
        # Performance chart
        lines.append(self._generate_performance_chart(results))
        lines.append("")
        
        # Cache efficiency
        lines.append(self._generate_cache_report(results))
        lines.append("")
        
        # Error summary (if any)
        if results.errors or results.warnings:
            lines.append(self._generate_error_summary(results))
            lines.append("")
        
        # Recommendations
        lines.append(self._generate_recommendations(results))
        
        return "\\n".join(lines)

    def generate_error_report(self, errors: List[Dict[str, Any]]) -> str:
        """
        Generate an error report with suggestions.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Formatted error report
        """
        if not errors:
            return ""
        
        lines = []
        
        # Error header
        header = "🚨 RAPPORT D'ERREURS"
        if self.use_colors:
            header = colorize(header, 'red', bold=True)
        lines.append(header)
        lines.append(TerminalUtils.create_separator(width=50, style='simple'))
        lines.append("")
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Display each error group
        for error_type, error_list in error_groups.items():
            lines.append(self._format_error_group(error_type, error_list))
            lines.append("")
        
        return "\\n".join(lines)

    def create_ascii_chart(self, data: Dict[str, int], title: str, 
                          max_width: int = 50) -> str:
        """
        Create an ASCII bar chart.
        
        Args:
            data: Data dictionary (label -> value)
            title: Chart title
            max_width: Maximum width for bars
            
        Returns:
            ASCII chart string
        """
        if not data:
            return f"{title}: No data available"
        
        lines = []
        
        # Title
        if self.use_colors:
            title_line = colorize(f"📈 {title}", 'bright_cyan', bold=True)
        else:
            title_line = f"📈 {title}"
        lines.append(title_line)
        
        # Find max value for scaling
        max_value = max(data.values()) if data.values() else 1
        
        # Generate bars
        for label, value in data.items():
            # Calculate bar length
            if max_value > 0:
                bar_length = int((value / max_value) * max_width)
            else:
                bar_length = 0
            
            # Create bar
            bar = "█" * bar_length
            if self.use_colors:
                if value == max_value:
                    bar = colorize(bar, 'green')
                elif value > max_value * 0.7:
                    bar = colorize(bar, 'yellow')
                else:
                    bar = colorize(bar, 'red')
            
            # Format line
            label_formatted = f"{label:<15}"
            if self.use_colors:
                label_formatted = colorize(label_formatted, 'bright_white')
            
            value_formatted = f"{value:>4}"
            if self.use_colors:
                value_formatted = colorize(value_formatted, 'cyan')
            
            line = f"{label_formatted} {bar} {value_formatted}"
            lines.append(line)
        
        return "\\n".join(lines)

    def create_status_table(self, items: List[Dict[str, Any]], 
                           headers: List[str] = None) -> str:
        """
        Create a formatted status table.
        
        Args:
            items: List of item dictionaries
            headers: Table headers (auto-generated if None)
            
        Returns:
            Formatted table string
        """
        if not items:
            return "No data available"
        
        # Auto-generate headers if not provided
        if headers is None:
            headers = list(items[0].keys()) if items else []
        
        # Calculate column widths
        col_widths = {}
        for header in headers:
            col_widths[header] = len(header)
            for item in items:
                value_str = str(item.get(header, ''))
                # Remove ANSI codes for width calculation
                clean_value = self._strip_ansi_codes(value_str)
                col_widths[header] = max(col_widths[header], len(clean_value))
        
        lines = []
        
        # Table header
        header_line = "┌"
        separator_line = "├"
        for i, header in enumerate(headers):
            width = col_widths[header] + 2  # Add padding
            header_line += "─" * width
            separator_line += "─" * width
            if i < len(headers) - 1:
                header_line += "┬"
                separator_line += "┼"
        header_line += "┐"
        separator_line += "┤"
        
        lines.append(header_line)
        
        # Header row
        header_row = "│"
        for header in headers:
            width = col_widths[header]
            formatted_header = f" {header:<{width}} "
            if self.use_colors:
                formatted_header = colorize(formatted_header, 'bright_white', bold=True)
            header_row += formatted_header + "│"
        lines.append(header_row)
        lines.append(separator_line)
        
        # Data rows
        for item in items:
            row = "│"
            for header in headers:
                width = col_widths[header]
                value = item.get(header, '')
                
                # Format value based on type
                if isinstance(value, bool):
                    if value:
                        formatted_value = colorize("✅ Oui", 'green') if self.use_colors else "Oui"
                    else:
                        formatted_value = colorize("❌ Non", 'red') if self.use_colors else "Non"
                elif isinstance(value, (int, float)):
                    formatted_value = str(value)
                    if self.use_colors:
                        formatted_value = colorize(formatted_value, 'cyan')
                else:
                    formatted_value = str(value)
                
                # Calculate padding (accounting for ANSI codes)
                clean_value = self._strip_ansi_codes(formatted_value)
                padding = width - len(clean_value)
                padded_value = f" {formatted_value}{' ' * padding} "
                row += padded_value + "│"
            lines.append(row)
        
        # Table footer
        footer_line = "└"
        for i, header in enumerate(headers):
            width = col_widths[header] + 2
            footer_line += "─" * width
            if i < len(headers) - 1:
                footer_line += "┴"
        footer_line += "┘"
        lines.append(footer_line)
        
        return "\\n".join(lines)

    def _generate_sources_table(self, sources: List[Dict[str, Any]]) -> str:
        """Generate the sources configuration table."""
        table_data = []
        for source in sources:
            status_icon = "✅" if source.get('active', True) else "❌"
            status_text = "Actif" if source.get('active', True) else "Inactif"
            
            if self.use_colors:
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
        
        title = "📊 Configuration Système:"
        if self.use_colors:
            title = colorize(title, 'bright_blue', bold=True)
        
        return title + "\\n" + self.create_status_table(table_data)

    def _generate_system_status(self, config: Dict[str, Any]) -> str:
        """Generate system status summary."""
        lines = []
        
        # Cache status
        cache_status = config.get('cache_status', 'unknown')
        if cache_status == 'connected':
            cache_line = "💾 Cache Redis: ✅ Connecté"
            if self.use_colors:
                cache_line = colorize(cache_line, 'green')
        else:
            cache_line = "💾 Cache Redis: ❌ Déconnecté (FakeRedis actif)"
            if self.use_colors:
                cache_line = colorize(cache_line, 'yellow')
        lines.append(cache_line)
        
        # AI services status
        ai_status = config.get('ai_services', 'unknown')
        if ai_status == 'operational':
            ai_line = "🤖 IA Services: ✅ Jina Reader + Google Gemini opérationnels"
            if self.use_colors:
                ai_line = colorize(ai_line, 'green')
        else:
            ai_line = "🤖 IA Services: ⚠️ Vérification en cours..."
            if self.use_colors:
                ai_line = colorize(ai_line, 'yellow')
        lines.append(ai_line)
        
        return "\\n".join(lines)

    def _generate_executive_summary(self, results: ReportData) -> str:
        """Generate the executive summary box."""
        # Determine overall status
        success_rate = results.successful_sources / max(results.total_sources, 1)
        if success_rate >= 0.8:
            status = "SUCCÈS"
            status_color = 'green'
        elif success_rate >= 0.5:
            status = "SUCCÈS PARTIEL"
            status_color = 'yellow'
        else:
            status = "ÉCHEC PARTIEL"
            status_color = 'red'
        
        # Format processing time
        if results.processing_time < 60:
            time_str = f"{results.processing_time:.0f}s"
        elif results.processing_time < 3600:
            time_str = f"{results.processing_time/60:.1f}m"
        else:
            time_str = f"{results.processing_time/3600:.1f}h"
        
        # Create summary content
        summary_lines = [
            f"✅ Statut: {status}",
            f"📊 Jobs traités: {results.total_jobs_processed} sur {results.total_urls_found} URLs découvertes ({(results.total_jobs_processed/max(results.total_urls_found,1)*100):.0f}% de succès)",
            f"⏱️ Temps total: {time_str}",
            f"🌐 Sources actives: {results.successful_sources}/{results.total_sources}"
        ]
        
        if results.successful_sources < results.total_sources:
            failed_sources = results.total_sources - results.successful_sources
            summary_lines[-1] += f" ({failed_sources} temporairement indisponibles)"
        
        summary_content = "\\n".join(summary_lines)
        
        # Create colored box
        title = "🎯 RÉSUMÉ EXÉCUTIF"
        if self.use_colors:
            title = colorize(title, 'bright_cyan', bold=True)
        
        box_content = f"{title}\\n{TerminalUtils.create_separator(width=60, style='simple')}\\n{summary_content}"
        return create_box(box_content, width=80, style='single', padding=1)

    def _generate_performance_chart(self, results: ReportData) -> str:
        """Generate performance chart by source."""
        if not results.source_details:
            return ""
        
        # Prepare data for chart
        chart_data = {}
        for source in results.source_details:
            name = source.get('name', 'Unknown')
            jobs = source.get('jobs_processed', 0)
            chart_data[name] = jobs
        
        return self.create_ascii_chart(chart_data, "PERFORMANCE PAR SOURCE", max_width=20)

    def _generate_cache_report(self, results: ReportData) -> str:
        """Generate cache efficiency report."""
        lines = []
        
        title = "💾 EFFICACITÉ CACHE"
        if self.use_colors:
            title = colorize(title, 'bright_blue', bold=True)
        lines.append(title)
        
        # Hit rate bar
        hit_rate = results.cache_hit_rate
        bar_width = 40
        filled = int(hit_rate * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        if self.use_colors:
            if hit_rate >= 0.8:
                bar = colorize(bar, 'green')
            elif hit_rate >= 0.5:
                bar = colorize(bar, 'yellow')
            else:
                bar = colorize(bar, 'red')
        
        hit_rate_line = f"Hit Rate: [{bar}] {hit_rate*100:.0f}%"
        lines.append(hit_rate_line)
        
        # Savings calculation
        if hit_rate > 0:
            estimated_savings = int(results.total_urls_found * hit_rate)
            time_saved = estimated_savings * 2  # Assume 2s per API call
            if time_saved < 60:
                time_str = f"{time_saved:.0f}s"
            else:
                time_str = f"{time_saved/60:.1f}m"
            
            savings_line = f"Économies: {estimated_savings} appels API évités | Temps gagné: ~{time_str}"
            if self.use_colors:
                savings_line = colorize(savings_line, 'green')
            lines.append(savings_line)
        
        return "\\n".join(lines)

    def _generate_error_summary(self, results: ReportData) -> str:
        """Generate error and warning summary."""
        lines = []
        
        if results.errors:
            title = f"🚨 ERREURS ({len(results.errors)})"
            if self.use_colors:
                title = colorize(title, 'red', bold=True)
            lines.append(title)
            
            for error in results.errors[:3]:  # Show max 3 errors
                error_line = f"  • {error.get('message', 'Unknown error')}"
                if self.use_colors:
                    error_line = colorize(error_line, 'red')
                lines.append(error_line)
            
            if len(results.errors) > 3:
                more_line = f"  ... et {len(results.errors) - 3} autres erreurs"
                if self.use_colors:
                    more_line = colorize(more_line, 'bright_black')
                lines.append(more_line)
        
        if results.warnings:
            if lines:
                lines.append("")
            title = f"⚠️ AVERTISSEMENTS ({len(results.warnings)})"
            if self.use_colors:
                title = colorize(title, 'yellow', bold=True)
            lines.append(title)
            
            for warning in results.warnings[:3]:  # Show max 3 warnings
                warning_line = f"  • {warning.get('message', 'Unknown warning')}"
                if self.use_colors:
                    warning_line = colorize(warning_line, 'yellow')
                lines.append(warning_line)
        
        return "\\n".join(lines)

    def _generate_recommendations(self, results: ReportData) -> str:
        """Generate recommendations based on results."""
        lines = []
        
        title = "🎉 FÉLICITATIONS! Le scraping s'est terminé avec succès."
        subtitle = f"   {results.total_urls_found} nouvelles offres d'emploi découvertes pour le Togo."
        
        if self.use_colors:
            title = colorize(title, 'green', bold=True)
            subtitle = colorize(subtitle, 'bright_green')
        
        lines.append(title)
        lines.append(subtitle)
        lines.append("")
        
        # Recommendations
        recommendations = []
        
        # Check for failed sources
        failed_sources = results.total_sources - results.successful_sources
        if failed_sources > 0:
            if failed_sources == 1:
                recommendations.append("• Vérifier la connectivité de la source défaillante")
            else:
                recommendations.append(f"• Vérifier la connectivité des {failed_sources} sources défaillantes")
        
        # Check cache efficiency
        if results.cache_hit_rate < 0.5:
            recommendations.append("• Optimiser la stratégie de cache pour améliorer les performances")
        
        # Check processing time
        if results.processing_time > 300:  # 5 minutes
            recommendations.append("• Considérer l'optimisation du temps de traitement")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("• Relancer dans 1h pour découvrir de nouvelles offres")
        
        if recommendations:
            rec_title = "📋 Actions recommandées:"
            if self.use_colors:
                rec_title = colorize(rec_title, 'bright_cyan', bold=True)
            lines.append(rec_title)
            
            for rec in recommendations:
                if self.use_colors:
                    rec = colorize(rec, 'cyan')
                lines.append(f"   {rec}")
        
        lines.append("")
        
        # Save prompt
        save_prompt = "💾 Sauvegarder ce rapport? [O/n] _"
        if self.use_colors:
            save_prompt = colorize(save_prompt, 'bright_yellow', bold=True)
        lines.append(save_prompt)
        
        return "\\n".join(lines)

    def _format_error_group(self, error_type: str, error_list: List[Dict[str, Any]]) -> str:
        """Format a group of errors by type."""
        lines = []
        
        # Error type header
        type_header = f"🔴 {error_type.upper()} ({len(error_list)})"
        if self.use_colors:
            type_header = colorize(type_header, 'red', bold=True)
        lines.append(type_header)
        
        # Error details
        for error in error_list:
            message = error.get('message', 'Unknown error')
            source = error.get('source', 'Unknown')
            error_line = f"  • {source}: {message}"
            if self.use_colors:
                error_line = colorize(error_line, 'bright_red')
            lines.append(error_line)
            
            # Add suggestions if available
            suggestions = error.get('suggestions', [])
            for suggestion in suggestions:
                suggestion_line = f"    → {suggestion}"
                if self.use_colors:
                    suggestion_line = colorize(suggestion_line, 'yellow')
                lines.append(suggestion_line)
        
        return "\\n".join(lines)

    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI color codes from text for width calculation."""
        import re
        ansi_escape = re.compile(r'\\x1B(?:[@-Z\\\\-_]|\\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)


# Convenience functions
def generate_startup_header() -> str:
    """Generate a simple startup header."""
    generator = ReportGenerator()
    config = {
        'sources': [
            {'name': 'Emploi.tg', 'active': True, 'description': 'Source gouvernementale principale'},
            {'name': 'ANPE Togo', 'active': True, 'description': 'Agence nationale pour l\'emploi'},
        ],
        'cache_status': 'connected',
        'ai_services': 'operational'
    }
    return generator.generate_startup_report(config)


def generate_sample_final_report() -> str:
    """Generate a sample final report for testing."""
    generator = ReportGenerator()
    sample_data = ReportData(
        total_sources=6,
        successful_sources=4,
        total_urls_found=139,
        total_jobs_processed=107,
        cache_hit_rate=0.75,
        processing_time=147.23,
        errors=[
            {'type': 'timeout', 'message': 'LinkedIn Togo timeout', 'source': 'linkedin_togo'},
            {'type': 'http_error', 'message': 'HTTP 400 error', 'source': 'indeed_togo'}
        ],
        warnings=[],
        performance_metrics={'avg_processing_time': 1.2},
        source_details=[
            {'name': 'Emploi.tg', 'jobs_processed': 25},
            {'name': 'ANPE Togo', 'jobs_processed': 15},
            {'name': 'EmploiTogo.info', 'jobs_processed': 64},
            {'name': 'YOP L-FRII', 'jobs_processed': 35}
        ]
    )
    return generator.generate_final_report(sample_data)