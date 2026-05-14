import platform
import requests


VERSION = "1.1"
# 2026-05-10: v1.0 发布
# 2026-05-14: v1.1 发布 - 增加 Xanax 统计和 30 日平均计算，优化日志记录和用户提示，拆分文件结构，增强代码可读性和维护性


# Xanax 相关配置
MAX_XAN_DAYS = 30


# 文件路径配置
# 这里定义了日志文件的目录，实际日志文件名会在 logger.py 中根据时间戳动态生成
LOG_DIR = './logs'
# 数据库文件夹路径，存放员工数据、效率数据、库存数据等
DATABASE_DIR = './Database'

EMPLOYEE_DB_PATH = f"{DATABASE_DIR}/EmployeeDB.xlsx"
HISTORY_DB_PATH = f"{DATABASE_DIR}/HistoryDB.xlsx"
STOCK_DB_PATH = f"{DATABASE_DIR}/StockDB.xlsx"
USER_PERK_DB_PATH = f"{DATABASE_DIR}/UserPerkDB.xlsx"

REPORT_DIR = './Report'
EFFICIENCY_REPORT_PATH = f"{REPORT_DIR}/Company_Efficiency_Report.xlsx"


# ==================== 股票字典 ====================
STOCK_MAP = {
    13: ("(TCP) TC Media Productions", "Company sales boost"),
    23: ("(TGP) Tell Group Plc.", "Company advertising boost"),
}

# ==================== 教育字典 (eid, code, full_name, effect, category) ====================
EDUCATION_MAP = {
    1:  (1,  "BUS1100", "BUS1100 Introduction to Business", "Basic", None),
    2:  (2,  "BUS2200", "BUS2200 Statistics", "Gain 2% productivity for your company", "Productivity"),
    3:  (3,  "BUS2300", "BUS2300 Communication", "Gain 5% employee effectiveness for your company", "Employee Effectiveness"),
    4:  (4,  "BUS2400", "BUS2400 Marketing", "Gain an increase in advertising effectiveness for your company", "Advertising"),
    5:  (5,  "BUS2500", "BUS2500 Corporate Finance", "Gain 2% productivity for your company", "Productivity"),
    6:  (6,  "BUS2600", "BUS2600 Corporate Strategy", "Gain 7% employee effectiveness for your company", "Employee Effectiveness"),
    7:  (7,  "BUS2700", "BUS2700 Pricing Strategy", "Gain 10% perceived product value for your company", "Perceived Product Value"),
    8:  (8,  "BUS2800", "BUS2800 Logistics", "Gain 2% productivity for your company", "Productivity"),
    9:  (9,  "BUS2900", "BUS2900 Product Management", "Gain 5% perceived product value for your company", "Perceived Product Value"),
    10: (10, "BUS2100", "BUS2100 Business Ethics", "Gain 2% productivity for your company", "Productivity"),
    11: (11, "BUS2110", "BUS2110 Human Resource Management", "Gain a passive bonus to employee working stats in your company", "Employee Effectiveness"),
    12: (12, "BUS2120", "BUS2120 E-Commerce", "Gain 2% productivity for your company", "Productivity"),
    13: (13, "BUS3130", "BUS3130 Bachelor of Commerce", "Unlock new size, storage size & staff room upgrades for your company", None),
    88: (88, "LAW1880", "LAW1880 Introduction to Law", "Basic", None),
    100: (100, "LAW2100", "LAW2100 Media Law", "Gain an increase in advertising effectiveness for your company", "Advertising"),
    22: (22, "MTH1220", "MTH1220 Introduction to Mathematics", "Basic", None),
    28: (28, "MTH2280", "MTH2280 Probability", "Gain 1% productivity for your company", "Productivity"),
}


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


__all__ = [
    'VERSION', 'MAX_XAN_DAYS',
    'LOG_DIR', 'DATABASE_DIR', 'REPORT_DIR',
    'EMPLOYEE_DB_PATH', 'HISTORY_DB_PATH', 'STOCK_DB_PATH',
    'USER_PERK_DB_PATH', 'EFFICIENCY_REPORT_PATH',
    'STOCK_MAP', 'EDUCATION_MAP',
    'get_user_agent', 'get_session'
]
