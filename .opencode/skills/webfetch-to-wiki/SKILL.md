---
name: webfetch-to-wiki
description: Use when the user wants to batch-scrape web pages and build a local browsable wiki from the fetched content. Triggers include "抓取网页做wiki"、"网页保存为本地wiki"、"批量抓取建wiki"、"web scrape to wiki"、"build local wiki from URLs". Also use when the user provides a URL list and asks to create offline-readable HTML documentation.
---

# Webfetch-to-Wiki

## Overview

将用户提供的 URL 列表抓取为本地 HTML 文件包，形成可离线浏览的 wiki。核心原则：**模板先行、并行生成、侧边栏后注入、图片后下载、全量验证**。

## Mandatory Startup Questions

开始任何工作前，必须向用户确认以下 3 个问题。使用 AskUserQuestion 工具一次性询问：

1. **图片处理**：是否下载图片到本地？选项：(A) 下载图片到本地 `images/` 目录，HTML 中使用本地路径；(B) 保留原文中的远程图片 URL，不下载。
2. **显示语言**：页面显示哪种语言？选项：(A) 翻译为中文（仅显示中文译文，不保留原文）；(B) 保留原文语言（仅显示原文，不翻译）。**注意：只输出所选语言，禁止双语对照。翻译时不得删减或歪曲原意。**
3. **侧边栏结构**：wiki 侧边栏树形结构如何生成？选项：(A) 根据用户提供的 URL 列表顺序和层级生成；(B) 由你自行判断——根据页面内容中的链接关系自动推断层级结构。

## HTML 内容约束

每个生成的 HTML 页面正文必须包含以下 4 个结构元素：

| 元素 | 要求 |
|------|------|
| **标题** | `<h1>` 标签，取自源页面 `<title>` 或正文主标题 |
| **正文** | 源页面全部文字内容，保留原文段落、列表、表格结构 |
| **来源** | `<hr>` 分隔后，注明原始 URL 链接 |
| **相邻导航** | 上一页 / 下一页 超链接，连接到 wiki 中相邻页面 |

HTML 标签原则：**极简、可读、易用**。参考 `references/styles.css` 中的选择器即定义了可用标签集：`h1-h3, p, ul, ol, li, table, th, td, blockquote, code, pre, img, hr, a`。不引入额外 CSS 框架或 JS 库。

## 参考模板

本 skill 自带参考文件，位于 `.claude/skills/webfetch-to-wiki/references/`：
- `references/styles.css` — 完整 CSS 样式表，定义所有支持的标签和 CSS 变量
- `references/architecture-center-platforms.html` — 完整的 wiki 页面示例，包含侧边栏结构和正文布局

开始生成前，必须先读取上述两个参考文件，了解：
- CSS 支持的标签集：`h1-h3, p, ul, ol, li, table, th, td, blockquote, code, pre, img, hr, a`
- 页面布局骨架：`body > nav.sidebar` + `main.content`
- 侧边栏树形结构：`<details><summary>` 嵌套模式
- 正文 4 元素：标题(h1)、正文、来源(source)、相邻导航(page-nav)

同时抓取目标 URL 列表中的前 3 个页面，了解源内容结构。

基于参考文件和前 3 个页面内容，生成一个**模板 HTML 文件**（保存为 `wiki/template.html`）。后续所有页面必须以此模板约束结构和标签使用。

初始化时将 `references/styles.css` 复制到 `wiki/styles.css` 作为输出目录的样式文件。

## Workflow

整个流程分 7 个阶段，严格按序执行：

### Phase 1: 询问 & 读取参考
1. 向用户询问 3 个必答问题
2. 读取 `.claude/skills/webfetch-to-wiki/references/styles.css` 和 `.claude/skills/webfetch-to-wiki/references/architecture-center-platforms.html` 作为风格参考
3. 抓取目标 URL 列表的前 3 个页面，了解内容结构
4. 初始化输出目录：创建 `wiki/`、`wiki/pages/`、`wiki/images/`，将 `references/styles.css` 复制到 `wiki/styles.css`

### Phase 2: 生成模板 HTML
1. 基于参考文件和前 3 个页面，生成 `wiki/template.html`
2. 模板包含：完整 `<head>`（charset, title占位, link to styles.css）、侧边栏**占位符** `<!-- SIDEBAR_PLACEHOLDER -->`、正文区域（标题占位、正文占位、来源占位、导航占位）
3. 模板作为后续所有页面的生成约束——所有页面必须使用相同的标签集和结构

