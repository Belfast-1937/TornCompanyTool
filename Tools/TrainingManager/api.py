# -*- coding: utf-8 -*-
"""Torn API 调用与员工数据解析"""
import time
import requests

from constants import API_URL_TEMPLATE, API_TIMEOUT, API_RETRY_WAIT, API_NETWORK_WAIT, API_MAX_RETRIES


def fetch_company_data(company_id, api_key):
    """调用 Torn API 获取公司数据。返回 JSON 字典；出错时返回包含 "error" 键的字典。"""
    url = API_URL_TEMPLATE.format(company_id=company_id, api_key=api_key)

    for attempt in range(1, API_MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'error' in data:
                error = data['error']
                code = error.get('code')
                msg = error.get('error', '未知错误')
                if code == 5:  # 限流
                    if attempt < API_MAX_RETRIES:
                        time.sleep(API_RETRY_WAIT)
                        continue
                return {"error": f"Torn API 错误 [{code}]: {msg}"}

            return data

        except requests.exceptions.RequestException as e:
            if attempt == API_MAX_RETRIES:
                return {"error": f"网络请求失败：{str(e)}"}
            time.sleep(API_NETWORK_WAIT)

    return {"error": "已达到最大重试次数"}


def parse_company_type(response):
    """从 API 返回的 JSON 中提取公司行业类型（company_type）。"""
    company = response.get('company', {})
    if isinstance(company, dict):
        return company.get('company_type')
    return None


def parse_employees(response):
    """
    从 API 返回的 JSON 中提取员工列表。
    API 返回结构中 manual_labor/intelligence/endurance 是员工顶层字段，
    effectiveness.total 是效率值。
    """
    employees_dict = response.get('company_employees', {})
    if not employees_dict:
        return []

    rows = []
    for emp_id, details in employees_dict.items():
        eff_data = details.get('effectiveness', {})
        eff_total = eff_data.get('total', 0) if isinstance(
            eff_data, dict) else 0

        rows.append({
            'EmployeeID': int(emp_id),
            'name': details.get('name', ''),
            'position': details.get('position', ''),
            'manual_labor': int(details.get('manual_labor', 0)),
            'intelligence': int(details.get('intelligence', 0)),
            'endurance': int(details.get('endurance', 0)),
            'eff_total': int(eff_total) if eff_total else 0,
        })

    return rows
