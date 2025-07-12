import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                           QPushButton, QTextEdit, QDateEdit, QCheckBox,
                           QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
import io
import sys
from contextlib import redirect_stdout
import twitter_Crawler
import main as crawler_main
import config
import signal
import json
import importlib
import time
import logging
from pathlib import Path
# 移除直接导入set_cookie

"""
Twitter爬虫图形界面程序

本模块提供了一个基于PyQt6的图形用户界面,用于控制Twitter爬虫的运行。
主要功能包括:
- 配置爬虫参数(关键词、时间范围、数量限制等)
- 实时显示爬虫运行状态和输出信息
- 支持中途停止爬虫任务
- 错误处理和异常显示

主要类:
- OutputRedirector: 用于重定向标准输出到GUI界面
- CrawlerThread: 在独立线程中运行爬虫任务
- MainWindow: 主窗口类,包含所有GUI组件和交互逻辑

作者: Msgren
创建日期: 2025-07-10
最后修改: 2025-07-10
"""



class OutputRedirector(io.StringIO):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def write(self, text):
        self.signal.emit(text)
        super().write(text)

class CrawlerThread(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, config_data):
        super().__init__()
        self.config_data = config_data
        self._is_running = True

    def stop(self):
        self._is_running = False
        twitter_Crawler.running = False
        self.output_signal.emit("\n正在停止爬虫任务...")

    def run(self):
        try:
            # 重新导入并重置所有相关模块
            import download_method
            importlib.reload(config)
            importlib.reload(twitter_Crawler)
            importlib.reload(crawler_main)
            importlib.reload(download_method)
            
            # 重置所有模块的状态
            download_method.log_file_path = None
            download_method.target_folder = None
            twitter_Crawler.running = True
            crawler_main.running = True
            
            # 创建结果文件夹
            result_folder = crawler_main.create_result_folder()
            self.output_signal.emit(f"创建结果文件夹: {result_folder}")

            # 根据选择的模式执行不同的爬虫
            crawler_mode = self.config_data['crawler_mode']
            
            # 使用重定向器包装所有输出
            with redirect_stdout(OutputRedirector(self.output_signal)):
                if crawler_mode == 0:  # 全部爬取
                    self.output_signal.emit("\n开始执行全部爬取模式...")
                    crawler_main.run_twitter_crawler(result_folder)
                    if self._is_running:
                        crawler_main.run_dz_crawler(result_folder)
                
                elif crawler_mode == 1:  # 最新爬取
                    self.output_signal.emit("\n开始执行最新爬取模式...")
                    crawler_main.run_twitter_crawler(result_folder)
                
                elif crawler_mode == 2:  # 热度爬取
                    self.output_signal.emit("\n开始执行热度爬取模式...")
                    crawler_main.run_dz_crawler(result_folder)

                self.output_signal.emit("\n爬取任务执行完成！")

        except Exception as e:
            self.error_signal.emit(str(e))
            self.output_signal.emit(f"错误: {str(e)}")

