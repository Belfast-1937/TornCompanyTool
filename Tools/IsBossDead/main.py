import os
import sys
import logging
import configparser
import time
from datetime import datetime
import pandas as pd

from api_client import fetch_industry_data, fetch_company_profile, fetch_player_profile
from utils import print_startup_info, check_network, file_access_handler, get_script_dir
from logger import setup_logger
from config import RESULT_DIR


@file_access_handler
def get_config():
    """读取配置文件"""
    config = configparser.ConfigParser()
    ini_file = 'Industry.ini'

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    ini_file = os.path.join(base_dir, ini_file)

    if os.path.exists(ini_file):
        logging.info(f"正在读取配置文件: {ini_file}")
        try:
            config.read(ini_file, encoding='utf-8')
            key = config.get('Settings', 'ApiKey').strip()
            iid = config.get('Settings', 'IndustryID').strip()
            boss_days = config.getint(
                'Settings', 'BossOfflineDays', fallback=3)
            emp_days = config.getint(
                'Settings', 'EmployeeActiveDays', fallback=1)
            minimum_star_rating = config.getint(
                'Settings', 'MinimumStarRating', fallback=3)

            if "Your_" in key or "Your_" in iid:
                logging.warning("配置文件中仍包含默认占位符")
                print("⚠️  警告: 检测到配置内仍是默认占位符，请修改 Industry.ini。")
                return None, None, boss_days, emp_days, minimum_star_rating
            return key, iid, boss_days, emp_days, minimum_star_rating
        except Exception as e:
            logging.error(f"读取 Industry.ini 出错: {e}")
    else:
        logging.info("未找到 Industry.ini，将进入手动输入模式。")
    return None, None, boss_days, emp_days, minimum_star_rating


def get_last_action_timestamp(emp):
    """从员工信息中提取 last_action timestamp"""
    try:
        if isinstance(emp, dict) and 'last_action' in emp:
            last_action = emp['last_action']
            if isinstance(last_action, dict):
                return last_action.get('timestamp')
    except:
        pass
    return None


def get_director_status(emp):
    """获取老板状态，特别检测是否被联邦监狱封禁"""
    try:
        if isinstance(emp, dict) and 'status' in emp:
            status = emp['status']
            if isinstance(status, dict):
                return {
                    'description': status.get('description', ''),
                    'state': status.get('state', ''),
                    'color': status.get('color', ''),
                    'is_banned': status.get('state') == 'Federal' or 'Federal' in status.get('description', '').lower()
                }
    except:
        pass
    return {'description': '', 'state': '', 'color': '', 'is_banned': False}


def get_director_faction(player_profile):
    """提取 Director 的 Faction 名称"""
    try:
        if isinstance(player_profile, dict) and 'faction' in player_profile:
            faction = player_profile.get('faction')
            if isinstance(faction, dict):
                return faction.get('faction_name', 'None')
    except:
        pass
    return 'None'


