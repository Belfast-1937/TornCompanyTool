# -*- coding: utf-8 -*-
"""配置管理"""
import json
import os

from constants import CONFIG_FILE


def load_config():
    """加载配置文件。"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(api_key, user_id, company_id="", company_type=None):
    """保存配置文件。"""
    config = {
        "api_key": api_key,
        "user_id": user_id,
        "company_id": company_id,
    }
    if company_type is not None:
        config["company_type"] = company_type
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def clear_config():
    """清除配置文件。"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
