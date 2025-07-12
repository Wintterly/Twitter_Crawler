import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 生成cookies
browser = webdriver.Chrome()

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
            print("\n\033[92m登录成功,已保存cookies\033[0m")
            with open('X_cookie.json', 'w') as f:
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
