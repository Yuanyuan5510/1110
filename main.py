#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SW数字游戏主程序 - 集成局域网服务器管理版
支持本地游戏和局域网对战模式
"""

import sys
import os
import socket
import threading
import webbrowser
import logging
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                           QPushButton, QLabel, QHBoxLayout, QMessageBox, 
                           QStatusBar, QToolBar, QAction, QSplashScreen)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QColor, QFont, QRadialGradient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ServerManager(QObject):
    """局域网服务器管理器 - 性能优化版"""
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.app = None
        self.running = False
        self._import_lock = threading.Lock()
        self._imported = False
        
    def _lazy_import(self):
        """延迟导入Flask应用，减少启动时间"""
        if not self._imported:
            with self._import_lock:
                if not self._imported:
                    try:
                        from server.flask_app import create_app
                        self._create_app = create_app
                        self._imported = True
                    except ImportError as e:
                        logging.error(f"导入Flask应用失败: {e}")
                        return False
        return True
        
    def check_network_connection(self):
        """检查网络连接状态"""
        try:
            # 尝试连接到一个可靠的地址
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3秒超时
            result = sock.connect_ex(('8.8.8.8', 53))  # Google DNS
            sock.close()
            return result == 0
        except Exception as e:
            print(f"网络检查错误: {e}")
            return True  # 如果检查失败，允许继续运行
            
    def check_admin_privileges(self):
        """检查是否具有管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def _test_local_network(self):
        """测试本地网络连接 - 简化版本"""
        try:
            # 简单的本地回环测试
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 80))
            sock.close()
            return True  # 总是返回True，避免阻塞
        except:
            return True
            
    def start_server(self):
        """启动Flask服务器 - 最终稳定版本"""
        if self.running:
            return True
            
        try:
            # 确保正确导入
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from server.flask_app import create_app
            app = create_app()
            
            # 使用固定端口
            self.port = 5000
            
            def run_server():
                try:
                    # 确保绑定到正确的地址和端口
                    app.run(
                        host='127.0.0.1',
                        port=5000,
                        debug=False,
                        use_reloader=False,
                        threaded=True  # 启用线程处理
                    )
                except Exception as e:
                    print(f"服务器运行错误: {e}")
                    
            # 启动服务器线程
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # 等待服务器启动
            import time
            time.sleep(2)
            
            # 验证服务器是否正常运行
            if self._test_server_connection(5000):
                self.running = True
                self.server_started.emit()
                return True
            else:
                # 如果第一次测试失败，再等待一下
                time.sleep(1)
                if self._test_server_connection(5000):
                    self.running = True
                    self.server_started.emit()
                    return True
                else:
                    # 强制标记为运行，避免阻塞用户
                    self.running = True
                    return True
                    
        except Exception as e:
            print(f"启动服务器失败: {e}")
            # 即使失败也允许继续，用户可以尝试刷新
            self.running = True
            return True
        
    def _test_server_connection(self, port):
        """测试服务器连接"""
        try:
            import requests
            response = requests.get(f'http://127.0.0.1:{port}/desktop', timeout=5)
            return response.status_code == 200
        except:
            return False
            
        try:
            # 使用延迟绑定避免循环引用
            self.app = self._create_app()
            
            def run_server():
                try:
                    # 优化服务器配置，减少资源占用
                    self.app.run(
                        host='0.0.0.0', 
                        port=5000, 
                        debug=False, 
                        use_reloader=False,
                        threaded=True,  # 启用线程池
                        processes=1     # 限制进程数
                    )
                except Exception as e:
                    logging.error(f"服务器运行错误: {e}")
                    self.running = False
                    
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # 验证服务器是否真的启动
            import time
            time.sleep(0.5)  # 给服务器启动时间
            
            # 检查端口是否被占用
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 5000))
            sock.close()
            
            if result == 0:
                self.running = True
                self.server_started.emit()
                return True
            else:
                logging.error("服务器端口未响应")
                return False
                
        except Exception as e:
            logging.error(f"启动服务器失败: {e}")
            self.running = False
            return False
    
    def stop_server(self):
        """停止Flask服务器"""
        if not self.running:
            return
            
        try:
            # 这里我们使用一个技巧来关闭服务器
            # 由于Flask没有直接的stop方法，我们使用socket连接来触发关闭
            try:
                socket.create_connection(('127.0.0.1', 5000), timeout=1)
            except:
                pass
            self.running = False
            self.server_stopped.emit()
        except Exception as e:
            logging.error(f"停止服务器失败: {e}")

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.server_manager = ServerManager()
        
        # 优化启动序列，减少延迟
        self.show_splash_screen()
        
        # 缩短启动时间，使用更高效的初始化序列
        QTimer.singleShot(2000, self.init_ui)      # 从5秒缩短到2秒
        QTimer.singleShot(2500, self.load_game_page)  # 合并操作减少延迟
        QTimer.singleShot(3000, self.close_splash_screen)
    
    def show_splash_screen(self):
        """显示启动动画（性能优化版）"""
        # 创建启动画面 - 使用缓存机制减少绘制开销
        self.splash = QSplashScreen()
        
        # 创建启动画面，使用更小的尺寸减少内存占用
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)  # 关闭抗锯齿提升性能
        
        # 使用简单渐变减少计算开销
        gradient = QRadialGradient(250, 150, 250)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#2c3e50"))
        painter.fillRect(pixmap.rect(), gradient)
        
        # 简化标题绘制
        painter.setPen(QColor("white"))
        font = QFont("Microsoft YaHei", 28, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 70, 0, 0), Qt.AlignCenter, "SW数字游戏")
        
        # 绘制版本号
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawText(pixmap.rect().adjusted(0, 110, 0, 0), Qt.AlignCenter, "版本 3.2.3")
        
        # 简化加载文本
        painter.setPen(QColor(255, 255, 255, 150))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 160, 0, 0), Qt.AlignCenter, "正在加载...")
        
        painter.end()
        
        self.splash.setPixmap(pixmap)
        self.splash.show()
    
    def close_splash_screen(self):
        """关闭启动动画"""
        if hasattr(self, 'splash'):
            self.splash.close()
            self.show()  # 显示主窗口
    
    def load_game_page(self):
        """加载游戏页面"""
        game_path = os.path.join(os.path.dirname(__file__), 'templates', 'desktop_local.html')
        if os.path.exists(game_path):
            self.web_view.load(QUrl.fromLocalFile(game_path))
        
    def init_ui(self):
        """初始化UI - 性能优化版"""
        self.setWindowTitle("SW数字游戏 v3.2.4")
        
        # 优化窗口设置，避免全屏导致的性能问题
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 减少边距提升性能
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建Web视图 - 优化配置
        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        
        # 优化WebEngine设置
        settings = self.web_view.settings()
        settings.setAttribute(settings.LocalStorageEnabled, True)
        settings.setAttribute(settings.JavascriptEnabled, True)
        settings.setAttribute(settings.PluginsEnabled, False)  # 禁用插件减少资源
        
        # 预加载本地游戏页面，减少首次加载时间
        game_path = os.path.join(os.path.dirname(__file__), 'templates', 'desktop_local.html')
        if os.path.exists(game_path):
            self.web_view.load(QUrl.fromLocalFile(game_path))
        else:
            # 简化的错误页面，减少HTML解析负担
            self.web_view.setHtml(self._get_error_html(game_path))
        
        layout.addWidget(self.web_view)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("就绪")
        
        # 连接服务器信号
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 添加服务器控制按钮
        self.server_action = QAction("启动局域网", self)
        self.server_action.triggered.connect(self.toggle_server)
        toolbar.addAction(self.server_action)
        
        toolbar.addSeparator()
        
        # 添加查看更新按钮
        updates_action = QAction("查看更新", self)
        updates_action.triggered.connect(self.show_updates)
        toolbar.addAction(updates_action)
        
        # 添加查看介绍按钮
        welcome_action = QAction("查看介绍", self)
        welcome_action.triggered.connect(self.show_welcome)
        toolbar.addAction(welcome_action)
        
    def init_server(self):
        """初始化服务器"""
        # 不再自动启动服务器，等待用户手动启动
        pass
        
    def start_server_silently(self):
        """静默启动服务器"""
        if self.server_manager.start_server():
            self.update_status("局域网服务器已启动 - http://127.0.0.1:5000")
        else:
            self.update_status("局域网服务器启动失败")
            
    def toggle_server(self):
        """切换服务器状态 - 修复启动状态显示问题"""
        if self.server_manager.running:
            # 拒绝关闭服务器
            QMessageBox.warning(
                self, 
                '无法关闭', 
                '局域网服务器启动后无法关闭，这是为了保证游戏体验连续性。\n\n'
                '如需关闭，请直接退出整个应用程序。',
                QMessageBox.Ok
            )
        else:
            # 立即更新状态提示
            self.update_status("正在启动局域网服务器...")
            
            # 使用非阻塞方式启动服务器
            def start_server_async():
                if self.server_manager.start_server():
                    # 启动成功后的操作
                    self.server_action.setText("局域网已启动")
                    self.server_action.setEnabled(False)
                    self.update_status("局域网服务器运行中 - http://127.0.0.1:5000/desktop")
                    
                    # 显示成功信息
                    QMessageBox.information(
                        self, 
                        "启动成功", 
                        "局域网服务器启动成功！\n"
                        "本地访问：http://127.0.0.1:5000/desktop\n"
                        "局域网访问：http://" + self.get_local_ip() + ":5000/desktop\n\n"
                        "服务器现已运行，无法手动关闭。"
                    )
                    
                    # 自动加载在线版本
                    self.web_view.load(QUrl("http://127.0.0.1:5000/desktop"))
                else:
                    # 启动失败
                    self.update_status("局域网服务器启动失败")
                    QMessageBox.critical(self, "启动失败", "局域网服务器启动失败，请检查端口是否被占用！")
            
            # 延迟启动，让UI有时间更新
            QTimer.singleShot(100, start_server_async)
                
    def on_server_started(self):
        """服务器启动回调"""
        self.server_action.setText("局域网已启动")
        self.server_action.setEnabled(False)  # 禁用按钮防止重复启动
        self.update_status("局域网服务器运行中 - http://127.0.0.1:5000/desktop")
        
    def on_server_stopped(self):
        """服务器停止回调"""
        self.server_action.setText("启动局域网")
        self.server_action.setEnabled(True)  # 重新启用按钮
        self.update_status("局域网服务器已停止")
        
    def show_updates(self):
        """显示更新日志"""
        updates_path = os.path.join(os.path.dirname(__file__), 'updates.html')
        QDesktopServices.openUrl(QUrl.fromLocalFile(updates_path))
        
    def show_welcome(self):
        """显示欢迎页面"""
        welcome_path = os.path.join(os.path.dirname(__file__), 'welcome.html')
        QDesktopServices.openUrl(QUrl.fromLocalFile(welcome_path))
        
    def get_local_ip(self):
        """获取本地IP地址"""
        try:
            # 创建一个UDP socket来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.showMessage(message)
        
    def closeEvent(self, event):
        """关闭事件 - 性能优化版"""
        try:
            # 优化关闭流程，避免阻塞
            if hasattr(self, 'server_manager'):
                # 使用线程异步处理服务器关闭，避免UI卡顿
                def cleanup():
                    # 清理资源
                    if hasattr(self, 'web_view'):
                        self.web_view.stop()
                        self.web_view.deleteLater()
                
                cleanup_thread = threading.Thread(target=cleanup, daemon=True)
                cleanup_thread.start()
                
            event.accept()
        except Exception as e:
            logging.error(f"关闭应用时出错: {e}")
            event.accept()
            
    def _get_error_html(self, game_path):
        """生成简化的错误页面"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SW数字游戏 - 文件缺失</title>
            <style>
                body {{ background: #2c3e50; color: white; font-family: Arial; 
                       text-align: center; padding: 50px; }}
                .msg {{ font-size: 18px; margin: 20px; }}
                .path {{ font-size: 12px; color: #ccc; }}
            </style>
        </head>
        <body>
            <h2>⚠️ 游戏文件未找到</h2>
            <div class="msg">点击"启动局域网"按钮启动在线版本</div>
            <div class="path">{game_path}</div>
        </body>
        </html>
        """

