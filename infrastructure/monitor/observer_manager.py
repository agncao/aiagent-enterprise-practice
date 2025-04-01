"""
Base classes for the monitoring system.
Provides the foundation for event handlers and observer management.
"""
import time
from typing import Dict, List
from watchdog.observers import Observer
from infrastructure.monitor.base_handler import BaseEventHandler

class ObserverManager:
    """
    Manager for watchdog observers that allows multiple handlers to be registered.
    Provides a centralized way to manage file system monitoring.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObserverManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._observer = Observer()
        self._handlers: Dict[str, BaseEventHandler] = {}
        self._paths: Dict[str, str] = {}
        self._is_running = False
        self._initialized = True
    
    def register_handler(self, 
                         handler: BaseEventHandler, 
                         path: str, 
                         recursive: bool = True) -> None:
        """
        Register a new event handler for the specified path.
        
        Args:
            handler: The event handler to register
            path: The path to monitor
            recursive: Whether to monitor subdirectories
        """
        if handler.name in self._handlers:
            raise ValueError(f"Handler with name '{handler.name}' already registered")
        
        self._handlers[handler.name] = handler
        self._paths[handler.name] = path
        
        # Initialize the handler
        handler.initialize()
        
        # Schedule the handler if the observer is already running
        if self._is_running:
            self._observer.schedule(handler, path, recursive=recursive)
    
    def unregister_handler(self, handler_name: str) -> None:
        """
        Unregister an event handler by name.
        
        Args:
            handler_name: The name of the handler to unregister
        """
        if handler_name not in self._handlers:
            raise ValueError(f"No handler with name '{handler_name}' registered")
        
        # Remove the handler
        del self._handlers[handler_name]
        del self._paths[handler_name]
        
        # If the observer is running, we need to restart it to apply changes
        if self._is_running:
            self.stop()
            self.start()
    
    def start(self) -> None:
        """Start the observer and all registered handlers."""
        if self._is_running:
            return
        
        # Schedule all handlers
        for name, handler in self._handlers.items():
            path = self._paths[name]
            self._observer.schedule(handler, path, recursive=True)
        
        # Start the observer
        self._observer.start()
        self._is_running = True
    
    def stop(self) -> None:
        """Stop the observer."""
        if not self._is_running:
            return
        
        self._observer.stop()
        self._observer.join()
        self._is_running = False
    
    def run_forever(self) -> None:
        """Run the observer in the foreground until interrupted."""
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        
    @property
    def is_running(self) -> bool:
        """Check if the observer is running."""
        return self._is_running
    
    @property
    def registered_handlers(self) -> List[str]:
        """Get a list of registered handler names."""
        return list(self._handlers.keys())
