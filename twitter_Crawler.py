import os
import time
import signal
import threading
import sys
from selenium.common.exceptions import TimeoutException
from manga_downloader import download_media
from driver_init import initialize_driver, cookies_web
from config import tag, user_choice, start_time, end_time
from termcolor import cprint as original_cprint
from datetime import datetime
from download_method import print, cprint  # 导入日志打印函数

"""
Twitter爬虫工具 1.0版本
------------------------
本程序用于爬取Twitter(X)上的媒体内容，支持按时间范围筛选帖子。

功能特点:
- 自动登录Twitter账号
- 支持按标签或用户筛选内容
- 可设置爬取的时间范围
- 自动下载图片和视频

使用方法:
1. 在config.py中配置爬取参数
2. 运行本脚本开始爬取
3. 爬取的内容将保存到指定目录

作者: Winter
创建日期: 2025-07-03
最后修改: 2025-07-03
版本: 1.0
"""

class TwitterCrawlerState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置所有状态"""
        self.running = True
        self.driver = None
        self.download_threads = []
        
    def cleanup(self):
        """清理所有资源"""
        self.running = False
        if self.driver:
            try:
                # 关闭所有窗口
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                self.driver.quit()
            except Exception as e:
                print(f"关闭浏览器时发生错误: {str(e)}")
                # 强制结束进程
                try:
                    import psutil
                    process = psutil.Process(self.driver.service.process.pid)
                    process.terminate()
                except:
                    pass
            finally:
                self.driver = None
        
        # 等待所有下载线程结束
        for thread in self.download_threads:
            if thread.is_alive():
                thread.join(timeout=5)

# 创建全局状态管理器
crawler_state = TwitterCrawlerState()

def signal_handler(signum, frame):
    print("\n正在安全退出程序...")
    crawler_state.cleanup()
    sys.exit(0)

def get_date_input(prompt):
    while True:
        date_str = input(prompt)
        try:
            # 验证日期格式
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            print("日期格式错误，请使用YYYY-MM-DD格式（例如：2024-01-01）")

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 重置状态
        crawler_state.reset()
        
        if datetime.strptime(start_time, '%Y-%m-%d') > datetime.strptime(end_time, '%Y-%m-%d'):
            print("开始日期不能晚于结束日期！")
            exit(1)
            
        cprint(f"\n将爬取 {start_time} 到 {end_time} 之间的帖子\n", "red")

        crawler_state.driver = initialize_driver()

        # 尝试访问X/Twitter登录页面
        try:
            crawler_state.driver.get('https://x.com/i/flow/login')
        except TimeoutException:
            crawler_state.driver.execute_script('window.stop()')
        crawler_state.driver.set_page_load_timeout(60)

        try:
            crawler_state.driver.get('https://x.com')  # 先访问一次目标域名
            cookies_web(crawler_state.driver, "X_cookie.json")
        except Exception as e:
            print(f"访问失败，请检查网络连接: {str(e)}")
            crawler_state.cleanup()
            exit(1)
            
        # 访问特定的Twitter页面
        print("访问推特页面中.....")
        target_url = f"https://x.com/search?q={tag}&src=typed_query&f=live" # 最新页面进行爬取
        crawler_state.driver.get(target_url)
        print("准备获取数据中.....")

        time.sleep(1)

        # 判断target_url是否包含"media"
        is_media = target_url.endswith("/media")

        # 获取并创建相应的文件夹
        folder = tag + "_image_" + time.strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(folder):
            os.makedirs(folder)

        video_folder = os.path.join(folder, "video & gif")
        if "2" in user_choice or "3" in user_choice:
            if not os.path.exists(video_folder):
                os.makedirs(video_folder)

        # 设置日志文件的目标文件夹
        from download_method import set_target_folder, move_log_file
        set_target_folder(folder)

        # 下载图片和视频
        cprint(f"开始爬取数据...., url为：{target_url}", "yellow")
        
        try:
            download_media(crawler_state.driver, folder, video_folder, user_choice, is_media, start_time, end_time)
            
        except KeyboardInterrupt:
            print("\n检测到用户中断，正在安全退出...")
        except Exception as e:
            print(f"发生错误: {str(e)}")
        finally:
            crawler_state.running = False
            
            # 显示下载统计
            try:
                print(f'\n共下载 {len([f for f in os.listdir(folder) if f.endswith(".png")])} 张图片')
                if "2" in user_choice or "3" in user_choice:
                    print(f'共下载 {len(os.listdir(video_folder))} 个视频')
            except Exception as e:
                print(f"统计文件数量时发生错误: {str(e)}")
            
            # 移动日志文件到目标文件夹
            move_log_file()
            print("程序已安全退出。")
            
            # 清理资源
            crawler_state.cleanup()

    except Exception as e:
        print(f"发生错误: {str(e)}")
        crawler_state.cleanup()

