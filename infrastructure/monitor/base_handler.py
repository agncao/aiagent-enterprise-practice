"""
Base classes for the monitoring system.
Provides the foundation for event handlers and observer management.
"""
from abc import ABC, abstractmethod
from watchdog.events import FileSystemEventHandler


class BaseEventHandler(FileSystemEventHandler, ABC):
    """
    Base class for all event handlers.
    Extends the watchdog FileSystemEventHandler with additional functionality.
    """
    def __init__(self, name: str = None):
        super().__init__()
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def initialize(self):
        """
        Initialize the handler. Called when the handler is registered.
        Implement this method to perform any setup tasks.
        """
        pass
