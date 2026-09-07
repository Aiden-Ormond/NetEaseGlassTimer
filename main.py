import os, sys, json, ctypes, webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QTimer, QTime, Signal, QPoint, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QLinearGradient, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTimeEdit, QListWidget, QListWidgetItem, QCheckBox, QFrame,
    QMessageBox, QSystemTrayIcon, QMenu, QSpinBox, QComboBox, QSlider,
    QDialog, QFormLayout, QDialogButtonBox, QTabWidget, QTextEdit,
    QStackedWidget, QSizePolicy
)

APP = "网易云定时播放"
DATA = Path(os.getenv("APPDATA", Path.home())) / "NetEaseGlassTimer" / "config.json"
DATA.parent.mkdir(parents=True, exist_ok=True)

DEFAULT = {
    "schedules": [],
    "settings": {
        "launch_minimized": False,
        "autostart": False,
        "notify": True,
        "netease_path": "",
        "theme": "dark",
    },
}


def load():
    try:
        d = json.loads(DATA.read_text("utf-8"))
        d.setdefault("schedules", [])
        d.setdefault("settings", {})
        d["settings"] = {**DEFAULT["settings"], **d["settings"]}
        return d
    except Exception:
        return json.loads(json.dumps(DEFAULT, ensure_ascii=False))


def save(d):
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def media_key(vk):
    if sys.platform != "win32":
        return False
    try:
        u = ctypes.windll.user32
        u.keybd_event(vk, 0, 0, 0)
        u.keybd_event(vk, 0, 2, 0)
        return True
    except Exception:
        return False


def open_url(url):
    try:
        return webbrowser.open(url)
    except Exception:
        return False


def detect_netease():
    if sys.platform != "win32":
        return ""
    roots = [os.getenv("LOCALAPPDATA", ""), os.getenv("PROGRAMFILES", ""), os.getenv("PROGRAMFILES(X86)", "")]
    rels = ["Netease/CloudMusic/cloudmusic.exe", "NetEase/CloudMusic/cloudmusic.exe", "CloudMusic/cloudmusic.exe"]
    for r in roots:
        if not r:
            continue
        for rel in rels:
            p = Path(r) / rel
            if p.exists():
                return str(p)
    return ""


def acrylic(hwnd):
    if sys.platform != "win32":
        return
    try:
        dwm = ctypes.windll.dwmapi
        backdrop = ctypes.c_int(3)
        dwm.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        corner = ctypes.c_int(2)
        dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))
    except Exception:
        pass


class SoftButton(QPushButton):
    def __init__(self, text="", primary=False, parent=None):
        super().__init__(text, parent)
        self.setProperty("primary", primary)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(38)


