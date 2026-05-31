#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torn City 员工训练规划工具
PySide6 GUI 应用程序，用于规划公司员工的最优训练岗位。
"""
import os
import sys

# --- 检查依赖 ---
try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    print("PySide6 未安装，正在尝试通过清华镜像安装...")
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "PySide6",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
        "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
    ])
    from PySide6.QtWidgets import QApplication

from constants import SCRIPT_DIR, VERSION
from gui_pyqt import TrainingPlannerApp

if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)
    app = QApplication(sys.argv)
    window = TrainingPlannerApp(VERSION)
    window.show()
    sys.exit(app.exec())