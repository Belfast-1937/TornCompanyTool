import platform
import requests


VERSION = "0.3"
# version 0.1: 初始版本，核心功能实现，已启用速率控制，日志记录，结果输出等基础功能。
# version 0.2: 增加了最小星级过滤功能, 增加了Director Faction信息, 加快了API请求频率。
# version 0.3: 新增Database缓存机制，缓存所有公司的老板last_action时间戳，
#             运行时先查缓存，离线未达阈值的老板直接跳过，大幅减少API请求频率。

# 文件路径配置
# 这里定义了日志文件的目录，实际日志文件名会在 logger.py 中根据时间戳动态生成
LOG_DIR = './logs'
RESULT_DIR = "./Results"
DB_DIR = "./Database"

# ==================== 速率控制 ====================
MIN_INTERVAL = 0.8  # 两次请求最小间隔（秒），安全且接近50次/分钟


def get_user_agent():
    """根据系统返回合适的 User-Agent"""
    system = platform.system().lower()
    if system == "windows":
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    elif system == "darwin":
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    else:
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"


# 全局 Session 对象，确保在整个程序中复用同一个 Session
_session = None


def get_session():
    """获取全局 Session 单例"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({'User-Agent': get_user_agent()})
    return _session
