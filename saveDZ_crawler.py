import os
import time
import signal
import threading
import sys
from selenium.common.exceptions import TimeoutException
from manga_downloader import safe_find_elements, safe_get_attribute
from driver_init import initialize_driver, cookies_web
import config  # 改为导入整个模块
from termcolor import cprint as original_cprint
from download_method import download_pic
from save_image_urls import main

"""
爬取特定标签的图片
只计算有图片的帖子，跳过没有图片的帖子
"""

# 全局变量用于控制程序运行
running = True
driver = None
download_count = 0  # 用于记录已下载的帖子数量
log_file_path = None  # 日志文件路径
download_threads = []  # 保存所有下载线程

def signal_handler(signum, frame):
    global running, driver
    log_print("\n正在安全退出程序...")
    running = False
    # 安全关闭浏览器
    if driver:
        try:
            driver.quit()
        except:
            pass
    # 使用sys.exit强制结束程序
    sys.exit(0)

# 保存原始的print函数
original_print = print

# 自定义日志函数
def log_print(text):
    """将文本同时输出到控制台和日志文件"""
    print(text)
    if hasattr(log_print, 'log_file'):
        with open(log_print.log_file, 'a', encoding='utf-8') as f:
            f.write(str(text) + "\n")

def log_cprint(text, color):
    """将彩色文本同时输出到控制台和日志文件"""
    original_cprint(text, color)
    if hasattr(log_print, 'log_file'):
        with open(log_print.log_file, 'a', encoding='utf-8') as f:
            f.write(str(text) + "\n")

# 生产者函数：获取图片URL
def url_producer(driver, q, folder):
    """生产者函数：获取图片URL"""
    global running, download_count
    log_print("等待页面加载...")
    
    processed_elements = set()  # 用于跟踪已处理的元素
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while running and download_count < config.urls_num:
        try:
            # 获取当前可见的帖子元素
            elements = safe_find_elements(driver, "css selector", "div[data-testid='cellInnerDiv']")
            if elements:
                # 处理新发现的元素
                for data in elements:
                    if not running or download_count >= config.urls_num:
                        break
                        
                    try:
                        element_id = data.id
                        if element_id in processed_elements:
                            continue

                        # 获取帖子链接和时间
                        try:
                            time_element = data.find_element("css selector", "time")
                            post_time = time_element.get_attribute("datetime")
                            post_link = time_element.find_element("xpath", "..").get_attribute("href")
                        except:
                            post_time = "未知时间"
                            post_link = "未知链接"
                        
                        # 查找图片
                        images = safe_find_elements(data, "tag name", "img")
                        has_images = False
                        media_urls = []
                        
                        for img in images:
                            src = safe_get_attribute(img, 'src')
                            if src and "profile_images" not in src and 'media' in src:
                                has_images = True
                                media_url = src[:src.find('?')] + "?format=png&name=large"
                                media_urls.append(media_url)
                        
                        # 如果有图片，增加帖子计数并下载
                        if has_images:
                            with threading.Lock():
                                download_count += 1
                                log_print(f"找到第 {download_count}/{config.urls_num} 条带图片的帖子")
                            
                            log_print(f"帖子链接: {post_link}")
                            log_print(f"发布时间: {post_time}")
                            log_print(f"找到 {len(media_urls)} 张图片")
                            
                            # 创建线程下载该帖子的所有图片
                            for media_url in media_urls:
                                log_print(f"媒体链接: {media_url}")
                                download_thread = threading.Thread(target=download_image, args=(post_link, media_url, folder))
                                download_threads.append(download_thread)  # 将线程添加到列表中
                                download_thread.start()
                        else:
                            # 如果没有图片，跳过并且不计数
                            log_print(f"帖子 {post_link} 没有图片，跳过")
                        
                        processed_elements.add(element_id)
                        
                    except Exception as element_error:
                        log_print(f"处理单个元素时发生错误: {str(element_error)}")
                        continue
            
            if not running or download_count >= config.urls_num:
                break
                
            # 滚动页面
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # 如果高度没有变化，可能是加载完了或者需要等待更久
                time.sleep(5)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    log_print("页面暂时没有新内容，继续尝试...")
            last_height = new_height
                
        except Exception as scroll_error:
            log_print(f"滚动过程中发生错误: {str(scroll_error)}")
            time.sleep(3)
            continue
    
    log_print("\n爬取结束，达到目标帖子数量或被手动停止")

