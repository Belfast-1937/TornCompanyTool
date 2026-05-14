import logging
import os
from datetime import datetime
import platform
from config import VERSION, LOG_DIR


def setup_logger():
    """配置日志系统"""
    log_dir = LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    log_dir_abs = os.path.abspath(log_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir_abs, f"TornCompany_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.FileHandler(log_file, encoding='utf-8')],
        force=True
    )

    logging.info("=" * 70)
    logging.info(f"🚀 Torn Company 数据自动化记录工具 v{VERSION}")
    logging.info(f"🖥️  操作系统: {platform.system()} {platform.release()}")
    logging.info(f"📁 日志文件: {log_file}")
    logging.info("=" * 70)

    return log_file
