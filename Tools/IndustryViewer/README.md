# IndustryViewer - Torn 行业公司数据查询工具

**当前版本：v1.1**

## 概述

单文件 HTML 工具，用于查询 Torn 游戏中指定行业所有公司的详细数据，包括排名、星级、收入、客户数、员工信息等，并提供星级分布分析与晋升门槛预估功能。

## 打开方式

直接用浏览器打开 `IndustryViewer.html` 即可使用，无需安装任何依赖。

## 功能

### 1. 行业公司数据查询
- 支持 39 个 Torn 行业的完整列表（ID 1-40，缺 17）
- 输入 Torn Public API Key（公开只读即可），一次性拉取行业内所有公司
- 数据包括：排名、公司ID、名称、董事、星级、日/周收入、日/周客户、员工雇佣/容量、成立天数
- API Key 支持本地存储（`localStorage`），保存/清除前均有确认提示

### 2. 数据浏览与排序
- 点击任意列表头可按该列升序/降序排序
- 分页功能，支持 10/20/50/100/200 条每页
- 公司名称和董事名称可点击跳转到 Torn 对应页面

### 3. 模糊搜索
- 支持公司名称模糊搜索（150ms 防抖），搜索结果高亮显示
- 支持纯数字精确搜索公司 ID
- 一键清除搜索

### 4. 星级分布与晋升门槛分析
- 各星级实际分布（公司数、占比、柱状图、收入范围）
- 晋升门槛预估（基于"一次只能升/降一星"规则及占位者顺延逻辑）
- 弹窗展示，支持点击遮罩/按 ESC 关闭

## 技术特性

- **纯前端**：无后端依赖，无构建工具，直接打开即用
- **多平台**：兼容 Windows / macOS / Linux 浏览器
- **响应式**：适配桌面端和移动端（≤768px）
- **打印友好**：`@media print` 样式支持打印输出
- **无障碍**：模态弹窗使用 `role="dialog"` / `aria-modal="true"`
- **背景配图**：页面内置半透明背景配图，加载无需额外请求
- **鼠标探照灯**：鼠标周围区域自动透明显示完整背景

## 平台兼容性

| 平台 | 状态 |
|------|------|
| Chrome (Windows/macOS/Linux) | ✅ |
| Firefox (Windows/macOS/Linux) | ✅ |
| Safari (macOS/iOS) | ✅ |
| Edge (Windows) | ✅ |
| 移动端浏览器 | ✅ |

## API 说明

使用 Torn v2 API：

```
GET https://api.torn.com/v2/company/{industry_id}/companies
```

- 自动处理分页（`limit=100, offset`）
- API Key 可通过"保存"按钮存入浏览器 `localStorage`（明文存储，有安全提示）
- 支持 AbortController 取消请求

## 文件结构

```
Tools/IndustryViewer/
├── IndustryViewer.html                # 最终发布文件（构建产物，禁止直接编辑）
├── IndustryViewer_Template.html       # HTML 骨架（含 INJECT_CSS 和 INJECT_JS 占位符）
├── IndustryViewer_Template.css        # 样式模板（独立维护）
├── IndustryViewer_Template.js         # 逻辑模板（独立维护）
├── background.png                     # 背景图片
├── _build.py                          # 构建脚本
└── README.md                          # 本文档
```

## 构建

修改任意 `*_Template.*` 源文件后，运行构建脚本重新生成 `IndustryViewer.html`：

```bash
cd Tools/IndustryViewer
python _build.py
```

构建流程：
1. 读取 `IndustryViewer_Template.html`
2. 读取 `IndustryViewer_Template.css` → 注入 `<!--INJECT_CSS-->`
3. 读取 `IndustryViewer_Template.js` → 注入 `<!--INJECT_JS-->`
4. 注入版本号到 JS（`/*INJECT_VERSION*/` → 实际版本）
5. 读取背景图片 → base64 编码 → 替换 `BG64_PLACEHOLDER_WILL_BE_REPLACED_BY_SCRIPT`
6. 注入版本号到 HTML 注释（`</head>` 前）
7. 写入 `IndustryViewer.html`

> 🚫 **严格禁止直接读取或编辑 `IndustryViewer.html`**。该文件是 `_build.py` 的构建产物，所有修改必须针对 `*_Template.*` 源文件，修改后运行 `_build.py` 重新生成。

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.1 | 2026-06-04 | 重构为多文件注入构建模式；CSS/JS 分离为独立模板文件；新增 API Key 本地存储（localStorage）；背景图片泛化命名；版本号注入（HTML 注释 + 控制台输出） |
| v1.0 | 2026-06-03 | 初始发布，含公司查询、排序、分页、搜索、星级分析、半透明UI、鼠标探照灯 |

## 许可