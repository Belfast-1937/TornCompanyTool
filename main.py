import os
import sys
import time
import logging
import pandas as pd
import configparser

from config import DATABASE_DIR, REPORT_DIR, \
    EMPLOYEE_DB_PATH, HISTORY_DB_PATH, STOCK_DB_PATH, \
    USER_PERK_DB_PATH, EFFICIENCY_REPORT_PATH, INDUSTRY_DB_PATH

from logger import setup_logger
from utils import file_access_handler, get_script_dir, print_startup_info, check_network
from api_client import fetch_company_data, fetch_user_data, fetch_industry_data
from data_processor import (get_employees, get_company_detailed, get_latest_gross_income,
                            get_company_stock, parse_xan_rehab_stats, calculate_stat_day_avg, parse_user_perks, get_industry_companies)
from excel_handler import save_to_excel, generate_horizontal_report


# === 配置读取 ===
@file_access_handler
def get_config():
    """读取配置文件"""
    config = configparser.ConfigParser()
    ini_file = 'Company.ini'

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    ini_file = os.path.join(base_dir, ini_file)

    if os.path.exists(ini_file):
        logging.info(f"正在读取配置文件: {ini_file}")
        try:
            config.read(ini_file, encoding='utf-8')
            cid = config.get('Settings', 'CompanyID').strip()
            key = config.get('Settings', 'ApiKey').strip()
            uid = config.get('Settings', 'UserID').strip()
            iid = config.get('Settings', 'IndustryID').strip()

            if "Your_" in cid or "Your_" in key or "Your_" in uid or "Your_" in iid:
                logging.warning("配置文件中仍包含默认占位符")
                print("⚠️  警告: 检测到配置内仍是默认占位符，请修改 Company.ini。")
                return None, None, None, None
            return cid, key, uid, iid
        except Exception as e:
            logging.error(f"读取 Company.ini 出错: {e}")
    else:
        logging.info("未找到 Company.ini，将进入手动输入模式。")
    return None, None, None, None


