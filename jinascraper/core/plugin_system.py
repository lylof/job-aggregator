"""Plugin system for extensible architecture."""

import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class PluginInterface(ABC):
    """Base interface for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return ""
    
    @property
    def dependencies(self) -> List[str]:
        """List of required plugin dependencies."""
        return []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class SourcePlugin(PluginInterface):
    """Plugin interface for job sources."""
    
    @abstractmethod
    async def extract_job_urls(self, listing_url: str) -> List[str]:
        """Extract job URLs from a listing page."""
        pass
    
    @abstractmethod
    async def extract_job_data(self, job_url: str) -> Dict[str, Any]:
        """Extract job data from a job page."""
        pass
    
    @abstractmethod
    def clean_urls(self, urls: List[str]) -> List[str]:
        """Clean and validate URLs."""
        pass


class ProcessorPlugin(PluginInterface):
    """Plugin interface for data processors."""
    
    @abstractmethod
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process job data."""
        pass
    
    @abstractmethod
    def get_supported_sources(self) -> List[str]:
        """Get list of supported source names."""
        pass


class StoragePlugin(PluginInterface):
    """Plugin interface for storage backends."""
    
    @abstractmethod
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Store a job record."""
        pass
    
    @abstractmethod
    async def store_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store multiple job records."""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job record."""
        pass


class NotificationPlugin(PluginInterface):
    """Plugin interface for notifications."""
    
    @abstractmethod
    async def send_notification(self, message: str, **kwargs) -> bool:
        """Send a notification."""
        pass
    
    @abstractmethod
    def get_supported_channels(self) -> List[str]:
        """Get list of supported notification channels."""
        pass


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_types: Dict[Type, List[str]] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.initialized_plugins: set = set()
    
    def register_plugin(self, plugin: PluginInterface) -> bool:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration was successful
        """
        try:
            plugin_name = plugin.name
            
            if plugin_name in self.plugins:
                logger.warning(f"Plugin {plugin_name} is already registered")
                return False
            
            # Check dependencies
            for dep in plugin.dependencies:
                if dep not in self.plugins:
                    logger.error(f"Plugin {plugin_name} requires dependency {dep} which is not registered")
                    return False
            
            self.plugins[plugin_name] = plugin
            
            # Track plugin types
            plugin_type = type(plugin).__bases__[0] if type(plugin).__bases__ else type(plugin)
            if plugin_type not in self.plugin_types:
                self.plugin_types[plugin_type] = []
            self.plugin_types[plugin_type].append(plugin_name)
            
            logger.info(f"Plugin {plugin_name} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {str(e)}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration was successful
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} is not registered")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            
            # Check if other plugins depend on this one
            dependents = [
                name for name, p in self.plugins.items()
                if plugin_name in p.dependencies and name != plugin_name
            ]
            
            if dependents:
                logger.error(f"Cannot unregister plugin {plugin_name}, it has dependents: {dependents}")
                return False
            
            # Cleanup plugin if it was initialized
            if plugin_name in self.initialized_plugins:
                asyncio.create_task(plugin.cleanup())
                self.initialized_plugins.discard(plugin_name)
            
            # Remove from registry
            del self.plugins[plugin_name]
            
            # Remove from type tracking
            for plugin_type, names in self.plugin_types.items():
                if plugin_name in names:
                    names.remove(plugin_name)
                    break
            
            logger.info(f"Plugin {plugin_name} unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_name}: {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a plugin by name."""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: Type) -> List[PluginInterface]:
        """Get all plugins of a specific type."""
        plugin_names = self.plugin_types.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all registered plugins with their info."""
        return {
            name: {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "type": type(plugin).__name__,
                "dependencies": plugin.dependencies,
                "initialized": name in self.initialized_plugins
            }
            for name, plugin in self.plugins.items()
        }
    
    async def initialize_plugin(self, plugin_name: str) -> bool:
        """Initialize a specific plugin."""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} is not registered")
            return False
        
        if plugin_name in self.initialized_plugins:
            logger.info(f"Plugin {plugin_name} is already initialized")
            return True
        
        try:
            plugin = self.plugins[plugin_name]
            
            # Initialize dependencies first
            for dep in plugin.dependencies:
                if dep not in self.initialized_plugins:
                    if not await self.initialize_plugin(dep):
                        logger.error(f"Failed to initialize dependency {dep} for plugin {plugin_name}")
                        return False
            
            # Initialize the plugin
            if await plugin.initialize():
                self.initialized_plugins.add(plugin_name)
                logger.info(f"Plugin {plugin_name} initialized successfully")
                return True
            else:
                logger.error(f"Plugin {plugin_name} initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize plugin {plugin_name}: {str(e)}")
            return False
    
    async def initialize_all_plugins(self) -> Dict[str, bool]:
        """Initialize all registered plugins."""
        results = {}
        
        for plugin_name in self.plugins.keys():
            results[plugin_name] = await self.initialize_plugin(plugin_name)
        
        return results
    
    async def cleanup_all_plugins(self) -> None:
        """Cleanup all initialized plugins."""
        for plugin_name in list(self.initialized_plugins):
            try:
                plugin = self.plugins[plugin_name]
                await plugin.cleanup()
                self.initialized_plugins.discard(plugin_name)
                logger.info(f"Plugin {plugin_name} cleaned up successfully")
            except Exception as e:
                logger.error(f"Failed to cleanup plugin {plugin_name}: {str(e)}")
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    async def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook."""
        if hook_name not in self.hooks:
            return []
        
        results = []
        for callback in self.hooks[hook_name]:
            try:
                if inspect.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} callback failed: {str(e)}")
                results.append(None)
        
        return results


