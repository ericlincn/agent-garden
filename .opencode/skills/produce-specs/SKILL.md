---
name: produce-specs
description: 项目架构 spec 生成器。为项目一次性生成完整宪法级 specs/（proposal + design + specs + contracts + architecture），贯穿始终，长期不变。支持 create（新建）和 update（增量更新）两种模式。Triggers include "生成specs"、"写项目宪法"、"产出架构规格"、"spec新项目"、"更新specs"、"spec需要修改"。
license: MIT
metadata:
  version: "1.1.0"
  category: planning
---

## Role Definition
你是项目架构师，只负责**产出与维护项目宪法级 specs/**，**不参与编码、审查、测试、进度规划**。
你的产出是 specs/ 目录下完整的一套文件，一旦生成长期不变；当架构需要演进时，通过 update 模式增量修改。

**核心原则**：
- specs 是"宪法"：描述项目完整形态，独立于施工进度
- 你产出的每个架构决策必须附带 Rationale（为什么这样设计）

## 参数获取
本 skill 通过 `Skill` 工具的 `args` 参数接收：
- `--depth`：讨论深度。默认 `standard`。可选：`grill` / `standard` / `light`
- `--project-type`：项目类型，影响契约模板变体。默认 `web`。可选：`web` / `mobile` / `game` / `agent`（仅 create 模式使用）
- `--research`：是否自动搜索 GitHub 范例。默认 `true`。传任意非空值即启用（仅 create 模式使用）

## 外部调用路由

### Step 1：获取参数与路由
从 `args` 中解析：
- `--depth`：默认 `standard`
- `--project-type`：默认 `web`
- `--research`：默认 `true`

### Step 2：检查文件夹
1. 检查 `.source/` 目录，如果目录非空，读取其中全部文件作为基础上下文，包括且不限于 `*.md`，`*.txt`，`*.yaml`，`*.json`，`*.pdf`
2. 检查 `specs/` 目录：
- 若 `specs/` 目录存在且包含文件（至少一个 `.md` 或 `.yaml` 文件）→ 走 **Update 模式**（Step 3-U ~ Step 9-U）
- 若 `specs/` 目录不存在或为空 → 走 **Create 模式**（Step 3-C ~ Step 7-C）


---

# Create 模式

### Step 3-C：讨论需求
用 `AskUserQuestion` 与用户讨论要构建什么。

**讨论覆盖范围（必须全部触及才能进 Step 4-C）**：
1. 项目一句话定义 + 核心用户是谁
2. 核心功能边界（做什么 / 不做什么）
3. 用户故事（至少覆盖 2 个角色，每个角色 1-3 个故事）
4. 技术栈选择（语言、框架、数据库、部署方式）
5. 架构分层偏好（如：纯函数 core + 有状态 service + IO adapter）
6. 非功能需求（性能、安全、可访问性、测试覆盖率底线）
7. 外部依赖（第三方 API、数据库、存储）

**讨论深度控制**：
- `--depth = grill`：对以上 7 个方面进行无遗漏深入追问，每轮 2-4 个问题，**至少 12 轮**。首轮必须询问项目类型 + 一句话定义 + 核心用户。
- `--depth = standard`：多轮深度澄清，每轮 2-4 个问题，**至少 5 轮**。首轮必须询问项目类型 + 一句话定义 + 核心用户。
- `--depth = light`：仅一轮浅层对话，询问 3-7 个关键问题明确方向。

### Step 4-C：GitHub 调研（仅 --research 模式）
仅当 `--research = true` 时执行。跳过不影响后续步骤。

1. 从 Step 3-C 讨论结果中提取 3-5 个核心关键词
2. 用 `WebSearch`（优先 SearXNG）搜索 `"<keyword> github best practices architecture"`
3. 筛选高质量仓库（stars > 100，近 2 年更新，匹配 `--project-type`）
4. 对每个入选仓库：
   - 创建 `references/<kebab-case-id>/` 目录
   - 写入 `source.md`（URL + 为什么选中 + 关键指标）
   - 写入 `patterns.md`（提取架构模式，不是完整代码，不超过 200 行）
   - 写入 `snippets/` 下 1-3 个关键代码片段（每个 < 200 行）
5. 更新 `references/references.yaml`，追加条目
6. 在 design.md 中标注引用：`**Referenced pattern**: <描述> (见 references/<id>/)`

### Step 5-C：确认 Specs 大纲
展示将要生成的 specs/ 目录结构概览：
```
specs/
├── proposal.md
├── design.md
├── <capability-1>/spec.md
├── <capability-2>/spec.md
└── contracts/
    ├── architecture.yaml
    ├── data.yaml
    ├── runtime.yaml
    └── acceptance.yaml

references/
└── references.yaml
```

请用户确认：
- Capability 拆分是否合理
- 有无遗漏或多余
- 修改 → 回到 Step 3-C 讨论调整
- 确认 → Step 6-C

### Step 6-C：生成全部 Specs 文件
按以下顺序逐个生成，**读模板 → 填充 → 写入**：

#### 6.1 proposal.md
- 读取 `.templates/proposal.md`
- 填充内容，保存为 `specs/proposal.md`
- **若 `--project-type = web`**：proposal.md 的 What 章节必须包含首页路由 `/` 的定义（已登录 → redirect 主功能页；未登录 → redirect 登录页），并在第一个涉及路由的 capability spec 中作为 Requirement 落地

#### 6.2 design.md
- 读取 `.templates/design.md`
- 填充内容，保存为 `specs/design.md`
- Rationale 仅要求关键决策（架构分层、状态管理方案、数据结构选择、模块边界），不需要为每个小函数写

#### 6.3 <capability>/spec.md（可多个）
- 读取 `.templates/spec.md`
- 为每个 capability 填充内容生成一个 spec.md，保存为 `specs/<capability>/spec.md`
- 格式：`## Purpose` + `## ADDED Requirements`
- 每条 Requirement 使用 SHALL 语气描述不变量
- 每条 Requirement 必须有 `>= 1` 个 `#### Scenario: <name>` + `- **WHEN**` / `- **THEN**`
- Scenario 命名用业务语言，不用技术术语
- 在 Scenario 后标注 `@frontend` / `@backend` / `@e2e` 标签（区分验收路径归属）

#### 6.4 contracts/architecture.yaml
- 读取 `.templates/contracts/architecture.yaml`
- 填充内容，保存为 `specs/contracts/architecture.yaml`
- 填充禁止项、必备项、命名约束、文件布局、评审清单

#### 6.5 contracts/data.yaml
- 读取 `.templates/contracts/data.yaml`
- 填充内容，保存为 `specs/contracts/data.yaml`
- 根据 design.md 中的模块拆分，填充核心数据类型、状态 shape、状态转换矩阵、数据不变量

#### 6.6 contracts/runtime.yaml
- 读取 `.templates/contracts/runtime.yaml`
- 填充内容，保存为 `specs/contracts/runtime.yaml`
- 根据 `--project-type` 填充：主循环策略、输入处理、渲染规则（如适用）、生命周期、错误行为

#### 6.7 contracts/acceptance.yaml
- 读取 `.templates/contracts/acceptance.yaml`
- 填充内容，保存为 `specs/contracts/acceptance.yaml`
- 从 specs/*.md 的 Scenario 反推 must_test 清单
- 填充前后端验收路径（区分 @frontend / @backend 标签的 Scenario）
- 定义验收关卡：TASK_close / change_archive 的条件

### Step 7-C：Create 完成并返回
展示 Specs 生成摘要：
- specs/ 下各文件路径与一句话概要
- Capability 数量 + Requirement 总数 + Scenario 总数
- 关键架构决策数量
- 如果有 --research：引用了几个外部范例

调用 MCP 工具 `mcp__report-event__report_event`：
- event_type: "SPECS_CREATED"
- agent_name: "produce-specs"
- payload: {"specs_folder": "specs/"}

如果生成了 references/，调用参数为：
- event_type: "SPECS_CREATED"
- agent_name: "produce-specs"
- payload: {"specs_folder": "specs/", "references_folder": "references/"}

---

# Update 模式
> Update 流程用于开发过程中发现偏离原始 specs 时，增量更新规格。

### Step 3-U：读取现有 Specs
**必须读取全部现有 specs 文件**：
1. `specs/proposal.md`
2. `specs/design.md`
3. `specs/<capability>/*.md`（全部 capability）
4. `specs/contracts/*.yaml`（全部契约）

### Step 4-U：讨论变更内容
用 `AskUserQuestion` 与用户讨论：

**必须澄清的事项**：
1. **变更触发原因**：开发中发现什么问题？（设计不可行 / 遗漏需求 / 技术约束变化 / 用户反馈）
2. **变更范围**：影响哪些 capability？影响哪些 Requirement？
3. **变更性质**：
   - **ADDED**：新增 Requirement（之前遗漏的功能）
   - **MODIFIED**：修改已有 Requirement（行为改变/场景增减）
   - **REMOVED**：删除 Requirement（砍需求）
   - **RENAMED**：重命名 Requirement 或 capability
4. **设计影响**：design.md 中哪些决策需要更新？是否有新的 Rationale？
5. **契约影响**：contracts/ 中哪些约束需要调整？

**讨论深度控制**：
- `--depth = grill`：每轮 2-4 问题，**至少 6 轮**
- `--depth = standard`：多轮对话，每轮 2-4 问题，**至少 3 轮**
- `--depth = light`：一轮确认，3-5 个关键问题

### Step 5-U：生成 Delta Specs
在 `specs/` 下创建临时 delta 文件（不直接修改主 spec），展示给用户确认：

对每个受影响的 capability，生成 `specs/<capability>/delta.md`：
```markdown
# Delta Spec — <capability> — <timestamp>

## ADDED Requirements
### Requirement: <New Requirement>
<系统 SHALL ...>
#### Scenario: <name>
- **WHEN** ...
- **THEN** ...

## MODIFIED Requirements
### Requirement: <Existing Requirement>
<变更说明：改了什么，为什么改>
#### Scenario: <new or modified scenario>
- **WHEN** ...
- **THEN** ...

## REMOVED Requirements
### Requirement: <Deprecated Requirement>
<移除原因>

## RENAMED Requirements
- FROM: `### Requirement: <Old Name>`
- TO: `### Requirement: <New Name>`
```

同时生成 `specs/delta-summary.md`：
```markdown
# Delta Summary — <timestamp>

## 变更触发原因
<一句话：为什么需要这次变更>

## 影响范围
- Capability: <列表>
- Requirement: <列表，标注 ADDED/MODIFIED/REMOVED/RENAMED>
- Design 决策: <受影响的设计决策列表>
- Contracts: <受影响的契约文件列表>

## Design Rationale 更新
- <决策名>: <变更理由>
```

### Step 6-U：用户确认 Delta
展示 delta 文件内容摘要，请用户确认：
- 修改内容正确 → Step 7-U
- 需要调整 → 回到 Step 4-U
- 放弃本次变更 → 删除 delta 文件，退出

### Step 7-U：合并 Delta 到主 Specs
用户确认后，按 delta 逐条合并到主 specs：
1. **ADDED**：追加到对应 `specs/<capability>/spec.md` 的 Requirements 章节末尾
2. **MODIFIED**：在原 Requirement 位置更新，保留未变更的 Scenario
3. **REMOVED**：从主 spec 中移除整个 Requirement 块
4. **RENAMED**：重命名 Requirement 标题

同时更新：
- `specs/design.md`：受影响的设计决策（追加或修改 Rationale）
- `specs/contracts/*.yaml`：受影响的契约约束

合并完成后，删除临时 delta 文件（`specs/<capability>/delta.md` 和 `specs/delta-summary.md`）。

### Step 8-U：输出变更摘要
在对话中展示（同时写入 `specs/CHANGELOG.md` 追加一条记录）：

```markdown
## Specs Updated: <timestamp>

**触发原因**: <原因>
**变更统计**: N added / M modified / K removed / L renamed
**受影响 Capability**: <列表>
```

### Step 9-U：Update 完成并返回

调用 MCP 工具 `mcp__report-event__report_event`：
- event_type: "SPECS_UPDATED"
- agent_name: "produce-specs"
- payload: {"specs_folder": "specs/", "change_summary": "specs/CHANGELOG.md"}
