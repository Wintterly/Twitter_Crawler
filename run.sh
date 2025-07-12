#!/bin/bash

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Twitter爬虫启动脚本 - Mac版${NC}"
echo -e "${YELLOW}=============================${NC}"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}未检测到Python环境，请安装Python 3.6或更高版本。${NC}"
    echo -e "${YELLOW}推荐使用Homebrew安装Python：${NC}"
    echo -e "1. 安装Homebrew (如果尚未安装):"
    echo -e "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo -e "2. 安装Python:"
    echo -e "   brew install python"
    exit 1
fi

echo -e "${GREEN}检测到Python环境: $(python3 --version)${NC}"

# 创建虚拟环境（可选）
echo -e "${YELLOW}是否创建虚拟环境? (推荐) [y/n]${NC}"
read -r create_venv
if [[ "$create_venv" == "y" || "$create_venv" == "Y" ]]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    echo -e "${GREEN}虚拟环境已激活${NC}"
else
    echo -e "${YELLOW}跳过虚拟环境创建，将使用系统Python${NC}"
fi

# 安装依赖
echo -e "${YELLOW}正在安装所需依赖...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}依赖安装成功${NC}"
else
    echo -e "${RED}依赖安装失败，请检查网络连接或手动运行: pip install -r requirements.txt${NC}"
    exit 1
fi

# 检查ChromeDriver
echo -e "${YELLOW}检查ChromeDriver...${NC}"
if [ ! -f "chromedriver" ]; then
    echo -e "${YELLOW}未找到Mac版ChromeDriver，尝试下载...${NC}"
    
    # 获取Chrome版本
    chrome_version=$(defaults read /Applications/Google\ Chrome.app/Contents/Info.plist CFBundleShortVersionString)
    major_version=$(echo $chrome_version | cut -d. -f1)
    
    echo -e "${YELLOW}检测到Chrome版本: $chrome_version${NC}"
    
    # 下载对应版本的ChromeDriver (简化版，实际使用时可能需要更精确的版本匹配)
    curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$major_version" > chromedriver_version.txt
    driver_version=$(cat chromedriver_version.txt)
    
    echo -e "${YELLOW}下载ChromeDriver版本: $driver_version${NC}"
    curl -L "https://chromedriver.storage.googleapis.com/$driver_version/chromedriver_mac64.zip" -o chromedriver.zip
    
    # 解压并设置权限
    unzip -o chromedriver.zip
    chmod +x chromedriver
    rm chromedriver.zip chromedriver_version.txt
fi

echo -e "${GREEN}准备就绪，启动Twitter爬虫UI界面...${NC}"

# 启动爬虫UI界面
python3 twitter_crawler_ui.py

echo -e "${YELLOW}程序已退出${NC}" 