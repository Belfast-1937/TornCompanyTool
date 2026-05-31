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
from config import RESULT_DIR, DB_DIR


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


def load_boss_database(industry_id):
    """加载老板状态数据库，缓存所有公司老板的last_action时间戳
    
    数据库文件: Database/Industry_BossDB_{IndustryID}.xlsx
    列: CompanyID, DirectorID, BossLastActionTS
    
    Returns:
        dict 或 None: {company_id: {'director_id': int, 'boss_last_action_ts': int}}
    """
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        db_file = os.path.join(DB_DIR, f"Industry_BossDB_{industry_id}.xlsx")
        if not os.path.exists(db_file):
            logging.info("数据库文件不存在，所有公司将请求API")
            print("📋 未找到缓存数据库，将正常扫描所有公司\n")
            return None

        df = pd.read_excel(db_file)
        required_cols = {'CompanyID', 'DirectorID', 'BossLastActionTS'}
        if not required_cols.issubset(df.columns):
            logging.warning("数据库文件缺少必要列，放弃使用缓存")
            print("⚠️ 数据库文件格式不兼容，将正常扫描所有公司\n")
            return None

        db = {}
        for _, row in df.iterrows():
            cid = int(row['CompanyID'])
            db[cid] = {
                'director_id': int(row.get('DirectorID', 0)),
                'boss_last_action_ts': int(row['BossLastActionTS'])
            }

        logging.info(f"加载数据库: {db_file} ({len(db)} 条记录)")
        print(f"📋 加载缓存数据库 ({len(db)} 条记录)\n")
        return db
    except Exception as e:
        logging.warning(f"加载数据库失败: {e}")
        print(f"⚠️ 加载数据库出错: {e}，将正常扫描所有公司\n")
        return None


def save_boss_database(industry_id, db_data):
    """保存老板状态数据库
    
    Args:
        industry_id: 行业ID
        db_data: {company_id: {'director_id': int, 'boss_last_action_ts': int}}
    """
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        db_file = os.path.join(DB_DIR, f"Industry_BossDB_{industry_id}.xlsx")

        rows = []
        for cid, info in db_data.items():
            rows.append({
                'CompanyID': cid,
                'DirectorID': info['director_id'],
                'BossLastActionTS': info['boss_last_action_ts']
            })

        df = pd.DataFrame(rows)
        df.to_excel(db_file, index=False)
        logging.info(f"数据库已保存: {db_file} ({len(rows)} 条记录)")
        print(f"💾 缓存数据库已更新 ({len(rows)} 条记录)")
    except Exception as e:
        logging.warning(f"保存数据库失败: {e}")
        print(f"⚠️ 保存数据库出错: {e}")


def should_skip_by_cache(company_id, director_id, db, current_ts, boss_offline_days):
    """根据数据库缓存判断是否可以跳过API请求
    
    直接使用数据库中记录的BossLastActionTS计算离线天数。
    如果离线天数还未达到阈值且老板未换人，则可以跳过。
    
    Args:
        company_id: 公司ID
        director_id: 当前老板ID
        db: 数据库字典
        current_ts: 当前时间戳
        boss_offline_days: 配置文件中的老板离线天数阈值
    
    Returns:
        bool: True 表示应该跳过
    """
    if not db or company_id not in db:
        return False

    entry = db[company_id]

    # 如果老板换了，不能依赖缓存
    if entry['director_id'] and director_id and entry['director_id'] != int(director_id):
        return False

    # 直接计算离线天数
    offline_days = (current_ts - entry['boss_last_action_ts']) / 86400.0
    if offline_days < boss_offline_days:
        return True

    return False


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
    os.makedirs(DB_DIR, exist_ok=True)

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

    # 2.5 加载老板状态数据库
    db = load_boss_database(industry_id) or {}

    results = []

    for _, row in df.iterrows():
        cid = row['company_id']
        name = row['name']
        director_id = row['director_id']

        print(
            f"检查: {name} (ID: {cid}) | 员工: {row['employees_hired']} | 日收入: {row['daily_income']:,}")

        # 预判断：查数据库缓存，判断是否可跳过API请求
        if should_skip_by_cache(cid, director_id, db, current_ts, boss_offline_days):
            print(f"  📋 缓存命中，老板离线尚未达阈值，跳过\n")
            continue

        comp_data = fetch_company_profile(cid, api_key)
        if 'error' in comp_data or 'company' not in comp_data:
            print("  ❌ 获取公司数据失败，跳过\n")
            continue

        company = comp_data['company']
        employees = company.get('employees', {})

        # 检查老板
        boss = employees.get(str(director_id))
        if not boss:
            print("  ⚠️ 未找到老板信息\n")
            continue

        boss_ts = get_last_action_timestamp(boss)
        boss_status = get_director_status(boss)
        if not boss_ts:
            print("  ⚠️ 无法获取老板上线时间\n")
            continue

        # 更新数据库（无论老板是否离线达标，都记录最新 last_action 时间戳）
        db[cid] = {
            'director_id': int(director_id) if director_id else 0,
            'boss_last_action_ts': boss_ts
        }

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

    # 保存数据库
    save_boss_database(industry_id, db)

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
