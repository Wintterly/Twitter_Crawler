import os
import time
import json
import queue
import signal
import threading
import sys
import requests
import subprocess
from download_method import download_pic, download_video, print, cprint
from selenium.common.exceptions import InvalidArgumentException, TimeoutException, WebDriverException
from json_process import json_value_find, get_max_bitrate_url
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from tenacity import retry, stop_after_attempt, wait_exponential
from termcolor import cprint as original_cprint
from datetime import datetime

"""
漫画下载器

这个模块提供了一个用于下载漫画内容的工具。它支持从各种在线平台下载漫画图片和视频内容，
并提供了多线程下载、错误重试和优雅退出等功能。

主要功能:
- 多线程并发下载
- 支持图片和视频内容
- 自动重试失败的下载
- 时间范围过滤
- 优雅退出机制

依赖:
- selenium: 用于网页交互和内容抓取
- requests: 用于HTTP请求
- tenacity: 用于实现重试机制
- termcolor: 用于彩色终端输出

作者: Winter
创建日期: 2025-07-03
最后修改: 2025-07-03
版本: 1.0
"""



# 全局变量用于控制程序运行
running = True
def signal_handler(signum, frame):
    global running
    print("\n检测到停止信号，正在优雅退出...")
    running = False
    # 使用sys.exit强制结束程序
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def safe_find_elements(driver, by, value, max_retries=3):
    """安全地查找元素，带有重试机制"""
    for attempt in range(max_retries):
        try:
            elements = driver.find_elements(by, value)
            return elements
        except WebDriverException as e:
            if attempt == max_retries - 1:
                print(f"查找元素失败: {str(e)}")
                return []
            time.sleep(2 ** attempt)
    return []

def safe_get_attribute(element: WebElement, attribute: str, default=None):
    """安全地获取元素属性"""
    try:
        value = element.get_attribute(attribute)
        return value if value else default
    except Exception as e:
        print(f"获取属性失败: {str(e)}")
        return default

def is_post_in_timerange(post_time: str, start_time: str, end_time: str) -> bool:
    """
    判断帖子是否在指定的时间范围内
    
    Args:
        post_time: 帖子时间，格式为 ISO 8601 (例如: '2025-06-10T09:00:07.000Z')
        start_time: 开始时间，格式为 'YYYY-MM-DD'
        end_time: 结束时间，格式为 'YYYY-MM-DD'
    
    Returns:
        bool: 是否在时间范围内
    """
    try:
        post_datetime = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
        start_datetime = datetime.fromisoformat(f"{start_time}T00:00:00+00:00")
        end_datetime = datetime.fromisoformat(f"{end_time}T23:59:59+00:00")
        
        return start_datetime <= post_datetime <= end_datetime
    except:
        return False
    

def is_system_continue(post_time: str, start_time: str) -> bool:
    """
    判断帖子时间是否在指定的时间范围内，用于判断是否需要继续爬取，如果在start_time之前，则结束程序
    Args:
        post_time: 帖子时间，格式为 ISO 8601 (例如: '2025-06-10T09:00:07.000Z')
    """
    try:
        post_datetime = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
        start_datetime = datetime.fromisoformat(f"{start_time}T00:00:00+00:00")

        return post_datetime <= start_datetime
    except:
        return False


