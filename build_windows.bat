@echo off
chcp 65001 >nul
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name "网易云定时播放" main.py
pause
