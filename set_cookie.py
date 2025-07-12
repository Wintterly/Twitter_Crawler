import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 资源路径处理函数
def get_resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    if hasattr(sys, '_MEIPASS'):  # PyInstaller打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 初始化浏览器
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    try:
        # 尝试使用打包后的chromedriver
        chromedriver_path = get_resource_path("chromedriver.exe")
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
            return webdriver.Chrome(service=service, options=options)
        else:
            # 如果找不到打包的chromedriver，使用webdriver_manager下载
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
    except Exception:
        # 如果上述方法都失败，尝试直接创建
        return webdriver.Chrome(options=options)

# 生成cookies
browser = init_browser()

try:
    browser.get("https://x.com/i/flow/login")
    print("\033[93m请在浏览器中登录X账号,登录完成后可手动关闭浏览器或等待90秒自动关闭\033[0m")
    
    # 等待90秒或直到浏览器关闭
    start_time = time.time()
    while time.time() - start_time < 90:
        try:
            # 检查浏览器是否还在运行
            browser.current_url
            time.sleep(1)
        except:
            print("\n\033[93m检测到浏览器已关闭,正在保存cookies...\033[0m")
            break
            
    # 获取cookies并验证
    try:
        cookies = browser.get_cookies()
        # 验证是否包含关键cookie
        has_auth = any(cookie['name'] == 'auth_token' for cookie in cookies)
        
        if has_auth:
            jsonCookies = json.dumps(cookies)
            cookie_path = 'X_cookie.json'
            print("\n\033[92m登录成功,已保存cookies\033[0m")
            with open(cookie_path, 'w') as f:
                f.write(jsonCookies)
        else:
            print("\n\033[91m登录失败,未获取到有效cookies,请重试\033[0m")
            
    except Exception as e:
        print("\n\033[91m浏览器已关闭,无法获取cookies,请重新运行程序\033[0m")
        
finally:
    try:
        browser.quit()
    except:
        pass
