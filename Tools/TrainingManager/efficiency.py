# -*- coding: utf-8 -*-
"""效率计算函数"""
import math


def calculate_efficiency(p_stat: int, p_req: int, s_stat: int, s_req: int) -> float:
    """计算员工在当前属性下对某岗位的效率值（浮点数）"""
    try:
        p_base = min(45, (p_stat / p_req) * 45) if p_req > 0 else 0
        s_base = min(45, (s_stat / s_req) * 45) if s_req > 0 else 0
        p_bonus = max(0, 5 * math.log2(p_stat / p_req)) if p_stat > p_req and p_req > 0 else 0
        s_bonus = max(0, 5 * math.log2(s_stat / s_req)) if s_stat > s_req and s_req > 0 else 0
        return p_base + s_base + p_bonus + s_bonus
    except:
        return 0.0


def calculate_efficiency_int(p_stat: int, p_req: int, s_stat: int, s_req: int) -> int:
    """计算员工在当前属性下对某岗位的效率值（游戏中实际值，向下取整）。"""
    return math.floor(calculate_efficiency(p_stat, p_req, s_stat, s_req))
