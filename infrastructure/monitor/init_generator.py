"""
Specific event handlers for the monitoring system.
"""
import os
from infrastructure.monitor.base_handler import BaseEventHandler


class InitFileGenerator(BaseEventHandler):
    """
    Event handler that automatically creates __init__.py files in newly created directories.
    """
    def __init__(self, name: str = "InitFileGenerator"):
        super().__init__(name)
    
    def initialize(self):
        """Create __init__.py files in existing directories if needed."""
        # This will be called when the handler is registered
        pass
    
    def on_created(self, event):
        """Handle directory creation events."""
        if event.is_directory:
            src_path = str(event.src_path)
            if os.path.basename(src_path).startswith('.'):
                return
            init_path = os.path.join(src_path, '__init__.py')
            if not os.path.exists(init_path):
                with open(init_path, 'a') as f:
                    pass
                print(f"已创建: {init_path}")

    @staticmethod
    def create_init_for_existing_dirs(start_path: str):
        """Create __init__.py files for existing directories.
        
        Args:
            start_path: The root directory to start from
        """
        for root, dirs, files in os.walk(start_path):
            # Skip hidden directories (starting with .)
            if os.path.basename(root).startswith('.'):
                continue
            
            if '__init__.py' not in files:
                init_path = os.path.join(root, '__init__.py')
                with open(init_path, 'a') as f:
                    pass
                print(f"已创建: {init_path}")