def main():
    log_file = setup_logger()
    script_dir = get_script_dir()

    print(
        f"📦 运行模式: {'PyInstaller' if getattr(sys, 'frozen', False) else 'Python'}")
    print_startup_info()
    print("等待15秒以确保认真阅读以上信息...\n")
    time.sleep(15)

    os.chdir(script_dir)
    print(f"📂 工作目录已切换到: {script_dir}")

    os.makedirs(RESULT_DIR, exist_ok=True)

    if not check_network():
        logging.error("网络连接失败，程序退出")
        time.sleep(15)
        sys.exit(1)

    api_key, industry_id, boss_offline_days, employee_online_days, minimum_star_rating = get_config()

    if not all([api_key, industry_id]):
        print("💡 未能通过配置文件自动登录，请手动输入：")
        api_key = input("请输入 API Key: ")
        industry_id = input("请输入 Industry ID: ")
        boss_offline_days = int(input("老板离线多少天视为目标 (默认 3): ") or 3)
        employee_online_days = int(input("员工多少天内活跃视为目标 (默认 1): ") or 1)
        minimum_star_rating = int(input("最小星级 (默认 3): ") or 3)

    current_ts = int(time.time())
    print(
        f"开始扫描行业 {industry_id} | 当前时间: {datetime.fromtimestamp(current_ts)}\n")

    # 1. 获取行业公司列表
    industry_data = fetch_industry_data(industry_id, api_key)
    if 'error' in industry_data or not isinstance(industry_data.get('company'), dict):
        print("❌ 获取行业数据失败")
        return

    companies = industry_data['company']
    print(f"行业共有 {len(companies)} 家公司\n")

    # 2. 筛选有员工的公司
    candidates = [
        {
            'company_id': int(cid),
            'name': info.get('name'),
            'director_id': info.get('director'),
            'employees_hired': info.get('employees_hired', 0),
            'daily_income': info.get('daily_income', 0)
        }
        for cid, info in companies.items()
        if info.get('employees_hired', 0) > 0 and info.get('rating', 0) >= minimum_star_rating
    ]

    if not candidates:
        print("没有找到有员工的公司")
        return

    df = pd.DataFrame(candidates).sort_values('daily_income', ascending=False)
    print(f"共 {len(df)} 家有员工的公司不低于最小星级要求{minimum_star_rating}\n")

    results = []

    for _, row in df.iterrows():
        cid = row['company_id']
        name = row['name']

        print(
            f"检查: {name} (ID: {cid}) | 员工: {row['employees_hired']} | 日收入: {row['daily_income']:,}")

        comp_data = fetch_company_profile(cid, api_key)
        if 'error' in comp_data or 'company' not in comp_data:
            print("  ❌ 获取公司数据失败，跳过\n")
            continue

        company = comp_data['company']
        employees = company.get('employees', {})

        # 检查老板
        director_id = row['director_id']
        boss = employees.get(str(director_id))
        if not boss:
            print("  ⚠️ 未找到老板信息\n")
            continue

        boss_ts = get_last_action_timestamp(boss)
        boss_status = get_director_status(boss)
        if not boss_ts:
            print("  ⚠️ 无法获取老板上线时间\n")
            continue

        boss_offline = (current_ts - boss_ts) / 86400.0

        is_banned = boss_status['is_banned']
        if is_banned:
            print(f"  🚨 【BANNED】老板已被联邦监狱封禁！ {boss_status['description']}")
        elif boss_offline < boss_offline_days:
            print(f"  👤 老板仅离线 {boss_offline:.1f} 天，跳过\n")
            continue

        print(f"  ✅ 老板已离线 {boss_offline:.1f} 天，检查员工...")

        # 检查员工
        active_count = 0
        active_names = []

        for eid_str, emp in employees.items():
            if int(eid_str) == director_id:
                continue
            ts = get_last_action_timestamp(emp)
            if ts and (current_ts - ts) / 86400.0 <= employee_online_days:
                active_count += 1
                active_names.append(emp.get('name', eid_str))

        if active_count > 0:
            company_url = f"https://www.torn.com/joblist.php#!p=corpinfo&ID={cid}"
            print(f"  🎯 【目标公司】{active_count} 名员工最近上线！ {active_names}\n")
            results.append({
                'CompanyID': cid,
                'CompanyName': name,
                'DirectorID': director_id,
                'BossOfflineDays': round(boss_offline, 2),
                'ActiveEmployees': active_count,
                'DailyIncome': int(row['daily_income']),
                'CompanyURL': company_url
            })
        else:
            print("  ❌ 没有最近上线的员工\n")

    # 输出结果
    print("\n" + "="*80)
    if results:
        result_df = pd.DataFrame(results)

        print("🔍 正在为目标公司查询老板派系信息...")
        faction_list = []

        for _, row in result_df.iterrows():
            director_id = row.get('DirectorID')
            if director_id and director_id != 0:
                try:
                    profile_data = fetch_player_profile(
                        int(director_id), api_key)
                    faction_name = get_director_faction(profile_data)
                    faction_list.append(faction_name)
                    print(f"   Director {director_id} → {faction_name}")
                except:
                    faction_list.append("None")
            else:
                faction_list.append("None")

        result_df['DirectorFaction'] = faction_list

        # 调整列顺序
        cols = ['CompanyID', 'CompanyName', 'DirectorID', 'DirectorFaction', 'BossOfflineDays',
                'ActiveEmployees', 'DailyIncome', 'CompanyURL']
        result_df = result_df[cols]

        print(result_df.to_string(index=False))

        # 保存结果
        result_file = f"{RESULT_DIR}/Industry_Targets_{datetime.now().strftime('%Y%m%d')}.xlsx"
        result_df.to_excel(result_file, index=False)
        print(f"\n✅ 共找到 {len(results)} 家目标公司！结果已保存至：{result_file}")
    else:
        print("本轮扫描未找到符合条件的目标公司。")

    print(f"\n📊 扫描完成！程序将在 30 秒后自动关闭。")
    time.sleep(30)


if __name__ == "__main__":
    main()
