
from infrastructure.config import config
from infrastructure.monitor.base_handler import BaseEventHandler

class ConfigChangeHandler(BaseEventHandler):
    """
    Event handler that monitors configuration file changes for hot reloading.
    This is an example of another handler that could be implemented.
    """
    def __init__(self, name: str = "ConfigChangeHandler"):
        super().__init__(name)
        env = config.get_env().value
        self.config_path = f"config/{env}/.env.{env}"
    
    def initialize(self):
        """Initialize the config change handler."""
        print(f"开始监控配置文件: {self.config_path}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path == self.config_path:
            print(f"配置文件已更改: {self.config_path}")
            config.reload_if_changed()
