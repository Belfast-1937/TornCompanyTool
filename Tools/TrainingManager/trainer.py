# -*- coding: utf-8 -*-
"""训练规划引擎"""
from constants import TRAIN_PRIMARY_BONUS, TRAIN_SECONDARY_BONUS
from efficiency import calculate_efficiency


def get_emp_stats(emp):
    """获取员工的三个属性值字典。"""
    return {
        "MAN": emp.get('manual_labor', 0),
        "INT": emp.get('intelligence', 0),
        "END": emp.get('endurance', 0),
    }


def simulate_train(stats, gain_primary_stat, gain_secondary_stat):
    """模拟训练一天后的属性值。返回新的 stats 字典。"""
    new_stats = dict(stats)
    if gain_primary_stat in new_stats:
        new_stats[gain_primary_stat] += TRAIN_PRIMARY_BONUS
    if gain_secondary_stat in new_stats:
        new_stats[gain_secondary_stat] += TRAIN_SECONDARY_BONUS
    return new_stats


def find_best_training_job(emp, target_job, all_jobs):
    """
    为一名员工找到最优训练岗位。

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

    results = []
    best_job_name = None
    best_improvement = -999.0

    for job in all_jobs:
        new_stats = simulate_train(
            current_stats, job['primary_gain_stat'], job['secondary_gain_stat'])
        new_eff = calculate_efficiency(
            new_stats[target_job['primary_req_stat']],
            target_job['primary_req_value'],
            new_stats[target_job['secondary_req_stat']],
            target_job['secondary_req_value'],
        )
        improvement = new_eff - current_eff
        results.append((job['name'], job['primary_gain_stat'],
                       job['secondary_gain_stat'], improvement))

        if improvement > best_improvement:
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