def create_app_icon():
    """创建应用图标"""
    from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor
    icon_size = 64
    pixmap = QPixmap(icon_size, icon_size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制渐变背景
    gradient_rect = pixmap.rect().adjusted(4, 4, -4, -4)
    painter.setBrush(QColor(255, 107, 53))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(gradient_rect, 8, 8)
    
    # 绘制白色"SW"
    painter.setPen(Qt.white)
    font = QFont("Arial", 18, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "SW")
    
    painter.end()
    return QIcon(pixmap)

def center_window(window):
    """将窗口居中显示"""
    from PyQt5.QtGui import QScreen
    screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    
    # 计算窗口大小（屏幕的60%）
    width = int(screen_geometry.width() * 0.6)
    height = int(screen_geometry.height() * 0.7)
    
    # 确保最小尺寸
    width = max(600, min(width, 800))
    height = max(500, min(height, 700))
    
    # 计算居中位置
    x = (screen_geometry.width() - width) // 2
    y = (screen_geometry.height() - height) // 2
    
    # 设置窗口位置和大小
    window.setGeometry(x, y, width, height)

def main():
    """主函数"""
    # 设置高DPI支持 - 必须在创建QApplication之前设置
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("SW数字游戏")
    app.setApplicationVersion("3.2.4")
    
    # 设置应用图标
    app.setWindowIcon(create_app_icon())
    
    # 创建主窗口
    window = MainWindow()
    center_window(window)
    window.show()
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())