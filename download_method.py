import os
import time
import requests
import threading
from urllib.parse import unquote
from termcolor import cprint as termcolor_cprint
import sys

"""
下载方法模块

本模块提供了图片和视频下载的相关功能，包括：
- 线程控制和信号量管理
- 日志记录功能
- 下载进度显示
- 文件保存和错误处理

主要函数:
- download_pic: 下载图片文件
- download_video: 下载视频文件 (在文件其他部分实现)

作者: Winter
创建日期: 2025-07-03
最后修改: 2025-07-03
版本: 1.0
"""

# 全局变量
img_connections = 10  # 定义最大线程数最多10个图片下载线程，可根据网速修改
img_sema = threading.BoundedSemaphore(img_connections)  # 或使用Semaphore方法
video_connections = 3  # 定义最大线程数最多3个视频下载线程，可根据网速修改
video_sema = threading.BoundedSemaphore(video_connections)  # 或使用Semaphore方法

# 日志文件路径和目标文件夹
log_file_path = None
target_folder = None

def set_target_folder(folder):
    """设置目标文件夹和日志文件路径"""
    global target_folder, log_file_path
    target_folder = folder
    log_file_path = os.path.join(folder, "download_log.txt")

def log_print(*args, **kwargs):
    """打印到控制台并写入日志文件"""
    # 直接使用sys.stdout.write而不是print，避免递归
    message = " ".join(map(str, args))
    sys.stdout.write(message + "\n")
    sys.stdout.flush()
    
    # 写入日志文件
    if log_file_path:
        try:
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(message + "\n")
        except Exception as e:
            sys.stderr.write(f"写入日志文件时发生错误: {str(e)}\n")
            sys.stderr.flush()

def log_cprint(text, color=None, **kwargs):
    """带颜色打印到控制台并写入日志文件"""
    # 使用termcolor_cprint进行彩色输出
    termcolor_cprint(text, color, **kwargs)
    
    # 写入日志文件(不含颜色信息)
    if log_file_path:
        try:
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(str(text) + "\n")
        except Exception as e:
            sys.stderr.write(f"写入日志文件时发生错误: {str(e)}\n")
            sys.stderr.flush()

def move_log_file():
    """将日志文件移动到目标文件夹"""
    global target_folder, log_file_path
    if target_folder and os.path.exists(log_file_path):
        try:
            # 构建新的日志文件路径
            new_log_path = os.path.join(target_folder, "download_log.txt")
            # 如果目标文件夹不存在，创建它
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            # 移动文件
            if os.path.exists(new_log_path):
                os.remove(new_log_path)
            os.rename(log_file_path, new_log_path)
            log_file_path = new_log_path
            return True
        except Exception as e:
            sys.stderr.write(f"移动日志文件时发生错误: {str(e)}\n")
            sys.stderr.flush()
            return False
    return False

# 替换全局函数
print = log_print
cprint = log_cprint


def download_pic(post_link, url, folder):

    try:

        # 从URL中提取文件名
        filename = url.split('/')[-1].split('?')[0] + '.png'
        filename = unquote(filename)  # URL解码
        filepath = os.path.join(folder, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            # 文件存在时不打印任何信息，静默跳过
            return
            
        # 打印帖子链接和下载URL（紧密关联在一起）
        if post_link:
            print(f"帖子链接{post_link}")
        cprint(f"开始下载{url}", "yellow")
        
        # 设置较短的超时时间
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            cprint(f"{filename} 下载完成\n", "green")
            
            # 添加下载间隔
            time.sleep(0.5)
            
    except requests.Timeout:
        print(f"下载超时: {url}")
    except Exception as e:
        print(f"下载图片时发生错误: {str(e)}")

# 下载视频，待完善
def download_video(url, folder):

    try:
        # 设置较短的超时时间
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # 从URL中提取文件名
            filename = url.split('/')[-1].split('?')[0]
            if 'pu' in filename:
                filename = filename + '.mp4'
            else:
                filename = filename + '.gif'
            filename = unquote(filename)  # URL解码
            filepath = os.path.join(folder, filename)
            
            # 检查文件是否已存在
            if os.path.exists(filepath):
                print(f"{filename} 已存在，跳过下载")
                return
                
            print(f"{filename} 正在下载...")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"{filename} 下载完成")
            
            # 添加下载间隔
            time.sleep(0.5)
            
    except requests.Timeout:
        print(f"下载超时: {url}")
    except Exception as e:
        print(f"下载视频时发生错误: {str(e)}")




