#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torn City 员工训练规划工具
独立的 Python GUI 应用程序，用于规划公司员工的最优训练岗位。
"""
import os
import sys

# --- 检查依赖 ---
try:
    import requests
except ImportError:
    print("请先安装 requests 库: pip install requests")
    sys.exit(1)

import tkinter as tk

from constants import SCRIPT_DIR, VERSION
from gui import TrainingPlannerApp


def main():
    """启动 Torn City 员工训练规划工具 GUI 应用"""
    os.chdir(SCRIPT_DIR)
    root = tk.Tk()
    app = TrainingPlannerApp(root, VERSION)
    root.mainloop()


if __name__ == "__main__":
    main()
