# 网易云音乐定时播放助手 (NetEase Music Scheduler)

基于 **Python 3 + PySide6 (Qt for Python)** 打造的 Windows 11 Fluent 风格定时播放软件。

## 功能特性
- **Win11 Fluent 视觉风格**：流畅的界面过渡动画、卡片化布局、圆角与亚克力视觉感受。
- **网易云唤醒与播放**：支持通过网易云音乐 `orpheus://` 协议精准打开与播放指定歌单。
- **定时与重复策略**：支持单次、每日、周末、工作日模式切换。
- **高级扩展功能**：渐进式音量唤醒（淡入）、系统托盘后台静默常驻、自动关机等。
- **GitHub Actions 自动打包**：项目已预置 GitHub Workflows，可以直接在 GitHub 上提交代码并一键自动打包出 EXE。

## 本地运行
1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```
2. 运行主程序:
   ```bash
   python main.py
   ```

## 本地打包 EXE
使用 PyInstaller 打包：
```bash
pyinstaller --noconfirm --onedir --windowed --name "NetEaseScheduler" main.py
```
打包生成的可执行文件将在 `dist/NetEaseScheduler/` 目录下。