# 下载图片（不计数）
def download_image(post_link, url, folder):
    """下载图片（不计数）"""
    try:
        # 从URL中提取文件名
        filename = url.split('/')[-1].split('?')[0] + '.png'
        filepath = os.path.join(folder, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            return
            
        # 打印下载URL
        log_cprint(f"开始下载: {url}", "yellow")
        
        # 设置较短的超时时间
        import requests
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            log_cprint(f"{filename} 下载完成", "green")
            
            # 添加下载间隔
            time.sleep(0.5)
            
    except Exception as e:
        log_print(f"下载图片时发生错误: {str(e)}")


def crawl_tag_images(custom_tag=None, save_folder=None):
    """
    爬取指定标签的图片
    
    Args:
        custom_tag: 自定义标签，如果为None则使用config中的tag
        save_folder: 保存目录，如果为None则创建新目录
    """
    try:
        global running, download_count, download_threads
        running = True
        download_count = 0
        download_threads = []
        
        # 使用自定义标签或配置中的标签
        tag_to_use = custom_tag if custom_tag is not None else config.tag  # 使用config.tag
        
        # 设置日志文件路径
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if save_folder is None:
            save_folder = f"dianzan__{tag_to_use}_{timestamp}"
        
        # 确保保存目录存在
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            
        # 设置日志文件路径
        log_file_path = os.path.join(save_folder, f"@{tag_to_use}_dianzan_log.txt")
        
        # 设置全局日志文件路径
        log_print.log_file = log_file_path
        
        # 创建并初始化日志文件
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"下载日志创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取标签: {tag_to_use}\n")
            f.write("-" * 50 + "\n")
            f.write(f"图片将保存在文件夹: {save_folder}\n")
            f.write(f"目标爬取帖子数量: {config.urls_num}\n")  # 使用config.urls_num
            f.write(f"日志文件: {log_file_path}\n\n")
            f.write("开始爬取...\n")

        log_print(f"图片将保存在文件夹: {save_folder}")
        log_print(f"目标爬取帖子数量: {config.urls_num}")  # 使用config.urls_num
        log_print(f"日志文件: {log_file_path}")

        driver = initialize_driver()
        
        try:
            driver.get('https://x.com/i/flow/login')
        except TimeoutException:
            driver.execute_script('window.stop()')
        driver.set_page_load_timeout(60)

        try:
            driver.get('https://x.com')  # 先访问一次目标域名
            cookies_web(driver, "X_cookie.json")
        except Exception as e:
            log_print(f"访问失败，请检查网络连接: {str(e)}")
            driver.quit()
            return None, None

        # 访问标签页面
        log_print("访问推特页面中.....")
        target_url = f"https://x.com/hashtag/{tag_to_use}?src=hashtag_click"
        driver.get(target_url)
        log_print("准备获取数据中.....")

        time.sleep(1)
        
        # 开始爬取图片
        log_print(f"开始爬取数据...., url为：{target_url}")

        try:
            # 创建并启动生产者线程
            producer_thread = threading.Thread(target=url_producer, args=(driver, None, save_folder))
            producer_thread.start()
            
            # 等待生产者线程完成或被中断
            producer_thread.join()
            
            # 等待所有下载线程完成
            try:
                # 等待所有下载线程完成
                log_print("\n等待所有图片下载完成...")
                for thread in download_threads:
                    thread.join()
                log_cprint("\n所有图片下载完成！", "green")
                
                image_count = len([f for f in os.listdir(save_folder) if f.endswith(".png")])
                
                # 更新日志文件
                with open(log_file_path, "a", encoding="utf-8") as f:
                    f.write("\n" + "-" * 50 + "\n")
                    f.write(f"爬取完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"共找到 {download_count} 条带图片的帖子\n")
                    f.write(f"共下载了 {image_count} 张图片\n")
                
                log_print(f"\n共找到 {download_count} 条带图片的帖子")
                log_print(f"共下载了 {image_count} 张图片")
                
                # 使用save_image_urls模块生成image.txt
                from save_image_urls import main as save_image_urls
                save_image_urls(log_file_path, save_folder)
                
            except Exception as e:
                log_print(f"统计文件数量时发生错误: {str(e)}")

        except KeyboardInterrupt:
            running = False
            log_print("\n检测到用户中断，正在安全退出...")
        except Exception as e:
            log_print(f"发生错误: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            log_print("程序已安全退出。")
            
        return save_folder, log_file_path

    except Exception as e:
        log_print(f"爬虫运行出错: {str(e)}")
        return None, None


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 替换全局print和cprint为日志版本
    print = log_print
    
    # 直接运行爬虫
    folder, log_file_path = crawl_tag_images()
    
    # 确保所有下载线程都完成后再进行统计
    print("开始进行日志统计...")
    main(log_file_path, folder)