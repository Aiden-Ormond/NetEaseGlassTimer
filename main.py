import sys
import os
import time
import subprocess
import webbrowser
from PySide6.QtCore import Qt, QTime, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QIcon, QFont, QAction
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QTimeEdit, QComboBox, 
                             QCheckBox, QStackedWidget, QFrame, QSystemTrayIcon, QMenu,
                             QListWidget, QListWidgetItem, QSlider, QGraphicsOpacityEffect)

class FluentButton(QPushButton):
    """Windows 11 风格圆角按钮，带平滑悬停过渡"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(36)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)

class SecondaryButton(QPushButton):
    """次要按钮风格"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(36)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #1A1A1A;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(240, 240, 240, 0.9);
            }
        """)

class CardWidget(QFrame):
    """Windows 11 卡片容器，卡片化展现模块"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 12))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("网易云音乐定时播放助手 - Windows 11 Fluent")
        self.resize(920, 600)
        self.setMinimumSize(800, 520)
        
        # 建立主窗体背景样式 (Mica/Light 风格)
        self.setStyleSheet("QMainWindow { background-color: #F3F3F3; }")

        # 定时器管理
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_schedule)
        self.timer.start(1000)

        # 状态变量
        self.is_task_active = False
        self.playlist_url = ""
        self.scheduled_time = QTime.currentTime()
        self.fade_in_enabled = True
        self.fade_duration = 30
        
        self.init_ui()
        self.init_tray()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- 侧边栏 ---
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: rgba(243, 243, 243, 0.5);
                border-right: 1px solid rgba(0, 0, 0, 0.06);
            }
            QPushButton {
                text-align: left;
                padding-left: 14px;
                border: none;
                border-radius: 5px;
                height: 36px;
                font-size: 13px;
                color: #202020;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.04);
            }
            QPushButton:checked {
                background-color: rgba(0, 0, 0, 0.08);
                font-weight: bold;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(6, 12, 6, 12)

        title_label = QLabel("  音乐定时器")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(15)

        self.btn_nav_task = QPushButton("⏰ 定时任务")
        self.btn_nav_task.setCheckable(True)
        self.btn_nav_task.setChecked(True)
        self.btn_nav_task.clicked.connect(lambda: self.switch_page(0))
        
        self.btn_nav_settings = QPushButton("⚙️ 高级设置")
        self.btn_nav_settings.setCheckable(True)
        self.btn_nav_settings.clicked.connect(lambda: self.switch_page(1))

        self.btn_nav_logs = QPushButton("📋 执行日志")
        self.btn_nav_logs.setCheckable(True)
        self.btn_nav_logs.clicked.connect(lambda: self.switch_page(2))

        sidebar_layout.addWidget(self.btn_nav_task)
        sidebar_layout.addWidget(self.btn_nav_settings)
        sidebar_layout.addWidget(self.btn_nav_logs)
        sidebar_layout.addStretch()

        # --- 多页面 Stacked Widget ---
        self.stacked_widget = QStackedWidget()
        
        # 页面 1: 任务设置
        page_task = self.create_task_page()
        # 页面 2: 高级设置
        page_settings = self.create_settings_page()
        # 页面 3: 执行日志
        page_logs = self.create_logs_page()

        self.stacked_widget.addWidget(page_task)
        self.stacked_widget.addWidget(page_settings)
        self.stacked_widget.addWidget(page_logs)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stacked_widget, 1)

    def create_task_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # 头部标题
        header = QLabel("配置定时播放任务")
        header.setFont(QFont("Segoe UI Variable Display", 16, QFont.Bold))
        layout.addWidget(header)

        # 卡片1: 歌单地址配置
        card1 = CardWidget()
        c1_layout = QVBoxLayout(card1)
        c1_layout.addWidget(QLabel("<b>网易云歌单 / 播放链接:</b>"))
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("例如: https://music.163.com/#/playlist?id=XXXXXXXXXX 或 歌单ID")
        self.input_url.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                padding: 6px 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0078D4;
            }
        """)
        c1_layout.addWidget(self.input_url)
        layout.addWidget(card1)

        # 卡片2: 时间与频率设置
        card2 = CardWidget()
        c2_layout = QHBoxLayout(card2)
        
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("<b>设定播放时间:</b>"))
        self.time_picker = QTimeEdit()
        self.time_picker.setTime(QTime.currentTime().addSecs(300))
        self.time_picker.setDisplayFormat("HH:mm:ss")
        self.time_picker.setStyleSheet("font-size: 14px; padding: 4px;")
        v1.addWidget(self.time_picker)
        c2_layout.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("<b>重复模式:</b>"))
        self.combo_repeat = QComboBox()
        self.combo_repeat.addItems(["仅一次", "每天重复", "周一至周五", "周末"])
        self.combo_repeat.setStyleSheet("padding: 4px;")
        v2.addWidget(self.combo_repeat)
        c2_layout.addLayout(v2)

        layout.addWidget(card2)

        # 卡片3: 控制开关与状态
        card3 = CardWidget()
        c3_layout = QVBoxLayout(card3)
        self.label_status = QLabel("状态: 待就绪")
        self.label_status.setStyleSheet("color: #666666; font-size: 13px;")
        
        btn_layout = QHBoxLayout()
        self.btn_toggle = FluentButton("开启定时播放")
        self.btn_toggle.clicked.connect(self.toggle_task)
        self.btn_test = SecondaryButton("立即测试播放")
        self.btn_test.clicked.connect(self.trigger_play)

        btn_layout.addWidget(self.btn_toggle)
        btn_layout.addWidget(self.btn_test)

        c3_layout.addWidget(self.label_status)
        c3_layout.addLayout(btn_layout)
        layout.addWidget(card3)

        layout.addStretch()
        return page

    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("扩展功能与系统设置")
        header.setFont(QFont("Segoe UI Variable Display", 16, QFont.Bold))
        layout.addWidget(header)

        card = CardWidget()
        c_layout = QVBoxLayout(card)

        # 渐进式音量唤醒 (Fade-in)
        self.chk_fade = QCheckBox("启用渐进式音量唤醒 (平滑淡入)")
        self.chk_fade.setChecked(True)
        c_layout.addWidget(self.chk_fade)

        fade_layout = QHBoxLayout()
        fade_layout.addWidget(QLabel("淡入时长 (秒):"))
        self.slider_fade = QSlider(Qt.Horizontal)
        self.slider_fade.setRange(5, 120)
        self.slider_fade.setValue(30)
        fade_layout.addWidget(self.slider_fade)
        c_layout.addLayout(fade_layout)

        c_layout.addSpacing(10)

        # 自动关机/睡眠扩展
        self.chk_auto_shutdown = QCheckBox("播放触发后定时关闭计算机")
        c_layout.addWidget(self.chk_auto_shutdown)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def create_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("运行日志历史")
        header.setFont(QFont("Segoe UI Variable Display", 16, QFont.Bold))
        layout.addWidget(header)

        self.log_list = QListWidget()
        self.log_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.log_list)
        return page

    def switch_page(self, index):
        """带淡入淡出位移过渡动画的页面切换机制"""
        if self.stacked_widget.currentIndex() == index:
            return

        # 更新侧边栏选中状态
        self.btn_nav_task.setChecked(index == 0)
        self.btn_nav_settings.setChecked(index == 1)
        self.btn_nav_logs.setChecked(index == 2)

        # 切换动画
        next_widget = self.stacked_widget.widget(index)
        curr_widget = self.stacked_widget.currentWidget()

        # 透明度渐变效果
        opacity_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(opacity_effect)

        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)

        self.stacked_widget.setCurrentIndex(index)
        anim.start()

    def toggle_task(self):
        self.is_task_active = not self.is_task_active
        if self.is_task_active:
            self.btn_toggle.setText("停止定时任务")
            self.btn_toggle.setStyleSheet("background-color: #D13438; color: white; border-radius: 6px;")
            target_time = self.time_picker.time().toString("HH:mm:ss")
            self.label_status.setText(f"状态: 定时中，将在 {target_time} 触发")
            self.add_log(f"定时任务已开启，目标时间: {target_time}")
        else:
            self.btn_toggle.setText("开启定时播放")
            self.btn_toggle.setStyleSheet("""
                QPushButton { background-color: #0078D4; color: white; border-radius: 6px; }
                QPushButton:hover { background-color: #106EBE; }
            """)
            self.label_status.setText("状态: 已停止")
            self.add_log("定时任务已停用")

    def check_schedule(self):
        if not self.is_task_active:
            return

        now = QTime.currentTime()
        target = self.time_picker.time()

        if now.hour() == target.hour() and now.minute() == target.minute() and now.second() == target.second():
            self.trigger_play()
            if self.combo_repeat.currentIndex() == 0:  # 仅一次
                self.toggle_task()

    def trigger_play(self):
        url = self.input_url.text().strip()
        self.add_log("正在唤醒播放任务...")

        # 解析与唤醒网易云音乐 Schema
        if "163.com" in url or url.isdigit():
            playlist_id = url.split("id=")[-1] if "id=" in url else url
            # 协议调用唤醒网易云
            target_schema = f"orpheus://playlist/{playlist_id}"
            webbrowser.open(target_schema)
        elif url != "":
            webbrowser.open(url)
        else:
            # 默认打开网易云音乐
            webbrowser.open("orpheus://")

        self.label_status.setText("状态: 已触发播放！")
        self.add_log("播放指令已发出")

    def add_log(self, message):
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        self.log_list.addItem(f"[{timestamp}] {message}")

    def init_tray(self):
        """系统托盘最小化"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("media-playback-start"))
        
        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        quit_action = QAction("退出", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        """关闭主窗口时退回系统托盘后台"""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "网易云音乐定时器",
                "程序已最小化到系统托盘，定时任务将继续运行。",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 启用高 DPI 缩放适配 Windows 11
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
