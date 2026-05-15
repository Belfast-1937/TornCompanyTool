import platform
import requests


VERSION = "1.3"
# 2026-05-10: v1.0 发布
# 2026-05-14: v1.1 发布 - 增加 Xanax 统计和 30 日平均计算，优化日志记录和用户提示，拆分文件结构，增强代码可读性和维护性
# 2026-05-14: v1.2 发布 - 增加 Reheb 统计和 自定义日Xanax及Reheb平均计算，增加行业信息，增加日志记录，更新配置文件模板
# 2026-05-14: v1.3 发布 - 修复Xanax平均计算bug，将 Rehab 次数改为 switravel（去瑞士次数），更准确反映员工主动解毒频率


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
INDUSTRY_DB_PATH = f"{DATABASE_DIR}/IndustryDB.xlsx"

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

# ==================== 行业字典 ===================
INDUSTRY_MAP = {
    1: "Hair Salon",
    2: "Law Firm",
    3: "Flower Shop",
    4: "Car Dealership",
    5: "Clothing Store",
    6: "Gun Shop",
    7: "Game Shop",
    8: "Candle Shop",
    9: "Toy Shop",
    10: "Adult Novelties",
    11: "Cyber Cafe",
    12: "Grocery Store",
    13: "Theater",
    14: "Sweet Shop",
    15: "Cruise Line",
    16: "Television Network",
    18: "Zoo",
    19: "Firework Stand",
    20: "Property Broker",
    21: "Furniture Store",
    22: "Gas Station",
    23: "Music Store",
    24: "Nightclub",
    25: "Pub",
    26: "Gents Strip Club",
    27: "Restaurant",
    28: "Oil Rig",
    29: "Fitness Center",
    30: "Mechanic Shop",
    31: "Amusement Park",
    32: "Lingerie Store",
    33: "Meat Warehouse",
    34: "Farm",
    35: "Software Corporation",
    36: "Ladies Strip Club",
    37: "Private Security Firm",
    38: "Mining Corporation",
    39: "Detective Agency",
    40: "Logistics Management"
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