def main():
    log_file = setup_logger()
    script_dir = get_script_dir()

    print(
        f"📦 运行模式: {'PyInstaller' if getattr(sys, 'frozen', False) else 'Python'}")
    print_startup_info()

    os.chdir(script_dir)
    print(f"📂 工作目录已切换到: {script_dir}")

    if not check_network():
        logging.error("网络连接失败，程序退出")
        time.sleep(15)
        sys.exit(1)

    for folder in [DATABASE_DIR, REPORT_DIR]:
        os.makedirs(folder, exist_ok=True)

    cid, key, user_id, industry_id = get_config()
    if not all([cid, key, user_id, industry_id]):
        print("💡 未能通过配置文件自动登录，请手动输入：")
        user_id = input("请输入 User ID: ")
        cid = input("请输入 Company ID: ")
        key = input("请输入 API Key: ")
        industry_id = input("请输入 Industry ID: ")

    if not all([cid, key, user_id, industry_id]):
        logging.error("缺少必要参数，程序退出")
        print("❌ 错误：缺少参数，10秒后程序退出。")
        time.sleep(10)
        return

    logging.info(f"开始获取公司数据 (Company ID: {cid})")
    print(f"📡 正在连接 API 获取公司数据 (ID: {cid})...")
    company_res = fetch_company_data(cid, key)
    if "error" in company_res:
        print(f"❌ API 错误: {company_res['error']}")
        logging.error(f"API 错误: {company_res['error']}")
        time.sleep(10)
        return

    logging.info(f"开始获取用户股票与教育数据 (User ID: {user_id})")
    print(f"📡 正在获取用户股票与教育数据 (User ID: {user_id})...")
    user_res = fetch_user_data(user_id, key)
    if "error" in user_res:
        print(f"⚠️ 用户数据获取失败: {user_res.get('error')}")
        logging.warning(f"用户数据获取失败: {user_res.get('error')}")

    logging.info(f"开始处理行业数据 (Industry ID: {industry_id})")
    print(f"📡 正在获取行业数据 (Industry ID: {industry_id})...")
    industry_res = fetch_industry_data(industry_id, key)
    if "error" in industry_res:
        print(f"⚠️ 行业数据获取失败: {industry_res.get('error')}")
        logging.warning(f"行业数据获取失败: {industry_res.get('error')}")

    df_emp = get_employees(company_res)
    df_inc = get_latest_gross_income(company_res)
    df_comp = get_company_detailed(company_res)
    df_stock = get_company_stock(company_res)

    if df_emp.empty:
        print("❌ 错误：未能获取员工信息。")
        logging.error("未能获取员工信息。")
        time.sleep(10)
        return

    if df_inc.empty or 'torn_time' not in df_inc.columns:
        print("❌ 错误：未能获取公司收入信息或缺少 torn_time 字段。")
        logging.error("未能获取公司收入信息或缺少 torn_time 字段。")
        time.sleep(10)
        return

    today_date = df_inc['torn_time'].dt.date.iloc[0]
    print(f"📅 目标日期: {today_date}")
    logging.info(f"目标日期: {today_date}")

    logging.info("开始处理员工效率数据并生成每日记录...")
    if 'eff_total' not in df_emp.columns:
        df_emp['eff_total'] = 0
    df_sorted = df_emp.sort_values(
        ['position', 'eff_total'], ascending=[True, False])
    df_sorted['pos_rank'] = df_sorted.groupby('position').cumcount() + 1
    df_sorted['position'] = df_sorted['position'].astype(str) + \
        df_sorted['pos_rank'].astype(str)

    daily_data = df_sorted[['position', 'eff_total']].copy()
    daily_data.rename(columns={'eff_total': 'Efficiency_Sum'}, inplace=True)
    daily_data['日期'] = today_date

    metrics = pd.DataFrame([
        {"position": "合计效率",
            "Efficiency_Sum": df_emp['eff_total'].sum(), "日期": today_date},
        {"position": "环境 (%)", "Efficiency_Sum": df_comp['environment'].iloc[0]
         if not df_comp.empty else 0, "日期": today_date},
        {"position": "广告费 (M)", "Efficiency_Sum": (
            df_comp['advertising_budget'].iloc[0]/1000000) if not df_comp.empty else 0, "日期": today_date},
        {"position": "日收入",
            "Efficiency_Sum": df_inc['gross_income'].iloc[0], "日期": today_date}
    ])
    daily_data = pd.concat([daily_data, metrics], ignore_index=True)
    logging.info(
        f"当日共处理 {len(df_emp)} 名员工，合计效率: {df_emp['eff_total'].sum():,.0f}")

    if os.path.exists(HISTORY_DB_PATH):
        history = pd.read_excel(HISTORY_DB_PATH)
        history['日期'] = pd.to_datetime(history['日期']).dt.date
        if today_date not in history['日期'].values:
            pd.concat([history, daily_data], ignore_index=True).to_excel(
                HISTORY_DB_PATH, index=False)
            print("✅ 历史数据已更新。")
            logging.info(f"历史数据已更新 → 新增日期 {today_date}")
        else:
            print(f"⚠️ 历史数据中已存在日期 {today_date}，跳过追加。")
            logging.info(f"历史数据中已存在日期 {today_date}，跳过追加")
    else:
        daily_data.to_excel(HISTORY_DB_PATH, index=False)
        print("✅ 初始历史记录已建立。")
        logging.info(f"初始历史记录已建立 → 日期 {today_date}")

    sheet_name_str = today_date.strftime("%Y-%m-%d")

    df_emp = parse_xan_rehab_stats(df_emp, key)
    logging.info("员工 Xanax 和 Rehabs 数据已获取并解析完成")
    df_emp = calculate_stat_day_avg(
        df_emp, today_date, EMPLOYEE_DB_PATH, 'xantaken')
    logging.info("员工 Xanax 日均增长数据已计算完成")
    df_emp = calculate_stat_day_avg(
        df_emp, today_date, EMPLOYEE_DB_PATH, 'rehabs')
    logging.info("员工 Rehabs 日均增长数据已计算完成")
    save_to_excel(EMPLOYEE_DB_PATH, df_emp, sheet_name_str)
    if not df_stock.empty:
        save_to_excel(STOCK_DB_PATH, df_stock, sheet_name_str)

    # 保存 User_Perks
    user_file = USER_PERK_DB_PATH
    df_perks = parse_user_perks(user_res)
    save_to_excel(user_file, df_perks, sheet_name_str, header=False)

    df_industry = get_industry_companies(industry_res)
    if not df_industry.empty:
        save_to_excel(INDUSTRY_DB_PATH, df_industry, sheet_name_str)

    generate_horizontal_report(
        HISTORY_DB_PATH, EFFICIENCY_REPORT_PATH, today_date)

    print(f"📊 同步完成！请查看 {DATABASE_DIR} 和 {REPORT_DIR} 文件夹内容。")
    print("程序结束，30秒后自动关闭。")
    time.sleep(30)


if __name__ == "__main__":
    main()