def url_producer(driver, q, user_choice, is_media, start_time=None, end_time=None):
    global running
    print("等待页面加载...")
    
    try:
        # 使用显式等待，最多等待60秒直到元素出现
        wait = WebDriverWait(driver, 60)
        print("正在等待页面元素加载，最长等待时间为60秒...")
        
        try:
            elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']"))
            )
            print(f"找到 {len(elements)} 个帖子元素")
        except TimeoutException:
            print("\n等待超时：1分钟内未能找到任何推文元素，可能是：")
            print("1. 网络连接较慢")
            print("2. 页面加载异常")
            print("3. Twitter页面结构可能已更新")
            print("\n正在退出程序...")
            running = False
            q.put(None)  # 确保在超时情况下也发送结束信号
            return
        
        processed_elements = set()  # 用于跟踪已处理的元素
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while running:
            try:
                # 检查浏览器是否还活着
                try:
                    driver.execute_script("return 1")
                except WebDriverException:
                    print("\n浏览器已关闭")
                    break
                
                # 获取当前可见的元素
                elements = safe_find_elements(driver, By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
                if elements:
                    # 处理新发现的元素
                    for data in elements:
                        if not running:
                            break
                            
                        try:
                            element_id = data.id
                            if element_id in processed_elements:
                                continue

                            # 获取帖子链接和时间
                            try:
                                time_element = data.find_element(By.CSS_SELECTOR, "time")
                                post_time = time_element.get_attribute("datetime")
                                post_link = time_element.find_element(By.XPATH, "..").get_attribute("href")
                            except:
                                post_time = "未知时间"
                                post_link = "未知链接"
                            
                            # 检查帖子时间是否在指定范围内，因为是根据最新的页面进行爬取，所以如果遇到超过end_time的帖子，直接结束程序
                            if start_time and end_time and post_time != "未知时间":
                                # 先检查帖子时间是否在start_time之前，如果是，则结束程序
                                if is_system_continue(post_time, start_time):
                                    cprint(f"获取到帖子时间为{post_time}，已经超出start_time，停止获取新帖子\n", "red")
                                    cprint("=" * 30 + "下载线程继续运行" + "=" * 30 + "\n", "blue")
                                    processed_elements.add(element_id)
                                    running = False  # 结束当前获取URL的线程
                                    q.put(None)  # 确保在提前结束时也发送结束信号
                                    return  # 直接返回，结束url_producer函数，但不影响下载线程

                                # 调用is_post_in_timerange函数判断帖子时间是否在指定范围内
                                if not is_post_in_timerange(post_time, start_time, end_time):
                                    cprint(f"\n跳过时间范围外的帖子：{post_link}", "yellow")
                                    cprint(f"帖子时间：{post_time}", "yellow")
                                    processed_elements.add(element_id)
                                    continue

                            if "1" in user_choice:
                                images = safe_find_elements(data, By.TAG_NAME, "img")
                                if images:
                                    cprint(f"\n当前帖子的url为：{post_link}", "green")
                                    print(f"时间为：{post_time}，找到{len(images)}张图片")
                                    # print(f"找到 {len(images)} 张图片")
                                
                                for img in images:
                                    src = safe_get_attribute(img, 'src')
                                    if src and "profile_images" not in src and 'media' in src:
                                        media_url = src[:src.find('?')] + "?format=png&name=large"
                                        print(f"媒体链接: {media_url}")
                                        # 将帖子链接和媒体URL一起添加到队列，修改前为只添加media_url，打印到log文件中
                                        q.put((post_link, media_url))
                                        
                            processed_elements.add(element_id)
                            
                        except Exception as element_error:
                            print(f"处理单个元素时发生错误: {str(element_error)}")
                            continue
                
                if not running:
                    break
                    
                # 滚动页面
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # 增加等待时间到3秒
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # 如果高度没有变化，可能是加载完了或者需要等待更久
                        time.sleep(5)  # 增加等待时间到5秒
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            print("页面暂时没有新内容，继续尝试...")
                    last_height = new_height
                except WebDriverException:
                    print("\n浏览器已关闭")
                    break
                    
            except Exception as scroll_error:
                print(f"滚动过程中发生错误: {str(scroll_error)}")
                if "no such window" in str(scroll_error):
                    break
                time.sleep(3)  # 增加错误后的等待时间到3秒
                continue
                
    except Exception as e:
        print(f"发生错误：{str(e)}")
    
    # 程序结束前的清理工作
    try:
        if running:  # 如果不是用户手动停止的，尝试处理视频内容
            media_video(driver, q, user_choice, is_media)
    except Exception as video_error:
        print(f"处理视频内容时发生错误: {str(video_error)}")
    
    q.put(None)  # 发送结束信号
    print("\n爬取结束，正在等待下载完成...")

def url_consumer(q, folder, video_folder, active_threads):
    empty_count = 0  # 记录队列连续为空的次数
    max_empty_count = 10  # 最大允许的连续空队列次数，可以根据需要调整
    while True:
        try:
            try:
                item = q.get(timeout=5)
                empty_count = 0  # 重置空队列计数
            except queue.Empty:
                # 清理已完成的线程
                active_threads[:] = [t for t in active_threads if t.is_alive()]
                empty_count += 1
                if empty_count >= max_empty_count:
                    cprint("队列长时间为空，没有新的下载任务，结束下载线程", "red")
                    return  # 使用return而不是break确保线程完全终止
                continue

            if item is None:
                q.task_done()
                cprint("收到结束信号，结束下载线程", "green")
                return  # 使用return而不是break确保线程完全终止
                
            # 处理新的元组格式(post_link, src)或旧的单一URL格式
            if isinstance(item, tuple):
                post_link, src = item
            else:
                post_link, src = None, item

            # 清理已完成的线程
            active_threads[:] = [t for t in active_threads if t.is_alive()]

            # 如果活跃线程太多，等待一些完成
            while len(active_threads) > 5:
                time.sleep(0.5)
                active_threads[:] = [t for t in active_threads if t.is_alive()]

            # 创建新的下载线程，如果src为视频，则创建视频下载线程，否则创建图片下载线程
            if "mp4" not in src:
                thread = download_thread_png(post_link, src, folder)
            else:
                thread = download_thread_video(src, video_folder)

            active_threads.append(thread)
            q.task_done()

        except Exception as e:
            print(f"下载过程中发生错误: {str(e)}")
            continue

def download_thread_png(post_link, src, folder):
    # 创建线程下载图片
    thread = threading.Thread(target=download_pic, args=(post_link, src, folder), daemon=True)
    thread.start()

    return thread

def download_thread_video(src, video_folder):
    # 创建线程下载视频
    thread = threading.Thread(target=download_video, args=(src, video_folder), daemon=True)
    thread.start()
    return thread

def media_video(driver, q, user_choice, is_media):
    # 从浏览器日志network中提取视频URL
    logs_raw = driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
    # print(logs)
    def log_filter(log_):
        # if (log_["method"] == "Network.responseReceived" and "json" in log_["params"]["response"]["mimeType"]
        #         and 'UserMedia' in log_["params"]["response"]["url"]):
        #     print(log_["params"]["response"])
        url_keyword = 'UserMedia' if is_media else 'Usertwitters'
        return (
            log_["method"] == "Network.responseReceived"
            and "json" in log_["params"]["response"]["mimeType"]
            and url_keyword in log_["params"]["response"]["url"]
        )

    variants_lists = []
    for log in filter(log_filter, logs):
        request_id = log["params"]["requestId"]
        resp_url = log["params"]["response"]["url"]
        # print(f"Caught {resp_url}")
        res = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body']
        res = json.loads(res)
        # print(res)

        all_variants = json_value_find(res, "variants")
        # print(all_variants)
        for variants in all_variants:
            if variants not in variants_lists:
                variants_lists.append(variants)
                temp = get_max_bitrate_url(variants)
                if "2" in user_choice:
                    if not any(isinstance(item, tuple) and item[1] == temp or item == temp for item in list(q.queue)) and 'pu' in temp:
                        # print(temp)
                        q.put((None, temp))
                if "3" in user_choice:
                    if not any(isinstance(item, tuple) and item[1] == temp or item == temp for item in list(q.queue)) and 'pu' not in temp:
                        # print(temp)
                        q.put((None, temp))

def download_media(driver, folder, video_folder, user_choice, is_media, start_time=None, end_time=None):
    """
    下载媒体文件的主函数
    
    Args:
        driver: Selenium WebDriver实例
        folder: 图片保存文件夹路径
        video_folder: 视频保存文件夹路径
        user_choice: 用户选择的下载类型
        is_media: 是否是媒体页面
        start_time: 开始日期（YYYY-MM-DD格式）
        end_time: 结束日期（YYYY-MM-DD格式）
    """
    # 重置全局状态和浏览器状态
    reset_browser_state(driver)
    
    q = queue.Queue()
    
    # 创建活跃线程列表，用于跟踪所有下载线程
    active_threads = []
    
    # 创建并启动生产者线程
    producer = threading.Thread(target=url_producer, args=(driver, q, user_choice, is_media, start_time, end_time), daemon=True)
    producer.start()

    # 给页面足够的加载时间
    time.sleep(5)  # 等待5秒让页面加载
    
    # 检查队列是否为空，但要给一定的等待时间
    empty_check_count = 0
    while q.empty() and empty_check_count < 6:  # 最多等待30秒
        time.sleep(5)
        empty_check_count += 1
        
    if q.empty():
        cprint("没有找到需要下载的媒体文件，结束程序", "yellow")
        return
    
    # 创建并启动消费者线程
    consumer = threading.Thread(target=url_consumer, args=(q, folder, video_folder, active_threads), daemon=True)
    consumer.start()
    
    # 等待生产者线程完成
    producer.join()

    # 等待消费者线程完成，添加超时机制
    consumer.join(timeout=60)  # 设置较长的超时时间
    
    # 如果消费者线程仍在运行，可能是卡住了，发送结束信号
    if consumer.is_alive():
        cprint("下载线程超时，发送结束信号", "yellow")
        q.put(None)  # 再次发送结束信号
        
        # 等待一段时间看是否能够结束
        consumer.join(timeout=10)
        if consumer.is_alive():
            cprint("下载线程未能正常结束，程序将继续执行", "red")
    
    # 等待所有活跃下载线程完成
    for t in active_threads:
        if t.is_alive():
            t.join(timeout=5)
    
    # 下载完成后，调用save_image_urls.py脚本保存媒体链接
    try:
        cprint("\n正在从日志中提取媒体链接...", "blue")
        # 检查save_image_urls.py是否存在
        if os.path.exists("save_image_urls.py"):
            # 方法1: 直接在当前进程中运行脚本
            try:
                from save_image_urls import extract_media_urls, save_urls_to_file
                
                # 提取媒体链接
                media_urls = extract_media_urls("download_log.txt")
                
                # 将链接保存到图片文件夹中的image.txt
                image_txt_path = os.path.join(folder, "image.txt")
                if media_urls and save_urls_to_file(media_urls, image_txt_path):
                    cprint(f"已将 {len(media_urls)} 个媒体链接保存到 {image_txt_path}", "green")
                else:
                    print(f"未找到媒体链接或保存失败")
            except Exception as e:
                cprint(f"提取媒体链接时发生错误: {str(e)}", "red")
                # 如果方法1失败，尝试方法2
                subprocess.run([sys.executable, "save_image_urls.py"], check=False)
        else:
            cprint("未找到save_image_urls.py脚本，跳过提取媒体链接", "yellow")
    except Exception as e:
        cprint(f"调用save_image_urls.py脚本时出错: {str(e)}", "red")
            
    cprint("所有下载任务已完成", "green")

def reset_browser_state(driver):
    """
    重置浏览器状态，解决连续运行时的问题
    
    Args:
        driver: Selenium WebDriver实例
    """
    global running
    running = True  # 重置全局运行状态
    
    print("重置浏览器状态...")
    
    try:
        # 清除浏览器缓存和Cookies
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        
        # 刷新页面以确保获取最新内容
        driver.refresh()
        time.sleep(2)
        
        # 尝试滚动到页面顶部
        driver.execute_script("window.scrollTo(0, 0);")
        
        # 清除性能日志以避免前一次运行的日志影响
        driver.get_log("performance")
        
        print("浏览器状态已重置")
    except Exception as e:
        print(f"重置浏览器状态时出错: {str(e)}")
        
    return

