import time
import logging
import re
import pandas as pd

from config import get_session


def fetch_with_retry(url, max_retries=3, delay=20):
    """带重试的 API 请求"""
    session = get_session()
    log_url = re.sub(r'key=[^&]+', 'key=******', url)

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"正在请求: {log_url} (尝试 {attempt}/{max_retries})")
            print(f"📡 正在请求 API (尝试 {attempt}/{max_retries})...")

            response = session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'error' in data:
                error = data['error']
                code = error.get('code')
                msg = error.get('error', '未知错误')
                logging.error(f"Torn API 错误 [{code}]: {msg}")
                print(f"❌ Torn API 错误 [{code}]: {msg}")

                if code == 5:  # 限流
                    time.sleep(65)
                    continue
                return data

            logging.info("API 请求成功")
            return data

        except Exception as e:
            logging.warning(f"请求失败 (尝试 {attempt}): {e}")
            if attempt == max_retries:
                return {"error": str(e)}
            time.sleep(delay)

    return {"error": "未知错误"}


def fetch_company_data(company_id, api_key):
    url = f"https://api.torn.com/company/{company_id}?selections=detailed,employees,news,profile,timestamp,stock&key={api_key}"
    return fetch_with_retry(url)


def fetch_industry_data(industry_id, api_key):
    """使用 v2 API 分页获取行业全部公司数据"""
    all_companies = []
    offset = 0
    limit = 100
    companies_timestamp = None
    companies_delay = None

    while True:
        url = f"https://api.torn.com/v2/company/{industry_id}/companies?limit={limit}&offset={offset}&striptags=false&key={api_key}"
        response = fetch_with_retry(url)

        if "error" in response:
            return response

        companies = response.get("companies", [])
        all_companies.extend(companies)

        if companies_timestamp is None:
            companies_timestamp = response.get("companies_timestamp")
            companies_delay = response.get("companies_delay")

        # 检查是否有下一页
        links = response.get("_metadata", {}).get("links", {})
        next_url = links.get("next")
        if not next_url or len(companies) == 0:
            break

        offset += limit

    return {
        "companies": all_companies,
        "companies_timestamp": companies_timestamp,
        "companies_delay": companies_delay,
    }


def fetch_user_data(user_id, api_key):
    url = f"https://api.torn.com/user/{user_id}?selections=education,stocks&key={api_key}"
    return fetch_with_retry(url)


def fetch_employee_data(employee_id, api_key):
    url = f"https://api.torn.com/user/{employee_id}?selections=personalstats&key={api_key}"
    return fetch_with_retry(url)
