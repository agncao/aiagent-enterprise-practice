import logging
import sys
import os
from typing import Any, Optional
from infrastructure.config import config

class Logger:
    """
    日志工具类，提供类似于 Java Spring 生态中的日志接口
    """
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> 'Logger':
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，默认为调用者的模块名
            
        Returns:
            Logger: 日志记录器实例
        """
        if name is None:
            # 获取调用者的模块名
            frame = sys._getframe(1)
            name = frame.f_globals['__name__']
        
        if name not in cls._loggers:
            cls._loggers[name] = Logger(name)
        
        return cls._loggers[name]
    
    def __init__(self, name: str):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # 从配置中获取日志级别
        log_level = config.get('logging.level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level))
        
        # 如果没有处理器，添加一个控制台处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            
            # 从配置中获取日志格式，添加模块名和代码行号
            default_format = '%(asctime)s - %(name)s - %(levelname)s - [%(caller_file)s:%(caller_line)d] - %(message)s'
            log_format = config.get('logging.format', default_format)
            formatter = logging.Formatter(log_format)
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
            
            # 如果配置了日志文件，添加文件处理器
            log_file = config.get('logging.file', None)
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def _format_message(self, message: str, *args: Any) -> str:
        """
        格式化日志消息，支持类似于 Java 的 {} 占位符
        
        Args:
            message: 日志消息模板
            args: 替换占位符的参数
            
        Returns:
            str: 格式化后的消息
        """
        if not args:
            return message
        
        # 处理可能的异常情况
        try:
            return message.format(*args)
        except Exception:
            # 如果格式化失败，直接拼接
            return message + " " + " ".join(str(arg) for arg in args)
    
    def _log(self, level: int, message: str, *args: Any):
        """
        记录日志的内部方法
        
        Args:
            level: 日志级别
            message: 日志消息
            args: 格式化参数
        """
        # 获取调用者的堆栈信息
        frame = sys._getframe(2)  # 跳过 debug/info/warn/error 和 _log 方法
        file_path = frame.f_code.co_filename
        line_no = frame.f_lineno
        
        # 获取相对路径，使日志更简洁
        try:
            project_root = config.get_project_root()
            if file_path.startswith(str(project_root)):
                file_path = os.path.relpath(file_path, str(project_root))
        except Exception:
            # 如果获取相对路径失败，使用原始路径
            pass
        
        # 格式化消息
        formatted_message = self._format_message(message, *args)
        
        # 使用自定义字段名称，避免与内置字段冲突
        extra = {
            'caller_file': file_path,
            'caller_line': line_no
        }
        
        # 记录日志
        self.logger.log(level, formatted_message, extra=extra)
    
    def debug(self, message: str, *args: Any):
        """
        记录调试级别日志
        
        Args:
            message: 日志消息
            args: 格式化参数
        """
        self._log(logging.DEBUG, message, *args)
    
    def info(self, message: str, *args: Any):
        """
        记录信息级别日志
        
        Args:
            message: 日志消息
            args: 格式化参数
        """
        self._log(logging.INFO, message, *args)
    
    def warn(self, message: str, *args: Any):
        """
        记录警告级别日志
        
        Args:
            message: 日志消息
            args: 格式化参数
        """
        self._log(logging.WARNING, message, *args)
    
    def error(self, message: str, *args: Any):
        """
        记录错误级别日志
        
        Args:
            message: 日志消息
            args: 格式化参数
        """
        self._log(logging.ERROR, message, *args)
    
    def critical(self, message: str, *args: Any):
        """
        记录严重错误级别日志
        
        Args:
            message: 日志消息
            args: 格式化参数
        """
        self._log(logging.CRITICAL, message, *args)


# 创建一个全局日志对象，方便直接导入使用
log = Logger.get_logger('app')
