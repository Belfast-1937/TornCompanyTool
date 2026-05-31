# -*- coding: utf-8 -*-
"""常量与硬编码公司岗位数据（39 家公司）"""
import os as _os
import sys as _sys


def _get_script_dir():
    """兼容 Windows/Linux/macOS + PyInstaller"""
    if getattr(_sys, 'frozen', False):
        return _os.path.dirname(_sys.executable)
    return _os.path.dirname(_os.path.abspath(__file__))

# 1.0: 发布初始版本
# 1.1：删除不必要的用户ID输入；修复当多个训练岗位属性增益相同时，优先推荐员工当前岗位而非最后一个；同步游戏内效率计算函数，修正效率增加计算逻辑
# 1.2: 更换GUI框架为PySide6，提升界面性能和兼容性；优化代码结构和错误处理机制，提升稳定性和用户体验，增加背景图片和界面美化支持
VERSION = "1.2"

SCRIPT_DIR = _get_script_dir()
CONFIG_FILE = _os.path.join(SCRIPT_DIR, "config.json")

# 训练属性加成
TRAIN_PRIMARY_BONUS = 50
TRAIN_SECONDARY_BONUS = 25

# Torn API
API_URL_TEMPLATE = "https://api.torn.com/company/{company_id}?selections=profile,employees&key={api_key}"
API_TIMEOUT = 15
API_RETRY_WAIT = 65
API_NETWORK_WAIT = 20
API_MAX_RETRIES = 3


import company_data

COMPANIES_DATA = company_data.COMPANIES_DATA
