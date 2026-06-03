# IndustryViewer - Torn 行业公司数据查询工具

## 概述

单文件 HTML 工具，用于查询 Torn 游戏中指定行业所有公司的详细数据，包括排名、星级、收入、客户数、员工信息等，并提供星级分布分析与晋升门槛预估功能。

## 打开方式

直接用浏览器打开 `IndustryViewer.html` 即可使用，无需安装任何依赖。

## 功能

### 1. 行业公司数据查询
- 支持 40 个 Torn 行业的完整列表
- 输入 Torn API Key（v2），一次性拉取行业内所有公司
- 数据包括：排名、公司ID、名称、董事、星级、日/周收入、日/周客户、员工雇佣/容量、成立天数

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
- **暗色模式**：跟随系统 `prefers-color-scheme: dark`
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
- API Key 不会持久化存储，仅在当前会话有效
- 支持 AbortController 取消请求

## 文件结构

```
Tools/IndustryViewer/
├── IndustryViewer.html          # 主文件（单文件 HTML，含 base64 背景图）
├── IndustryViewer_Template.html # 模板文件（图片占位符，用于修改后重新生成）
└── README.md                    # 本文档
```

## 重新生成

如果修改了 `IndustryViewer_Template.html`，运行以下 Python 脚本重新注入背景图：

```python
import base64
with open("background.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
with open("IndustryViewer_Template.html", encoding="utf-8") as f:
    html = f.read()
html = html.replace("BG64_PLACEHOLDER_WILL_BE_REPLACED_BY_SCRIPT", f'url("data:image/png;base64,{b64}")')
with open("IndustryViewer.html", "w", encoding="utf-8") as f:
    f.write(html)
```

## 更新日志

- **v1.0** (2026-06-03)
  - 初始版本
  - 包含公司查询、排序、分页、搜索、星级分析等完整功能
  - 多平台支持、暗色模式、打印样式、无障碍
  - 背景配图与鼠标探照灯效果

## 许可