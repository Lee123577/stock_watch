import tkinter as tk
from tkinter import ttk
import psutil
import time
import threading
import requests

# 绕过系统代理（Clash/VPN 会让国内行情接口握手失败）
_session = requests.Session()
_session.trust_env = False

class TaskbarMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("系统监控")
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-alpha', 1.0)  # 完全不透明
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-transparentcolor', '#333333')  # 设置透明色
        
        # 计算位置，放在屏幕右上角
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 200
        window_height = 100
        x = screen_width - window_width - 10
        y = 10
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建样式
        style = ttk.Style()
        style.configure('TLabel', font=('微软雅黑', 10), foreground='black')
        
        # 创建主框架
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置背景颜色
        self.root.configure(background='#333333')
        self.frame.configure(style='TFrame')
        
        # 创建样式
        style.configure('TFrame', background='#333333')
        
        # 创建标签
        self.net_label = ttk.Label(self.frame, text="0", style='TLabel')
        self.net_label.pack(pady=10)
        
        # 记录上一次的网络字节数
        self.last_sent = psutil.net_io_counters().bytes_sent
        self.last_recv = psutil.net_io_counters().bytes_recv
        self.last_time = time.time()
        
        # 启动更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self.update_stats)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # 绑定鼠标事件
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.move_window)
        self.root.bind('<Button-3>', self.exit_program)
        # Windows 下无边框 + 透明色 + 置顶：点击其它窗口后可能“看不见”或沉到底下，
        # 失焦后重新 lift + 置顶可恢复显示。
        self.root.bind('<FocusOut>', self._on_focus_out)
        self._schedule_keep_visible()

    def _on_focus_out(self, event):
        if event.widget is not self.root:
            return
        self.root.after(10, self._ensure_visible)

    def _ensure_visible(self):
        if not self.running:
            return
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
        except tk.TclError:
            pass

    def _schedule_keep_visible(self):
        """定时重申置顶，防止某些情况下 FocusOut 不触发仍被盖住。"""
        if self.running:
            self._ensure_visible()
            self.root.after(3000, self._schedule_keep_visible)
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def move_window(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")
    
    def exit_program(self, event):
        self.running = False
        self.root.destroy()
    
    def update_stats(self):
        while self.running:
            # 获取API数据（新浪行情，国内可直连，不依赖 VPN）
            try:
                url = 'https://hq.sinajs.cn/list=sz002842'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
                    'Referer': 'https://finance.sina.com.cn',
                }
                response = _session.get(url, headers=headers, timeout=5)
                response.encoding = 'gbk'
                # 形如: var hq_str_sz002842="名称,今开,昨收,当前,最高,最低,..."
                parts = response.text.split('"')[1].split(',')
                prev_close = float(parts[2])
                current = float(parts[3])
                if prev_close > 0:
                    pct = (current - prev_close) / prev_close * 100
                    self.net_label.config(text=f"{pct:.2f}")
                else:
                    self.net_label.config(text="--")
            except Exception:
                self.net_label.config(text="获取失败")

            # 两秒钟更新一次
            time.sleep(1.9)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    monitor = TaskbarMonitor()
    monitor.run()
