import time
import logging
import re
from config import get_session, MIN_INTERVAL

last_request_time = 0.0


def wait_for_rate_limit():
    """简单固定间隔限流"""
    global last_request_time
    current_time = time.time()

    if current_time - last_request_time < MIN_INTERVAL:
        sleep_time = MIN_INTERVAL - (current_time - last_request_time)
        time.sleep(sleep_time)

    last_request_time = time.time()


def fetch_with_retry(url, max_retries=3, delay=25):
    """核心请求函数（带重试 + 限流）"""
    session = get_session()
    # 隐藏key用于日志
    log_url = re.sub(r'key=[^&]+', 'key=******', url)

    for attempt in range(1, max_retries + 1):
        try:
            wait_for_rate_limit()

            logging.info(f"请求: {log_url} (尝试 {attempt}/{max_retries})")
            print(f"📡 请求 API (尝试 {attempt}/{max_retries})...")

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
                    print("⚠️ API限流，等待65秒...")
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


def fetch_industry_data(industry_id: int, api_key: str):
    """使用 v2 API 分页获取行业全部公司数据"""
    all_companies = []
    offset = 0
    limit = 100

    while True:
        url = f"https://api.torn.com/v2/company/{industry_id}/companies?limit={limit}&offset={offset}&striptags=false&key={api_key}"
        response = fetch_with_retry(url)

        if "error" in response:
            return response

        companies = response.get("companies", [])
        all_companies.extend(companies)

        # 检查是否有下一页
        links = response.get("_metadata", {}).get("links", {})
        next_url = links.get("next")
        if not next_url or len(companies) == 0:
            break

        offset += limit

    return {"companies": all_companies}


def fetch_company_profile(company_id: int, api_key: str):
    """获取公司详细信息"""
    # 只请求必要的 selections，大幅减少数据量和解析负担
    url = f"https://api.torn.com/company/{company_id}?selections=profile&key={api_key}"
    return fetch_with_retry(url)


def fetch_player_profile(player_id, api_key):
    url = f"https://api.torn.com/user/{player_id}?selections=profile&key={api_key}"
    return fetch_with_retry(url)