class StatCard(QFrame):
    def __init__(self, title, value, detail, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        l = QVBoxLayout(self); l.setContentsMargins(17, 14, 17, 14); l.setSpacing(3)
        a = QLabel(title); a.setObjectName("Caption")
        v = QLabel(value); v.setObjectName("StatValue")
        d = QLabel(detail); d.setObjectName("Muted")
        l.addWidget(a); l.addWidget(v); l.addWidget(d)


class ScheduleDialog(QDialog):
    def __init__(self, existing=None, parent=None):
        super().__init__(parent)
        x = existing or {}
        self.setWindowTitle("新建任务")
        self.setMinimumWidth(590)
        root = QVBoxLayout(self); root.setContentsMargins(28, 25, 28, 25)
        title = QLabel("新建定时播放"); title.setObjectName("DialogTitle")
        sub = QLabel("选择网易云歌单，并设置自动播放时间。"); sub.setObjectName("Muted")
        root.addWidget(title); root.addWidget(sub); root.addSpacing(12)
        f = QFormLayout(); f.setHorizontalSpacing(20); f.setVerticalSpacing(13)
        self.name = QLineEdit(x.get("name", "")); self.name.setPlaceholderText("例如：晚间专注")
        self.url = QLineEdit(x.get("url", "")); self.url.setPlaceholderText("https://music.163.com/#/playlist?id=...")
        self.time = QTimeEdit(QTime.fromString(x.get("time", "08:00:00"), "HH:mm:ss")); self.time.setDisplayFormat("HH:mm:ss")
        self.delay = QSpinBox(); self.delay.setRange(0, 300); self.delay.setValue(int(x.get("delay", 8))); self.delay.setSuffix(" 秒")
        self.repeat = QComboBox(); self.repeat.addItems(["每天", "单次", "工作日", "周末"]); self.repeat.setCurrentText(x.get("repeat", "每天"))
        self.volume = QSlider(Qt.Horizontal); self.volume.setRange(0, 100); self.volume.setValue(int(x.get("volume", 50)))
        self.stop = QSpinBox(); self.stop.setRange(0, 1440); self.stop.setValue(int(x.get("stop_after", 0))); self.stop.setSuffix(" 分钟")
        f.addRow("任务名称", self.name); f.addRow("歌单链接", self.url); f.addRow("执行时间", self.time)
        f.addRow("打开后等待", self.delay); f.addRow("重复方式", self.repeat); f.addRow("目标音量", self.volume); f.addRow("自动停止", self.stop)
        root.addLayout(f)
        hint = QLabel("播放方式：打开歌单 → 等待 → 发送 Windows Play/Pause 媒体键。不保存账号、密码或 Cookie。")
        hint.setObjectName("Hint"); hint.setWordWrap(True); root.addWidget(hint)
        b = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); root.addWidget(b)

    def accept(self):
        url = self.url.text().strip()
        if "music.163.com" not in url:
            QMessageBox.warning(self, "链接不正确", "请粘贴 music.163.com 的歌单链接。")
            return
        super().accept()

    def value(self):
        return {"name": self.name.text().strip() or "未命名任务", "url": self.url.text().strip(),
                "time": self.time.time().toString("HH:mm:ss"), "delay": self.delay.value(),
                "repeat": self.repeat.currentText(), "volume": self.volume.value(),
                "stop_after": self.stop.value(), "enabled": True, "last_run": ""}


class SettingsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent); self.data = data
        self.setWindowTitle("设置"); self.resize(610, 450)
        root = QVBoxLayout(self); root.setContentsMargins(28, 25, 28, 25)
        title = QLabel("设置"); title.setObjectName("DialogTitle"); root.addWidget(title)
        tabs = QTabWidget(); root.addWidget(tabs, 1)
        general = QWidget(); f = QFormLayout(general); f.setVerticalSpacing(15)
        self.path = QLineEdit(data["settings"].get("netease_path") or detect_netease())
        self.autostart = QCheckBox("开机启动"); self.autostart.setChecked(data["settings"].get("autostart", False))
        self.notify = QCheckBox("任务执行时提醒"); self.notify.setChecked(data["settings"].get("notify", True))
        self.minimize = QCheckBox("启动后进入托盘"); self.minimize.setChecked(data["settings"].get("launch_minimized", False))
        f.addRow("网易云路径", self.path); f.addRow("", self.autostart); f.addRow("", self.notify); f.addRow("", self.minimize)
        tabs.addTab(general, "常规")
        info = QTextEdit(); info.setReadOnly(True)
        info.setPlainText("播放策略\n\n打开保存的网易云歌单链接，等待设定时间，再发送 Windows 系统 Play/Pause 媒体键。\n\n不读取或保存网易云账号密码、Cookie。不同网易云版本的内部界面可能变化，因此不依赖脆弱的坐标点击。")
        tabs.addTab(info, "播放策略")
        b = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); root.addWidget(b)

    def accept(self):
        s = self.data["settings"]
        s["netease_path"] = self.path.text().strip(); s["autostart"] = self.autostart.isChecked()
        s["notify"] = self.notify.isChecked(); s["launch_minimized"] = self.minimize.isChecked()
        save(self.data); super().accept()