class TwitterCrawlerUI(QMainWindow):
    # 在类级别定义信号
    output_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.crawler_thread = None
        self.setup_logging()
        self.load_config()  # 添加加载配置的调用
        self.initUI()
        # 连接信号到更新输出的槽
        self.output_signal.connect(self.update_output)

    def setup_logging(self):
        """设置日志记录器"""
        # 创建logs目录（如果不存在）
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 生成日志文件名（使用当前时间）
        log_filename = log_dir / f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # 配置日志记录器
        self.logger = logging.getLogger('TwitterCrawler')
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        self.logger.addHandler(file_handler)
        
        self.logger.info('日志系统初始化完成')

    def log_message(self, message, level='info'):
        """记录消息到日志文件
        
        Args:
            message (str): 要记录的消息
            level (str): 日志级别，可选值：'info', 'warning', 'error'
        """
        message = message.strip()
        if not message:
            return
            
        if level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)

    def initUI(self):
        self.setWindowTitle('Twitter爬虫控制面板')
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)  # 设置最小窗口大小

        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建表单布局
        form_layout = QVBoxLayout()

        # 爬虫模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel('爬取模式:')
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            '全部爬取 - 同时执行最新和热度爬虫',
            '最新爬取 - 按时间顺序爬取',
            '热度爬取 - 按点赞数爬取'
        ])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        form_layout.addLayout(mode_layout)

        # Tag输入
        tag_layout = QHBoxLayout()
        tag_label = QLabel('标签(Tag):')
        self.tag_input = QLineEdit()
        self.tag_input.setText(config.tag)
        tag_layout.addWidget(tag_label)
        tag_layout.addWidget(self.tag_input)
        form_layout.addLayout(tag_layout)

        # 下载选项
        choice_layout = QHBoxLayout()
        choice_label = QLabel('下载内容:')
        self.choice_combo = QComboBox()
        self.choice_combo.addItems(['1 - 仅图片', '2 - 仅视频', '3 - 仅GIF', '123 - 全部'])
        choice_layout.addWidget(choice_label)
        choice_layout.addWidget(self.choice_combo)
        form_layout.addLayout(choice_layout)

        # 延迟时间
        late_time_layout = QHBoxLayout()
        late_time_label = QLabel('延迟时间(秒):')
        self.late_time_spin = QSpinBox()
        self.late_time_spin.setRange(1, 30)
        self.late_time_spin.setValue(config.late_time)
        late_time_layout.addWidget(late_time_label)
        late_time_layout.addWidget(self.late_time_spin)
        form_layout.addLayout(late_time_layout)

        # 时间范围选择
        date_layout = QHBoxLayout()
        self.date_flag_check = QCheckBox('启用时间范围')
        self.date_flag_check.setChecked(config.date_flag)
        date_layout.addWidget(self.date_flag_check)
        form_layout.addLayout(date_layout)

        # 开始时间
        start_date_layout = QHBoxLayout()
        start_date_label = QLabel('开始时间:')
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.fromString(config.start_time, 'yyyy-MM-dd'))
        self.start_date.setCalendarPopup(True)
        start_date_layout.addWidget(start_date_label)
        start_date_layout.addWidget(self.start_date)
        form_layout.addLayout(start_date_layout)

        # 结束时间
        end_date_layout = QHBoxLayout()
        end_date_label = QLabel('结束时间:')
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.fromString(config.end_time, 'yyyy-MM-dd'))
        self.end_date.setCalendarPopup(True)
        end_date_layout.addWidget(end_date_label)
        end_date_layout.addWidget(self.end_date)
        form_layout.addLayout(end_date_layout)

        # URLs数量
        urls_num_layout = QHBoxLayout()
        urls_num_label = QLabel('按照热度爬取推文数量(仅热度爬取模式有效):')
        self.urls_num_spin = QSpinBox()
        self.urls_num_spin.setRange(1, 1000)
        self.urls_num_spin.setValue(config.urls_num)
        urls_num_layout.addWidget(urls_num_label)
        urls_num_layout.addWidget(self.urls_num_spin)
        form_layout.addLayout(urls_num_layout)

        # 添加表单到主布局
        layout.addLayout(form_layout)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        self.set_cookie_button = QPushButton('设置Cookie')
        self.save_config_button = QPushButton('保存配置')  # 新增保存配置按钮
        self.start_button = QPushButton('开始爬取')
        self.stop_button = QPushButton('停止爬取')
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_crawler)
        self.stop_button.clicked.connect(self.stop_crawler)
        self.set_cookie_button.clicked.connect(self.set_cookie)
        self.save_config_button.clicked.connect(self.save_config)  # 连接保存配置事件
        button_layout.addWidget(self.set_cookie_button)
        button_layout.addWidget(self.save_config_button)  # 添加保存配置按钮到布局
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # 创建输出显示区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 禁用换行
        self.output_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # 显示水平滚动条
        self.output_text.setMinimumHeight(150)  # 设置最小高度为150像素
        layout.addWidget(self.output_text, 1)  # 添加拉伸因子1，使输出区域可以随窗口调整大小

        # 设置样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                font-size: 14px;
                min-width: 100px;
                color: white;
            }
            QLineEdit, QComboBox, QSpinBox, QDateEdit {
                padding: 5px;
                font-size: 14px;
                min-width: 200px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #2d2d2d;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
                margin-right: 5px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2d2d2d;
                border: none;
            }
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
            QPushButton {
                padding: 8px 15px;
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
            }
            QTextEdit {
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
                padding: 5px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                line-height: 1.2;
            }
            QCalendarWidget {
                background-color: #2d2d2d;
                color: white;
            }
            QCalendarWidget QWidget {
                background-color: #2d2d2d;
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
            }
            QCalendarWidget QMenu {
                background-color: #2d2d2d;
                color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #4CAF50;
            }
        """)

    def load_config(self):
        """从config.py文件加载最新配置"""
        try:
            # 重新导入config模块以获取最新配置
            importlib.reload(config)
            self.log_message("已加载最新配置文件")
        except Exception as e:
            error_msg = f"加载配置文件失败: {str(e)}"
            self.log_message(error_msg, 'error')
            QMessageBox.critical(self, '错误', error_msg)

    def update_ui_from_config(self):
        """根据config更新界面显示"""
        try:
            # 更新界面控件的值
            self.tag_input.setText(config.tag)
            
            # 更新下载选项
            choice_text = ''
            if config.user_choice == '1':
                choice_text = '1 - 仅图片'
            elif config.user_choice == '2':
                choice_text = '2 - 仅视频'
            elif config.user_choice == '3':
                choice_text = '3 - 仅GIF'
            elif config.user_choice == '123':
                choice_text = '123 - 全部'
            index = self.choice_combo.findText(choice_text)
            if index >= 0:
                self.choice_combo.setCurrentIndex(index)
            
            self.late_time_spin.setValue(config.late_time)
            self.date_flag_check.setChecked(config.date_flag)
            self.start_date.setDate(QDate.fromString(config.start_time, 'yyyy-MM-dd'))
            self.end_date.setDate(QDate.fromString(config.end_time, 'yyyy-MM-dd'))
            self.urls_num_spin.setValue(config.urls_num)
            
            self.log_message("界面已更新为最新配置")
        except Exception as e:
            error_msg = f"更新界面配置失败: {str(e)}"
            self.log_message(error_msg, 'error')
            QMessageBox.critical(self, '错误', error_msg)

    def check_cookie_valid(self):
        try:
            cookie_file = 'X_cookie.json'
            if not os.path.exists(cookie_file):
                return False
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                
            # 只检查cookie是否为空或null
            return cookie_data is not None and len(cookie_data) > 0
                
        except Exception as e:
            return False

    def set_cookie(self):
        try:
            self.output_text.append("\n开始设置Cookie...")
            # 重新导入set_cookie模块
            if 'set_cookie' in sys.modules:
                importlib.reload(sys.modules['set_cookie'])
            else:
                importlib.import_module('set_cookie')
            
            self.output_text.append("请在浏览器中登录X账号，登录完成后可手动关闭浏览器或等待90秒自动关闭")
            
            # 等待一段时间，让用户有机会完成登录
            time.sleep(2)  # 给一点时间让消息显示出来
            
            # 验证cookie是否设置成功
            if self.check_cookie_valid():
                self.output_text.append("Cookie验证成功！")
            else:
                self.output_text.append("警告：Cookie可能未正确设置，请重试！")
                
        except Exception as e:
            error_msg = f"设置Cookie时发生错误：{str(e)}，请重新点击设置Cookie按钮"
            self.output_text.append(error_msg)
            QMessageBox.critical(self, '错误', error_msg)
    
    # 爬虫主程序启动
    def start_crawler(self):
        try:
            # 重新导入所有相关模块
            import download_method
            import saveDZ_crawler
            importlib.reload(config)
            importlib.reload(twitter_Crawler)
            importlib.reload(crawler_main)
            importlib.reload(download_method)
            importlib.reload(saveDZ_crawler)
            
            # 重置所有模块的状态
            download_method.log_file_path = None
            download_method.target_folder = None
            twitter_Crawler.running = True  # 修改为True
            crawler_main.running = True     # 修改为True
            saveDZ_crawler.running = True
            saveDZ_crawler.download_count = 0
            saveDZ_crawler.download_threads = []
            
            self.log_message("已重新加载最新配置文件和相关模块")
            
            # 检查Cookie
            if not self.check_cookie_valid():
                error_msg = "Cookie无效或不存在，请重新设置Cookie！"
                self.output_text.append(error_msg)
                QMessageBox.warning(self, '警告', error_msg)
                return
            else:
                self.output_text.append("Cookie有效，开始启动爬虫...")

            # 验证日期
            if config.date_flag:
                start_datetime = datetime.strptime(config.start_time, '%Y-%m-%d')
                end_datetime = datetime.strptime(config.end_time, '%Y-%m-%d')
                if start_datetime > end_datetime:
                    error_msg = "开始时间不能晚于结束时间！"
                    self.log_message(error_msg, 'error')
                    QMessageBox.warning(self, '警告', error_msg)
                    return

            # 直接使用config中的配置
            config_data = {
                'tag': config.tag,
                'user_choice': config.user_choice,
                'late_time': config.late_time,
                'date_flag': config.date_flag,
                'start_time': config.start_time,
                'end_time': config.end_time,
                'urls_num': config.urls_num,
                'crawler_mode': self.mode_combo.currentIndex()  # 0: 全部, 1: 最新, 2: 热度
            }

            # 在输出框中显示当前使用的配置
            self.output_text.append("\n当前使用的配置：")
            self.output_text.append(f"标签(Tag): {config.tag}")
            self.output_text.append(f"下载内容: {config.user_choice}")
            self.output_text.append(f"延迟时间: {config.late_time}秒")
            self.output_text.append(f"启用时间范围: {'是' if config.date_flag else '否'}")
            if config.date_flag:
                self.output_text.append(f"时间范围: {config.start_time} 至 {config.end_time}")
            self.output_text.append(f"爬取数量: {config.urls_num}")

            # 禁用开始按钮，启用停止按钮
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # 创建并启动爬虫线程
            self.crawler_thread = CrawlerThread(config_data)
            self.crawler_thread.output_signal.connect(self.update_output)
            self.crawler_thread.error_signal.connect(self.handle_error)
            self.crawler_thread.finished.connect(self.crawler_finished)
            self.crawler_thread.start()

        except Exception as e:
            error_msg = f'启动爬虫时发生错误：{str(e)}'
            self.log_message(error_msg, 'error')
            QMessageBox.critical(self, '错误', error_msg)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def stop_crawler(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.output_text.append("\n正在停止爬虫...")
            self.stop_button.setEnabled(False)

    def update_output(self, text):
        # 移除文本中的额外换行符
        text = text.rstrip('\n')
        if text:
            current_text = self.output_text.toPlainText()
            if current_text:
                self.output_text.append(text)
            else:
                self.output_text.setText(text)
            # 记录到日志文件
            self.log_message(text)
            # 滚动到底部
            self.output_text.verticalScrollBar().setValue(
                self.output_text.verticalScrollBar().maximum()
            )

    def handle_error(self, error_msg):
        QMessageBox.critical(self, '错误', error_msg)
        # 记录错误信息到日志
        self.log_message(error_msg, 'error')
        self.crawler_finished()

    def crawler_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        finish_msg = "爬虫任务已完成！"
        self.output_text.append("\n" + finish_msg)
        self.log_message("\n" + finish_msg)

    def save_config(self):
        """保存用户配置到config文件"""
        try:
            # 更新内存中的配置
            config.tag = self.tag_input.text()
            config.user_choice = self.choice_combo.currentText()[0]
            config.late_time = self.late_time_spin.value()
            config.date_flag = self.date_flag_check.isChecked()
            
            start_date = self.start_date.date().toString('yyyy-MM-dd')
            end_date = self.end_date.date().toString('yyyy-MM-dd')
            
            # 验证日期
            if config.date_flag:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                
                if start_datetime > end_datetime:
                    error_msg = "开始时间不能晚于结束时间！"
                    self.log_message(error_msg, 'error')
                    QMessageBox.warning(self, '警告', error_msg)
                    return
            
            config.start_time = start_date
            config.end_time = end_date
            config.urls_num = self.urls_num_spin.value()

            # 将配置写入config.py文件
            config_content = f'''# -*- coding: utf-8 -*-
# @Time    : 2025/07/05 17:00
# @Author  : Winter
# @File    : config.py
# @Version : 1.0

tag = "{config.tag}" # 需要爬取的tag
user_choice = '{config.user_choice}' # 设置下载选项，1为图片，2为视频，3为GIF动图，123为全部，目前暂时只支持图片
late_time = {config.late_time} # 设置延迟时间，每隔4s向下滑动，为保险可设置10-5之间最佳，建议默认

date_flag = {str(config.date_flag)} # 设置是否根据日期进行爬取，true为获取全部，false为到指定时间

# 设置时间范围
start_time = '{config.start_time}' # 设置开始的获取日期，格式为2023-10-08
end_time = '{config.end_time}' # 设置结束的获取日期，格式为2023-10-08

# 按热度（点赞数）爬取时设置，爬取多少条带图片的推文
urls_num = {config.urls_num}
'''
            # 写入文件
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 记录配置更新
            success_msg = "配置已成功保存到config.py文件！"
            self.log_message(success_msg)
            self.output_text.append("\n" + success_msg)
            QMessageBox.information(self, '成功', success_msg)
            
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            self.log_message(error_msg, 'error')
            QMessageBox.critical(self, '错误', error_msg)

def main():
    # 在主线程中设置信号处理
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    window = TwitterCrawlerUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 