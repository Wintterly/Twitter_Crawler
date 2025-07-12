# Twitter_Crawler

这是一个Twitter（现X平台）图片爬虫工具，支持按标签和时间范围爬取图片、视频和GIF。(目前暂时只支持图片爬取)

**有效时间：截止到2025/07/12可正常使用，由于x会不定时变换页面，故若爬虫失效，请针对查找页面元素的代码进行修改即可**

**本软件仅供学习交流，如作他用所承受的法律责任一概与作者无关（下载使用即代表你同意上述观点）**

## 主要功能

- 🔍 按标签（tag）搜索并下载内容
- 📅 支持设置时间范围过滤
- 🖼️ 支持下载图片、视频和GIF（视频和GIF功能待完善）
- ❤️ 支持按热度（点赞数）爬取内容
- 📝 自动生成下载日志
- 🔗 保存所有下载内容的原始链接
- 🔄 支持连续运行多次爬虫任务而不需要重启程序

## 环境要求

- Python 3.6+
- Chrome浏览器
- ChromeDriver（已包含），如果发现浏览器弹出失败，请删除chromedriver.exe并重新运行程序，会根据你的chrome版本下载对应驱动
- 依赖的Python库:
  - selenium 4.15.2+
  - requests 2.31.0+
  - termcolor 2.3.0+
  - tenacity 8.2.2+
  - urllib3 2.0.0+
  - datetime 5.0+
  - PyQt6 6.4.0+
  - psutil 5.9.0+ (新增依赖，用于浏览器资源管理)

## 安装步骤

1. 克隆项目到本地
```bash
git clone https://github.com/Wintterly/Twitter_Crawler.git
cd twitter_Crawler
```

2. 安装依赖包
```bash
pip install -r requirements.txt
```

## 使用源码

### 1. 配置Cookie

首次使用需要获取Twitter的登录Cookie，如果是使用ui界面请直接点击获取cookie按钮即可

1. 运行Cookie设置脚本：
```bash
python set_cookie.py
```

2. 在打开的浏览器窗口中登录Twitter（90秒内完成）
3. 等待浏览器自动关闭，Cookie将保存为`X_cookie.json`

注意：请勿手动关闭浏览器，否则可能导致Cookie获取失败，原因是手动关闭浏览器但是驱动会异常关闭

### 2. 配置爬虫参数

在`config.py`中设置以下参数：

- `tag`：要爬取的标签（不需要加#）
- `user_choice`：下载内容类型（1:图片，2:视频，3:GIF，123:全部）
- `late_time`：页面滚动延迟时间（建议5-10秒，不建议修改）
- `date_flag`：是否启用时间范围过滤（建议启用）
- `start_time`：开始时间（格式：YYYY-MM-DD）
- `end_time`：结束时间（格式：YYYY-MM-DD）
- `urls_num`：按热度爬取时的推文数量

### 3. 运行爬虫

执行主程序：
```bash
python main.py
```

或者运行UI界面：
```bash
python twitter_crawler_ui.py
```

程序会同时启动两个爬虫线程：
- Twitter爬虫：按时间顺序爬取内容
- 热度爬虫：按点赞数爬取内容

**重要更新**：现在支持连续运行多次爬虫任务而不需要退出程序。两次爬虫运行之间会自动清理浏览器资源，确保每次爬取都有一个干净的环境。

### 4. 输出结果

所有结果将保存在以下格式的文件夹中：
```
result_[标签名]_[时间戳]/
├── time_crawler_result/    # 按时间顺序爬取的结果
│   ├── 图片文件
│   ├── video & gif/          # 视频和GIF文件夹
│   ├── download_log.txt      # 下载日志
│   └── image.txt             # 图片链接文件
└── hot_crawler_result/   # 按热度爬取的结果
    ├── 图片文件
    ├── [标签名]_dianzan_log.txt
    └── image.txt
```

**log文件会有三份，如果使用批处理文件run.sh和run.bat启动程序，会额外生成run_log.txt文件**

## 一键启动

如果你是Windows且无python环境，直接双击run.bat启动项目即可，会自动下载所需环境并启动ui界面

如果你是Mac用户，可以使用以下步骤：
1. 打开终端，进入项目目录
2. 给脚本添加执行权限：`chmod +x run.sh`
3. 运行脚本：`./run.sh`

