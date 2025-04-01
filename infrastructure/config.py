import os
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional, Union, Type
from pydantic import Field, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import yaml

# 从环境变量中获取项目根目录的绝对路径，如果不存在则使用相对路径计算
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', str(Path(__file__).parent.parent.absolute())))

class AppEnv(str, Enum):
    """应用环境枚举"""
    DEV = "dev"
    PROD = "prod"


class BaseAppSettings(BaseSettings):
    """应用基础设置类"""
    # 应用环境
    env: AppEnv = Field(default=AppEnv.DEV)
    
    # 模型配置
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class AppConfig:
    """应用配置管理类，实现Spring风格的配置管理"""
    # 单例实例
    _instance = None
    
    # 当前环境
    _env: AppEnv = None
    
    # 配置实例
    _settings: Optional[BaseAppSettings] = None
    
    # 配置文件路径
    _config_files: Dict[str, Path] = {}
    
    # 配置文件最后修改时间
    _last_modified_times: Dict[str, float] = {}
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, env: Union[AppEnv, str] = None):
        """初始化配置管理器"""
        if getattr(self, "_initialized", False):
            return
            
        # 设置环境
        self._set_env(env)
        
        # 初始化配置
        self._initialize()
        
        self._initialized = True
    
    def _set_env(self, env: Union[AppEnv, str] = None) -> None:
        """设置当前环境
        优先级：
        1. 显式传入的环境参数
        2. 环境变量 APP_ENV
        3. 配置文件中的 application.env (将在加载配置后检查)
        """
        # 如果未指定环境，尝试从环境变量获取
        if env is None:
            env_str = os.getenv("APP_ENV", AppEnv.DEV.value)
            self._env = AppEnv(env_str)
        elif isinstance(env, str):
            self._env = AppEnv(env)
        else:
            self._env = env
            
        # 设置环境变量，确保其他组件可以访问
        os.environ["APP_ENV"] = self._env.value
    
    def _initialize(self) -> None:
        """初始化配置"""
        # 确定配置文件路径
        self._discover_config_files()
        
        # 加载配置
        self._load_config()
        
        print(f"配置系统已初始化，当前环境: {self._env.value}")
    
    def _discover_config_files(self) -> None:
        """发现当前环境的所有配置文件"""
        # 项目根目录
        root_dir = PROJECT_ROOT
        
        # 配置目录
        config_dir = root_dir / "config"
        
        # 通用配置文件
        common_yaml = config_dir / "application.yml"
        common_yaml_exists = common_yaml.exists()
        
        # 环境特定配置文件
        env_yaml = config_dir / self._env.value / f"application-{self._env.value}.yml"
        env_yaml_exists = env_yaml.exists()
        
        # 环境变量文件
        env_file = config_dir / self._env.value / f".env.{self._env.value}"
        env_file_exists = env_file.exists()
        
        # 记录配置文件路径
        self._config_files = {
            "common_yaml": common_yaml if common_yaml_exists else None,
            "env_yaml": env_yaml if env_yaml_exists else None,
            "env_file": env_file if env_file_exists else None
        }
        
        # 如果配置文件不存在，创建默认配置
        if not common_yaml_exists:
            raise FileNotFoundError(f"通用配置文件不存在: {common_yaml}，请创建此文件并配置必要的配置项")
        
        if not env_yaml_exists:
            raise FileNotFoundError(f"环境配置文件不存在: {env_yaml}，请创建此文件并配置必要的配置项")
        
        if not env_file_exists:
            raise FileNotFoundError(f"环境变量文件不存在: {env_file}，请创建此文件并配置必要的环境变量")
            
    def _load_config(self) -> None:
        """加载所有配置"""
        # 加载环境变量
        if self._config_files["env_file"]:
            load_dotenv(self._config_files["env_file"])
            self._last_modified_times["env_file"] = os.path.getmtime(self._config_files["env_file"])
            print(f"已加载环境变量: {self._config_files['env_file']}")
        
        # 加载YAML配置
        config_data = {}
        
        # 先加载通用配置
        if self._config_files["common_yaml"]:
            with open(self._config_files["common_yaml"], 'r', encoding='utf-8') as f:
                common_config = yaml.safe_load(f)
                if common_config:
                    config_data.update(common_config)
            self._last_modified_times["common_yaml"] = os.path.getmtime(self._config_files["common_yaml"])
            print(f"已加载通用配置: {self._config_files['common_yaml']}")
            
            # 检查配置文件中是否指定了环境
            if 'application' in common_config and 'env' in common_config['application']:
                config_env = common_config['application']['env']
                try:
                    env = AppEnv(config_env)
                    if env != self._env:
                        print(f"从配置文件中检测到环境设置: {env.value}，重新加载配置...")
                        self._env = env
                        os.environ["APP_ENV"] = env.value
                        # 重新发现配置文件
                        self._discover_config_files()
                        # 重新加载环境变量
                        if self._config_files["env_file"]:
                            load_dotenv(self._config_files["env_file"], override=True)
                            self._last_modified_times["env_file"] = os.path.getmtime(self._config_files["env_file"])
                            print(f"已加载环境变量: {self._config_files['env_file']}")
                except ValueError:
                    print(f"警告: 配置文件中指定的环境 '{config_env}' 无效")
        
        # 重新加载通用配置（如果环境已更改）
        if self._config_files["common_yaml"]:
            with open(self._config_files["common_yaml"], 'r', encoding='utf-8') as f:
                common_config = yaml.safe_load(f)
                if common_config:
                    config_data = common_config
        
        # 再加载环境特定配置（覆盖通用配置）
        if self._config_files["env_yaml"]:
            with open(self._config_files["env_yaml"], 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    self._deep_update(config_data, env_config)
            self._last_modified_times["env_yaml"] = os.path.getmtime(self._config_files["env_yaml"])
            print(f"已加载环境配置: {self._config_files['env_yaml']}")
        
        # 解析配置中的环境变量引用
        self._resolve_env_vars(config_data)
        
        # 创建配置模型
        self._create_settings_model(config_data)
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """深度更新字典，用于合并配置"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _resolve_env_vars(self, config_data: Dict) -> None:
        """解析配置中的环境变量引用，如 ${VAR_NAME}"""
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                if isinstance(value, (dict, list)):
                    self._resolve_env_vars(value)
                elif isinstance(value, str) and "${" in value and "}" in value:
                    # 解析所有环境变量引用
                    result = value
                    print(f"正在解析环境变量引用: {value}")
                    while "${" in result and "}" in result:
                        start = result.find("${")
                        end = result.find("}", start)
                        if start != -1 and end != -1:
                            env_var = result[start+2:end]
                            print(f"  - 查找环境变量: {env_var}")
                            env_value = os.getenv(env_var, "")
                            print(f"  - 从系统环境中获取的值: '{env_value}'")
                            if not env_value and self._config_files["env_file"] and os.path.exists(self._config_files["env_file"]):
                                # 如果环境变量为空，尝试从环境变量文件中直接读取
                                print(f"  - 尝试从环境变量文件中读取: {self._config_files['env_file']}")
                                with open(self._config_files["env_file"], 'r', encoding='utf-8') as f:
                                    for line in f:
                                        line = line.strip()
                                        if line and not line.startswith('#'):
                                            var_parts = line.split('=', 1)
                                            if len(var_parts) == 2 and var_parts[0] == env_var:
                                                env_value = var_parts[1].strip('"\'')
                                                print(f"  - 从文件中读取到的值: '{env_value}'")
                                                break
                            result = result.replace(f"${{{env_var}}}", env_value)
                    print(f"  - 最终解析结果: '{result}'")
                    config_data[key] = result
        elif isinstance(config_data, list):
            for i, item in enumerate(config_data):
                if isinstance(item, (dict, list)):
                    self._resolve_env_vars(item)
                elif isinstance(item, str) and "${" in item and "}" in item:
                    # 解析所有环境变量引用
                    result = item
                    print(f"正在解析环境变量引用: {item}")
                    while "${" in result and "}" in result:
                        start = result.find("${")
                        end = result.find("}", start)
                        if start != -1 and end != -1:
                            env_var = result[start+2:end]
                            print(f"  - 查找环境变量: {env_var}")
                            env_value = os.getenv(env_var, "")
                            print(f"  - 从系统环境中获取的值: '{env_value}'")
                            if not env_value and self._config_files["env_file"] and os.path.exists(self._config_files["env_file"]):
                                # 如果环境变量为空，尝试从环境变量文件中直接读取
                                print(f"  - 尝试从环境变量文件中读取: {self._config_files['env_file']}")
                                with open(self._config_files["env_file"], 'r', encoding='utf-8') as f:
                                    for line in f:
                                        line = line.strip()
                                        if line and not line.startswith('#'):
                                            var_parts = line.split('=', 1)
                                            if len(var_parts) == 2 and var_parts[0] == env_var:
                                                env_value = var_parts[1].strip('"\'')
                                                print(f"  - 从文件中读取到的值: '{env_value}'")
                                                break
                            result = result.replace(f"${{{env_var}}}", env_value)
                    print(f"  - 最终解析结果: '{result}'")
                    config_data[i] = result
    
    def _create_settings_model(self, config_data: Dict) -> None:
        """创建配置模型"""
        # 将配置数据扁平化为字典
        flat_config = self._flatten_dict(config_data)
        
        # 创建动态模型
        self._settings = BaseAppSettings(env=self._env, **flat_config)
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """将嵌套字典扁平化，用点号连接键名"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def reload_if_changed(self) -> bool:
        """检查配置文件是否已更改并在必要时重新加载"""
        changed = False
        
        for file_type, file_path in self._config_files.items():
            if file_path and os.path.exists(file_path):
                current_mtime = os.path.getmtime(file_path)
                if file_type not in self._last_modified_times or current_mtime > self._last_modified_times[file_type]:
                    changed = True
                    break
        
        if changed:
            print("配置文件已更改，正在重新加载...")
            self._load_config()
            return True
            
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号表示法"""
        if not self._settings:
            self._initialize()
            
        # 尝试从设置对象获取属性
        try:
            # 首先尝试直接从扁平化的配置中获取
            all_config = self.get_all()
            if key in all_config:
                return all_config[key]
                
            # 如果扁平化配置中没有，尝试通过属性访问
            value = self._settings
            for part in key.split('.'):
                value = getattr(value, part)
            return value
        except (AttributeError, KeyError):
            # 如果以上方法都失败，返回默认值
            return default
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        if not self._settings:
            self._initialize()
            
        return self._settings.model_dump()
    
    def set_env(self, env: Union[AppEnv, str]) -> None:
        """切换环境并重新加载配置"""
        if isinstance(env, str):
            env = AppEnv(env)
            
        if self._env != env:
            self._env = env
            os.environ["APP_ENV"] = env.value
            self._initialize()
    
    def get_env(self) -> AppEnv:
        """获取当前环境"""
        return self._env


# 创建全局配置实例
config = AppConfig()