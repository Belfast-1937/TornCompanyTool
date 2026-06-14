# -*- coding: utf-8 -*-
"""训练规划引擎 — 支持 DP 全局最优（≤20次）和凸优化（>20次）"""
from constants import TRAIN_PRIMARY_BONUS, TRAIN_SECONDARY_BONUS
from efficiency import calculate_efficiency, calculate_efficiency_int


def get_emp_stats(emp):
    """获取员工的三个属性值字典"""
    return {
        "MAN": emp.get('manual_labor', 0),
        "INT": emp.get('intelligence', 0),
        "END": emp.get('endurance', 0),
    }


def simulate_train_n(stats, gain_primary_stat, gain_secondary_stat, n):
    """模拟训练 n 天后的属性值，返回新的 stats 字典"""
    new_stats = dict(stats)
    if gain_primary_stat in new_stats:
        new_stats[gain_primary_stat] += TRAIN_PRIMARY_BONUS * n
    if gain_secondary_stat in new_stats:
        new_stats[gain_secondary_stat] += TRAIN_SECONDARY_BONUS * n
    return new_stats


def calc_train_eff_after_n(stats, gain_primary_stat, gain_secondary_stat, n, target_job):
    """计算训练 n 天后对目标岗位的效率（向下取整）"""
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

    hi = 1
    while calc_train_eff_after_n(current_stats, best_train_job['primary_gain_stat'],
                                  best_train_job['secondary_gain_stat'], hi, target_job) < target_eff:
        hi *= 2
        if hi > 100000:
            return 100000

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


# ==================== 全局最优训练规划 ====================

def _eff_of_state(state_tuple, p_stat_name, p_req, s_stat_name, s_req):
    """从 (MAN, INT, END) 元组计算目标岗位效率（浮点）"""
    stat_map = {'MAN': state_tuple[0], 'INT': state_tuple[1], 'END': state_tuple[2]}
    return calculate_efficiency(
        stat_map[p_stat_name], p_req,
        stat_map[s_stat_name], s_req,
    )


def _simulate_dp(emp, target_job, all_jobs, total_trains):
    """
    DP 全局最优（≤20次）。
    状态 = (MAN, INT, END) 元组，dp[step][state] = (best_eff_float, prev_state, job_name)
    回溯得到完整训练序列。
    """
    init = get_emp_stats(emp)
    p_stat = target_job['primary_req_stat']
    p_req = target_job['primary_req_value']
    s_stat = target_job['secondary_req_stat']
    s_req = target_job['secondary_req_value']
    target_position = target_job['name']

    # 岗位增益向量
    job_vectors = []
    for job in all_jobs:
        v = {"MAN": 0, "INT": 0, "END": 0}
        v[job['primary_gain_stat']] = TRAIN_PRIMARY_BONUS
        v[job['secondary_gain_stat']] = TRAIN_SECONDARY_BONUS
        job_vectors.append((job['name'], v))

    initial = (init['MAN'], init['INT'], init['END'])
    init_eff = _eff_of_state(initial, p_stat, p_req, s_stat, s_req)

    dp = [{initial: (init_eff, None, None)}]

    for step in range(total_trains):
        prev = dp[-1]
        cur = {}
        for state, (eff, _, _) in prev.items():
            for name, vec in job_vectors:
                ns = (state[0] + vec['MAN'], state[1] + vec['INT'], state[2] + vec['END'])
                ne = _eff_of_state(ns, p_stat, p_req, s_stat, s_req)
                if ns not in cur or ne > cur[ns][0]:
                    cur[ns] = (ne, state, name)
        dp.append(cur)

    # 在最后一步找效率最高的状态，然后回溯
    best_state = None
    best_eff = -1.0
    for state, (eff, _, _) in dp[-1].items():
        if eff > best_eff or (abs(eff - best_eff) < 1e-10 and best_state is None):
            best_eff = eff
            best_state = state

    # 回溯
    seq = []
    cur_state = best_state
    for step in range(total_trains, 0, -1):
        _, prev_state, job_name = dp[step][cur_state]
        assert prev_state is not None, "DP backtracking failed"
        seq.append((job_name, cur_state))
        cur_state = prev_state
    seq.reverse()

    # 构建 history
    history = []
    stats = dict(init)
    for job_name, state_after in seq:
        eff_before = calculate_efficiency_int(
            stats[p_stat], p_req, stats[s_stat], s_req)
        stats = {'MAN': state_after[0], 'INT': state_after[1], 'END': state_after[2]}
        eff_after = calculate_efficiency_int(
            stats[p_stat], p_req, stats[s_stat], s_req)
        history.append({
            'best_job': job_name,
            'eff_before': eff_before,
            'eff_after': eff_after,
            'gain': eff_after - eff_before,
            'stats': dict(stats),
        })

    return history


