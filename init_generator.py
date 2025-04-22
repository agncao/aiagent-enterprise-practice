import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from infrastructure.logger import log

class InitFileGenerator(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            src_path = str(event.src_path)
            init_path = os.path.join(src_path, '__init__.py')
            if not os.path.exists(init_path):
                with open(init_path, 'a') as f:
                    pass
                print(f"已创建: {init_path}")

def create_init_for_existing_dirs(start_path):
    """为现有目录创建__init__.py文件"""
    for root, dirs, files in os.walk(start_path):
        if '__init__.py' not in files:
            init_path = os.path.join(root, '__init__.py')
            with open(init_path, 'a') as f:
                pass
            print(f"已创建: {init_path}")

# 弃用, 需要的话,可以解除注释
# if __name__ == "__main__":
#     path_to_watch = "./"
    
#     # 先处理现有目录
#     print("开始处理现有目录...")
#     create_init_for_existing_dirs(path_to_watch)
#     print("现有目录处理完成")
    
#     # 启动监控新目录
#     event_handler = InitFileGenerator()
#     observer = Observer()
#     observer.schedule(event_handler, path_to_watch, recursive=True)
#     observer.start()
    
#     try:
#         print(f"开始监控目录: {path_to_watch}")
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()