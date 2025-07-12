import os
import sys
import logging
from pathlib import Path

def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境
    
    Args:
        relative_path: 相对路径
        
    Returns:
        绝对路径
    """
    if hasattr(sys, '_MEIPASS'):  # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def ensure_dir(directory):
    """确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def setup_logging(log_dir='logs'):
    """设置日志记录器
    
    Args:
        log_dir: 日志目录
        
    Returns:
        logger实例
    """
    from datetime import datetime
    
    # 创建logs目录（如果不存在）
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名（使用当前时间）
    log_filename = log_dir / f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # 配置日志记录器
    logger = logging.getLogger('TwitterCrawler')
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    
    return logger 