def _simulate_greedy(emp, target_job, all_jobs, total_trains):
    """
    贪心法。每次选浮点效率提升最大的岗位。
    属性全部达标后与大 N 下，贪心与全局最优等价。
    """
    current_stats = get_emp_stats(emp)
    target_position = target_job['name']
    history = []

    for _ in range(total_trains):
        current_eff_float = calculate_efficiency(
            current_stats[target_job['primary_req_stat']],
            target_job['primary_req_value'],
            current_stats[target_job['secondary_req_stat']],
            target_job['secondary_req_value'],
        )
        current_eff_int = calculate_efficiency_int(
            current_stats[target_job['primary_req_stat']],
            target_job['primary_req_value'],
            current_stats[target_job['secondary_req_stat']],
            target_job['secondary_req_value'],
        )

        best_job_name = None
        best_float_improvement = -999.0
        best_new_stats = None

        for job in all_jobs:
            new_stats = simulate_train_n(current_stats, job['primary_gain_stat'],
                                         job['secondary_gain_stat'], 1)
            new_eff_float = calculate_efficiency(
                new_stats[target_job['primary_req_stat']],
                target_job['primary_req_value'],
                new_stats[target_job['secondary_req_stat']],
                target_job['secondary_req_value'],
            )
            float_improvement = new_eff_float - current_eff_float

            if (float_improvement > best_float_improvement or
                    (abs(float_improvement - best_float_improvement) < 1e-10
                     and job['name'] == target_position)):
                best_float_improvement = float_improvement
                best_job_name = job['name']
                best_new_stats = new_stats

        current_stats = best_new_stats
        new_eff_int = calculate_efficiency_int(
            current_stats[target_job['primary_req_stat']],
            target_job['primary_req_value'],
            current_stats[target_job['secondary_req_stat']],
            target_job['secondary_req_value'],
        )

        history.append({
            'best_job': best_job_name,
            'eff_before': current_eff_int,
            'eff_after': new_eff_int,
            'gain': new_eff_int - current_eff_int,
            'stats': dict(current_stats),
        })

    return history