run.sh脚本会自动检查Python环境，安装依赖，下载适合Mac的ChromeDriver并启动UI界面。

## 注意事项

1. 由于Twitter页面是动态加载的，程序使用Selenium模拟浏览器操作，请确保网络连接稳定
2. 下载使用线程锁控制，默认同时下载10张图片和3个视频，可在`download_method.py`中调整`video_connections`和`img_connections`的值
3. 时间范围过滤仅在标签搜索页面有效，用户主页由于有置顶功能可能导致过滤异常
4. 如果爬虫失效，请先检查Twitter页面元素是否更新
5. ui界面修改配置后需点击保存配置，看到保存成功信息和提示框就可以了
6. 多次连续运行爬虫时，会自动清理浏览器资源，无需手动关闭程序重新启动，全程不需要手动关闭浏览器，等待即可
7. 延迟时间可以根据网速修改，但不建议修改短，如果网速较慢请修改长一些
8. Mac用户运行run.sh脚本时可能需要确认是否允许脚本下载和运行ChromeDriver

## 开发说明

- 项目使用Selenium进行页面操作
- 使用多线程处理并发下载
- 实现了断点续传功能
- 包含详细的日志记录
- 内置浏览器资源清理机制，确保连续运行稳定性
- 默认不开启无头浏览器模式，便于调试和发现问题

## 最近更新（问题及修改）

- **2024/07/08**: 修复连续运行爬虫时，time模块无法正常运行的问题
  - 添加浏览器状态重置功能，确保每次爬取都有一个干净的环境
  - 改进浏览器资源清理机制，解决浏览器实例残留问题
  - 增强帖子处理逻辑，提高爬取成功率
  - 新增依赖：psutil库，用于更有效地管理浏览器进程
- **2024/07/08**:  mac上运行源码ui界面正常可以更新配置，使用pyinstaller在Windows上打包exe文件时修改配置文件后，无法正常更新配置文件，会沿用之前的配置进行爬取，内存未重新刷新
- **2024/07/11**: 增加了UI界面的使用说明，添加了更详细的注意事项
- **2024/07/12**: 为Mac用户添加了run.sh启动脚本，提供了与Windows版本类似的一键启动功能

## 文件功能说明

本项目包含多个Python模块，每个文件都有特定的功能，下面是主要文件的功能说明：

### 核心文件
- `main.py`: 爬虫程序的主入口，协调不同爬虫功能的执行，包括时间顺序爬虫和热度爬虫
- `twitter_Crawler.py`: 实现Twitter时间顺序爬虫的核心逻辑，用于按时间顺序爬取指定标签的内容
- `saveDZ_crawler.py`: 实现热度爬虫功能，按点赞数爬取内容
- `download_method.py`: 提供图片和视频的下载方法，包括线程控制、信号量管理和日志记录

### 配置与初始化
- `config.py`: 存储爬虫的配置参数，包括标签、时间范围、下载选项等
- `driver_init.py`: 负责初始化Selenium浏览器驱动
- `set_cookie.py`: 用于获取并保存Twitter的登录Cookie
- `X_cookie.json`: 保存Twitter的登录Cookie数据

### 用户界面
- `twitter_crawler_ui.py`: 提供基于PyQt6的图形用户界面，方便用户配置和操作爬虫
- `run.bat`: Windows平台的一键启动脚本
- `run.sh`: Mac平台的一键启动脚本

### 数据处理
- `manga_downloader.py`: 负责从Twitter页面提取媒体内容并启动下载
- `json_process.py`: 处理JSON格式的数据
- `save_image_urls.py`: 保存图片URL到文本文件，方便后续使用

### 工具与辅助
- `utils.py`: 包含各种辅助功能，如资源路径处理、目录创建等
- `chromedriver.exe`: Chrome浏览器的驱动程序(Windows版)
- `LICENSE.chromedriver`: ChromeDriver的许可证文件
- `THIRD_PARTY_NOTICES.chromedriver`: ChromeDriver的第三方通知

### 说明文档
- `README.md`: 项目说明文档
- `way.md`: 可能包含一些额外的使用说明或注意事项
- `注意事项.txt`: 中文版的注意事项说明

## 许可证

本项目使用的ChromeDriver遵循[LICENSE.chromedriver](LICENSE.chromedriver)。

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目。
