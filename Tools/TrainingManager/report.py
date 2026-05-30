# -*- coding: utf-8 -*-
"""训练规划报告生成"""
import os
from datetime import datetime

from constants import SCRIPT_DIR


def generate_report(company_name, target_company_id, plan_results):
    """
    生成训练规划 TXT 报告。

    参数:
        company_name: 公司名称
        target_company_id: 公司 ID
        plan_results: list[dict]，每个 dict 包含 emp, target_job_name, plan, trains_needed
    """
    reports_dir = os.path.join(SCRIPT_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_plan_{timestamp}.txt"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Torn City 员工训练规划报告\n")
        f.write(f"公司: {company_name} (ID: {target_company_id})\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        for pr in plan_results:
            emp = pr['emp']
            target_job_name = pr['target_job_name']
            plan = pr['plan']
            target_job = pr['target_job']
            stats = plan['current_stats']

            f.write(f"=== 员工: {emp['name']} | 期待岗位: {target_job_name} ===\n")
            f.write(
                f"MAN: {stats['MAN']} | INT: {stats['INT']} | END: {stats['END']}\n")
            f.write(
                f"最终需求 → 主: {target_job['primary_req_stat']} ({target_job['primary_req_value']}) "
                f"| 副: {target_job['secondary_req_stat']} ({target_job['secondary_req_value']})\n")
            f.write(f"\n")
            trains_needed = pr.get('trains_needed', '?')
            trains_str = f"{trains_needed}次" if isinstance(trains_needed, int) and trains_needed < 100000 else ">10万"
            f.write(
                f"→ **最佳训练岗位: {plan['best_job_name']}** (效率提升 {plan['best_improvement']:.4f})\n")
            f.write(f"→ 训练 {trains_str} 后工作效率可增加至少 1 点\n")
            f.write(f"\n")
            f.write(f"训练岗位{'':20s}主属性   副属性   效率Δ\n")
            f.write(f"{'-' * 50}\n")
            for job_name, p_gain, s_gain, imp in plan['all_results']:
                f.write(f"{job_name:<30s}{p_gain:<10s}{s_gain:<10s}{imp:.4f}\n")
            f.write(f"\n")

    return filepath