def _simulate_convex(emp, target_job, all_jobs, total_trains):
    """
    凸优化（>20次，大规模训练）。
    扫描纯策略和两两混合策略，找到全局最优分配，再展开为 step-by-step。
    """
    init = get_emp_stats(emp)
    p_stat = target_job['primary_req_stat']
    p_req = target_job['primary_req_value']
    s_stat = target_job['secondary_req_stat']
    s_req = target_job['secondary_req_value']

    # 岗位增益向量
    job_vecs = []
    for job in all_jobs:
        v = {"MAN": 0, "INT": 0, "END": 0}
        v[job['primary_gain_stat']] = TRAIN_PRIMARY_BONUS
        v[job['secondary_gain_stat']] = TRAIN_SECONDARY_BONUS
        job_vecs.append({'name': job['name'], 'vec': v, 'job': job})

    def _final_eff(allocation):
        """allocation: {job_name: count, ...}  sum of counts == total_trains"""
        m, i, e = init['MAN'], init['INT'], init['END']
        for job_name, cnt in allocation.items():
            for jv in job_vecs:
                if jv['name'] == job_name:
                    m += jv['vec']['MAN'] * cnt
                    i += jv['vec']['INT'] * cnt
                    e += jv['vec']['END'] * cnt
                    break
        return calculate_efficiency(
            {'MAN': m, 'INT': i, 'END': e}[p_stat], p_req,
            {'MAN': m, 'INT': i, 'END': e}[s_stat], s_req,
        )

    N = total_trains
    best_eff = -1.0
    best_allocation = None

    # 1. 纯策略
    for jv in job_vecs:
        name = jv['name']
        eff = _final_eff({name: N})
        if eff > best_eff + 1e-10:
            best_eff = eff
            best_allocation = ({name: N}, eff)

    # 2. 两两混合策略（扫描权重 a ∈ [0, 1]，步长 0.01）
    for i in range(len(job_vecs)):
        for j in range(i + 1, len(job_vecs)):
            name_a = job_vecs[i]['name']
            name_b = job_vecs[j]['name']
            for k in range(101):
                a = k / 100.0
                cnt_a = int(round(a * N))
                cnt_b = N - cnt_a
                if cnt_a < 0:
                    cnt_a = 0
                if cnt_b < 0:
                    cnt_b = 0
                allocation = {}
                if cnt_a > 0:
                    allocation[name_a] = cnt_a
                if cnt_b > 0:
                    allocation[name_b] = cnt_b
                if not allocation:
                    continue
                eff = _final_eff(allocation)
                if eff > best_eff + 1e-10:
                    best_eff = eff
                    best_allocation = (dict(allocation), eff)

    # 将最优分配展开成 step-by-step（用于 GUI 显示）
    allocation, final_eff_float = best_allocation

    # 按岗位排序展开
    expanded = []
    for name in sorted(allocation.keys()):
        expanded.extend([name] * allocation[name])

    # 构建 step-by-step history
    current_stats = dict(init)
    history = []
    for step_idx, job_name in enumerate(expanded):
        eff_before = calculate_efficiency_int(
            current_stats[p_stat], p_req, current_stats[s_stat], s_req)
        job = next(j for j in all_jobs if j['name'] == job_name)
        current_stats = simulate_train_n(current_stats, job['primary_gain_stat'],
                                         job['secondary_gain_stat'], 1)
        eff_after = calculate_efficiency_int(
            current_stats[p_stat], p_req, current_stats[s_stat], s_req)
        history.append({
            'best_job': job_name,
            'eff_before': eff_before,
            'eff_after': eff_after,
            'gain': eff_after - eff_before,
            'stats': dict(current_stats),
        })

    return history


def simulate_training_plan(emp, target_job, all_jobs, total_trains):
    """
    模拟 N 次训练的最优规划。

    策略:
    - 属性未全达标时：DP 全局最优（≤20次）或凸优化（>20次）
    - 属性全达标后：贪心（所有方法等效）

    参数:
        emp: 员工字典
        target_job: 目标岗位字典
        all_jobs: 所有岗位列表
        total_trains: 训练次数

    返回:
        list[dict]: 每次训练的结果
    """
    current_stats = get_emp_stats(emp)
    p_stat = target_job['primary_req_stat']
    p_req = target_job['primary_req_value']
    s_stat = target_job['secondary_req_stat']
    s_req = target_job['secondary_req_value']

    # 判断是否全部达标
    p_met = current_stats[p_stat] >= p_req
    s_met = current_stats[s_stat] >= s_req
    all_met = p_met and s_met

    if all_met:
        # 达标后所有方法等效，直接用贪心
        return _simulate_greedy(emp, target_job, all_jobs, total_trains)
    elif total_trains <= 20:
        return _simulate_dp(emp, target_job, all_jobs, total_trains)
    else:
        return _simulate_convex(emp, target_job, all_jobs, total_trains)


def find_best_training_job(emp, target_job, all_jobs):
    """
    为一名员工找到最优训练岗位。当效率提升相同时，优先推荐期待岗位。

    参数:
        emp: 员工字典（包含 manual_labor, intelligence, endurance）
        target_job: 目标岗位字典（包含需求属性）
        all_jobs: 该公司所有岗位的列表

    返回:
        dict: {
            "best_job_name": 最优训练岗位名称,
            "best_improvement": 效率提升值,
            "all_results": [(岗位名称, 主属性, 副属性, 提升值), ...],
            "current_eff": 当前效率值,
            "current_stats": 当前属性字典,
        }
    """
    current_stats = get_emp_stats(emp)
    current_eff = calculate_efficiency(
        current_stats[target_job['primary_req_stat']],
        target_job['primary_req_value'],
        current_stats[target_job['secondary_req_stat']],
        target_job['secondary_req_value'],
    )
    target_position = target_job['name']

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

        if (improvement > best_improvement or
                (abs(improvement - best_improvement) < 1e-10 and job['name'] == target_position)):
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