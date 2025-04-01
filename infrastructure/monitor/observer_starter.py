"""
Example usage of the monitoring system.
This demonstrates how to use the ObserverManager with multiple event handlers.
"""
from infrastructure.monitor.config_handler import ConfigChangeHandler
from infrastructure.monitor.init_generator import InitFileGenerator
from infrastructure.monitor.observer_manager import ObserverManager
from infrastructure.config import PROJECT_ROOT

def start():
    # Create the observer manager (singleton)
    observer_manager = ObserverManager()
    
    # Create and register the init file generator
    init_generator = InitFileGenerator()
    path_to_watch = PROJECT_ROOT  # Watch the current directory
    
    # Process existing directories first
    print("开始处理现有目录...")
    InitFileGenerator.create_init_for_existing_dirs(path_to_watch)
    print("现有目录处理完成")
    
    # Register the handler with the observer manager
    observer_manager.register_handler(init_generator, path_to_watch, recursive=True)
    
    # Register a config change handler
    config_handler = ConfigChangeHandler()
    observer_manager.register_handler(config_handler, path_to_watch, recursive=False)
    
    # Start monitoring
    print(f"开始监控目录: {path_to_watch}")
    observer_manager.run_forever()


if __name__ == "__main__":
    start()
