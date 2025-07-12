import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    if hasattr(sys, '_MEIPASS'):  # PyInstaller打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def initialize_driver():
    # 初始化Chrome浏览器驱动
    options = ChromeOptions()
    
    # 设置性能日志
    options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )

    # 添加必要的参数来提高稳定性
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    
    # 设置更现代的用户代理
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # # 启用无头浏览器模式
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")  # 禁用GPU加速
    # options.add_argument("--window-size=1920x1080")  # 设置窗口大小，防止某些元素不可见

    # 不启用无头模式时开启，调式代码或者看报错的时候使用。
    options.add_argument("window-position=660,0")

    # 设置页面加载策略
    options.page_load_strategy = 'eager'

    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # 尝试使用打包后的chromedriver
            try:
                chromedriver_path = get_resource_path("chromedriver.exe")
                if os.path.exists(chromedriver_path):
                    service = Service(executable_path=chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    # 如果找不到打包的chromedriver，使用webdriver_manager下载
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
            except Exception:
                # 如果上述方法都失败，尝试直接创建
                driver = webdriver.Chrome(options=options)
                
            driver.set_page_load_timeout(30)  # 增加页面加载超时时间
            driver.set_script_timeout(30)     # 设置脚本执行超时时间
            return driver
        except WebDriverException as e:
            if attempt == max_retries - 1:
                raise e
            print(f"创建驱动失败，正在重试 ({attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2  # 指数退避


def cookies_web(driver, cookie_path):
    # 设置浏览器的cookie
    print("设置cookie中.....")
    try:
        cookie_path = get_resource_path(cookie_path)
        with open(cookie_path, 'r') as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"添加cookie失败: {str(e)}")
                continue
        print("Cookie设置完成")
    except FileNotFoundError:
        print(f"Cookie文件 {cookie_path} 不存在")
    except json.JSONDecodeError:
        print(f"Cookie文件格式错误")
    except Exception as e:
        print(f"设置cookie时发生错误: {str(e)}")


# def get_twitter_name(driver):
#     # 获取Twitter用户的名称
#     name = driver.find_elements(By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[1]/div[1]/div/div/div/div/div/div[2]/div/h2/div/div/div/div/span[1]/span/span[1]')
#     folder = name[0].text.replace('/', '-')  # 防止斜杠视作创建多级文件夹

#     return folder