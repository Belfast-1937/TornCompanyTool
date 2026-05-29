#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torn City 员工训练规划工具
独立的 Python GUI 应用程序，用于规划公司员工的最优训练岗位。
"""

import math
import json
import os
import time
import threading
from datetime import datetime
import sys

# --- 检查依赖 ---
try:
    import requests
except ImportError:
    print("请先安装 requests 库: pip install requests")
    sys.exit(1)

import tkinter as tk
from tkinter import ttk, messagebox


def get_script_dir():
    """兼容 Windows/Linux/macOS + PyInstaller"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ============================================================
# 一、硬编码公司岗位数据（39 家公司）
# ============================================================
COMPANIES_DATA = {
    1: {
        "company_name": "Hair Salon",
        "jobs": [
            {"name": "Stylist", "primary_req_stat": "MAN", "primary_req_value": 1500, "secondary_req_stat": "END",
                "secondary_req_value": 750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Colorist", "primary_req_stat": "MAN", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Nail Technician", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "MAN",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Apprentice", "primary_req_stat": "MAN", "primary_req_value": 500, "secondary_req_stat": "END",
                "secondary_req_value": 250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Shampooist", "primary_req_stat": "MAN", "primary_req_value": 1000, "secondary_req_stat": "END",
                "secondary_req_value": 500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Senior Stylist", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 2500, "secondary_req_stat": "INT",
                "secondary_req_value": 1250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Aesthetician", "primary_req_stat": "INT", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    2: {
        "company_name": "Law Firm",
        "jobs": [
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 5500, "secondary_req_stat": "END",
                "secondary_req_value": 2750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 22000, "secondary_req_stat": "END",
                "secondary_req_value": 11000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Consultant", "primary_req_stat": "INT", "primary_req_value": 33000, "secondary_req_stat": "END",
                "secondary_req_value": 16500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Secretary", "primary_req_stat": "END", "primary_req_value": 16500, "secondary_req_stat": "INT",
                "secondary_req_value": 8250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Assistant", "primary_req_stat": "END", "primary_req_value": 5500, "secondary_req_stat": "INT",
                "secondary_req_value": 2750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Attorney", "primary_req_stat": "INT", "primary_req_value": 11000, "secondary_req_stat": "END",
                "secondary_req_value": 5500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    3: {
        "company_name": "Flower Shop",
        "jobs": [
            {"name": "Florist", "primary_req_stat": "END", "primary_req_value": 1000, "secondary_req_stat": "MAN",
                "secondary_req_value": 500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Arranger", "primary_req_stat": "INT", "primary_req_value": 1000, "secondary_req_stat": "MAN",
                "secondary_req_value": 500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Apprentice", "primary_req_stat": "END", "primary_req_value": 500, "secondary_req_stat": "MAN",
                "secondary_req_value": 250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 500, "secondary_req_stat": "END",
                "secondary_req_value": 250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 2000, "secondary_req_stat": "INT",
                "secondary_req_value": 1000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "INT",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
        ]
    },
    4: {
        "company_name": "Car Dealership",
        "jobs": [
            {"name": "Training Adviser", "primary_req_stat": "INT", "primary_req_value": 63000, "secondary_req_stat": "END",
                "secondary_req_value": 31500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 42000, "secondary_req_stat": "INT",
                "secondary_req_value": 21000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Webmaster", "primary_req_stat": "INT", "primary_req_value": 42000, "secondary_req_stat": "END",
                "secondary_req_value": 21000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 31500, "secondary_req_stat": "INT",
                "secondary_req_value": 15750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Mechanic", "primary_req_stat": "MAN", "primary_req_value": 26500, "secondary_req_stat": "END",
                "secondary_req_value": 13250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Sales Executive", "primary_req_stat": "INT", "primary_req_value": 21000, "secondary_req_stat": "END",
                "secondary_req_value": 10500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 10500, "secondary_req_stat": "END",
                "secondary_req_value": 5250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Sales Apprentice", "primary_req_stat": "INT", "primary_req_value": 5500, "secondary_req_stat": "END",
                "secondary_req_value": 2750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    5: {
        "company_name": "Clothing Store",
        "jobs": [
            {"name": "Line Manager", "primary_req_stat": "INT", "primary_req_value": 6000, "secondary_req_stat": "END",
                "secondary_req_value": 3000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Store Manager", "primary_req_stat": "END", "primary_req_value": 4000, "secondary_req_stat": "INT",
                "secondary_req_value": 2000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketing Manager", "primary_req_stat": "INT", "primary_req_value": 4000, "secondary_req_stat": "END",
                "secondary_req_value": 2000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "INT",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Security Guard", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Salesperson", "primary_req_stat": "INT", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Cashier", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "MAN",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1000, "secondary_req_stat": "END",
                "secondary_req_value": 500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Sales Trainee", "primary_req_stat": "INT", "primary_req_value": 500, "secondary_req_stat": "END",
                "secondary_req_value": 250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    6: {
        "company_name": "Gun Shop",
        "jobs": [
            {"name": "Clerk", "primary_req_stat": "END", "primary_req_value": 7500, "secondary_req_stat": "MAN",
                "secondary_req_value": 3750, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Gunsmith", "primary_req_stat": "MAN", "primary_req_value": 15000, "secondary_req_stat": "INT",
                "secondary_req_value": 7500, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 4000, "secondary_req_stat": "END",
                "secondary_req_value": 2000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 15000, "secondary_req_stat": "INT",
                "secondary_req_value": 7500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 11500, "secondary_req_stat": "INT",
                "secondary_req_value": 5750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 15000, "secondary_req_stat": "END",
                "secondary_req_value": 7500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Instructor", "primary_req_stat": "INT", "primary_req_value": 22500, "secondary_req_stat": "END",
                "secondary_req_value": 11250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    7: {
        "company_name": "Game Shop",
        "jobs": [
            {"name": "Clerk", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "MAN",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Game Advisor", "primary_req_stat": "INT", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1500, "secondary_req_stat": "END",
                "secondary_req_value": 750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Store Manager", "primary_req_stat": "END", "primary_req_value": 6000, "secondary_req_stat": "INT",
                "secondary_req_value": 3000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 4500, "secondary_req_stat": "INT",
                "secondary_req_value": 2250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 6000, "secondary_req_stat": "END",
                "secondary_req_value": 3000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    8: {
        "company_name": "Candle Shop",
        "jobs": [
            {"name": "Chandler", "primary_req_stat": "MAN", "primary_req_value": 4500, "secondary_req_stat": "INT",
                "secondary_req_value": 2250, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Quality Control", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "INT",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 2500, "secondary_req_stat": "INT",
                "secondary_req_value": 1250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Salesperson", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "INT",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1000, "secondary_req_stat": "END",
                "secondary_req_value": 500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    9: {
        "company_name": "Toy Shop",
        "jobs": [
            {"name": "Sales Assistant", "primary_req_stat": "END", "primary_req_value": 5000, "secondary_req_stat": "MAN",
                "secondary_req_value": 2500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 2500, "secondary_req_stat": "END",
                "secondary_req_value": 1250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Store Manager", "primary_req_stat": "END", "primary_req_value": 10000, "secondary_req_stat": "INT",
                "secondary_req_value": 5000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Office Clerk", "primary_req_stat": "END", "primary_req_value": 7500, "secondary_req_stat": "INT",
                "secondary_req_value": 3750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketing Executive", "primary_req_stat": "INT", "primary_req_value": 10000, "secondary_req_stat": "END",
                "secondary_req_value": 5000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Training Advisor", "primary_req_stat": "INT", "primary_req_value": 15000, "secondary_req_stat": "END",
                "secondary_req_value": 7500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Stock Clerk", "primary_req_stat": "MAN", "primary_req_value": 4000, "secondary_req_stat": "END",
                "secondary_req_value": 2000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    10: {
        "company_name": "Adult Novelties",
        "jobs": [
            {"name": "Human Resources", "primary_req_stat": "INT", "primary_req_value": 12000, "secondary_req_stat": "END",
                "secondary_req_value": 6000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Sexpert", "primary_req_stat": "INT", "primary_req_value": 10000, "secondary_req_stat": "END",
                "secondary_req_value": 5000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Store Manager", "primary_req_stat": "END", "primary_req_value": 8000, "secondary_req_stat": "INT",
                "secondary_req_value": 4000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketing Manager", "primary_req_stat": "INT", "primary_req_value": 8000, "secondary_req_stat": "END",
                "secondary_req_value": 4000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 6000, "secondary_req_stat": "INT",
                "secondary_req_value": 3000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Sales Assistant", "primary_req_stat": "END", "primary_req_value": 4000, "secondary_req_stat": "MAN",
                "secondary_req_value": 2000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    11: {
        "company_name": "Cyber Cafe",
        "jobs": [
            {"name": "Cashier", "primary_req_stat": "END", "primary_req_value": 10000, "secondary_req_stat": "INT",
                "secondary_req_value": 5000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 5000, "secondary_req_stat": "END",
                "secondary_req_value": 2500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 20000, "secondary_req_stat": "INT",
                "secondary_req_value": 10000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 15000, "secondary_req_stat": "INT",
                "secondary_req_value": 7500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 20000, "secondary_req_stat": "END",
                "secondary_req_value": 10000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Teacher", "primary_req_stat": "INT", "primary_req_value": 30000, "secondary_req_stat": "END",
                "secondary_req_value": 15000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Administrator", "primary_req_stat": "INT", "primary_req_value": 20000, "secondary_req_stat": "END",
                "secondary_req_value": 10000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Technician", "primary_req_stat": "INT", "primary_req_value": 17500, "secondary_req_stat": "MAN",
                "secondary_req_value": 8750, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
        ]
    },
    12: {
        "company_name": "Grocery Store",
        "jobs": [
            {"name": "Cashier", "primary_req_stat": "END", "primary_req_value": 6000, "secondary_req_stat": "MAN",
                "secondary_req_value": 3000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Stock Clerk", "primary_req_stat": "MAN", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 12000, "secondary_req_stat": "INT",
                "secondary_req_value": 6000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 9000, "secondary_req_stat": "INT",
                "secondary_req_value": 4500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 12000, "secondary_req_stat": "END",
                "secondary_req_value": 6000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 18000, "secondary_req_stat": "END",
                "secondary_req_value": 9000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Delivery Driver", "primary_req_stat": "MAN", "primary_req_value": 7500, "secondary_req_stat": "END",
                "secondary_req_value": 3750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cart Attendant", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    13: {
        "company_name": "Theater",
        "jobs": [
            {"name": "Ticketing Agent", "primary_req_stat": "END", "primary_req_value": 20000, "secondary_req_stat": "INT",
                "secondary_req_value": 10000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Technician", "primary_req_stat": "MAN", "primary_req_value": 60000, "secondary_req_stat": "INT",
                "secondary_req_value": 30000, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Programmer", "primary_req_stat": "INT", "primary_req_value": 50000, "secondary_req_stat": "END",
                "secondary_req_value": 25000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Janitor", "primary_req_stat": "MAN", "primary_req_value": 20000, "secondary_req_stat": "END",
                "secondary_req_value": 10000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 80000, "secondary_req_stat": "INT",
                "secondary_req_value": 40000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 60000, "secondary_req_stat": "INT",
                "secondary_req_value": 30000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketing Manager", "primary_req_stat": "INT", "primary_req_value": 80000, "secondary_req_stat": "END",
                "secondary_req_value": 40000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Usher", "primary_req_stat": "END", "primary_req_value": 20000, "secondary_req_stat": "MAN",
                "secondary_req_value": 10000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
        ]
    },
    14: {
        "company_name": "Sweet Shop",
        "jobs": [
            {"name": "Confectionist", "primary_req_stat": "INT", "primary_req_value": 2500, "secondary_req_stat": "END",
                "secondary_req_value": 1250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Packager", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "MAN",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1000, "secondary_req_stat": "END",
                "secondary_req_value": 500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 4000, "secondary_req_stat": "INT",
                "secondary_req_value": 2000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "INT",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 4000, "secondary_req_stat": "END",
                "secondary_req_value": 2000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Clerk", "primary_req_stat": "END", "primary_req_value": 2000, "secondary_req_stat": "MAN",
                "secondary_req_value": 1000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
        ]
    },
    15: {
        "company_name": "Cruise Line",
        "jobs": [
            {"name": "Captain", "primary_req_stat": "INT", "primary_req_value": 154500, "secondary_req_stat": "END",
                "secondary_req_value": 77250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "First Officer", "primary_req_stat": "INT", "primary_req_value": 105000, "secondary_req_stat": "END",
                "secondary_req_value": 52500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Doctor", "primary_req_stat": "INT", "primary_req_value": 103000, "secondary_req_stat": "END",
                "secondary_req_value": 51500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Specialist", "primary_req_stat": "INT", "primary_req_value": 90000, "secondary_req_stat": "END",
                "secondary_req_value": 45000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Bosun", "primary_req_stat": "END", "primary_req_value": 74000, "secondary_req_stat": "INT",
                "secondary_req_value": 37000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 72000, "secondary_req_stat": "END",
                "secondary_req_value": 36000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Chef", "primary_req_stat": "INT", "primary_req_value": 64500, "secondary_req_stat": "END",
                "secondary_req_value": 32250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Engineer", "primary_req_stat": "MAN", "primary_req_value": 54500, "secondary_req_stat": "INT",
                "secondary_req_value": 27250, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 42000, "secondary_req_stat": "INT",
                "secondary_req_value": 21000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Steward", "primary_req_stat": "END", "primary_req_value": 41500, "secondary_req_stat": "INT",
                "secondary_req_value": 20750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bartender", "primary_req_stat": "END", "primary_req_value": 38500, "secondary_req_stat": "MAN",
                "secondary_req_value": 19250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Deckhand", "primary_req_stat": "MAN", "primary_req_value": 26000, "secondary_req_stat": "END",
                "secondary_req_value": 13000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Ticket Agent", "primary_req_stat": "END", "primary_req_value": 26000, "secondary_req_stat": "INT",
                "secondary_req_value": 13000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
        ]
    },
    16: {
        "company_name": "Television Network",
        "jobs": [
            {"name": "Producer", "primary_req_stat": "INT", "primary_req_value": 99000, "secondary_req_stat": "END",
                "secondary_req_value": 49500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Programmer", "primary_req_stat": "INT", "primary_req_value": 66000, "secondary_req_stat": "END",
                "secondary_req_value": 33000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Camera Operator", "primary_req_stat": "INT", "primary_req_value": 49500, "secondary_req_stat": "MAN",
                "secondary_req_value": 24750, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Sales Executive", "primary_req_stat": "END", "primary_req_value": 49500, "secondary_req_stat": "INT",
                "secondary_req_value": 24750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 33000, "secondary_req_stat": "END",
                "secondary_req_value": 16500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Attorney", "primary_req_stat": "INT", "primary_req_value": 132000, "secondary_req_stat": "END",
                "secondary_req_value": 66000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Secretary", "primary_req_stat": "END", "primary_req_value": 99000, "secondary_req_stat": "INT",
                "secondary_req_value": 49500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 132000, "secondary_req_stat": "END",
                "secondary_req_value": 66000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Writer", "primary_req_stat": "INT", "primary_req_value": 115500, "secondary_req_stat": "END",
                "secondary_req_value": 57750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Stagehand", "primary_req_stat": "MAN", "primary_req_value": 33000, "secondary_req_stat": "END",
                "secondary_req_value": 16500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Anchor", "primary_req_stat": "INT", "primary_req_value": 132000, "secondary_req_stat": "END",
                "secondary_req_value": 66000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Reporter", "primary_req_stat": "INT", "primary_req_value": 82500, "secondary_req_stat": "END",
                "secondary_req_value": 41250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    18: {
        "company_name": "Zoo",
        "jobs": [
            {"name": "Zoo Keeper", "primary_req_stat": "MAN", "primary_req_value": 58000, "secondary_req_stat": "END",
                "secondary_req_value": 29000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Animal Trainer", "primary_req_stat": "INT", "primary_req_value": 72500, "secondary_req_stat": "MAN",
                "secondary_req_value": 36250, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Aquarist", "primary_req_stat": "END", "primary_req_value": 58000, "secondary_req_stat": "INT",
                "secondary_req_value": 29000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Intern", "primary_req_stat": "MAN", "primary_req_value": 14500, "secondary_req_stat": "END",
                "secondary_req_value": 7250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 116000, "secondary_req_stat": "INT",
                "secondary_req_value": 58000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 87000, "secondary_req_stat": "INT",
                "secondary_req_value": 43500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Photographer", "primary_req_stat": "INT", "primary_req_value": 116000, "secondary_req_stat": "END",
                "secondary_req_value": 58000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Consultant", "primary_req_stat": "INT", "primary_req_value": 174000, "secondary_req_stat": "END",
                "secondary_req_value": 87000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Veterinarian", "primary_req_stat": "INT", "primary_req_value": 116000, "secondary_req_stat": "MAN",
                "secondary_req_value": 58000, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Cashier", "primary_req_stat": "END", "primary_req_value": 29000, "secondary_req_stat": "INT",
                "secondary_req_value": 14500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
        ]
    },
    19: {
        "company_name": "Firework Stand",
        "jobs": [
            {"name": "Salesperson", "primary_req_stat": "END", "primary_req_value": 1000, "secondary_req_stat": "INT",
                "secondary_req_value": 500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Pyrotechnician", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "INT",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Picker  Packer", "primary_req_stat": "MAN", "primary_req_value": 500, "secondary_req_stat": "END",
                "secondary_req_value": 250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 2000, "secondary_req_stat": "INT",
                "secondary_req_value": 1000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "INT",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Advertising Manager", "primary_req_stat": "INT", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    20: {
        "company_name": "Property Broker",
        "jobs": [
            {"name": "Property Broker", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "INT",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Valuation Specialist", "primary_req_stat": "INT", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Associate Broker", "primary_req_stat": "END", "primary_req_value": 500, "secondary_req_stat": "INT",
                "secondary_req_value": 250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1000, "secondary_req_stat": "END",
                "secondary_req_value": 500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Team Manager", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "INT",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 2500, "secondary_req_stat": "INT",
                "secondary_req_value": 1250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Graphic Designer", "primary_req_stat": "INT", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Broker Support", "primary_req_stat": "INT", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    21: {
        "company_name": "Furniture Store",
        "jobs": [
            {"name": "Sales Clerk", "primary_req_stat": "END", "primary_req_value": 6500, "secondary_req_stat": "INT",
                "secondary_req_value": 3250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Delivery Driver", "primary_req_stat": "MAN", "primary_req_value": 8000, "secondary_req_stat": "END",
                "secondary_req_value": 4000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Apprentice", "primary_req_stat": "END", "primary_req_value": 1500, "secondary_req_stat": "INT",
                "secondary_req_value": 750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 3500, "secondary_req_stat": "END",
                "secondary_req_value": 1750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 13000, "secondary_req_stat": "INT",
                "secondary_req_value": 6500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 10000, "secondary_req_stat": "INT",
                "secondary_req_value": 5000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 13000, "secondary_req_stat": "END",
                "secondary_req_value": 6500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 19500, "secondary_req_stat": "END",
                "secondary_req_value": 9750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    22: {
        "company_name": "Gas Station",
        "jobs": [
            {"name": "Attendant", "primary_req_stat": "END", "primary_req_value": 26000, "secondary_req_stat": "INT",
                "secondary_req_value": 13000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 17500, "secondary_req_stat": "END",
                "secondary_req_value": 8750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 60000, "secondary_req_stat": "INT",
                "secondary_req_value": 30000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 40000, "secondary_req_stat": "END",
                "secondary_req_value": 20000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 70500, "secondary_req_stat": "END",
                "secondary_req_value": 35250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    23: {
        "company_name": "Music Store",
        "jobs": [
            {"name": "Sales Assistant", "primary_req_stat": "END", "primary_req_value": 3500, "secondary_req_stat": "INT",
                "secondary_req_value": 1750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Musician", "primary_req_stat": "INT", "primary_req_value": 9000, "secondary_req_stat": "MAN",
                "secondary_req_value": 4500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Sales Apprentice", "primary_req_stat": "END", "primary_req_value": 1000, "secondary_req_stat": "INT",
                "secondary_req_value": 500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Supervisor", "primary_req_stat": "END", "primary_req_value": 7000, "secondary_req_stat": "INT",
                "secondary_req_value": 3500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 5500, "secondary_req_stat": "INT",
                "secondary_req_value": 2750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 10500, "secondary_req_stat": "END",
                "secondary_req_value": 5250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    24: {
        "company_name": "Nightclub",
        "jobs": [
            {"name": "Bartender", "primary_req_stat": "END", "primary_req_value": 27000, "secondary_req_stat": "MAN",
                "secondary_req_value": 13500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Bouncer", "primary_req_stat": "MAN", "primary_req_value": 48000, "secondary_req_stat": "END",
                "secondary_req_value": 24000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Barback", "primary_req_stat": "END", "primary_req_value": 20500, "secondary_req_stat": "MAN",
                "secondary_req_value": 10250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 13500, "secondary_req_stat": "END",
                "secondary_req_value": 6750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 54000, "secondary_req_stat": "INT",
                "secondary_req_value": 27000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Personal Assistant", "primary_req_stat": "END", "primary_req_value": 40500, "secondary_req_stat": "INT",
                "secondary_req_value": 20250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Promoter", "primary_req_stat": "INT", "primary_req_value": 54000, "secondary_req_stat": "END",
                "secondary_req_value": 27000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 81000, "secondary_req_stat": "END",
                "secondary_req_value": 40500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Disk-jockey", "primary_req_stat": "INT", "primary_req_value": 40500, "secondary_req_stat": "END",
                "secondary_req_value": 20250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    25: {
        "company_name": "Pub",
        "jobs": [
            {"name": "Bartender", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "MAN",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Bouncer", "primary_req_stat": "MAN", "primary_req_value": 6000, "secondary_req_stat": "END",
                "secondary_req_value": 3000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Waiter", "primary_req_stat": "END", "primary_req_value": 3000, "secondary_req_stat": "MAN",
                "secondary_req_value": 1500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 1500, "secondary_req_stat": "END",
                "secondary_req_value": 750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 6000, "secondary_req_stat": "INT",
                "secondary_req_value": 3000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 4500, "secondary_req_stat": "INT",
                "secondary_req_value": 2250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 9000, "secondary_req_stat": "END",
                "secondary_req_value": 4500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Promoter", "primary_req_stat": "INT", "primary_req_value": 6000, "secondary_req_stat": "END",
                "secondary_req_value": 3000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    26: {
        "company_name": "Gents Strip Club",
        "jobs": [
            {"name": "Stripper", "primary_req_stat": "END", "primary_req_value": 14500, "secondary_req_stat": "MAN",
                "secondary_req_value": 7250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Security", "primary_req_stat": "MAN", "primary_req_value": 29000, "secondary_req_stat": "END",
                "secondary_req_value": 14500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 7500, "secondary_req_stat": "END",
                "secondary_req_value": 3750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 29000, "secondary_req_stat": "INT",
                "secondary_req_value": 14500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 22000, "secondary_req_stat": "INT",
                "secondary_req_value": 11000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Photographer", "primary_req_stat": "INT", "primary_req_value": 29000, "secondary_req_stat": "END",
                "secondary_req_value": 14500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    27: {
        "company_name": "Restaurant",
        "jobs": [
            {"name": "Waiter", "primary_req_stat": "END", "primary_req_value": 2500, "secondary_req_stat": "MAN",
                "secondary_req_value": 1250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Sous Chef", "primary_req_stat": "INT", "primary_req_value": 4000, "secondary_req_stat": "END",
                "secondary_req_value": 2000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Head Chef", "primary_req_stat": "END", "primary_req_value": 5000, "secondary_req_stat": "INT",
                "secondary_req_value": 2500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Kitchen Assistant", "primary_req_stat": "MAN", "primary_req_value": 1500, "secondary_req_stat": "END",
                "secondary_req_value": 750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Head Waiter", "primary_req_stat": "END", "primary_req_value": 4000, "secondary_req_stat": "INT",
                "secondary_req_value": 2000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Line Cook", "primary_req_stat": "INT", "primary_req_value": 2500, "secondary_req_stat": "MAN",
                "secondary_req_value": 1250, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Chef", "primary_req_stat": "INT", "primary_req_value": 3000, "secondary_req_stat": "MAN",
                "secondary_req_value": 1500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Apprentice Chef", "primary_req_stat": "INT", "primary_req_value": 1500, "secondary_req_stat": "MAN",
                "secondary_req_value": 750, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Dishwasher", "primary_req_stat": "MAN", "primary_req_value": 1500, "secondary_req_stat": "END",
                "secondary_req_value": 750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    28: {
        "company_name": "Oil Rig",
        "jobs": [
            {"name": "Driller", "primary_req_stat": "MAN", "primary_req_value": 150000, "secondary_req_stat": "INT",
                "secondary_req_value": 75000, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Roughneck", "primary_req_stat": "MAN", "primary_req_value": 75000, "secondary_req_stat": "END",
                "secondary_req_value": 37500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Derrick Hand", "primary_req_stat": "MAN", "primary_req_value": 94000, "secondary_req_stat": "END",
                "secondary_req_value": 47000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Secretary", "primary_req_stat": "END", "primary_req_value": 112500, "secondary_req_stat": "INT",
                "secondary_req_value": 56250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Inspector", "primary_req_stat": "INT", "primary_req_value": 225000, "secondary_req_stat": "END",
                "secondary_req_value": 112500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Sales Executive", "primary_req_stat": "INT", "primary_req_value": 131500, "secondary_req_stat": "END",
                "secondary_req_value": 65750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Motor Hand", "primary_req_stat": "MAN", "primary_req_value": 112500, "secondary_req_stat": "INT",
                "secondary_req_value": 56250, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
        ]
    },
    29: {
        "company_name": "Fitness Center",
        "jobs": [
            {"name": "Personal Trainer", "primary_req_stat": "MAN", "primary_req_value": 31000, "secondary_req_stat": "END",
                "secondary_req_value": 15500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Swimming Instructor", "primary_req_stat": "END", "primary_req_value": 46500, "secondary_req_stat": "MAN",
                "secondary_req_value": 23250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Lifeguard", "primary_req_stat": "END", "primary_req_value": 39000, "secondary_req_stat": "MAN",
                "secondary_req_value": 19500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 15500, "secondary_req_stat": "END",
                "secondary_req_value": 7750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 62000, "secondary_req_stat": "INT",
                "secondary_req_value": 31000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 10000, "secondary_req_stat": "INT",
                "secondary_req_value": 5000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 62000, "secondary_req_stat": "END",
                "secondary_req_value": 31000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Human Resources", "primary_req_stat": "END", "primary_req_value": 46500, "secondary_req_stat": "INT",
                "secondary_req_value": 23250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Nutritionist", "primary_req_stat": "INT", "primary_req_value": 54500, "secondary_req_stat": "MAN",
                "secondary_req_value": 27250, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Fitness Instructor", "primary_req_stat": "MAN", "primary_req_value": 46500, "secondary_req_stat": "END",
                "secondary_req_value": 23250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    30: {
        "company_name": "Mechanic Shop",
        "jobs": [
            {"name": "Technician", "primary_req_stat": "MAN", "primary_req_value": 8500, "secondary_req_stat": "END",
                "secondary_req_value": 4250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Apprentice Technician", "primary_req_stat": "MAN", "primary_req_value": 2000, "secondary_req_stat": "END",
                "secondary_req_value": 1000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 4500, "secondary_req_stat": "END",
                "secondary_req_value": 2250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 17000, "secondary_req_stat": "INT",
                "secondary_req_value": 8500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Receptionist", "primary_req_stat": "END", "primary_req_value": 13000, "secondary_req_stat": "INT",
                "secondary_req_value": 6500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Trainer", "primary_req_stat": "INT", "primary_req_value": 25500, "secondary_req_stat": "END",
                "secondary_req_value": 12750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    31: {
        "company_name": "Amusement Park",
        "jobs": [
            {"name": "Inspector", "primary_req_stat": "INT", "primary_req_value": 135000, "secondary_req_stat": "END",
                "secondary_req_value": 67500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 90000, "secondary_req_stat": "INT",
                "secondary_req_value": 45000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 90000, "secondary_req_stat": "END",
                "secondary_req_value": 45000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Security Guard", "primary_req_stat": "MAN", "primary_req_value": 79000, "secondary_req_stat": "END",
                "secondary_req_value": 39500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Mechanic", "primary_req_stat": "MAN", "primary_req_value": 67500, "secondary_req_stat": "INT",
                "secondary_req_value": 33750, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Accountant", "primary_req_stat": "END", "primary_req_value": 67500, "secondary_req_stat": "INT",
                "secondary_req_value": 33750, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Ride Attendant", "primary_req_stat": "END", "primary_req_value": 45000, "secondary_req_stat": "INT",
                "secondary_req_value": 22500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Entertainer", "primary_req_stat": "MAN", "primary_req_value": 34000, "secondary_req_stat": "END",
                "secondary_req_value": 17000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Ticket Agent", "primary_req_stat": "END", "primary_req_value": 22500, "secondary_req_stat": "INT",
                "secondary_req_value": 11250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Janitor", "primary_req_stat": "MAN", "primary_req_value": 22500, "secondary_req_stat": "END",
                "secondary_req_value": 11250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    32: {
        "company_name": "Lingerie Store",
        "jobs": [
            {"name": "Salesperson", "primary_req_stat": "END", "primary_req_value": 4500, "secondary_req_stat": "INT",
                "secondary_req_value": 2250, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 2500, "secondary_req_stat": "END",
                "secondary_req_value": 1250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Store Manager", "primary_req_stat": "END", "primary_req_value": 9000, "secondary_req_stat": "INT",
                "secondary_req_value": 4500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Lingerie Model", "primary_req_stat": "INT", "primary_req_value": 9000, "secondary_req_stat": "END",
                "secondary_req_value": 4500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Human Resources", "primary_req_stat": "INT", "primary_req_value": 13500, "secondary_req_stat": "END",
                "secondary_req_value": 6750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Trainee", "primary_req_stat": "END", "primary_req_value": 1000, "secondary_req_stat": "INT",
                "secondary_req_value": 500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
        ]
    },
    33: {
        "company_name": "Meat Warehouse",
        "jobs": [
            {"name": "Quality Controller", "primary_req_stat": "INT", "primary_req_value": 25000, "secondary_req_stat": "MAN",
                "secondary_req_value": 12500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Packer", "primary_req_stat": "MAN", "primary_req_value": 9500, "secondary_req_stat": "END",
                "secondary_req_value": 4750, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Apprentice Butcher", "primary_req_stat": "MAN", "primary_req_value": 3000, "secondary_req_stat": "END",
                "secondary_req_value": 1500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 6500, "secondary_req_stat": "END",
                "secondary_req_value": 3250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 25000, "secondary_req_stat": "INT",
                "secondary_req_value": 12500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Assistant", "primary_req_stat": "END", "primary_req_value": 19000, "secondary_req_stat": "INT",
                "secondary_req_value": 9500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Supervisor", "primary_req_stat": "INT", "primary_req_value": 37500, "secondary_req_stat": "END",
                "secondary_req_value": 18750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Butcher", "primary_req_stat": "MAN", "primary_req_value": 12500, "secondary_req_stat": "END",
                "secondary_req_value": 6250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Retailer", "primary_req_stat": "INT", "primary_req_value": 12500, "secondary_req_stat": "END",
                "secondary_req_value": 6250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    34: {
        "company_name": "Farm",
        "jobs": [
            {"name": "Harvester", "primary_req_stat": "MAN", "primary_req_value": 14000, "secondary_req_stat": "END",
                "secondary_req_value": 7000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Delivery Driver", "primary_req_stat": "MAN", "primary_req_value": 23000, "secondary_req_stat": "END",
                "secondary_req_value": 11500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Herdsperson", "primary_req_stat": "MAN", "primary_req_value": 18500, "secondary_req_stat": "END",
                "secondary_req_value": 9250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Farm Manager", "primary_req_stat": "END", "primary_req_value": 37000, "secondary_req_stat": "INT",
                "secondary_req_value": 18500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 28000, "secondary_req_stat": "INT",
                "secondary_req_value": 14000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Consultant", "primary_req_stat": "INT", "primary_req_value": 55500, "secondary_req_stat": "END",
                "secondary_req_value": 27750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Retailer", "primary_req_stat": "INT", "primary_req_value": 18500, "secondary_req_stat": "END",
                "secondary_req_value": 9250, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Dairy Farmer", "primary_req_stat": "MAN", "primary_req_value": 23000, "secondary_req_stat": "END",
                "secondary_req_value": 11500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Poultry Farmer", "primary_req_stat": "MAN", "primary_req_value": 18500, "secondary_req_stat": "END",
                "secondary_req_value": 9250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
        ]
    },
    35: {
        "company_name": "Software Corporation",
        "jobs": [
            {"name": "Developer", "primary_req_stat": "INT", "primary_req_value": 24000, "secondary_req_stat": "END",
                "secondary_req_value": 12000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Tester", "primary_req_stat": "INT", "primary_req_value": 12000, "secondary_req_stat": "END",
                "secondary_req_value": 6000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Graphic Designer", "primary_req_stat": "INT", "primary_req_value": 18000, "secondary_req_stat": "END",
                "secondary_req_value": 9000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Apprentice", "primary_req_stat": "INT", "primary_req_value": 6000, "secondary_req_stat": "END",
                "secondary_req_value": 3000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 12000, "secondary_req_stat": "END",
                "secondary_req_value": 6000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Lead Developer", "primary_req_stat": "END", "primary_req_value": 48000, "secondary_req_stat": "INT",
                "secondary_req_value": 24000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Analyst", "primary_req_stat": "END", "primary_req_value": 36000, "secondary_req_stat": "INT",
                "secondary_req_value": 18000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Marketer", "primary_req_stat": "INT", "primary_req_value": 48000, "secondary_req_stat": "END",
                "secondary_req_value": 24000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Consultant", "primary_req_stat": "INT", "primary_req_value": 72000, "secondary_req_stat": "END",
                "secondary_req_value": 36000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    36: {
        "company_name": "Ladies Strip Club",
        "jobs": [
            {"name": "Male Stripper", "primary_req_stat": "END", "primary_req_value": 14500, "secondary_req_stat": "MAN",
                "secondary_req_value": 7250, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Security", "primary_req_stat": "MAN", "primary_req_value": 29000, "secondary_req_stat": "END",
                "secondary_req_value": 14500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Cleaner", "primary_req_stat": "MAN", "primary_req_value": 8500, "secondary_req_stat": "END",
                "secondary_req_value": 4250, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Manager", "primary_req_stat": "END", "primary_req_value": 33000, "secondary_req_stat": "INT",
                "secondary_req_value": 16500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Bookkeeper", "primary_req_stat": "END", "primary_req_value": 25000, "secondary_req_stat": "INT",
                "secondary_req_value": 12500, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
            {"name": "Photographer", "primary_req_stat": "INT", "primary_req_value": 33000, "secondary_req_stat": "END",
                "secondary_req_value": 16500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    37: {
        "company_name": "Private Security Firm",
        "jobs": [
            {"name": "Security Contractor", "primary_req_stat": "MAN", "primary_req_value": 70000, "secondary_req_stat": "END",
                "secondary_req_value": 35000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Team Leader", "primary_req_stat": "MAN", "primary_req_value": 110000, "secondary_req_stat": "END",
                "secondary_req_value": 55000, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Defence Consultant", "primary_req_stat": "INT", "primary_req_value": 135000, "secondary_req_stat": "END",
                "secondary_req_value": 67500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Spokesperson", "primary_req_stat": "INT", "primary_req_value": 80000, "secondary_req_stat": "END",
                "secondary_req_value": 40000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Company Liaison", "primary_req_stat": "END", "primary_req_value": 115000, "secondary_req_stat": "INT",
                "secondary_req_value": 57500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Chief Strategist", "primary_req_stat": "INT", "primary_req_value": 165000, "secondary_req_stat": "END",
                "secondary_req_value": 82500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Reconnaissance", "primary_req_stat": "MAN", "primary_req_value": 80000, "secondary_req_stat": "INT",
                "secondary_req_value": 40000, "primary_gain_stat": "MAN", "secondary_gain_stat": "INT"},
            {"name": "Disposal Engineer", "primary_req_stat": "INT", "primary_req_value": 85000, "secondary_req_stat": "END",
                "secondary_req_value": 42500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Armourer", "primary_req_stat": "END", "primary_req_value": 80000, "secondary_req_stat": "MAN",
                "secondary_req_value": 40000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Medic", "primary_req_stat": "INT", "primary_req_value": 90000, "secondary_req_stat": "END",
                "secondary_req_value": 45000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Comms Engineer", "primary_req_stat": "INT", "primary_req_value": 85000, "secondary_req_stat": "END",
                "secondary_req_value": 42500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    38: {
        "company_name": "Mining Corporation",
        "jobs": [
            {"name": "Sales Executive", "primary_req_stat": "INT", "primary_req_value": 83000, "secondary_req_stat": "END",
                "secondary_req_value": 41500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Mill Operator", "primary_req_stat": "MAN", "primary_req_value": 75000, "secondary_req_stat": "END",
                "secondary_req_value": 37500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Production Foreman", "primary_req_stat": "END", "primary_req_value": 79000, "secondary_req_stat": "MAN",
                "secondary_req_value": 39500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Mine Engineer", "primary_req_stat": "INT", "primary_req_value": 81000, "secondary_req_stat": "END",
                "secondary_req_value": 40500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Electrician", "primary_req_stat": "END", "primary_req_value": 78000, "secondary_req_stat": "MAN",
                "secondary_req_value": 39000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Safety Inspector", "primary_req_stat": "INT", "primary_req_value": 95000, "secondary_req_stat": "MAN",
                "secondary_req_value": 47500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Site Manager", "primary_req_stat": "INT", "primary_req_value": 97000, "secondary_req_stat": "END",
                "secondary_req_value": 48750, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Secretary", "primary_req_stat": "END", "primary_req_value": 78000, "secondary_req_stat": "INT",
                "secondary_req_value": 39000, "primary_gain_stat": "END", "secondary_gain_stat": "INT"},
        ]
    },
    39: {
        "company_name": "Detective Agency",
        "jobs": [
            {"name": "Private Investigator", "primary_req_stat": "INT", "primary_req_value": 45500, "secondary_req_stat": "MAN",
                "secondary_req_value": 22500, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Trainee Investigator", "primary_req_stat": "INT", "primary_req_value": 28000, "secondary_req_stat": "MAN",
                "secondary_req_value": 14000, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Secretary", "primary_req_stat": "END", "primary_req_value": 25000, "secondary_req_stat": "MAN",
                "secondary_req_value": 12500, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Intelligence Analyst", "primary_req_stat": "INT", "primary_req_value": 58000, "secondary_req_stat": "END",
                "secondary_req_value": 29000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Surveillance", "primary_req_stat": "INT", "primary_req_value": 52000, "secondary_req_stat": "MAN",
                "secondary_req_value": 26000, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Chief Investigator", "primary_req_stat": "INT", "primary_req_value": 80000, "secondary_req_stat": "MAN",
                "secondary_req_value": 40000, "primary_gain_stat": "INT", "secondary_gain_stat": "MAN"},
            {"name": "Client Liaison", "primary_req_stat": "INT", "primary_req_value": 62000, "secondary_req_stat": "END",
                "secondary_req_value": 31000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
    40: {
        "company_name": "Logistics Management",
        "jobs": [
            {"name": "Lumper", "primary_req_stat": "MAN", "primary_req_value": 45000, "secondary_req_stat": "END",
                "secondary_req_value": 22500, "primary_gain_stat": "MAN", "secondary_gain_stat": "END"},
            {"name": "Driver", "primary_req_stat": "END", "primary_req_value": 57500, "secondary_req_stat": "MAN",
                "secondary_req_value": 28750, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Forklift Operator", "primary_req_stat": "END", "primary_req_value": 60000, "secondary_req_stat": "MAN",
                "secondary_req_value": 30000, "primary_gain_stat": "END", "secondary_gain_stat": "MAN"},
            {"name": "Transport Coordinator", "primary_req_stat": "INT", "primary_req_value": 85000, "secondary_req_stat": "END",
                "secondary_req_value": 42500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Warehouse Manager", "primary_req_stat": "INT", "primary_req_value": 115000, "secondary_req_stat": "END",
                "secondary_req_value": 57500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Shift Manager", "primary_req_stat": "INT", "primary_req_value": 90000, "secondary_req_stat": "END",
                "secondary_req_value": 45000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Supply Chain Manager", "primary_req_stat": "INT", "primary_req_value": 125000, "secondary_req_stat": "END",
                "secondary_req_value": 62500, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
            {"name": "Procurement Manager", "primary_req_stat": "INT", "primary_req_value": 140000, "secondary_req_stat": "END",
                "secondary_req_value": 70000, "primary_gain_stat": "INT", "secondary_gain_stat": "END"},
        ]
    },
}


# ============================================================
# 二、效率计算函数
# ============================================================
def calculate_efficiency(p_stat: int, p_req: int, s_stat: int, s_req: int) -> float:
    """计算员工在当前属性下对某岗位的效率值。"""
    try:
        p_base = min(45, (p_stat / p_req) * 45) if p_req > 0 else 0
        s_base = min(45, (s_stat / s_req) * 45) if s_req > 0 else 0
        p_bonus = max(0, 5 * math.log2(p_stat / p_req)
                      ) if p_stat > p_req and p_req > 0 else 0
        s_bonus = max(0, 5 * math.log2(s_stat / s_req)
                      ) if s_stat > s_req and s_req > 0 else 0
        return p_base + s_base + p_bonus + s_bonus
    except:
        return 0.0


# ============================================================
# 三、Torn API 调用逻辑
# ============================================================
def fetch_company_data(company_id, api_key):
    """
    调用 Torn API 获取公司数据。
    返回 JSON 字典；出错时返回包含 "error" 键的字典。
    """
    url = f"https://api.torn.com/company/{company_id}?selections=employees&key={api_key}"
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'error' in data:
                error = data['error']
                code = error.get('code')
                msg = error.get('error', '未知错误')
                if code == 5:  # 限流
                    if attempt < max_retries:
                        time.sleep(65)
                        continue
                return {"error": f"Torn API 错误 [{code}]: {msg}"}

            return data

        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                return {"error": f"网络请求失败：{str(e)}"}
            time.sleep(20)

    return {"error": "已达到最大重试次数"}


def parse_employees(response):
    """
    从 API 返回的 JSON 中提取员工列表。
    API 返回结构中 manual_labor/intelligence/endurance 是员工顶层字段，
    effectiveness.total 是效率值。
    返回 list[dict]，每个 dict 包含：
        EmployeeID, name, position, manual_labor, intelligence, endurance, eff_total
    """
    employees_dict = response.get('company_employees', {})
    if not employees_dict:
        return []

    rows = []
    for emp_id, details in employees_dict.items():
        eff_data = details.get('effectiveness', {})
        eff_total = eff_data.get('total', 0) if isinstance(
            eff_data, dict) else 0

        row = {
            'EmployeeID': int(emp_id),
            'name': details.get('name', ''),
            'position': details.get('position', ''),
            # 属性值在员工对象的顶层
            'manual_labor': int(details.get('manual_labor', 0)),
            'intelligence': int(details.get('intelligence', 0)),
            'endurance': int(details.get('endurance', 0)),
            'eff_total': int(eff_total) if eff_total else 0,
        }
        rows.append(row)

    return rows


# ============================================================
# 四、训练规划引擎
# ============================================================
def get_emp_stats(emp):
    """获取员工的三个属性值字典。"""
    return {
        "MAN": emp.get('manual_labor', 0),
        "INT": emp.get('intelligence', 0),
        "END": emp.get('endurance', 0),
    }


def simulate_train(stats, gain_primary_stat, gain_secondary_stat):
    """
    模拟训练一天后的属性值。
    主增益属性 +50，副增益属性 +25，其余不变。
    返回新的 stats 字典。
    """
    new_stats = dict(stats)
    if gain_primary_stat in new_stats:
        new_stats[gain_primary_stat] += 50
    if gain_secondary_stat in new_stats:
        new_stats[gain_secondary_stat] += 25
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
            "all_results": [(job_name, primary_gain, secondary_gain, improvement), ...]
        }
    """
    current_stats = get_emp_stats(emp)

    # 当前效率
    current_eff = calculate_efficiency(
        current_stats[target_job['primary_req_stat']],
        target_job['primary_req_value'],
        current_stats[target_job['secondary_req_stat']],
        target_job['secondary_req_value']
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
            target_job['secondary_req_value']
        )
        improvement = new_eff - current_eff
        results.append((job['name'], job['primary_gain_stat'],
                       job['secondary_gain_stat'], improvement))

        if improvement > best_improvement:
            best_improvement = improvement
            best_job_name = job['name']

    # 按 improvement 降序排序
    results.sort(key=lambda x: x[3], reverse=True)

    return {
        "best_job_name": best_job_name,
        "best_improvement": best_improvement,
        "all_results": results,
        "current_eff": current_eff,
        "current_stats": current_stats,
    }


# ============================================================
# 五、配置管理
# ============================================================
SCRIPT_DIR = get_script_dir()
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")


def load_config():
    """加载配置文件。"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(api_key, user_id, company_id="", company_type=None):
    """保存配置文件。"""
    config = {
        "api_key": api_key,
        "user_id": user_id,
        "company_id": company_id,
    }
    if company_type is not None:
        config["company_type"] = company_type
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def clear_config():
    """清除配置文件。"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

# ============================================================
# 六、报告生成
# ============================================================


def generate_report(company_name, target_company_id, employees_data, plan_results):
    """
    生成训练规划 TXT 报告。

    参数:
        company_name: 公司名称
        target_company_id: 公司 ID
        employees_data: 员工列表
        plan_results: list[dict]，每个 dict 包含 emp, target_job_name, plan

    返回:
        报告文件路径
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
                f"最终需求 → 主: {target_job['primary_req_stat']} ({target_job['primary_req_value']}) | 副: {target_job['secondary_req_stat']} ({target_job['secondary_req_value']})\n")
            f.write(f"\n")
            f.write(
                f"→ **最佳训练岗位: {plan['best_job_name']}** (效率提升 {plan['best_improvement']:.4f})\n")
            f.write(f"\n")
            f.write(f"训练岗位{'':20s}主属性   副属性   效率Δ\n")
            f.write(f"{'-' * 50}\n")
            for job_name, p_gain, s_gain, imp in plan['all_results']:
                f.write(f"{job_name:<30s}{p_gain:<10s}{s_gain:<10s}{imp:.4f}\n")
            f.write(f"\n")

    return filepath


# ============================================================
# 七、GUI 应用
# ============================================================
class TrainingPlannerApp:
    """Torn City 员工训练规划工具 GUI 应用。"""

    def __init__(self, root):
        self.root = root
        self.root.title("Torn City 员工训练规划工具")
        self.root.geometry("1100x700")
        self.root.minsize(900, 500)

        # 状态变量
        self.employees_data = []  # 从 API 获取的员工数据
        self.company_job_names = []  # 当前公司的岗位名称列表

        self._build_ui()
        self._load_config()

    # ---- UI 构建 ----

    def _build_ui(self):
        """构建完整 GUI 界面。"""
        # --- 顶部控制栏（两行布局） ---
        top_frame = ttk.Frame(self.root, padding="10 10 10 5")
        top_frame.pack(fill=tk.X)

        # --- 第一行 ---
        # 公司类型下拉框（行业ID，对应 Excel 中的 Sheet 序号）
        ttk.Label(top_frame, text="公司类型:").grid(
            row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.company_var = tk.StringVar()
        self.company_combo = ttk.Combobox(
            top_frame, textvariable=self.company_var, state="readonly", width=28)
        company_list = [
            f"{cid} - {data['company_name']}" for cid, data in COMPANIES_DATA.items()]
        self.company_combo['values'] = company_list
        if company_list:
            self.company_combo.current(0)
        self.company_combo.grid(row=0, column=1, padx=(0, 15), sticky=tk.W)
        self.company_combo.bind('<<ComboboxSelected>>',
                                self._on_company_changed)

        # 公司ID（手动输入，对应 Torn 中具体公司的 ID）
        ttk.Label(top_frame, text="公司 ID:").grid(
            row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.company_id_var = tk.StringVar()
        self.company_id_entry = ttk.Entry(
            top_frame, textvariable=self.company_id_var, width=10)
        self.company_id_entry.grid(row=0, column=3, padx=(0, 15), sticky=tk.W)

        # API Key
        ttk.Label(top_frame, text="API:").grid(
            row=0, column=4, padx=(0, 5), sticky=tk.W)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            top_frame, textvariable=self.api_key_var, show="*", width=30)
        self.api_key_entry.grid(row=0, column=5, padx=(0, 15), sticky=tk.W)

        # --- 第二行 ---
        # User ID
        ttk.Label(top_frame, text="用户 ID:").grid(
            row=1, column=0, padx=(0, 5), sticky=tk.W, pady=(8, 0))
        self.user_id_var = tk.StringVar()
        self.user_id_entry = ttk.Entry(
            top_frame, textvariable=self.user_id_var, width=15)
        self.user_id_entry.grid(row=1, column=1, padx=(
            0, 15), sticky=tk.W, pady=(8, 0))

        # 保存配置
        self.save_btn = ttk.Button(
            top_frame, text="保存配置", command=self._save_config)
        self.save_btn.grid(row=1, column=2, padx=(0, 5), pady=(8, 0))

        # 清除配置
        self.clear_btn = ttk.Button(
            top_frame, text="清除配置", command=self._clear_config)
        self.clear_btn.grid(row=1, column=3, pady=(8, 0))

        # --- 中部操作区 ---
        mid_frame = ttk.Frame(self.root, padding="10 5 10 5")
        mid_frame.pack(fill=tk.X)

        self.fetch_btn = ttk.Button(
            mid_frame, text="拉取员工数据", command=self._fetch_employees)
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 20))

        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(
            mid_frame, textvariable=self.status_var, foreground="gray")
        self.status_label.pack(side=tk.LEFT)

        # --- 表格区域 ---
        table_frame = ttk.Frame(self.root, padding="10 5 10 5")
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 定义列
        columns = ("employee_id", "name", "current_position",
                   "eff_total", "target_position")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("employee_id", text="员工ID")
        self.tree.column("employee_id", width=80, anchor=tk.CENTER)
        self.tree.heading("name", text="姓名")
        self.tree.column("name", width=120)
        self.tree.heading("current_position", text="当前岗位")
        self.tree.column("current_position", width=150)
        self.tree.heading("eff_total", text="当前效率")
        self.tree.column("eff_total", width=100, anchor=tk.CENTER)
        self.tree.heading("target_position", text="期待岗位")
        self.tree.column("target_position", width=180)

        # 滚动条
        tree_scroll_y = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(
            table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set,
                            xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Combobox 随滚动同步刷新
        self.tree.bind("<ButtonRelease-1>",
                       lambda e: self.root.after(100, self._refresh_combos))
        self.tree.bind("<MouseWheel>", lambda e: self.root.after(
            100, self._refresh_combos))

        # --- 底部操作区 ---
        bottom_frame = ttk.Frame(self.root, padding="10 5 10 10")
        bottom_frame.pack(fill=tk.X)

        self.plan_btn = ttk.Button(
            bottom_frame, text="规划训练", command=self._plan_training)
        self.plan_btn.pack(side=tk.LEFT)

    # ---- 事件处理 ----

    def _on_company_changed(self, event=None):
        """公司切换时更新期待岗位列表。"""
        self._update_job_names()

    def _update_job_names(self):
        """根据当前选中的公司更新岗位名称列表。"""
        company_id = self._get_selected_company_id()
        if company_id and company_id in COMPANIES_DATA:
            data = COMPANIES_DATA[company_id]
            self.company_job_names = [job['name'] for job in data['jobs']]
        else:
            self.company_job_names = []

    def _get_selected_company_id(self):
        """获取当前选中的公司 ID。"""
        val = self.company_var.get()
        if " - " in val:
            try:
                return int(val.split(" - ")[0])
            except:
                return None
        return None

    def _load_config(self):
        """从 config.json 加载配置。"""
        config = load_config()
        if config:
            if 'api_key' in config:
                self.api_key_var.set(config['api_key'])
            if 'user_id' in config:
                self.user_id_var.set(config['user_id'])
            if 'company_id' in config:
                self.company_id_var.set(config['company_id'])
            if 'company_type' in config:
                # 尝试恢复公司类型下拉框选择
                for i, val in enumerate(self.company_combo['values']):
                    if val.startswith(str(config['company_type']) + " - "):
                        self.company_combo.current(i)
                        self._on_company_changed()
                        break

    def _save_config(self):
        """保存当前配置。"""
        api_key = self.api_key_var.get().strip()
        user_id = self.user_id_var.get().strip()
        company_id = self.company_id_var.get().strip()
        company_type = self._get_selected_company_id()
        config = {
            "api_key": api_key,
            "user_id": user_id,
            "company_id": company_id,
        }
        if company_type is not None:
            config["company_type"] = company_type
        save_config(api_key, user_id, company_id, company_type)
        messagebox.showinfo("成功", "配置已保存到 config.json")

    def _clear_config(self):
        """清除配置。"""
        self.api_key_var.set("")
        self.user_id_var.set("")
        self.company_id_var.set("")
        clear_config()
        messagebox.showinfo("成功", "配置已清除")

    # ---- 拉取员工数据 ----

    def _fetch_employees(self):
        """拉取员工数据按钮回调。使用手动输入的公司ID调用 API。"""
        # 公司类型下拉框用于获取岗位数据模板
        company_type = self._get_selected_company_id()
        if company_type is None:
            messagebox.showerror("错误", "请先选择一个公司类型")
            return

        # 公司ID 用于 Torn API 调用
        tornado_company_id_str = self.company_id_var.get().strip()
        if not tornado_company_id_str:
            messagebox.showerror("错误", "请输入公司ID（Torn 中的公司 ID）")
            return
        try:
            tornado_company_id = int(tornado_company_id_str)
        except ValueError:
            messagebox.showerror("错误", "公司ID 必须是数字")
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入 API Key")
            return

        # 禁用按钮，显示加载状态
        self.fetch_btn.configure(state=tk.DISABLED)
        self.plan_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在拉取员工数据...")
        self.root.update()

        def worker():
            response = fetch_company_data(tornado_company_id, api_key)
            if "error" in response:
                self.root.after(
                    0, lambda: self._on_fetch_error(response["error"]))
            else:
                employees = parse_employees(response)
                self.root.after(0, lambda: self._on_fetch_success(employees))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, employees):
        """拉取成功回调。"""
        self.employees_data = employees
        self._update_job_names()
        self._populate_table()

        self.fetch_btn.configure(state=tk.NORMAL)
        self.plan_btn.configure(state=tk.NORMAL)
        self.status_var.set(f"成功获取 {len(employees)} 名员工数据")
        self.status_label.configure(foreground="green")

    def _on_fetch_error(self, error_msg):
        """拉取失败回调。"""
        self.fetch_btn.configure(state=tk.NORMAL)
        self.plan_btn.configure(state=tk.NORMAL)
        self.status_var.set("获取失败")
        self.status_label.configure(foreground="red")
        messagebox.showerror("API 请求失败", error_msg)

    # ---- 表格操作 ----

    def _populate_table(self):
        """填充员工表格。"""
        # 清空现有行和 combobox 控件
        self._clear_combos()
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.employees_data:
            return

        for emp in self.employees_data:
            # 默认期待岗位：优先选择当前岗位，否则选第一个
            target_pos = emp.get('position', '')
            if target_pos not in self.company_job_names:
                target_pos = self.company_job_names[0] if self.company_job_names else ''

            row_id = self.tree.insert("", tk.END, values=(
                emp.get('EmployeeID', ''),
                emp.get('name', ''),
                emp.get('position', ''),
                f"{emp.get('eff_total', 0):.2f}" if emp.get(
                    'eff_total') is not None else "N/A",
                target_pos,
            ))
            # 为该行期待岗位列创建常驻 Combobox
            self._create_combo_for_row(row_id, target_pos)

    def _clear_combos(self):
        """移除所有已放置的 Combobox 控件。"""
        if hasattr(self, '_row_combos'):
            for combo in self._row_combos:
                combo.destroy()
        self._row_combos = []

    def _create_combo_for_row(self, row_id, current_val):
        """为指定行创建期待岗位列的常驻 Combobox。"""
        if not hasattr(self, '_row_combos'):
            self._row_combos = []

        if not self.company_job_names:
            return

        # 获取期待岗位列的位置
        try:
            x, y, width, height = self.tree.bbox(row_id, "#5")
        except:
            return  # 行不可见，暂不创建

        combo = ttk.Combobox(
            self.tree, values=self.company_job_names, state="readonly")
        combo.place(x=x, y=y, width=width, height=height)
        if current_val in self.company_job_names:
            combo.set(current_val)
        else:
            combo.set(self.company_job_names[0])

        def on_select(event=None, rid=row_id, cb=combo):
            new_val = cb.get()
            values = list(self.tree.item(rid, "values"))
            values[4] = new_val
            self.tree.item(rid, values=values)

        combo.bind("<<ComboboxSelected>>", on_select)
        self._row_combos.append(combo)

    def _refresh_combos(self):
        """刷新所有行的 Combobox（在表格数据变化后调用）。"""
        self._clear_combos()
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            current_val = values[4] if len(values) >= 5 else ''
            self._create_combo_for_row(item_id, current_val)

    # ---- 规划训练 ----

    def _plan_training(self):
        """规划训练按钮回调。"""
        if not self.employees_data:
            messagebox.showerror("错误", "请先拉取员工数据")
            return

        company_id = self._get_selected_company_id()
        if company_id is None or company_id not in COMPANIES_DATA:
            messagebox.showerror("错误", "请选择有效的公司")
            return

        company_data = COMPANIES_DATA[company_id]
        company_name = company_data['company_name']
        all_jobs = company_data['jobs']

        # 建立岗位名称 -> 岗位数据的映射
        job_map = {job['name']: job for job in all_jobs}

        # 保存当前表格中的期待岗位值
        tree_items = self.tree.get_children()
        target_positions = {}
        for item_id in tree_items:
            values = self.tree.item(item_id, "values")
            emp_id = int(values[0])
            target_positions[emp_id] = values[4]  # 期待岗位

        # 删除现有的额外列（如果存在）
        current_columns = list(self.tree['columns'])
        if 'best_train_job' in current_columns:
            self.tree.heading("best_train_job", text="")
            self.tree.heading("eff_improvement", text="")
            # 重建列配置
            self.tree['columns'] = (
                "employee_id", "name", "current_position", "eff_total", "target_position")
            self.tree.heading("employee_id", text="员工ID")
            self.tree.heading("name", text="姓名")
            self.tree.heading("current_position", text="当前岗位")
            self.tree.heading("eff_total", text="当前效率")
            self.tree.heading("target_position", text="期待岗位")

        # 先清除旧的 combos（列结构即将变化）
        self._clear_combos()

        # 添加新列
        self.tree['columns'] = ("employee_id", "name", "current_position",
                                "eff_total", "target_position", "best_train_job", "eff_improvement")
        self.tree.heading("best_train_job", text="推荐训练岗位")
        self.tree.column("best_train_job", width=160)
        self.tree.heading("eff_improvement", text="效率提升值")
        self.tree.column("eff_improvement", width=100, anchor=tk.CENTER)
        # 确保原有列 heading 不丢失
        self.tree.heading("employee_id", text="员工ID")
        self.tree.heading("name", text="姓名")
        self.tree.heading("current_position", text="当前岗位")
        self.tree.heading("eff_total", text="当前效率")
        self.tree.heading("target_position", text="期待岗位")
        self.tree.column("target_position", width=180)

        # 禁用按钮
        self.plan_btn.configure(state=tk.DISABLED)
        self.fetch_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在规划训练方案...")
        self.root.update()

        plan_results = []

        try:
            for item_id in self.tree.get_children():
                values = self.tree.item(item_id, "values")
                emp_id = int(values[0])
                target_job_name = target_positions.get(emp_id, '')

                # 查找员工数据
                emp = None
                for e in self.employees_data:
                    if e['EmployeeID'] == emp_id:
                        emp = e
                        break

                if emp is None:
                    continue

                # 查找目标岗位
                target_job = job_map.get(target_job_name)
                if target_job is None:
                    # 目标岗位不在当前公司中，使用第一个岗位
                    target_job = all_jobs[0]
                    target_job_name = target_job['name']

                # 计算最优训练岗位
                plan = find_best_training_job(emp, target_job, all_jobs)

                # 更新表格行
                new_values = list(values)
                new_values.append(plan['best_job_name']
                                  if plan['best_job_name'] else 'N/A')
                new_values.append(
                    f"{plan['best_improvement']:.4f}" if plan['best_improvement'] > -999 else 'N/A')
                self.tree.item(item_id, values=new_values)

                plan_results.append({
                    'emp': emp,
                    'target_job_name': target_job_name,
                    'target_job': target_job,
                    'plan': plan,
                })

            # 生成报告
            report_path = generate_report(
                company_name, company_id, self.employees_data, plan_results)

            self.status_var.set("训练规划完成")
            self.status_label.configure(foreground="green")
            messagebox.showinfo("规划完成", f"训练规划已完成！\n报告已保存至:\n{report_path}")

        except Exception as e:
            self.status_var.set("规划失败")
            self.status_label.configure(foreground="red")
            messagebox.showerror("规划失败", f"发生错误：{str(e)}")

        finally:
            self.plan_btn.configure(state=tk.NORMAL)
            self.fetch_btn.configure(state=tk.NORMAL)
            # 规划完成后刷新 Combobox（列结构已变化）
            self.root.after(150, self._refresh_combos)


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    script_dir = get_script_dir()
    os.chdir(script_dir)

    root = tk.Tk()
    app = TrainingPlannerApp(root)
    root.mainloop()
