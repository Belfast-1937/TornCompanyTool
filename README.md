# TornCompanyTool

一个用于自动化记录和分析 **Torn City** 游戏中公司数据的工具集。通过 Torn API 实时获取公司、员工和行业数据，自动生成历史数据库和绩效报告，并包含多个辅助子工具。

---

## 🎯 主要功能

### 📊 核心工具（根目录）

#### 数据获取与记录
- **公司数据**：员工名单、职位效率、库存、日/周收入等
- **员工统计**：Xanax 使用次数、去瑞士旅游次数及其日均增长率
- **用户信息**：已完成教育课程、持有股票及其效果状态
- **行业数据**：指定行业内所有公司的排名与绩效

#### 数据分析与报表
- **历史数据库**：逐日保存公司效率汇总、环境等级、广告预算、日收入
- **员工数据库**：按日期保存员工详细数据（职位、效率、Xanax 平均增长等）
- **效率报告**：生成横向对比报表，展示历史效率变化趋势
- **动态计算**：自动计算 30 日（可配置）Xanax 和瑞士旅游平均增长率
- **利润计算**：自动计算净利润（日收入 - 工资支出 - 销售成本 - 广告费）

#### 智能处理
- **自动重试**：API 请求失败或限流时自动重试（支持 API 限流检测）
- **文件冲突处理**：Excel 文件被占用时自动重试
- **新员工支持**：正确处理新雇佣员工的数据初始化与平均值计算
- **版本升级**：自动检测并升级旧版报表格式

### 🛠️ 辅助工具（Tools/ 目录）

#### TrainingManager — 员工训练规划工具
- 通过 GUI 界面拉取公司员工数据
- 基于员工当前属性（MAN / INT / END）模拟各岗位训练效果
- 计算训练一天后对指定目标岗位的效率提升值
- 为每位员工推荐最优训练岗位
- 自动生成 TXT 格式的训练规划报告

#### IsBossDead — 行业招聘侦查工具
- 扫描指定行业内所有公司
- 识别"老板长时间离线但仍有活跃员工"的公司
- 可自定义老板离线天数阈值、员工活跃天数阈值和最低星级要求
- 自动查询目标公司老板的派系信息
- 输出 Excel 格式的候选公司列表，包含直达公司页面的链接

---

## 📋 核心工具：生成文件说明

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

