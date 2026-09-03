# 网易云定时播放 · Apple Music 风格 V4

一个基于 PySide6 的 Windows 桌面定时播放工具。

## UI 方向
- Apple Music 风格：深色、留白、低饱和、克制玻璃
- 网易云红色只作为强调色
- 去除右上角版本信息
- 简洁侧栏 + Now Playing 式播放控制
- Windows 11 Acrylic 背景

## 运行
```bash
pip install -r requirements.txt
python main.py
```

## Windows 打包
运行 `build_windows.bat`，生成 `dist/网易云定时播放.exe`。

## 播放机制
打开保存的网易云歌单 URL，等待设定时间，然后发送 Windows 系统 Play/Pause 媒体键。
不会保存网易云账号密码或 Cookie。
