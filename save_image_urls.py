import os
import re
import sys
import glob
from termcolor import cprint

"""
此模块用于保存和处理Twitter图片URL
主要功能包括从日志文件中提取媒体链接、从URL中获取文件名以及检查文件是否存在
"""


def extract_media_urls(log_file_path):
    """从日志文件中提取所有媒体链接"""
    if not os.path.exists(log_file_path):
        print(f"日志文件 {log_file_path} 不存在")
        return []
    
    # 用于匹配媒体链接的正则表达式（支持多种格式）
    media_patterns = [
        re.compile(r'开始下载(https://[^\s]+)'),   # 匹配"开始下载https://..."格式
        re.compile(r'媒体链接: (https://[^\s]+)'), # 匹配"媒体链接: https://..."格式
        re.compile(r'(https://pbs\.twimg\.com/media/[^\s]+)') # 匹配任何Twitter媒体链接
    ]
    
    # 存储提取的媒体链接
    media_urls = []
    
    # 读取日志文件并提取链接
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            for pattern in media_patterns:
                match = pattern.search(line)
                if match:
                    media_url = match.group(1)
                    if media_url not in media_urls:  # 避免重复
                        media_urls.append(media_url)
                    break  # 一行只匹配一次
            
    return media_urls

def get_filename_from_url(url):
    """从URL中提取文件名和格式"""
    # 使用正则表达式从URL中提取media ID
    media_id_match = re.search(r'media/([A-Za-z0-9_\-]+)', url)
    if not media_id_match:
        return "未知文件名.png"
    
    media_id = media_id_match.group(1)
    
    # 从URL中提取格式
    format_match = re.search(r'format=([a-zA-Z0-9]+)', url)
    file_format = format_match.group(1) if format_match else "png"
    
    return f"{media_id}.{file_format}"

def is_file_exists(filename, search_dirs=None):
    """检查文件是否存在于任何指定的目录中"""
    if not search_dirs:
        # 如果没有指定搜索目录，使用当前目录
        search_dirs = [os.path.dirname(os.path.abspath(sys.argv[2]))]  # 使用输出文件所在的目录
    
    # 检查文件是否存在于任何搜索目录中
    for directory in search_dirs:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            return True
    
    return False

def save_urls_to_file(urls, output_file):
    """将URLs和对应的文件名保存到文件，并检查文件是否存在"""
    try:
        # 获取输出文件所在的目录作为搜索目录
        search_dirs = [os.path.dirname(os.path.abspath(output_file))]
        
        # 统计找到的文件和丢失的文件
        found_count = 0
        missing_count = 0
        
        # 确保输出文件的目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls:
                filename = get_filename_from_url(url)
                f.write(f"{url}\n")
                
                # 检查文件是否存在
                if is_file_exists(filename, search_dirs):
                    f.write(f"{filename}\n")
                    found_count += 1
                else:
                    f.write("下载失败\n")
                    missing_count += 1
            
            # 在文件末尾添加总结信息
            f.write("\n" + "=" * 50 + "\n")
            if missing_count == 0 and found_count > 0:
                f.write("所有图片均已成功下载！\n")
                f.write(f"共下载 {found_count} 张图片\n")
            else:
                f.write(f"下载统计：成功 {found_count} 张，失败 {missing_count} 张\n")
                    
        print(f"文件检查统计: 找到 {found_count} 个文件, 丢失 {missing_count} 个文件")
        return True
    except Exception as e:
        print(f"保存URLs时出错: {str(e)}")
        return False

def main(log_file_path, folder):
    # 日志文件路径
    # log_file_path = "download_log.txt"
    
    # 输出文件路径，支持命令行参数
    output_file = os.path.join(folder, "image.txt")
    
    # 提取媒体链接
    print("正在从日志文件中提取媒体链接...")
    media_urls = extract_media_urls(log_file_path)
    
    if not media_urls:
        print("未找到任何媒体链接")
        return
    
    # 保存链接到文件
    if save_urls_to_file(media_urls, output_file):
        cprint(f"已将 {len(media_urls)} 个媒体链接及其文件状态保存到 {output_file}", "green")
    else:
        print(f"保存链接失败")

if __name__ == "__main__":
    main() 