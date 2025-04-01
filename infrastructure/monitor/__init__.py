"""
Monitoring system for file system events.
Provides a decoupled way to handle multiple event handlers with a single Observer.
"""

__all__ = [
    'BaseEventHandler',
    'ObserverManager',
    'InitFileGenerator',
    'ConfigChangeHandler',
]