### Phase 3: 并行生成页面 HTML
1. 抓取所有目标 URL（页数多时分批并行，每批 ≤ 4 个并发 subagent）
2. 每个 subagent 接收：模板 HTML + 目标 URL + 用户选项（图片/语言）
3. 每个 subagent 产出：填充了正文内容的 HTML 文件，保存到 `wiki/pages/`，侧边栏位置保留占位符 `<!-- SIDEBAR_PLACEHOLDER -->`
4. **图片处理**：无论用户是否选择下载图片，subagent 在 HTML 中**只写入远程图片 URL**（`<img src="https://...">`），不下载、不替换为本地路径。跳过 data URI（`data:image/...`）
5. **语言处理**：如用户选择翻译为中文，正文仅输出中文译文，不保留原文。如选择保留原文，正文仅输出原文。**禁止双语对照**
6. **禁止生成侧边栏**：subagent 不得在 HTML 中生成任何 `<nav class="sidebar">` 或侧边栏相关内容，只保留 `<!-- SIDEBAR_PLACEHOLDER -->` 占位符
7. 文件命名规则：`{序号}-{slug}.html`，序号由 URL 在列表中的位置决定（零填充两位）
8. **相邻导航链接规则**：subagent 必须根据页面在其所在 URL 列表中的位置生成正确的 prev/next 链接。
   - 中间页（非首非尾）：prev 指向 `{前一序号}-{前一slug}.html`，next 指向 `{后一序号}-{后一slug}.html`
   - 首页（序号最小）：prev 留空（`<span class="prev"></span>`），next 指向第二页
   - 末页（序号最大）：next 留空（`<span class="next"></span>`），prev 指向倒数第二页
   - **禁止**：使用完整 URL（如 `https://...`）作为 href 值；使用臆测的文件名（如 `36-schedules.html` 而非实际存在的 `36-data-integration-overview.html`）

### Phase 4: 构建侧边栏
1. 所有页面 HTML 生成完毕后，根据阶段 1 中用户选择的侧边栏结构方案构建导航树
2. 生成侧边栏 HTML 片段，保存为 `wiki/sidebar-content.html`
3. 侧边栏使用 `<details><summary>` 嵌套实现树形折叠（参考 `references/architecture-center-platforms.html` 风格）
4. 当前页面对应的侧边栏项加 `class="active"`

### Phase 5: 注入侧边栏
1. 对每个页面 HTML，先将任何已存在的 `<nav class="sidebar">...</nav>` 整块剥离删除（防止 subagent 意外生成的侧边栏干扰注入）
2. 将 `<!-- SIDEBAR_PLACEHOLDER -->` 替换为实际侧边栏 HTML
3. 同时设置当前页面的 `active` 状态

### Phase 6: 下载图片到本地
**仅当用户在阶段 1 选择了"下载图片到本地"时执行此阶段。**

1. 扫描 `wiki/pages/` 下所有 HTML 文件，提取所有 `src` 为 `http://` 或 `https://` 开头的 `<img>` 标签
2. 收集去重后的远程图片 URL 列表
3. 并行派出 subagent（每批 ≤ 4 个），每个 subagent 负责下载一批图片到 `wiki/images/`
4. 文件名使用 URL 最后一段（保留原始文件名），重名时加序号后缀（`image.png` → `image-2.png`）
5. 下载成功后，在所有 HTML 文件中将该远程 URL 替换为 `../images/文件名`
6. 下载失败的图片保留原始远程 URL 作为 fallback
7. 跳过 data URI（`data:image/...`）——这些在 Phase 3 中已保留原样

### Phase 7: 质量验证
逐项检查：
- **连通性**：每个页面的侧边栏链接和相邻导航链接都指向存在的本地文件，无死链接（404）
- **完整性**：每个页面都包含标题、正文、来源、相邻导航 4 个元素
- **相邻导航完整性**：对每个页面逐一检查 `page-nav` 块：
  - 中间页（非首非尾）：`<span class="prev">` 和 `<span class="next">` 都必须包含有效的 `<a href="...">` 链接，不允许任何一方为空
  - 首页：`prev` 必须为空（`<span class="prev"></span>`），`next` 必须有链接
  - 末页：`next` 必须为空（`<span class="next"></span>`），`prev` 必须有链接
  - 链接目标文件必须实际存在，不允许使用完整 URL（如 `https://...`）替代本地相对路径
  - 文件名必须与 `pages/` 目录中的实际文件名完全一致（零填充两位序号 + 连字符 + slug + `.html`）
- **孤岛检测**：不存在没有被任何其他页面链接引用的孤立页面
- **标签统一**：所有页面使用相同的标签集，与模板一致
- **侧边栏纯净**：所有页面侧边栏结构一致，无残留的独立侧边栏 HTML
- **图片引用**（如选择下载图片）：所有 `<img src>` 指向本地 `images/` 目录且文件存在，无残留远程 URL（下载失败的除外）
- **内容保真**：原文文字内容无删减，翻译无歪曲，无意外双语并存

