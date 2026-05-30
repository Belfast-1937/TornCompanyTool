# -*- coding: utf-8 -*-
"""训练规划引擎"""
from constants import TRAIN_PRIMARY_BONUS, TRAIN_SECONDARY_BONUS
from efficiency import calculate_efficiency, calculate_efficiency_int


def get_emp_stats(emp):
    """获取员工的三个属性值字典。"""
    return {
        "MAN": emp.get('manual_labor', 0),
        "INT": emp.get('intelligence', 0),
        "END": emp.get('endurance', 0),
    }


def simulate_train_n(stats, gain_primary_stat, gain_secondary_stat, n):
    """模拟训练 n 天后的属性值。返回新的 stats 字典。"""
    new_stats = dict(stats)
    if gain_primary_stat in new_stats:
        new_stats[gain_primary_stat] += TRAIN_PRIMARY_BONUS * n
    if gain_secondary_stat in new_stats:
        new_stats[gain_secondary_stat] += TRAIN_SECONDARY_BONUS * n
    return new_stats


def calc_train_eff_after_n(stats, gain_primary_stat, gain_secondary_stat, n, target_job):
    """计算训练 n 天后对目标岗位的效率（向下取整）。"""
    new_stats = simulate_train_n(stats, gain_primary_stat, gain_secondary_stat, n)
    return calculate_efficiency_int(
        new_stats[target_job['primary_req_stat']],
        target_job['primary_req_value'],
        new_stats[target_job['secondary_req_stat']],
        target_job['secondary_req_value'],
    )


def calc_trains_to_next_point(current_stats, target_job, best_train_job):
    """
    计算需要训练多少次，目标岗位的效率才会增加至少 1 点。
    使用指数搜索+二分查找，复杂度 O(log n)。
    """
    current_eff_int = calculate_efficiency_int(
        current_stats[target_job['primary_req_stat']],
        target_job['primary_req_value'],
        current_stats[target_job['secondary_req_stat']],
        target_job['secondary_req_value'],
    )
    target_eff = current_eff_int + 1

    # 指数搜索确定上界
    hi = 1
    while calc_train_eff_after_n(current_stats, best_train_job['primary_gain_stat'],
                                  best_train_job['secondary_gain_stat'], hi, target_job) < target_eff:
        hi *= 2
        if hi > 100000:
            return 100000  # 安全上限

    lo = 1
    while lo < hi:
        mid = (lo + hi) // 2
        eff = calc_train_eff_after_n(current_stats, best_train_job['primary_gain_stat'],
                                     best_train_job['secondary_gain_stat'], mid, target_job)
        if eff >= target_eff:
            hi = mid
        else:
            lo = mid + 1

    return lo


def find_best_training_job(emp, target_job, all_jobs):
    """
    为一名员工找到最优训练岗位。当效率提升相同时，优先推荐员工当前岗位。

    参数:
        emp: 员工字典（包含 manual_labor, intelligence, endurance）
        target_job: 目标岗位字典（包含需求属性）
        all_jobs: 该公司所有岗位的列表

    返回:
        dict: {
            "best_job_name": str,
            "best_improvement": float,
            "all_results": [(job_name, primary_gain, secondary_gain, improvement), ...],
            "current_eff": float,
            "current_stats": dict,
        }
    """
    current_stats = get_emp_stats(emp)
    current_eff = calculate_efficiency(
        current_stats[target_job['primary_req_stat']],
        target_job['primary_req_value'],
        current_stats[target_job['secondary_req_stat']],
        target_job['secondary_req_value'],
    )
    emp_position = emp.get('position', '')

    results = []
    best_job_name = None
    best_improvement = -999.0

    for job in all_jobs:
        new_stats = simulate_train_n(current_stats, job['primary_gain_stat'],
                                     job['secondary_gain_stat'], 1)
        new_eff = calculate_efficiency(
            new_stats[target_job['primary_req_stat']],
            target_job['primary_req_value'],
            new_stats[target_job['secondary_req_stat']],
            target_job['secondary_req_value'],
        )
        improvement = new_eff - current_eff
        results.append((job['name'], job['primary_gain_stat'],
                       job['secondary_gain_stat'], improvement))

        # 优先选择提升更大的；提升相同时优先选当前岗位
        if (improvement > best_improvement or
                (improvement == best_improvement and job['name'] == emp_position)):
            best_improvement = improvement
            best_job_name = job['name']

    results.sort(key=lambda x: x[3], reverse=True)

    return {
        "best_job_name": best_job_name,
        "best_improvement": best_improvement,
        "all_results": results,
        "current_eff": current_eff,
        "current_stats": current_stats,
    }
