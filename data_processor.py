import os
import logging
import pandas as pd
import re
from datetime import datetime

from api_client import fetch_xantaken
from config import MAX_XAN_DAYS, STOCK_MAP, EDUCATION_MAP


def get_company_detailed(response):
    details = response.get('company_detailed', {}).copy()
    if not details:
        return pd.DataFrame()
    upgrades = details.pop('upgrades', {})
    return pd.DataFrame([{**details, **upgrades}])


def get_employees(response):
    employees_dict = response.get('company_employees', {})
    if not employees_dict:
        return pd.DataFrame()
    rows = []
    for emp_id, details in employees_dict.items():
        row = {'EmployeeID': int(
            emp_id), **{k: v for k, v in details.items() if not isinstance(v, dict)}}
        eff_data = details.get('effectiveness', {})
        if isinstance(eff_data, dict):
            for k, v in eff_data.items():
                row[f'eff_{k}'] = v
        rows.append(row)
    return pd.DataFrame(rows)


def get_latest_gross_income(response):
    news = response.get('news', {})
    news_items = sorted([{'ts': v['timestamp'], 'text': v['news']}
                        for v in news.values()], key=lambda x: x['ts'], reverse=True)

    for item in news_items:
        cust = re.search(
            r'total of\s+([\d,]+)\s+customers', item['text'], re.I)
        inc = re.search(r'gross income of\s+\$?([\d,]+)', item['text'], re.I)
        if cust and inc:
            return pd.DataFrame([{
                'torn_time': datetime.fromtimestamp(item['ts']),
                'customers': int(cust.group(1).replace(',', '')),
                'gross_income': int(inc.group(1).replace(',', ''))
            }])

    timestamp = response.get('timestamp', datetime.now().timestamp())
    return pd.DataFrame([{
        'torn_time': datetime.fromtimestamp(timestamp),
        'customers': response.get('company', {}).get('daily_customers', 0),
        'gross_income': response.get('company', {}).get('daily_income', 0)
    }])


def get_company_stock(response):
    stock_dict = response.get('company_stock', {})
    if not stock_dict:
        return pd.DataFrame()
    rows = [{'Item': name, **details} for name, details in stock_dict.items()]
    return pd.DataFrame(rows)


def add_xan_stats(df_emp, api_key):
    if df_emp.empty:
        return df_emp

    print("📊 正在获取员工 Xanax 服用记录...")
    logging.info("开始获取员工  Xanax 服用数据")

    xan_list = []
    for idx, row in df_emp.iterrows():
        xan = fetch_xantaken(int(row['EmployeeID']), api_key)
        xan_list.append(xan)
        if (idx + 1) % 10 == 0:
            print(f"   已处理 {idx+1}/{len(df_emp)} 名员工...")

    df_emp = df_emp.copy()
    df_emp['xantaken'] = xan_list
    print(f"✅ Xanax 当日数据获取完成！")
    return df_emp


def get_xan_day_avg(df_emp, today_date, employee_db_path):
    """计算近x日 Xanax 日均"""
    xan_key = "xan_{}day_avg".format(MAX_XAN_DAYS)
    if df_emp.empty or 'xantaken' not in df_emp.columns:
        df_emp[xan_key] = "N/A"
        return df_emp

    try:
        if not os.path.exists(employee_db_path):
            df_emp[xan_key] = "N/A"
            return df_emp

        xls = pd.ExcelFile(employee_db_path)
        history = {}

        for sheet in xls.sheet_names:
            try:
                sheet_date = pd.to_datetime(sheet).date()
                if sheet_date >= today_date.date():
                    continue
                df = pd.read_excel(xls, sheet_name=sheet)
                if 'EmployeeID' in df.columns and 'xantaken' in df.columns:
                    history[sheet_date] = dict(
                        zip(df['EmployeeID'].astype(int), df['xantaken']))
            except:
                continue

        avg_list = []
        today = today_date.date() if isinstance(today_date, datetime) else today_date

        for _, row in df_emp.iterrows():
            emp_id = int(row['EmployeeID'])
            current = int(row['xantaken'])
            past_dates = sorted([d for d in history if d < today], reverse=True)[
                :MAX_XAN_DAYS]

            if not past_dates:
                avg_list.append("N/A")
                continue

            total_inc = 0
            valid_days = 0
            prev = current

            for d in past_dates:
                prev_val = history[d].get(emp_id)
                if prev_val is not None:
                    inc = prev - prev_val
                    if inc >= 0:
                        total_inc += inc
                        valid_days += 1
                    prev = prev_val

            avg_list.append(round(total_inc / valid_days, 2)
                            if valid_days > 0 else "N/A")

        df_emp = df_emp.copy()
        df_emp[xan_key] = avg_list
        return df_emp

    except Exception as e:
        logging.error(f"计算{MAX_XAN_DAYS}日平均失败: {e}")
        df_emp[xan_key] = "N/A"
        return df_emp


# === User_Perks 解析函数 ===
def parse_user_perks(user_data):
    """生成 User_Perks.xlsx - 已修复状态判断和合计逻辑"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")

    rows = []

    # ====================== 股票部分 ======================
    rows.append(['股票', '', ''])
    rows.append([date_str, '效果', '是否生效'])

    stocks = user_data.get('stocks', {})
    active_stock_effects = []

    for sid, (name, effect) in STOCK_MAP.items():
        sid_str = str(sid)
        info = stocks.get(sid_str, {})
        total_shares = info.get('total_shares', 0)
        benefit = info.get('benefit') or info.get('dividend', {})
        progress = benefit.get('progress', 0)
        frequency = benefit.get('frequency', 7)
        status = '是' if (total_shares > 0 and progress >= frequency) else '否'

        rows.append([name, effect, status])

        if status == '是':
            active_stock_effects.append((name, effect))

    # ====================== 教育部分 ======================
    rows.append(['', '', ''])
    rows.append(['教育', '', ''])
    rows.append([date_str, '效果', '是否生效'])

    completed = set(user_data.get('education_completed', []))
    bonus_summary = {"Productivity": 0.0, "Employee Effectiveness": 0.0,
                     "Perceived Product Value": 0.0, "Advertising": 0.0}

    non_numeric = []  # (课程编号, 效果描述)

    for eid, code, full_name, effect, category in EDUCATION_MAP.values():
        status = '是' if eid in completed else '否'
        rows.append([full_name, effect, status])

        if eid in completed:
            if category and "%" in effect:
                match = re.search(r'Gain (\d+)%', effect)
                if match:
                    val = int(match.group(1)) / 100.0
                    bonus_summary[category] += val
            else:
                non_numeric.append((code, effect))

    # ====================== 合计效果 ======================
    rows.append(['', '', ''])
    rows.append(['合计效果', '', ''])

    # 数值加成
    summary_labels = {
        "Productivity": "Productivity加成",
        "Employee Effectiveness": "Employee Effectiveness加成",
        "Perceived Product Value": "Perceived Product Value加成",
        "Advertising": "Advertising Effectiveness加成",
    }

    for cat, value in bonus_summary.items():
        if value > 0:
            rows.append(
                [summary_labels.get(cat, cat + "加成"), '', round(value, 4)])

    # 非数值加成
    for name, effect in active_stock_effects:
        rows.append([name, effect, ''])

    for code, effect in non_numeric:
        rows.append([code, effect, ''])

    return pd.DataFrame(rows)
