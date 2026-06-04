# -*- coding: utf-8 -*-
"""PySide6 GUI 应用"""
import os
import sys
import threading

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QPalette, QBrush, QIcon

from constants import COMPANIES_DATA, SCRIPT_DIR
from api_client import fetch_company_data, parse_employees, parse_company_type
from trainer import find_best_training_job, calc_trains_to_next_point
from config import load_config, save_config, clear_config
from report import generate_report


_BG_PATH = "./background.png"


class _Signals(QObject):
    fetch_done = Signal(list, object)
    fetch_error = Signal(str)


class TrainingPlannerApp(QMainWindow):
    """Torn City 员工训练规划工具 GUI 应用。"""

    COL_COUNT_BASE = 5
    COL_COUNT_FULL = 8

    def __init__(self, version):
        super().__init__()
        self.setWindowTitle(f"Torn City 员工训练规划工具 v{version}")
        self.resize(1280, 720)
        self.setMinimumSize(1050, 500)

        self.employees_data = []
        self.company_job_names = []
        self._signals = _Signals()
        self._signals.fetch_done.connect(self._on_fetch_success)
        self._signals.fetch_error.connect(self._on_fetch_error)

        self._apply_background()
        self._set_window_icon()
        self._build_ui()
        self._load_config()

    # ---- 图标 ----

    def _set_window_icon(self):
        """设置窗口图标（任务栏和标题栏）。"""
        # 优先从 PyInstaller 打包目录 (_MEIPASS) 查找，其次从脚本目录查找
        if getattr(sys, 'frozen', False):
            base_dirs = [sys._MEIPASS, SCRIPT_DIR]
        else:
            base_dirs = [SCRIPT_DIR]
        for base in base_dirs:
            icon_path = os.path.join(base, "output.ico")
            if os.path.isfile(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                return

    # ---- 背景 ----

    def _apply_background(self):
        """设置背景图片，表格透明，控件半透明。"""
        widget_style = """
            QTableWidget {
                background-color: rgba(255, 255, 255, 160);
                border: 1px solid #ccc;
                gridline-color: #aaa;
            }
            QHeaderView {
                background-color: rgba(255, 255, 255, 160);
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
            QPushButton, QComboBox, QLineEdit {
                background-color: rgba(255, 255, 255, 220);
                border: 1px solid #aaa;
            }
            QPushButton {
                padding: 4px 12px;
            }
        """
        if os.path.isfile(_BG_PATH):
            bg_url = _BG_PATH.replace("\\", "/")
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url({bg_url});
                    background-repeat: no-repeat;
                    background-position: center;
                }}
                {widget_style}
            """)
        else:
            self.setStyleSheet(widget_style)

    # ---- UI 构建 ----

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # ===== 顶栏输入 =====
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(10)

        top_grid.addWidget(QLabel("公司类型:"), 0, 0)
        self.company_combo = QComboBox()
        self.company_combo.addItems(
            [f"{cid} - {d['company_name']}" for cid, d in COMPANIES_DATA.items()])
        self.company_combo.setMinimumWidth(240)
        self.company_combo.currentIndexChanged.connect(
            self._on_company_changed)
        top_grid.addWidget(self.company_combo, 0, 1)

        top_grid.addWidget(QLabel("公司 ID:"), 0, 2)
        self.company_id_edit = QLineEdit()
        self.company_id_edit.setFixedWidth(80)
        top_grid.addWidget(self.company_id_edit, 0, 3)

        top_grid.addWidget(QLabel("API:"), 0, 4)
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.Password)
        self.api_edit.setMinimumWidth(220)
        top_grid.addWidget(self.api_edit, 0, 5)

        btn_save = QPushButton("保存配置")
        btn_save.clicked.connect(self._save_config)
        top_grid.addWidget(btn_save, 0, 6)

        btn_clear = QPushButton("清除配置")
        btn_clear.clicked.connect(self._clear_config)
        top_grid.addWidget(btn_clear, 0, 7)

        root_layout.addLayout(top_grid)

        # ===== 操作栏 =====
        op_layout = QHBoxLayout()

        self.fetch_btn = QPushButton("拉取员工数据")
        self.fetch_btn.clicked.connect(self._fetch_employees)
        op_layout.addWidget(self.fetch_btn)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(
            "color: gray; background-color: transparent; border: none;")
        op_layout.addWidget(self.status_label)

        op_layout.addStretch()
        root_layout.addLayout(op_layout)

        # ===== 表格 =====
        self.table = QTableWidget()
        self.table.setColumnCount(self.COL_COUNT_BASE)
        self.table.setHorizontalHeaderLabels(
            ["员工ID", "姓名", "当前岗位", "当前效率", "期待岗位"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        # 设置默认行高避免文字重影
        self.table.verticalHeader().setDefaultSectionSize(26)
        root_layout.addWidget(self.table, 1)

        # ===== 底部 =====
        self.plan_btn = QPushButton("规划训练")
        self.plan_btn.clicked.connect(self._plan_training)
        root_layout.addWidget(self.plan_btn)

    # ---- 配置 ----

    def _on_company_changed(self, _index=None):
        self._update_job_names()

    def _update_job_names(self):
        cid = self._get_selected_company_id()
        if cid and cid in COMPANIES_DATA:
            self.company_job_names = [j['name']
                                      for j in COMPANIES_DATA[cid]['jobs']]
        else:
            self.company_job_names = []

    def _get_selected_company_id(self):
        text = self.company_combo.currentText()
        if " - " in text:
            try:
                return int(text.split(" - ")[0])
            except (ValueError, IndexError):
                return None
        return None

    def _load_config(self):
        cfg = load_config()
        if cfg:
            if 'api_key' in cfg:
                self.api_edit.setText(cfg['api_key'])
            if 'company_id' in cfg:
                self.company_id_edit.setText(cfg['company_id'])
            if 'company_type' in cfg:
                for i in range(self.company_combo.count()):
                    if self.company_combo.itemText(i).startswith(str(cfg['company_type']) + " - "):
                        self.company_combo.setCurrentIndex(i)
                        self._on_company_changed()
                        break

    def _save_config(self):
        save_config(self.api_edit.text().strip(), "",
                    self.company_id_edit.text().strip(), self._get_selected_company_id())
        QMessageBox.information(self, "成功", "配置已保存到 config.json")

    def _clear_config(self):
        self.api_edit.clear()
        self.company_id_edit.clear()
        clear_config()
        QMessageBox.information(self, "成功", "配置已清除")

    # ---- 输入验证 ----

    def _validate_inputs(self):
        cid = self.company_id_edit.text().strip()
        api = self.api_edit.text().strip()
        errors = []
        if not cid or not cid.isdigit() or int(cid) <= 0:
            errors.append("公司ID")
        if not api:
            errors.append("API Key")
        if errors:
            return False, "、".join(errors) + " 输入无效"
        return True, ""

    def _auto_select_company_type(self, ct):
        if ct is None or ct not in COMPANIES_DATA:
            return False
        for i in range(self.company_combo.count()):
            if self.company_combo.itemText(i).startswith(str(ct) + " - "):
                self.company_combo.setCurrentIndex(i)
                self._on_company_changed()
                return True
        return False

    # ---- 员工数据拉取 ----

    def _fetch_employees(self):
        valid, msg = self._validate_inputs()
        if not valid:
            self.status_label.setText(msg)
            self.status_label.setStyleSheet(
                "color: red; background-color: transparent; border: none;")
            cid = self.company_id_edit.text().strip()
            if not cid or not cid.isdigit() or int(cid) <= 0:
                self.company_id_edit.clear()
            if not self.api_edit.text().strip():
                self.api_edit.clear()
            return

        tornado_id = int(self.company_id_edit.text().strip())
        api_key = self.api_edit.text().strip()

        self.fetch_btn.setEnabled(False)
        self.plan_btn.setEnabled(False)
        self.status_label.setText("正在拉取员工数据...")
        self.status_label.setStyleSheet(
            "color: gray; background-color: transparent; border: none;")

        def worker():
            response = fetch_company_data(tornado_id, api_key)
            if "error" in response:
                self._signals.fetch_error.emit(response["error"])
            else:
                employees = parse_employees(response)
                company_type = parse_company_type(response)
                self._signals.fetch_done.emit(employees, company_type)

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, employees, company_type):
        self.employees_data = employees
        if company_type is not None:
            if not self._auto_select_company_type(company_type):
                self.status_label.setText(f"警告：未找到行业类型 {company_type}")
                self.status_label.setStyleSheet(
                    "color: orange; background-color: transparent; border: none;")
        else:
            self.status_label.setText("警告：无法获取行业类型，请手动选择")
            self.status_label.setStyleSheet(
                "color: orange; background-color: transparent; border: none;")

        self._update_job_names()
        self._populate_table()

        self.fetch_btn.setEnabled(True)
        self.plan_btn.setEnabled(True)
        if company_type is not None and company_type in COMPANIES_DATA:
            self.status_label.setText(f"成功获取 {len(employees)} 名员工数据")
            self.status_label.setStyleSheet(
                "color: green; background-color: transparent; border: none;")

    def _on_fetch_error(self, error_msg):
        self.fetch_btn.setEnabled(True)
        self.plan_btn.setEnabled(True)
        self.status_label.setText("获取失败")
        self.status_label.setStyleSheet(
            "color: red; background-color: transparent; border: none;")
        QMessageBox.critical(self, "API 请求失败", error_msg)

    # ---- 表格填充 ----

    def _populate_table(self):
        self.table.setColumnCount(self.COL_COUNT_BASE)
        self.table.setHorizontalHeaderLabels(
            ["员工ID", "姓名", "当前岗位", "当前效率", "期待岗位"])
        self.table.horizontalHeader().setStretchLastSection(True)

        # 固定列宽，避免 QComboBox 过宽
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        # 第4列（期待岗位）由 stretchLastSection 自动拉伸

        self.table.setRowCount(0)
        if not self.employees_data:
            return

        for emp in self.employees_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(
                str(emp.get('EmployeeID', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(emp.get('name', '')))
            self.table.setItem(
                row, 2, QTableWidgetItem(emp.get('position', '')))
            eff = emp.get('eff_total')
            self.table.setItem(row, 3, QTableWidgetItem(
                f"{eff:.2f}" if eff is not None else "N/A"))

            target = emp.get('position', '')
            if target not in self.company_job_names:
                target = self.company_job_names[0] if self.company_job_names else ''
            combo = QComboBox()
            combo.addItems(
                self.company_job_names if self.company_job_names else [''])
            combo.setFixedHeight(24)
            if target in self.company_job_names:
                combo.setCurrentText(target)
            self.table.setCellWidget(row, 4, combo)

    def _read_target_positions(self):
        result = {}
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item is None:
                continue
            emp_id = int(id_item.text())
            widget = self.table.cellWidget(row, 4)
            if isinstance(widget, QComboBox):
                result[emp_id] = widget.currentText()
            else:
                item = self.table.item(row, 4)
                if item:
                    result[emp_id] = item.text()
        return result

    # ---- 规划训练 ----

    def _plan_training(self):
        if not self.employees_data:
            self.status_label.setText("请先拉取员工数据")
            self.status_label.setStyleSheet(
                "color: red; background-color: transparent; border: none;")
            return

        company_id = self._get_selected_company_id()
        if company_id is None or company_id not in COMPANIES_DATA:
            self.status_label.setText("请选择有效的公司")
            self.status_label.setStyleSheet(
                "color: red; background-color: transparent; border: none;")
            return

        target_positions = self._read_target_positions()
        company_data = COMPANIES_DATA[company_id]
        company_name = company_data['company_name']
        all_jobs = company_data['jobs']
        job_map = {job['name']: job for job in all_jobs}

        self.plan_btn.setEnabled(False)
        self.fetch_btn.setEnabled(False)
        self.status_label.setText("正在规划训练方案...")
        self.status_label.setStyleSheet(
            "color: gray; background-color: transparent; border: none;")
        self.table.setColumnCount(self.COL_COUNT_FULL)
        self.table.setHorizontalHeaderLabels(
            ["员工ID", "姓名", "当前岗位", "当前效率", "期待岗位",
             "推荐训练岗位", "效率提升值", "提升所需训练"])
        self.table.horizontalHeader().setStretchLastSection(True)

        # 固定列宽
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 180)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 130)

        plan_results = []
        try:
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                if id_item is None:
                    continue
                emp_id = int(id_item.text())
                tgt_name = target_positions.get(emp_id, '')

                emp = next(
                    (e for e in self.employees_data if e['EmployeeID'] == emp_id), None)
                if emp is None:
                    continue

                target_job = job_map.get(tgt_name) or all_jobs[0]
                tgt_name = target_job['name']

                plan = find_best_training_job(emp, target_job, all_jobs)
                best_job = job_map.get(plan['best_job_name'], all_jobs[0])
                trains = calc_trains_to_next_point(
                    plan['current_stats'], target_job, best_job)

                self.table.setItem(row, 4, QTableWidgetItem(tgt_name))
                self.table.setItem(row, 5, QTableWidgetItem(
                    plan['best_job_name'] or 'N/A'))
                self.table.setItem(row, 6, QTableWidgetItem(
                    f"{plan['best_improvement']:.4f}" if plan['best_improvement'] > -999 else 'N/A'))
                self.table.setItem(row, 7, QTableWidgetItem(
                    f"{trains}次" if trains < 100000 else ">10万"))

                plan_results.append({
                    'emp': emp, 'target_job_name': tgt_name,
                    'target_job': target_job, 'plan': plan, 'trains_needed': trains,
                })

            report_path = generate_report(
                company_name, company_id, plan_results)
            self.status_label.setText("训练规划完成")
            self.status_label.setStyleSheet(
                "color: green; background-color: transparent; border: none;")
            QMessageBox.information(
                self, "规划完成", f"训练规划已完成！\n报告已保存至:\n{report_path}")
        except Exception as e:
            self.status_label.setText("规划失败")
            self.status_label.setStyleSheet(
                "color: red; background-color: transparent; border: none;")
            QMessageBox.critical(self, "规划失败", f"发生错误：{str(e)}")
        finally:
            self.plan_btn.setEnabled(True)
            self.fetch_btn.setEnabled(True)