class Window(QWidget):
    log_signal = Signal(str)

    def __init__(self):
        super().__init__(); self.data = load(); self.drag_offset = None; self.page = "home"
        self.setWindowTitle(APP); self.resize(1220, 780); self.setMinimumSize(1050, 700)
        self.setAttribute(Qt.WA_TranslucentBackground, True); self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.apply_style(); self.build(); self.refresh()
        self.log_signal.connect(self.add_log)
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(500)
        self.tray = QSystemTrayIcon(self); self.tray.setIcon(self.style().standardIcon(self.style().SP_MediaPlay)); self.tray.setToolTip(APP)
        menu = QMenu(); menu.addAction("显示窗口", self.showNormal); menu.addAction("立即检查", self.tick); menu.addAction("播放选中任务", self.run_selected)
        menu.addSeparator(); menu.addAction("退出", QApplication.quit); self.tray.setContextMenu(menu); self.tray.show()

    def apply_style(self):
        self.setStyleSheet(r'''
        * { font-family: "SF Pro Display", "Segoe UI", "Microsoft YaHei UI"; }
        QWidget { color: #F5F5F7; }
        #Root { background: rgba(20,20,22,246); border: 1px solid rgba(255,255,255,.08); border-radius: 22px; }
        #Sidebar { background: rgba(255,255,255,.028); border-right: 1px solid rgba(255,255,255,.06); border-radius: 22px 0 0 22px; }
        #Brand { font-size: 16px; font-weight: 650; }
        #BrandSub { color: rgba(245,245,247,.43); font-size: 11px; }
        #Logo { background: #FA233B; border-radius: 10px; font-size: 20px; font-weight: 700; }
        #Nav { text-align:left; padding: 10px 12px; border:0; border-radius:9px; color:rgba(245,245,247,.58); background:transparent; font-size:13px; font-weight:500; }
        #Nav:hover { background:rgba(255,255,255,.05); color:#fff; }
        #Nav[selected="true"] { background:rgba(255,255,255,.085); color:#fff; }
        #Title { font-size: 30px; font-weight: 650; letter-spacing:-.5px; }
        #Subtitle, #Muted { color:rgba(245,245,247,.43); font-size:12px; }
        #Caption { color:rgba(245,245,247,.46); font-size:11px; }
        #StatValue { font-size:25px; font-weight:650; }
        #StatCard { background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.065); border-radius:15px; }
        #Panel { background:rgba(255,255,255,.032); border:1px solid rgba(255,255,255,.065); border-radius:17px; }
        #Quick { background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.07); border-radius:12px; }
        QLineEdit, QTimeEdit, QSpinBox, QComboBox { background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.10); border-radius:9px; padding:9px 10px; color:#fff; }
        QLineEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus { border:1px solid rgba(250,35,59,.75); }
        QPushButton { background:rgba(255,255,255,.055); border:1px solid rgba(255,255,255,.075); border-radius:9px; padding:8px 13px; font-weight:550; }
        QPushButton:hover { background:rgba(255,255,255,.095); }
        QPushButton[primary="true"] { background:#FA233B; border:0; }
        QPushButton[primary="true"]:hover { background:#ff4055; }
        #CloseBtn { background:transparent; border:0; font-size:17px; color:rgba(255,255,255,.6); }
        #CloseBtn:hover { background:rgba(255,255,255,.08); color:#fff; }
        QListWidget { background:transparent; border:0; outline:0; }
        QListWidget::item { border:1px solid rgba(255,255,255,.055); background:rgba(255,255,255,.025); border-radius:12px; margin:3px 0; padding:7px; }
        QListWidget::item:selected { background:rgba(255,255,255,.075); border:1px solid rgba(255,255,255,.12); }
        #TaskTitle { font-size:14px; font-weight:620; }
        #TaskTime { font-size:17px; font-weight:620; }
        #Pill { background:rgba(255,255,255,.055); border-radius:8px; padding:3px 7px; color:rgba(245,245,247,.55); }
        #Thumb { background:#2a2a2e; border-radius:9px; }
        #Hint { background:rgba(250,35,59,.07); border:1px solid rgba(250,35,59,.14); border-radius:10px; padding:9px; color:rgba(255,220,224,.78); }
        #DialogTitle { font-size:22px; font-weight:650; }
        QTabWidget::pane { border:0; }
        QTabBar::tab { padding:9px 15px; color:rgba(255,255,255,.48); }
        QTabBar::tab:selected { color:#fff; border-bottom:2px solid #FA233B; }
        QTextEdit { background:rgba(0,0,0,.20); border:1px solid rgba(255,255,255,.07); border-radius:10px; padding:10px; }
        QCheckBox { spacing:8px; }
        QSlider::groove:horizontal { height:4px; background:rgba(255,255,255,.12); border-radius:2px; }
        QSlider::handle:horizontal { width:12px; height:12px; margin:-4px 0; border-radius:6px; background:#fff; }
        QScrollBar:vertical { width:7px; background:transparent; }
        QScrollBar::handle:vertical { background:rgba(255,255,255,.14); border-radius:3px; }
        ''')

    def build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        root=QFrame(); root.setObjectName("Root"); outer.addWidget(root)
        layout=QHBoxLayout(root); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        side=QFrame(); side.setObjectName("Sidebar"); side.setFixedWidth(205); layout.addWidget(side)
        sl=QVBoxLayout(side); sl.setContentsMargins(16,22,16,18); sl.setSpacing(6)
        brand=QHBoxLayout(); logo=QLabel("♪"); logo.setObjectName("Logo"); logo.setAlignment(Qt.AlignCenter); logo.setFixedSize(36,36)
        bt=QVBoxLayout(); bn=QLabel("网易云定时播放"); bn.setObjectName("Brand"); bs=QLabel("Scheduled Music"); bs.setObjectName("BrandSub"); bt.addWidget(bn); bt.addWidget(bs); brand.addWidget(logo); brand.addLayout(bt); sl.addLayout(brand); sl.addSpacing(24)
        self.navs={}
        for key,text in [("home","⌂   现在"),("tasks","◷   定时任务"),("player","▶   播放控制"),("logs","≡   活动")]:
            b=QPushButton(text); b.setObjectName("Nav"); b.setProperty("selected",key=="home"); b.clicked.connect(lambda _,k=key:self.switch_page(k)); self.navs[key]=b; sl.addWidget(b)
        sl.addStretch()
        setb=QPushButton("⚙   设置"); setb.setObjectName("Nav"); setb.clicked.connect(self.settings); sl.addWidget(setb)
        status=QFrame(); status.setObjectName("Panel"); st=QVBoxLayout(status); st.setContentsMargins(12,11,12,11); st.setSpacing(4)
        dot=QLabel("●  运行中"); dot.setStyleSheet("color:#5BD778;font-size:12px;"); st.addWidget(dot)
        self.status2=QLabel("后台监控已开启"); self.status2.setObjectName("Muted"); st.addWidget(self.status2); sl.addWidget(status)
        main=QWidget(); ml=QVBoxLayout(main); ml.setContentsMargins(30,25,30,24); ml.setSpacing(15); layout.addWidget(main,1)
        top=QHBoxLayout(); t=QVBoxLayout(); self.title=QLabel("现在"); self.title.setObjectName("Title"); self.subtitle=QLabel(""); self.subtitle.setObjectName("Subtitle"); t.addWidget(self.title); t.addWidget(self.subtitle); top.addLayout(t); top.addStretch()
        minb=QPushButton("—"); minb.setObjectName("CloseBtn"); minb.setFixedSize(34,32); minb.clicked.connect(self.showMinimized)
        closeb=QPushButton("×"); closeb.setObjectName("CloseBtn"); closeb.setFixedSize(34,32); closeb.clicked.connect(self.close)
        top.addWidget(minb); top.addWidget(closeb); ml.addLayout(top)
        quick=QFrame(); quick.setObjectName("Quick"); ql=QHBoxLayout(quick); ql.setContentsMargins(12,7,7,7)
        self.quick=QLineEdit(); self.quick.setPlaceholderText("粘贴网易云歌单链接…"); add=SoftButton("＋ 添加",True); add.clicked.connect(self.quick_add); ql.addWidget(self.quick,1); ql.addWidget(add); ml.addWidget(quick)
        self.stack=QStackedWidget(); ml.addWidget(self.stack,1)
        for p in [self.make_home(),self.make_tasks(),self.make_player(),self.make_logs()]: self.stack.addWidget(p)

    def make_home(self):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(14)
        cards=QHBoxLayout(); self.c_total=StatCard("任务", "0", "已保存任务"); self.c_on=StatCard("已启用", "0", "正在运行"); self.c_next=StatCard("下一次", "—", "暂无安排"); self.c_state=StatCard("播放器", "就绪", "媒体键控制")
        for c in [self.c_total,self.c_on,self.c_next,self.c_state]: cards.addWidget(c)
        l.addLayout(cards)
        panel=QFrame(); panel.setObjectName("Panel"); pl=QVBoxLayout(panel); pl.setContentsMargins(18,17,18,17)
        h=QHBoxLayout(); x=QLabel("接下来"); x.setStyleSheet("font-size:18px;font-weight:650;"); h.addWidget(x); h.addStretch(); b=SoftButton("查看全部"); b.clicked.connect(lambda:self.switch_page("tasks")); h.addWidget(b); pl.addLayout(h)
        self.home_list=QListWidget(); self.home_list.setSelectionMode(QListWidget.NoSelection); pl.addWidget(self.home_list); l.addWidget(panel,1)
        return w

    def make_tasks(self):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0)
        h=QHBoxLayout(); x=QLabel("定时任务"); x.setStyleSheet("font-size:20px;font-weight:650;"); h.addWidget(x); h.addStretch()
        for txt,fn in [("＋ 新建",self.new),("复制",self.copy),("删除",self.delete)]:
            b=SoftButton(txt,txt=="＋ 新建"); b.clicked.connect(fn); h.addWidget(b)
        l.addLayout(h)
        self.list=QListWidget(); l.addWidget(self.list,1)
        bottom=QHBoxLayout(); self.edit_btn=SoftButton("编辑"); self.edit_btn.clicked.connect(self.edit); test=SoftButton("▶ 测试选中"); test.clicked.connect(self.run_selected); bottom.addWidget(self.edit_btn); bottom.addWidget(test); bottom.addStretch(); l.addLayout(bottom)
        return w

    def make_player(self):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0)
        panel=QFrame(); panel.setObjectName("Panel"); p=QVBoxLayout(panel); p.setContentsMargins(34,34,34,34); p.setSpacing(14)
        title=QLabel("播放控制"); title.setStyleSheet("font-size:22px;font-weight:650;"); p.addWidget(title)
        self.player_status=QLabel("准备播放"); self.player_status.setObjectName("Muted"); p.addWidget(self.player_status)
        p.addStretch()
        album=QLabel("♪"); album.setObjectName("Logo"); album.setAlignment(Qt.AlignCenter); album.setFixedSize(118,118); p.addWidget(album,0,Qt.AlignHCenter)
        name=QLabel("网易云音乐"); name.setStyleSheet("font-size:18px;font-weight:650;"); p.addWidget(name,0,Qt.AlignHCenter)
        sub=QLabel("系统媒体控制"); sub.setObjectName("Muted"); p.addWidget(sub,0,Qt.AlignHCenter)
        p.addSpacing(10)
        self.vol=QSlider(Qt.Horizontal); self.vol.setRange(0,100); self.vol.setValue(50); p.addWidget(self.vol)
        center=QHBoxLayout(); center.addStretch()
        for txt,fn in [("⏮",lambda:media_key(0xB1)),("▶ / Ⅱ",lambda:media_key(0xB3)),("⏭",lambda:media_key(0xB0))]:
            b=SoftButton(txt); b.setFixedSize(112,48); center.addWidget(b); b.clicked.connect(fn)
        center.addStretch(); p.addLayout(center); p.addStretch(); l.addWidget(panel,1); return w

    def make_logs(self):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0)
        h=QHBoxLayout(); x=QLabel("活动"); x.setStyleSheet("font-size:20px;font-weight:650;"); h.addWidget(x); h.addStretch(); b=SoftButton("清空"); b.clicked.connect(lambda:self.log.clear()); h.addWidget(b); l.addLayout(h)
        self.log=QTextEdit(); self.log.setReadOnly(True); l.addWidget(self.log,1); return w

    def switch_page(self,key):
        idx={"home":0,"tasks":1,"player":2,"logs":3}[key]; self.stack.setCurrentIndex(idx)
        for k,b in self.navs.items(): b.setProperty("selected",k==key); b.style().unpolish(b); b.style().polish(b)

    def add_log(self,msg):
        if hasattr(self,"log"): self.log.append(f"<span style='color:#FA6A78'>{datetime.now():%H:%M:%S}</span>  {msg}")

    def selected(self):
        i=self.list.currentRow(); return i if 0<=i<len(self.data["schedules"]) else -1

    def task_widget(self,s,i):
        w=QFrame(); l=QHBoxLayout(w); l.setContentsMargins(8,6,8,6); l.setSpacing(12)
        icon=QLabel("♪"); icon.setObjectName("Thumb"); icon.setAlignment(Qt.AlignCenter); icon.setFixedSize(42,42); l.addWidget(icon)
        info=QVBoxLayout(); title=QLabel(s.get("name","未命名任务")); title.setObjectName("TaskTitle"); sub=QLabel(f"{s.get('repeat','每天')}  ·  {s.get('url','')}"); sub.setObjectName("Muted"); sub.setTextInteractionFlags(Qt.TextSelectableByMouse); info.addWidget(title); info.addWidget(sub); l.addLayout(info,1)
        tm=QLabel(s.get("time","08:00:00")); tm.setObjectName("TaskTime"); l.addWidget(tm)
        pill=QLabel(f"{s.get('volume',50)}%"); pill.setObjectName("Pill"); l.addWidget(pill)
        cb=QCheckBox(); cb.setChecked(s.get("enabled",True)); cb.stateChanged.connect(lambda st,idx=i:self.toggle(idx,st)); l.addWidget(cb)
        return w

    def refresh(self):
        if not hasattr(self,"list"): return
        self.list.clear(); self.home_list.clear(); ss=self.data["schedules"]
        for i,s in enumerate(ss):
            it=QListWidgetItem(); it.setSizeHint(QSize(0,64)); self.list.addItem(it); self.list.setItemWidget(it,self.task_widget(s,i))
            if len(self.home_list)<5:
                hi=QListWidgetItem(); hi.setSizeHint(QSize(0,64)); self.home_list.addItem(hi); self.home_list.setItemWidget(hi,self.task_widget(s,i))
        total=len(ss); enabled=sum(bool(s.get("enabled",True)) for s in ss)
        self._set_stat(self.c_total,str(total),"已保存任务"); self._set_stat(self.c_on,str(enabled),"正在运行")
        nxt=self.next_execution(); self._set_stat(self.c_next,nxt[0],nxt[1]); self._set_stat(self.c_state,"就绪","媒体键控制")
        now=datetime.now(); self.subtitle.setText(now.strftime("%Y年%m月%d日  %A"))
        self.countdown_target=nxt[2]

    def _set_stat(self,card,value,detail):
        labels=card.findChildren(QLabel); labels[1].setText(value); labels[2].setText(detail)

    def next_execution(self):
        now=datetime.now(); best=None
        for s in self.data["schedules"]:
            if not s.get("enabled",True): continue
            try: t=datetime.strptime(s.get("time","00:00:00"),"%H:%M:%S").time()
            except ValueError: continue
            candidate=datetime.combine(now.date(),t)
            if candidate<=now: candidate+=timedelta(days=1)
            if s.get("repeat")=="工作日":
                while candidate.weekday()>=5: candidate+=timedelta(days=1)
            elif s.get("repeat")=="周末":
                while candidate.weekday()<5: candidate+=timedelta(days=1)
            if best is None or candidate<best: best=candidate
        if not best: return ("—","暂无安排",None)
        mins=max(0,int((best-now).total_seconds()//60)); return (best.strftime("%H:%M"),f"约 {mins} 分钟后",best)

    def new(self):
        d=ScheduleDialog(parent=self)
        if d.exec(): self.data["schedules"].append(d.value()); save(self.data); self.refresh(); self.add_log("创建任务")

    def quick_add(self):
        url=self.quick.text().strip()
        if not url:return
        d=ScheduleDialog({"url":url},self)
        if d.exec(): self.data["schedules"].append(d.value()); save(self.data); self.quick.clear(); self.refresh(); self.add_log("快速创建任务")

    def edit(self):
        i=self.selected()
        if i<0:return
        old=self.data["schedules"][i]; d=ScheduleDialog(old,self)
        if d.exec():
            enabled=old.get("enabled",True); self.data["schedules"][i]=d.value(); self.data["schedules"][i]["enabled"]=enabled; save(self.data); self.refresh(); self.add_log("修改任务")

    def copy(self):
        i=self.selected()
        if i>=0:
            x=dict(self.data["schedules"][i]); x["name"]=x.get("name","任务")+" 副本"; x["last_run"]=""; self.data["schedules"].append(x); save(self.data); self.refresh(); self.add_log("复制任务")

    def delete(self):
        i=self.selected()
        if i>=0:
            self.data["schedules"].pop(i); save(self.data); self.refresh(); self.add_log("删除任务")

    def toggle(self,i,st):
        if 0<=i<len(self.data["schedules"]): self.data["schedules"][i]["enabled"]=bool(st); save(self.data)

    def run_selected(self):
        i=self.selected()
        if i<0: QMessageBox.information(self,"没有选择任务","先在定时任务中选择一个任务。"); return
        self.run(self.data["schedules"][i])

    def run(self,s):
        self.player_status.setText("正在打开歌单…"); self.add_log(f"打开歌单：{s.get('name','未命名任务')}")
        open_url(s["url"]); delay=int(s.get("delay",8)); self.add_log(f"等待 {delay} 秒后发送播放指令")
        QTimer.singleShot(delay*1000,lambda:self.finish(s))

    def finish(self,s):
        ok=media_key(0xB3); self.player_status.setText("播放指令已发送" if ok else "当前系统不支持媒体键"); self.add_log("发送系统 Play/Pause 媒体键")
        stop=int(s.get("stop_after",0))
        if stop: QTimer.singleShot(stop*60000,lambda:media_key(0xB3))

    def tick(self):
        now=datetime.now(); key=now.strftime("%Y-%m-%d")
        for s in self.data["schedules"]:
            if not s.get("enabled",True): continue
            repeat=s.get("repeat","每天")
            allowed=repeat=="每天" or (repeat=="工作日" and now.weekday()<5) or (repeat=="周末" and now.weekday()>=5) or repeat=="单次"
            if allowed and now.strftime("%H:%M:%S")==s.get("time") and s.get("last_run")!=key:
                s["last_run"]=key; save(self.data); self.run(s)
                if repeat=="单次": s["enabled"]=False; save(self.data)
        self.refresh()

    def settings(self):
        d=SettingsDialog(self.data,self)
        if d.exec(): self.data=load(); self.refresh(); self.add_log("设置已保存")

    def showEvent(self,e): super().showEvent(e); acrylic(int(self.winId()))
    def closeEvent(self,e): self.hide(); e.ignore()
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:self.drag_offset=e.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def mouseMoveEvent(self,e):
        if self.drag_offset is not None and e.buttons()&Qt.LeftButton:self.move(e.globalPosition().toPoint()-self.drag_offset)
    def mouseReleaseEvent(self,e): self.drag_offset=None


if __name__=="__main__":
    app=QApplication(sys.argv); app.setApplicationName(APP); w=Window(); w.show(); sys.exit(app.exec())
