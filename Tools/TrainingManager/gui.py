# -*- coding: utf-8 -*-
"""GUI 应用"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from constants import COMPANIES_DATA
from api import fetch_company_data, parse_employees, parse_company_type
from trainer import find_best_training_job, get_emp_stats, calc_trains_to_next_point
from config import load_config, save_config, clear_config
from report import generate_report


class TrainingPlannerApp:
    """Torn City 员工训练规划工具 GUI 应用。"""

    def __init__(self, root, version):
        self.root = root
        self.root.title(f"Torn City 员工训练规划工具 v{version}")
        self.root.geometry("1100x700")
        self.root.minsize(900, 500)

        self.employees_data = []
        self.company_job_names = []

        self._build_ui()
        self._load_config()

    # ---- UI 构建 ----

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding="10 10 10 5")
        top_frame.pack(fill=tk.X)

        # 第一行
        ttk.Label(top_frame, text="公司类型:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.company_var = tk.StringVar()
        self.company_combo = ttk.Combobox(top_frame, textvariable=self.company_var, state="readonly", width=28)
        company_list = [f"{cid} - {data['company_name']}" for cid, data in COMPANIES_DATA.items()]
        self.company_combo['values'] = company_list
        if company_list:
            self.company_combo.current(0)
        self.company_combo.grid(row=0, column=1, padx=(0, 15), sticky=tk.W)
        self.company_combo.bind('<<ComboboxSelected>>', self._on_company_changed)

        ttk.Label(top_frame, text="公司 ID:").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.company_id_var = tk.StringVar()
        self.company_id_entry = ttk.Entry(top_frame, textvariable=self.company_id_var, width=10)
        self.company_id_entry.grid(row=0, column=3, padx=(0, 15), sticky=tk.W)

        ttk.Label(top_frame, text="API:").grid(row=0, column=4, padx=(0, 5), sticky=tk.W)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(top_frame, textvariable=self.api_key_var, show="*", width=30)
        self.api_key_entry.grid(row=0, column=5, padx=(0, 15), sticky=tk.W)

        # 保存/清除
        self.save_btn = ttk.Button(top_frame, text="保存配置", command=self._save_config)
        self.save_btn.grid(row=0, column=6, padx=(0, 5))

        self.clear_btn = ttk.Button(top_frame, text="清除配置", command=self._clear_config)
        self.clear_btn.grid(row=0, column=7)

        # 中部
        mid_frame = ttk.Frame(self.root, padding="10 5 10 5")
        mid_frame.pack(fill=tk.X)

        self.fetch_btn = ttk.Button(mid_frame, text="拉取员工数据", command=self._fetch_employees)
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 20))

        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(mid_frame, textvariable=self.status_var, foreground="gray")
        self.status_label.pack(side=tk.LEFT)

        # 表格
        table_frame = ttk.Frame(self.root, padding="10 5 10 5")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("employee_id", "name", "current_position", "eff_total", "target_position")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

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

        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<ButtonRelease-1>", lambda e: self._schedule_refresh())
        self.tree.bind("<MouseWheel>", lambda e: self._schedule_refresh())
        table_frame.bind("<Configure>", lambda e: self._schedule_refresh(500))

        # 底部
        bottom_frame = ttk.Frame(self.root, padding="10 5 10 10")
        bottom_frame.pack(fill=tk.X)

        self.plan_btn = ttk.Button(bottom_frame, text="规划训练", command=self._plan_training)
        self.plan_btn.pack(side=tk.LEFT)

    # ---- 事件 ----

    def _on_company_changed(self, event=None):
        self._update_job_names()

    def _update_job_names(self):
        company_id = self._get_selected_company_id()
        if company_id and company_id in COMPANIES_DATA:
            self.company_job_names = [job['name'] for job in COMPANIES_DATA[company_id]['jobs']]
        else:
            self.company_job_names = []

    def _get_selected_company_id(self):
        val = self.company_var.get()
        if " - " in val:
            try:
                return int(val.split(" - ")[0])
            except:
                return None
        return None

    def _load_config(self):
        config = load_config()
        if config:
            if 'api_key' in config:
                self.api_key_var.set(config['api_key'])
            if 'company_id' in config:
                self.company_id_var.set(config['company_id'])
            if 'company_type' in config:
                for i, val in enumerate(self.company_combo['values']):
                    if val.startswith(str(config['company_type']) + " - "):
                        self.company_combo.current(i)
                        self._on_company_changed()
                        break

    def _save_config(self):
        api_key = self.api_key_var.get().strip()
        company_id = self.company_id_var.get().strip()
        company_type = self._get_selected_company_id()
        save_config(api_key, "", company_id, company_type)
        messagebox.showinfo("成功", "配置已保存到 config.json")

    def _clear_config(self):
        self.api_key_var.set("")
        self.company_id_var.set("")
        clear_config()
        messagebox.showinfo("成功", "配置已清除")

    # ---- 输入验证 ----

    def _validate_inputs(self):
        company_id = self.company_id_var.get().strip()
        api_key = self.api_key_var.get().strip()
        errors = []
        if not company_id or not company_id.isdigit():
            errors.append("公司ID")
        if not api_key:
            errors.append("API Key")
        if errors:
            return False, "、".join(errors) + " 输入无效，请检查后重试"
        return True, ""

    def _show_input_error(self, msg):
        self.status_var.set(msg)
        self.status_label.configure(foreground="red")
        if not self.company_id_var.get().strip() or not self.company_id_var.get().strip().isdigit():
            self.company_id_var.set("")
        if not self.api_key_var.get().strip():
            self.api_key_var.set("")

    def _auto_select_company_type(self, company_type_id):
        if company_type_id is None or company_type_id not in COMPANIES_DATA:
            return False
        for i, val in enumerate(self.company_combo['values']):
            if val.startswith(str(company_type_id) + " - "):
                self.company_combo.current(i)
                self._on_company_changed()
                return True
        return False

    # ---- 员工数据 ----

    def _fetch_employees(self):
        valid, msg = self._validate_inputs()
        if not valid:
            self._show_input_error(msg)
            return

        tornado_id = int(self.company_id_var.get().strip())
        api_key = self.api_key_var.get().strip()

        self.fetch_btn.configure(state=tk.DISABLED)
        self.plan_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在拉取员工数据...")
        self.status_label.configure(foreground="gray")
        self.root.update()

        def worker():
            response = fetch_company_data(tornado_id, api_key)
            if "error" in response:
                self.root.after(0, lambda: self._on_fetch_error(response["error"]))
            else:
                employees = parse_employees(response)
                company_type = parse_company_type(response)
                self.root.after(0, lambda: self._on_fetch_success(employees, company_type))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, employees, company_type):
        self.employees_data = employees

        if company_type is not None:
            if not self._auto_select_company_type(company_type):
                self.status_var.set(f"警告：未找到行业类型 {company_type}，请手动选择")
                self.status_label.configure(foreground="orange")
        else:
            self.status_var.set("警告：无法获取行业类型，请手动选择")
            self.status_label.configure(foreground="orange")

        self._update_job_names()
        self._populate_table()
        self.fetch_btn.configure(state=tk.NORMAL)
        self.plan_btn.configure(state=tk.NORMAL)

        if company_type is not None and company_type in COMPANIES_DATA:
            self.status_var.set(f"成功获取 {len(employees)} 名员工数据")
            self.status_label.configure(foreground="green")

    def _on_fetch_error(self, error_msg):
        self.fetch_btn.configure(state=tk.NORMAL)
        self.plan_btn.configure(state=tk.NORMAL)
        self.status_var.set("获取失败")
        self.status_label.configure(foreground="red")
        messagebox.showerror("API 请求失败", error_msg)

    # ---- 表格操作 ----

    def _populate_table(self):
        self._clear_combos()
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.employees_data:
            return

        for emp in self.employees_data:
            target_pos = emp.get('position', '')
            if target_pos not in self.company_job_names:
                target_pos = self.company_job_names[0] if self.company_job_names else ''

            row_id = self.tree.insert("", tk.END, values=(
                emp.get('EmployeeID', ''),
                emp.get('name', ''),
                emp.get('position', ''),
                f"{emp.get('eff_total', 0):.2f}" if emp.get('eff_total') is not None else "N/A",
                target_pos,
            ))
            self._create_combo_for_row(row_id, target_pos)

    def _clear_combos(self):
        if hasattr(self, '_row_combos'):
            for combo in self._row_combos:
                combo.destroy()
        self._row_combos = []

    def _create_combo_for_row(self, row_id, current_val):
        if not hasattr(self, '_row_combos'):
            self._row_combos = []
        if not self.company_job_names:
            return

        try:
            x, y, width, height = self.tree.bbox(row_id, "#5")
        except:
            return

        combo = ttk.Combobox(self.tree, values=self.company_job_names, state="readonly")
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

    def _schedule_refresh(self, delay=300):
        """延迟刷新 Combobox，连续事件时会取消旧任务重新计时。"""
        if hasattr(self, '_refresh_after_id'):
            self.root.after_cancel(self._refresh_after_id)
        self._refresh_after_id = self.root.after(delay, self._refresh_combos)

    def _refresh_combos(self):
        # 如果有 Combobox 正在展开下拉，跳过刷新
        if hasattr(self, '_row_combos'):
            for combo in self._row_combos:
                try:
                    if str(combo) == str(self.tree.focus_get()):
                        self._schedule_refresh(300)  # 稍后再试
                        return
                except:
                    pass

        self._clear_combos()
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            current_val = values[4] if len(values) >= 5 else ''
            self._create_combo_for_row(item_id, current_val)

    # ---- 规划训练 ----

    def _plan_training(self):
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
        job_map = {job['name']: job for job in all_jobs}

        tree_items = self.tree.get_children()
        target_positions = {}
        for item_id in tree_items:
            values = self.tree.item(item_id, "values")
            target_positions[int(values[0])] = values[4]

        # 重置列
        current_columns = list(self.tree['columns'])
        if 'best_train_job' in current_columns:
            self.tree['columns'] = ("employee_id", "name", "current_position", "eff_total", "target_position")
            self.tree.heading("employee_id", text="员工ID")
            self.tree.heading("name", text="姓名")
            self.tree.heading("current_position", text="当前岗位")
            self.tree.heading("eff_total", text="当前效率")
            self.tree.heading("target_position", text="期待岗位")

        self._clear_combos()

        # 添加结果列
        self.tree['columns'] = ("employee_id", "name", "current_position",
                                "eff_total", "target_position",
                                "best_train_job", "eff_improvement", "trains_needed")
        self.tree.heading("best_train_job", text="推荐训练岗位")
        self.tree.column("best_train_job", width=160)
        self.tree.heading("eff_improvement", text="效率提升值")
        self.tree.column("eff_improvement", width=130, anchor=tk.CENTER)
        self.tree.heading("trains_needed", text="提升所需训练")
        self.tree.column("trains_needed", width=120, anchor=tk.CENTER)
        self.tree.heading("employee_id", text="员工ID")
        self.tree.heading("name", text="姓名")
        self.tree.heading("current_position", text="当前岗位")
        self.tree.heading("eff_total", text="当前效率")
        self.tree.heading("target_position", text="期待岗位")
        self.tree.column("target_position", width=180)

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

                emp = None
                for e in self.employees_data:
                    if e['EmployeeID'] == emp_id:
                        emp = e
                        break
                if emp is None:
                    continue

                target_job = job_map.get(target_job_name) or all_jobs[0]
                target_job_name = target_job['name']

                plan = find_best_training_job(emp, target_job, all_jobs)

                # 计算效率+1所需训练次数
                best_job = job_map.get(plan['best_job_name'], all_jobs[0])
                trains_needed = calc_trains_to_next_point(
                    plan['current_stats'], target_job, best_job)

                new_values = list(values)
                new_values.append(plan['best_job_name'] if plan['best_job_name'] else 'N/A')
                new_values.append(f"{plan['best_improvement']:.4f}" if plan['best_improvement'] > -999 else 'N/A')
                new_values.append(f"{trains_needed}次" if trains_needed < 100000 else ">10万")
                self.tree.item(item_id, values=new_values)

                plan_results.append({
                    'emp': emp, 'target_job_name': target_job_name,
                    'target_job': target_job, 'plan': plan, 'trains_needed': trains_needed,
                })

            report_path = generate_report(company_name, company_id, plan_results)
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
            self.root.after(150, self._refresh_combos)