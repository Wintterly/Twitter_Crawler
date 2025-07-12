import os
import time
import shutil
import threading
import signal
from datetime import datetime
from termcolor import cprint
from config import tag
import twitter_Crawler
from saveDZ_crawler import crawl_tag_images
from save_image_urls import main as save_image_urls

# 全局变量用于控制程序运行
running = True

def signal_handler(signum, frame):
    """信号处理函数"""
    global running
    cprint("\n检测到用户中断，正在安全退出...", "yellow")
    running = False

def create_result_folder():
    """创建统一的结果文件夹"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    result_folder = f"result_{tag}_{timestamp}"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    return result_folder

def run_twitter_crawler(result_folder):
    """运行Twitter爬虫"""
    driver = None
    try:
        cprint("\n开始运行Twitter爬虫...", "blue")
        
        if datetime.strptime(twitter_Crawler.start_time, '%Y-%m-%d') > datetime.strptime(twitter_Crawler.end_time, '%Y-%m-%d'):
            print("开始日期不能晚于结束日期！")
            return
            
        cprint(f"\n将爬取 {twitter_Crawler.start_time} 到 {twitter_Crawler.end_time} 之间的帖子\n", "red")

        driver = twitter_Crawler.initialize_driver()

        try:
            driver.get('https://x.com/i/flow/login')
        except twitter_Crawler.TimeoutException:
            driver.execute_script('window.stop()')
        driver.set_page_load_timeout(60)

        try:
            driver.get('https://x.com')
            twitter_Crawler.cookies_web(driver, "X_cookie.json")
        except Exception as e:
            print(f"访问失败，请检查网络连接: {str(e)}")
            return

        print("访问推特页面中.....")
        target_url = f"https://x.com/search?q={tag}&src=typed_query&f=live"
        driver.get(target_url)
        print("准备获取数据中.....")

        time.sleep(1)

        is_media = target_url.endswith("/media")

        # 创建time_crawler_result文件夹
        folder = os.path.join(result_folder, "time_crawler_result")
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 创建视频文件夹
        video_folder = os.path.join(folder, "video & gif")
        if "2" in twitter_Crawler.user_choice or "3" in twitter_Crawler.user_choice:
            if not os.path.exists(video_folder):
                os.makedirs(video_folder)

        # 设置日志文件的目标文件夹和初始化日志文件
        from download_method import set_target_folder, move_log_file
        set_target_folder(folder)
        
        # 创建并初始化日志文件
        log_file_path = os.path.join(folder, "download_log.txt")
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"下载日志创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取标签: {tag}\n")
            f.write("-" * 50 + "\n")
            f.write(f"图片将保存在文件夹: {folder}\n")
            f.write(f"时间范围: {twitter_Crawler.start_time} 到 {twitter_Crawler.end_time}\n")
            f.write(f"日志文件: {log_file_path}\n\n")
            f.write("开始爬取...\n")

        cprint(f"开始爬取数据...., url为：{target_url}", "yellow")
        
        download_completed = False
        try:
            twitter_Crawler.download_media(driver, folder, video_folder, twitter_Crawler.user_choice, is_media, twitter_Crawler.start_time, twitter_Crawler.end_time)
            download_completed = True
            
        except KeyboardInterrupt:
            print("\n检测到用户中断，正在安全退出...")
        except Exception as e:
            print(f"发生错误: {str(e)}")
        finally:
            twitter_Crawler.running = False
            
            try:
                print(f'\n共下载 {len([f for f in os.listdir(folder) if f.endswith(".png")])} 张图片')
                if "2" in twitter_Crawler.user_choice or "3" in twitter_Crawler.user_choice:
                    print(f'共下载 {len(os.listdir(video_folder))} 个视频')
            except Exception as e:
                print(f"统计文件数量时发生错误: {str(e)}")
            
            print("程序已安全退出。")
        
        # 只有在下载完成后才执行后续操作
        if download_completed:
            cprint(f"Twitter爬虫结果已保存到: {folder}", "green")
            # 保存图片链接
            save_image_urls(os.path.join(folder, "download_log.txt"), folder)

    except Exception as e:
        cprint(f"Twitter爬虫运行出错: {str(e)}", "red")
    finally:
        # 确保浏览器实例被正确关闭
        if driver:
            try:
                # 关闭所有相关的窗口
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()
                driver.quit()
                
                # 确认浏览器真正关闭
                print("浏览器正在关闭...")
                time.sleep(1)  # 给予关闭时间
                
                # 尝试执行一个简单命令，如果失败说明浏览器已经关闭
                try:
                    driver.title
                    print("浏览器未能正常关闭，尝试强制终止...")
                    # 强制结束进程
                    try:
                        import psutil
                        driver_process = psutil.Process(driver.service.process.pid)
                        for proc in driver_process.children(recursive=True):
                            proc.kill()
                        driver_process.kill()
                    except:
                        pass
                except:
                    print("浏览器已成功关闭")
                
            except Exception as e:
                print(f"关闭浏览器时发生错误: {str(e)}")
                # 强制结束进程
                try:
                    import psutil
                    process = psutil.Process(driver.service.process.pid)
                    for proc in process.children(recursive=True):
                        proc.terminate()
                    process.terminate()
                except:
                    pass
            finally:
                driver = None  # 确保引用被清除

def run_dz_crawler(result_folder):
    """运行点赞爬虫"""
    try:
        cprint("\n开始运行根据热度（点赞数）爬取图片...", "blue")
        
        # 创建热度爬虫结果目录
        dz_folder = os.path.join(result_folder, "hot_crawler_result")
        if not os.path.exists(dz_folder):
            os.makedirs(dz_folder)
            
        # 运行热度爬虫，传入结果目录
        folder, log_file = crawl_tag_images(save_folder=dz_folder)
        
        if folder:
            cprint(f"热度爬虫结果已保存到: {dz_folder}", "green")
            # 保存图片链接
            save_image_urls(os.path.join(dz_folder, f"{tag}_dianzan_log.txt"), dz_folder)
            
    except Exception as e:
        cprint(f"热度爬虫运行出错: {str(e)}", "red")

def clean_browser_resources():
    """清理浏览器资源，确保不同爬虫之间不会互相影响"""
    print("\n正在清理浏览器资源...")
    
    # 尝试结束所有Chrome相关进程
    try:
        import psutil
        
        # 查找并终止所有Chrome相关进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                    print(f"尝试终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        print("未安装psutil库，无法清理Chrome进程")
    except Exception as e:
        print(f"清理Chrome进程时出错: {str(e)}")
    
    # 等待一段时间，确保进程完全终止
    time.sleep(3)
    
    # 清理临时文件
    try:
        import tempfile
        import shutil
        import glob
        
        # 尝试清理临时文件夹中的Chrome相关文件
        temp_dir = tempfile.gettempdir()
        chrome_temp_patterns = [
            os.path.join(temp_dir, "scoped_dir*"),
            os.path.join(temp_dir, "chrome_*"),
        ]
        
        for pattern in chrome_temp_patterns:
            for item in glob.glob(pattern):
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        os.remove(item)
                except:
                    pass
    except Exception as e:
        print(f"清理临时文件时出错: {str(e)}")
    
    print("浏览器资源清理完成\n")

def main():
    """主函数"""
    try:
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 创建结果文件夹
        result_folder = create_result_folder()
        cprint(f"创建结果文件夹: {result_folder}", "yellow")

        # 先运行时间爬虫
        cprint("\n开始执行全部爬取模式...", "blue")
        run_twitter_crawler(result_folder)
        
        # 在两个爬虫之间清理资源
        if running:
            clean_browser_resources()
        
        # 如果用户没有中断，再运行点赞爬虫
        if running:
            run_dz_crawler(result_folder)

        cprint("\n爬取任务执行完成！", "green")

    except KeyboardInterrupt:
        cprint("\n检测到用户中断，正在安全退出...", "yellow")
    except Exception as e:
        cprint(f"运行出错: {str(e)}", "red")

if __name__ == "__main__":
    main() 