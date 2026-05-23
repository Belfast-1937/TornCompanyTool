import os
import time
import sys
import subprocess
import platform
import logging
import pandas as pd
from functools import wraps
from config import VERSION, RESULT_DIR, MIN_INTERVAL


def file_access_handler(func):
    """装饰器：处理 Excel 文件被占用"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except PermissionError:
                logging.error("无法访问文件，它可能已被其他程序打开")
                print(f"❌ 错误: 无法访问文件，它可能已被其他程序（如 Excel）打开。")
                print(f"🔄 请关闭相关文件，程序将在 5 秒后重试 ({i+1}/3)...")
                time.sleep(5)
            except Exception as e:
                logging.exception(f"发生意外错误: {e}")
                print(f"⚠️ 发生意外错误: {e}")
                break
        return None
    return wrapper


def get_script_dir():
    """兼容 Windows/Linux/macOS + PyInstaller"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def print_startup_info():
    """启动说明与数据安全警告"""
    print("=" * 70)
    print(f"🚀 Torn Company 老板死了吗 v{VERSION}")
    print("-" * 70)
    print("📢 运行须知：")
    print("1. [配置读取] 本程序优先读取同目录下的 'Industry.ini' 文件，")
    print("   获取 IndustryID、ApiKey、BossOfflineDays、EmployeeActiveDays 和 MinimumStarRating 等配置信息。")
    print(f"2. [速率保护] 本程序已内置 API 调用频率控制（约{(60/MIN_INTERVAL)}次/分钟），")
    print("   请勿高频运行，以避免触发 Torn 官方限流。")
    print("3. [功能说明] 本工具用于扫描指定行业内：")
    print("   • 老板长时间不活跃")
    print("   • 但仍有活跃员工的公司")
    print(f"4. [结果输出] 扫描结果将保存至 → {RESULT_DIR}")
    print("=" * 70)
    print("程序启动中...\n")


def check_network():
    """网络连通性检测"""
    print("🌐 正在检测网络连接...")
    logging.info("开始网络连接检测")

    system = platform.system().lower()
    ping_base = ['ping', '-n', '1', '-w',
                 '4000'] if system == "windows" else ['ping', '-c', '1', '-W', '4']

    targets = ["223.5.5.5", "114.114.114.114", "8.8.8.8", "1.1.1.1"]

    for attempt in range(1, 6):
        print(f"\n📍 第 {attempt}/5 次尝试...")
        for target in targets:
            try:
                print(f"   正在 ping {target} ... ", end="")
                result = subprocess.run(
                    ping_base + [target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6)
                if result.returncode == 0:
                    print("✅ 网络连接正常！")
                    logging.info(f"网络连接正常！（通过 {target}）")
                    return True
            except Exception:
                print("失败")
        if attempt < 5:
            time.sleep(10 if attempt <= 2 else 6)

    print("❌ 网络连接失败")
    return False
