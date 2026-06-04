# IsBossDead — 行业招聘侦查工具

**当前版本：v1.1**

## 概述

CLI 工具，扫描指定行业中"老板长时间离线但仍有活跃员工"的公司，输出候选收购/挖角目标。通过老板状态缓存机制大幅减少重复扫描时的 API 请求量。

## 运行

```bash
cd Tools/IsBossDead
python main.py
```

## 配置文件（Industry.ini）

```ini
[Settings]
BossOfflineDays = 3          ; 老板离线多少天视为目标
EmployeeActiveDays = 1       ; 员工多少天内活跃视为目标
MinimumStarRating = 3        ; 最低星级过滤
ApiKey = Your_Public_Access_API_Key_Here
IndustryID = Your_IndustryID_Here
```

- API Key 使用 **Public Access Key** 即可
- 内置 39 种行业的完整 ID 列表（ID 1-40，缺 17）

## 功能

- 通过 v2 API 获取行业全部公司列表
- 过滤：达到最小星级 + 有员工 + 老板离线超阈值 + 有近期活跃员工
- **老板状态缓存**：将 `last_action` 时间戳缓存至 Excel（`Database/Industry_BossDB_{IndustryID}.xlsx`），二次扫描跳过离线未达阈值公司
- 自动获取目标公司老板派系信息
- 输出 Excel 结果含公司直链

## 工作流程

1. 验证网络 → 读取配置 → 拉取行业公司列表
2. 过滤（星级 + 有员工）→ 加载缓存数据库
3. 逐公司：
   - 缓存预判 → API 查询老板状态
   - 未达离线阈值：记录时间戳到缓存，跳过
   - 达到离线阈值：检查员工活跃 → 标记目标公司
4. 为每个目标公司：查询老板派系 → 保存结果 Excel
5. 保存更新后的缓存数据库

## 输出文件

### 扫描结果
`Results/Industry_Targets_YYYYMMDD.xlsx`

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

### 缓存数据库
`Database/Industry_BossDB_{IndustryID}.xlsx`

| 字段 | 说明 |
|------|------|
| CompanyID | 公司 ID |
| DirectorID | 老板 ID |
| BossLastActionTS | 最后活跃时间戳（Unix timestamp） |

## 技术细节

- **老板状态缓存**：缓存所有公司老板的 `last_action` 时间戳，二次扫描时跳过离线未达阈值的公司，大幅减少 API 请求
- API 调用频率限制：约 75 次/分钟（间隔 0.8 秒）
- 自动检测联邦监狱封禁状态
- 支持重试与限流等待

## 文件结构

```
IsBossDead/
├── main.py            # 入口 + 核心扫描逻辑
├── api_client.py      # API 请求 + 限流
├── config.py          # 常量 + Session 单例
├── logger.py          # 日志初始化
├── utils.py           # 通用工具 + 装饰器
├── Industry.ini       # 用户配置文件（需自创建）
├── output.ico         # 打包图标
├── Database/          # 老板缓存（自动创建）
└── Results/           # 扫描结果（自动创建）
```

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v0.1 | 2026-05-22 | 初始版本，核心扫描功能 |
| v0.2 | 2026-05-22 | 增加最小星级过滤、Director Faction 信息、加快请求频率 |
| v1.0 | 2026-05-31 | 新增老板状态数据库缓存机制，大幅减少重复扫描时的 API 请求量 |
| v1.1 | 2026-06-02 | 行业数据 API 升级到 v2，支持分页获取全部行业公司数据 |