class PluginLoader:
    """Utility for loading plugins from files or modules."""
    
    @staticmethod
    def load_plugin_from_module(module_path: str, plugin_class_name: str) -> Optional[PluginInterface]:
        """Load a plugin from a Python module."""
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, plugin_class_name)
            
            if not issubclass(plugin_class, PluginInterface):
                logger.error(f"Class {plugin_class_name} does not implement PluginInterface")
                return None
            
            return plugin_class()
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_path}.{plugin_class_name}: {str(e)}")
            return None
    
    @staticmethod
    def discover_plugins(plugin_directory: str) -> List[PluginInterface]:
        """Discover and load plugins from a directory."""
        plugins = []
        plugin_path = Path(plugin_directory)
        
        if not plugin_path.exists():
            logger.warning(f"Plugin directory {plugin_directory} does not exist")
            return plugins
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for plugin classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, PluginInterface) and 
                        obj != PluginInterface and 
                        not inspect.isabstract(obj)):
                        
                        plugin = obj()
                        plugins.append(plugin)
                        logger.info(f"Discovered plugin {plugin.name} in {plugin_file}")
                        
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {str(e)}")
        
        return plugins


# Global plugin registry
plugin_registry = PluginRegistry()


# Decorator for plugin hooks
def plugin_hook(hook_name: str):
    """Decorator to register a function as a plugin hook."""
    def decorator(func):
        plugin_registry.register_hook(hook_name, func)
        return func
    return decorator


# Example plugin implementations
class ExampleSourcePlugin(SourcePlugin):
    """Example source plugin implementation."""
    
    @property
    def name(self) -> str:
        return "example_source"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Example job source plugin"
    
    async def initialize(self) -> bool:
        logger.info("Example source plugin initialized")
        return True
    
    async def cleanup(self) -> None:
        logger.info("Example source plugin cleaned up")
    
    async def extract_job_urls(self, listing_url: str) -> List[str]:
        # Mock implementation
        return [f"{listing_url}/job/{i}" for i in range(5)]
    
    async def extract_job_data(self, job_url: str) -> Dict[str, Any]:
        # Mock implementation
        return {
            "title": "Example Job",
            "company": "Example Company",
            "url": job_url
        }
    
    def clean_urls(self, urls: List[str]) -> List[str]:
        # Mock implementation
        return [url for url in urls if url.startswith("http")]


class ExampleProcessorPlugin(ProcessorPlugin):
    """Example processor plugin implementation."""
    
    @property
    def name(self) -> str:
        return "example_processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Example job data processor plugin"
    
    async def initialize(self) -> bool:
        logger.info("Example processor plugin initialized")
        return True
    
    async def cleanup(self) -> None:
        logger.info("Example processor plugin cleaned up")
    
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Mock processing - add a processed flag
        processed_data = data.copy()
        processed_data["processed"] = True
        processed_data["processor"] = self.name
        return processed_data
    
    def get_supported_sources(self) -> List[str]:
        return ["example_source", "emploi_tg"]