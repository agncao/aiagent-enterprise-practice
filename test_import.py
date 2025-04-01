"""
Test script to verify that the infrastructure module can be imported correctly.
"""

try:
    from infrastructure.config import AppConfig, config
    print("Successfully imported infrastructure.config.AppConfig and config")
except ImportError as e:
    print(f"Failed to import infrastructure.config: {e}")

try:
    from infrastructure.monitor.observer_manager import ObserverManager
    print("Successfully imported infrastructure.monitor.observer_manager")
except ImportError as e:
    print(f"Failed to import infrastructure.monitor.observer_manager: {e}")