## ⚙️ 核心工具：配置文件

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
- **API Key** 可在 [Torn API 官网](https://www.torn.com/api.html) 获取（使用 Limited Access Key）

---

## 🚀 核心工具：快速开始

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

## 📖 核心工具：使用示例

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

## 🔄 核心工具：版本升级机制

从 v1.4 升级到 v1.5 时，程序会自动：
1. 检测 `Company_Efficiency_Report.xlsx` 的版本号
2. 如为旧版本，自动备份旧文件到 `Old_*` 文件
3. 删除旧版文件并基于原始数据库重新生成新版本格式的 HISTORY_DB
4. 无需手动操作

---

## 🛠️ 工具集：TrainingManager

### 功能介绍
Torn City 员工训练规划工具，通过 **Tkinter GUI** 界面操作。用于帮助公司管理者规划员工的最优训练方案——不需要实际转岗，只需训练一天即可观察效率变化。

### 配置文件
GUI 内输入的配置自动保存到 `config.json`，无需手动编辑。包含：
- API Key
- User ID
- Company ID
- Company Type

### 运行
```bash
cd Tools/TrainingManager
python main.py
```

### 使用步骤
1. 在 GUI 中选择公司类型（下拉框包含全部 39 种行业）
2. 输入 Company ID、API Key、User ID
3. 点击「**保存配置**」保存到 config.json
4. 点击「**拉取员工数据**」通过 API 获取当前员工的属性与效率
5. 在表格中为每位员工选择「**期待岗位**」（目标岗位）
6. 点击「**规划训练**」计算最优训练方案
7. 弹出的报告保存路径即为完整训练规划 TXT 文件

### 训练算法
- 计算员工在目标岗位的当前效率
- 模拟在每个可训练岗位训练一天后的属性增长（主属性 +50，副属性 +25）
- 重新计算训练后的目标岗位效率
- 推荐效率提升最大的训练岗位

### 报告输出
训练规划报告保存于 `Tools/TrainingManager/reports/` 目录，包含：
- 每位员工的当前属性值
- 目标岗位的属性需求
- **推荐训练岗位**及效率提升值
- 所有岗位按效率提升降序排列的详细对比表

### 技术细节
- 内置 39 家公司的完整岗位数据（共 300+ 岗位）
- API 拉取时自动匹配公司类型
- 多线程处理避免 GUI 卡顿

---

## 🛠️ 工具集：IsBossDead

### 功能介绍
行业招聘侦查工具。扫描指定行业中"**老板已长时间离线但仍有活跃员工**"的公司，用于发现可能缺少管理的优质目标公司，便于挖角或观察。

### 配置文件（Industry.ini）

```ini
[Settings]
BossOfflineDays = 3          ; 老板离线多少天视为目标
EmployeeActiveDays = 1       ; 员工多少天内活跃视为目标
MinimumStarRating = 3        ; 最低星级过滤
ApiKey = Your_Public_Access_API_Key_Here
IndustryID = Your_IndustryID_Here
```

- API Key 使用 **Public Access Key** 即可
- 内置 40 种行业的完整 ID 列表（注释在配置文件末尾）

### 运行
```bash
cd Tools/IsBossDead
python main.py
```

### 工作流程
1. 读取 `Industry.ini` 配置（或手动输入）
2. 获取指定行业内所有公司列表
3. 过滤：至少有一定星级且拥有员工的公司
4. 对每个候选公司：
   - 检查老板最近上线时间
   - 如老板离线超过阈值，检查员工活跃情况
   - 如存在活跃员工，标记为目标公司
5. 针对目标公司，获取老板的派系信息
6. 输出 Excel 格式结果，包含直达 Torn 公司页面的链接

### 输出文件
保存至 `Results/Industry_Targets_YYYYMMDD.xlsx`，包含字段：

| 字段 | 说明 |
|------|------|
| CompanyID | 公司 ID |
| CompanyName | 公司名称 |
| DirectorID | 老板 ID |
| DirectorFaction | 老板所属派系 |
| BossOfflineDays | 老板离线天数 |
| ActiveEmployees | 活跃员工数量 |
| DailyIncome | 日收入 |
| CompanyURL | 公司页面直链 |

### 技术细节
- 内置 API 调用频率限制（约 75 次/分钟），避免触发 Torn 官方限流
- 自动检测联邦监狱封禁状态
- 支持重试与限流等待

---

## 🔒 数据安全提示

⚠️ **重要警告**
- 📂 请勿删除或移动 `Database/` 文件夹，否则所有历史记录将永久丢失
- 🔐 `Company.ini` 包含敏感信息（API Key），请勿公开分享或提交到版本控制
- 🛡️ 建议将 `Company.ini` 和 `Industry.ini` 添加到 `.gitignore`

---

## 📝 完整文件结构

```
TornCompanyTool/
├── main.py                   # 核心工具：主程序入口
├── config.py                 # 核心工具：配置与常量定义
├── api_client.py             # 核心工具：API 请求处理
├── data_processor.py         # 核心工具：数据解析与计算
├── excel_handler.py          # 核心工具：Excel 文件读写
├── logger.py                 # 核心工具：日志配置
├── utils.py                  # 核心工具：通用工具函数
├── version_handler.py        # 核心工具：版本升级与兼容处理
├── Company.ini               # 核心工具：配置文件（需自创建）
├── output.ico                # 核心工具：打包用图标
├── Database/                 # 数据库文件夹（自动创建）
├── Report/                   # 报告文件夹（自动创建）
├── logs/                     # 日志文件夹（自动创建）
├── Data/
│   └── Torn_Company_Jobs.xlsx  # 公司岗位参考数据
├── Tools/
│   ├── TrainingManager/        # 员工训练规划工具
│   │   ├── main.py             #    GUI 程序入口
│   │   ├── gui.py              #    Tkinter GUI 界面
│   │   ├── api.py              #    Torn API 调用
│   │   ├── config.py           #    配置读写（JSON）
│   │   ├── constants.py        #    常量与 39 家公司岗位数据
│   │   ├── efficiency.py       #    效率计算公式
│   │   ├── trainer.py          #    训练规划引擎
│   │   ├── report.py           #    报告生成
│   │   ├── output.ico          #    打包用图标
│   │   └── reports/            #    规划报告输出（自动创建）
│   └── IsBossDead/             # 行业招聘侦查工具
│       ├── main.py             #    程序入口
│       ├── api_client.py       #    API 请求与限流
│       ├── config.py           #    配置与常量
│       ├── logger.py           #    日志配置
│       ├── utils.py            #    通用工具函数
│       ├── Industry.ini        #    配置文件（需自创建）
│       ├── output.ico          #    打包用图标
│       └── Results/            #    扫描结果输出（自动创建）
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

### 核心工具（TornCompanyTool）

| 版本 | 发布日期 | 主要更新 |
|------|----------|---------|
| v1.0 | 2026-05-10 | 初始发布 |
| v1.1 | 2026-05-14 | 添加 Xanax 统计与 30 日平均计算 |
| v1.2 | 2026-05-14 | 新增行业数据、优化结构 |
| v1.3 | 2026-05-14 | 修复 Xanax 计算、改为瑞士旅游次数追踪 |
| v1.4 | 2026-05-20 | 修复新员工平均值计算 bug |
| v1.5 | 2026-05-24 | 增加报告中净利润计算，增加版本检查和升级功能 |

### 子工具

| 工具 | 版本 | 发布日期 | 主要更新 |
|------|------|----------|---------|
| TrainingManager | v1.0 | 2026-05-30 | 初始发布，GUI 训练规划 |
| IsBossDead | v0.1 | 2026-05 | 初始版本，核心扫描功能 |
| IsBossDead | v0.2 | 2026-05 | 增加最小星级过滤、Director Faction 信息、加快请求频率 |

---

## 🆘 常见问题

### Q: 程序卡在 "正在请求 API" 如何处理？
A: 可能是 API 限流（100 请求/分钟）。程序会自动等待并重试，或检查网络连接。

### Q: Excel 文件打开时能否运行程序？
A: 不能。程序会提示错误并重试。请关闭 Excel 文件后重新运行。

### Q: 历史数据可以删除吗？
A: **不建议删除**。若要重新开始，可备份后删除 `HistoryDB.xlsx`，程序会重建。

### Q: 如何修改计算平均值的天数？
A: 编辑 `config.py` 中的 `MAX_XAN_DAYS` 参数。

### Q: TrainingManager 和 IsBossDead 有依赖冲突吗？
A: 没有。两个子工具各自独立，只需安装 `requests` 库；TrainingManager 额外需要 Tkinter（Python 内置）。

---

## 📞 反馈与支持

欢迎提交 Issue 和 Pull Request 改进此工具！