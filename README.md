# TornCompanyTool

一个用于自动化记录和分析 **Torn City** 游戏中公司数据的工具。通过 Torn API 实时获取公司、员工和行业数据，自动生成历史数据库和绩效报告。

---

## 🎯 主要功能

### 📊 数据获取与记录
- **公司数据**：员工名单、职位效率、库存、日/周收入等
- **员工统计**：Xanax 使用次数、去瑞士旅游次数及其日均增长率
- **用户信息**：已完成教育课程、持有股票及其效果状态
- **行业数据**：指定行业内所有公司的排名与绩效

### 📈 数据分析与报表
- **历史数据库**：逐日保存公司效率汇总、环境等级、广告预算、日收入
- **员工数据库**：按日期保存员工详细数据（职位、效率、Xanax 平均增长等）
- **效率报告**：生成横向对比报表，展示历史效率变化趋势
- **动态计算**：自动计算 30 日（可配置）Xanax 和瑞士旅游平均增长率

### 🔄 智能处理
- **自动重试**：API 请求失败或限流时自动重试（支持 API 限流检测）
- **文件冲突处理**：Excel 文件被占用时自动重试
- **新员工支持**：正确处理新雇佣员工的数据初始化与平均值计算

---

## 📋 生成文件说明

### 数据库文件（`Database/` 目录）
| 文件名 | 内容 | 更新频率 |
|--------|------|--------|
| `EmployeeDB.xlsx` | 每日员工详细数据（职位、效率、Xanax 值等） | 每次运行 |
| `HistoryDB.xlsx` | 公司每日统计（合计效率、环境、广告预算、收入） | 每次运行 |
| `StockDB.xlsx` | 公司持有股票数据 | 每次运行 |
| `UserPerkDB.xlsx` | 用户教育课程与股票效果汇总 | 每次运行 |
| `IndustryDB.xlsx` | 行业内公司排名与基本信息 | 每次运行 |

### 报告文件（`Report/` 目录）
| 文件名 | 内容 |
|--------|------|
| `Company_Efficiency_Report.xlsx` | 公司效率历史趋势横向对比报表 |

### 日志文件（`logs/` 目录）
- 按时间戳命名的日志文件，记录完整运行过程与错误信息

---

## ⚙️ 配置文件

### Company.ini（必需）
在程序同级目录创建 `Company.ini` 文件：

```ini
[Settings]
CompanyID=Your_Company_ID
ApiKey=Your_API_Key
UserID=Your_User_ID
IndustryID=Your_Industry_ID
```

- 如果配置文件不存在或包含占位符（`Your_*`），程序会进入**手动输入模式**
- **API Key** 可在 [Torn API 官网](https://www.torn.com/api.html) 获取

---

## 🚀 快速开始

### 前置要求
- Python 3.7+
- 依赖库：`pandas`, `openpyxl`, `requests`

### 安装依赖
```bash
pip install pandas openpyxl requests
```

### 运行工具
```bash
python main.py
```

### 运行流程
1. ✅ 验证网络连接
2. 📖 读取 `Company.ini` 或提示手动输入配置
3. 📡 连接 Torn API 获取数据
4. 📊 处理员工数据并计算平均增长率
5. 💾 保存数据到 Excel 文件
6. 📈 生成效率对比报告

---

## 📖 使用示例

### 日常使用（推荐）
每天运行一次以记录公司数据：
```bash
python main.py
```
数据自动追加到 `HistoryDB.xlsx` 和 `EmployeeDB.xlsx`

### PyInstaller 打包（可选）
转换为独立 .exe 文件：
```bash
pyinstaller --onefile --icon=output.ico main.py
```

---

## 🔒 数据安全提示

⚠️ **重要警告**
- 📂 请勿删除或移动 `Database/` 文件夹，否则所有历史记录将永久丢失
- 🔐 `Company.ini` 包含敏感信息（API Key），请勿公开分享或提交到版本控制
- 🛡️ 建议将 `Company.ini` 添加到 `.gitignore`

---

## 📝 文件结构

```
TornCompanyTool/
├── main.py                  # 主程序入口
├── config.py               # 配置与常量定义
├── api_client.py          # API 请求处理
├── data_processor.py      # 数据解析与计算
├── excel_handler.py       # Excel 文件导入/导出
├── logger.py              # 日志配置
├── utils.py               # 工具函数
├── Company.ini            # 配置文件（需自创建）
├── output.ico            # 打包用图标
├── Database/             # 数据库文件夹（自动创建）
├── Report/               # 报告文件夹（自动创建）
└── logs/                 # 日志文件夹（自动创建）
```

---

## 🔧 高级配置

编辑 `config.py` 调整以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_XAN_DAYS` | 30 | 计算 Xanax 平均增长的天数 |
| `LOG_DIR` | `./logs` | 日志文件存储目录 |
| `DATABASE_DIR` | `./Database` | 数据库文件存储目录 |
| `REPORT_DIR` | `./Report` | 报告文件存储目录 |

---

## 📊 版本历史

| 版本 | 发布日期 | 主要更新 |
|------|----------|---------|
| v1.0 | 2026-05-10 | 初始发布 |
| v1.1 | 2026-05-14 | 添加 Xanax 统计与 30 日平均计算 |
| v1.2 | 2026-05-14 | 新增行业数据、优化结构 |
| v1.3 | 2026-05-14 | 修复 Xanax 计算、改为瑞士旅游次数追踪 |
| v1.4 | 2026-05-20 | 修复新员工平均值计算 bug |

---

## 🆘 常见问题

### Q: 程序卡在 "正在请求 API" 如何处理？
A: 可能是 API 限流（100 请求/分钟）。程序会自动等待并重试，或检查网络连接。

### Q: Excel 文件打开时能否运行程序？
A: 不能。程序会提示错误并重试。请关闭 Excel 文件后重新运行。

### Q: 历史数据可以删除吗？
A: **不建议删除**。若要重新开始，可备份后删除 `HistoryDB.xlsx`，程序会重建。

### Q: 如何修改计算平均值的天数？
A: 编辑 `config.py` 中的 `MAX_XAN_DAYS` 参数，或联系开发者定制。

---

## 📞 反馈与支持

欢迎提交 Issue 和 Pull Request 改进此工具！