## HTML 文件结构规范

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>页面标题 — Wiki名称</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <!-- SIDEBAR_PLACEHOLDER -->

  <main class="content">
    <h1>页面标题</h1>
    <p class="section-meta">页面描述或摘要</p>

    <!-- 正文内容：p, ul, ol, table, blockquote, pre, code, img -->

    <hr>
    <p class="source">来源: <a href="原始URL" target="_blank" rel="noopener">原始URL</a></p>

    <div class="page-nav">
      <span class="prev"><a href="上一页.html">← 上一页标题</a></span>
      <span class="next"><a href="下一页.html">下一页标题 →</a></span>
    </div>
  </main>
</body>
</html>
```

## 图片处理细则

图片处理分两步走，在不同阶段完成：

**Phase 3 — subagent 生成 HTML 时：**
- `<img src>` 一律使用远程 URL（`https://...`），不下载、不替换为本地路径
- 如果源页面图片是相对路径，先解析为绝对 URL 再写入
- 跳过 data URI（`data:image/...`），原样保留

**Phase 6 — 全局图片下载与替换（仅当用户选择下载图片时）：**
1. 扫描 `wiki/pages/` 下所有 HTML，提取 `src` 为 `http://` 或 `https://` 的 `<img>` 标签
2. 去重后并行派出 subagent 下载到 `wiki/images/`
3. 文件名使用 URL 最后一段（保留原始文件名便于识别），重名时加序号后缀（如 `image.png` → `image-2.png`）
4. 下载成功后，在所有 HTML 文件中全局替换该远程 URL 为 `../images/文件名`
5. 下载失败的图片保留原始远程 URL 作为 fallback

当用户选择保留远程地址时：
- 跳过 Phase 6，`<img src>` 保持远程 URL 不变

## 翻译细则

当用户选择翻译为中文时：
1. 将正文全部文字内容翻译为中文，页面**仅显示中文译文**，不保留原文
2. 不翻译代码块、URL、技术术语、产品名称
3. 保留原文的段落、列表、表格等全部结构
4. 不删减任何内容，不歪曲原文意思

当用户选择保留原文时：
- 页面**仅显示原文**，不做任何翻译处理

## Common Mistakes

| 错误 | 纠正 |
|------|------|
| 跳过 3 个必答问题直接开始 | 必须先用 AskUserQuestion 确认 |
| 先做侧边栏再生成页面 | 侧边栏在所有页面生成完成后统一注入 |
| subagent 生成的 HTML 包含 `<nav class="sidebar">` | subagent 只能保留 `<!-- SIDEBAR_PLACEHOLDER -->` 占位符，Phase 5 注入前会剥离任何残留侧边栏 |
| 每个页面用不同的 HTML 结构 | 必须基于模板统一约束 |
| 用 JS 动态加载侧边栏 | 侧边栏直接写入 HTML，无 JS 依赖 |
| 引入外部 CSS/JS 框架 | 只用 `styles.css` 中定义的标签和样式 |
| 翻译后同时显示原文和译文（双语对照） | 用户选择哪种语言就只输出那种语言，禁止双语并存 |
| subagent 在 Phase 3 下载图片 | subagent 只写远程 URL，Phase 6 统一并行下载并替换 |
| 图片用 hash 命名 | 保留原始文件名，重名加序号 |
| 忘记检查死链接和孤岛页面 | Phase 7 必须逐项验证 |
| 引用不存在的参考文件路径 | 参考文件位于 `.claude/skills/webfetch-to-wiki/references/`，始终随 skill 存在 |
| 图片下载了但未插入 HTML 正文 | Phase 6 下载成功后全局替换远程 URL 为本地路径 |
| 相邻导航使用完整 URL 而非本地相对路径 | 严禁使用 `https://...` 作为 href，必须使用 `{序号}-{slug}.html` 格式的本地路径 |
| 相邻导航指向不存在的文件名 | 文件名必须与实际 pages/ 目录中的文件完全一致（如 `36-data-integration-overview.html` 而非臆测的 `36-schedules.html`） |
| 中间页（非首非尾）的 prev 或 next 缺了一方 | 中间页必须同时有 prev 和 next 链接，任何一方缺失即为错误 |
| 相邻导航中的文件名缺少 slug 部分（如 `67-security-glossary.html` 而非 `67-security-security-glossary.html`）| 文件名必须包含完整序号+slug，slug 必须是 pages-mapping 中的完整名称 |
