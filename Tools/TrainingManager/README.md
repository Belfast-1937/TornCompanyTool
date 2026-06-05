# TrainingManager — 员工训练规划工具

**当前版本：v1.3**

## 概述

基于 PySide6 的 GUI 桌面程序，帮助管理者在不实际转岗的情况下规划员工最优训练岗位。通过模拟在每个可训练岗位训练一天后的属性增长，推荐效率提升最大的训练岗位，并估算达到目标效率所需的训练次数。

## 安装依赖

```bash
pip install PySide6 requests
```

- PySide6 首次运行时会自动尝试通过清华镜像安装，无需手动操作

## 运行

```bash
cd Tools/TrainingManager
python main.py
```

## 使用步骤

1. 在 GUI 中选择公司类型（下拉框包含全部 39 种行业）
2. 输入 Company ID 和 API Key
3. 点击「**保存配置**」保存到 `config.json`
4. 点击「**拉取员工数据**」通过 API 获取当前员工的属性与效率
5. 在表格中为每位员工选择「**期待岗位**」（目标岗位）
6. 点击「**规划训练**」计算最优训练方案
7. 弹出的报告保存路径即为完整训练规划 TXT 文件

## 功能

- 通过 Torn API 拉取员工当前 MAN/INT/END 属性和岗位效率
- 自动匹配公司类型（从 39 种行业内置数据中选取）
- 模拟在每个可训练岗位训练一天后的目标岗位效率提升
- 推荐效率提升最大的训练岗位
- 估算达到目标岗位效率 +1 点所需的训练次数（指数+二分搜索）
- 生成 TXT 格式训练规划报告

## 关键数据

- 内置 `company_data.py`：39 家公司 × 多岗位的完整属性需求数据（硬编码）
- 训练收益：主属性 +50，副属性 +25（每日）
- 效率公式：`min(45, stat/req × 45) + max(0, 5 × log₂(stat/req))`（主副独立计算后求和）

## 配置文件

`config.json`（自动创建并保存），包含：
- `api_key`：Torn API Key
- `company_id`：公司 ID
- `company_type`：公司类型 ID（从下拉框选择）

## 报告输出

训练规划报告保存于 `reports/` 目录（`training_plan_YYYYMMDD_HHMMSS.txt`），包含：
- 每位员工的当前属性值
- 目标岗位的属性需求
- 推荐训练岗位及效率提升值
- 提升所需训练次数（达到效率提升 1 点所需的天数）
- 所有岗位按效率提升降序排列的详细对比表

## 文件结构

```
TrainingManager/
├── main.py            # 入口：QApplication 启动
├── gui_pyqt.py        # PySide6 GUI 界面
├── api_client.py      # Torn API 调用 + 员工解析
├── config.py          # JSON 配置文件读写
├── constants.py       # 常量定义
├── company_data.py    # 39 家公司岗位硬编码数据
├── efficiency.py      # 效率计算公式
├── trainer.py         # 训练规划引擎
├── report.py          # TXT 报告生成
├── output.ico         # 打包图标
├── config.json        # GUI 配置保存（自动创建）
└── reports/           # 规划报告输出（自动创建）
```

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-05-30 | 初始发布，Tkinter GUI 训练规划 |
| v1.1 | 2026-05-31 | 删除 User ID 输入；修复同效率岗位排序；修正效率计算逻辑 |
| v1.2 | 2026-05-31 | 更换 GUI 框架为 PySide6；增加背景图片美化；增加训练次数估算 |
| v1.3 | 2026-06-05 | 新增多步训练规划（DP全局最优/凸优化自适应）；选中员工反馈提示；UI交互优化 |
