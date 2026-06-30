---
author: eric.lin
version: 2.2
---

# 行为准则
- **先想后写**：不确定就提问，有多种解读就呈现出来，有更简单方案就说出来
- **简洁优先**：不写推测性代码、不为单次使用建抽象、不添加未要求的灵活性。200 行能变 80 行就重写
- **精准修改**：只改必须改的，不改相邻代码风格，不改没坏的东西。死代码提出来但别删。每行改动都要能追溯到需求
- **目标驱动**：任务转为可验证目标（"修复 bug" → "写复现测试" → "通过"），多步骤给出计划并逐步验证
- **对话语言**：中文


# 路径规范
- 事实来源（只读）： `.source/`
- 规格文档: `specs/`
- 参考： `references/`
- 规范文档（只读）：`rules/`
- 代码: `src/`
- 测试: `tests/`
- 开发 Phase: `phases/phase-XX-名称/`
- Task 文件夹: `phases/phase-XX-名称/tasks/`
- Task 文件: `phases/phase-XX-名称/tasks/TASK-XXX-简短描述.md`
- 全局快照（只读）：`STATE.json`
- Task 依赖关系图（只读）：`task_graph.json`

## 模块代码路径规范
- 代码文件的路径必须以 `src/` 为前缀（如 `src/services/xxx.py`、`src/app/blueprints/xxx.py`），不允许出现裸模块路径（如 `services/xxx.py`）
- 测试文件的路径必须以 `tests/` 为前缀


## 命名组合规范
- **Phase 文件夹**：必须按 `phase-<序号>-<名称>` 组合，序号从 1 开始，使用阿拉伯数字、零填充两位（如 `phase-01-`、`phase-02-`、…… `phase-99-`），单 phase 不允许跳号。
  - 合法示例：`phases/phase-01-用户认证/`、`phases/phase-02-订单查询/`
  - 非法示例：`phases/phase-1-...`（未零填充）、`phases/phase-001-...`（三位）、`phases/01-...`（缺 `phase-` 前缀）、`phases/phase-02/`（缺名称）
- **Task 文件**：必须按 `TASK-<序号>-<简短描述>.md` 组合，序号从 1 开始，使用阿拉伯数字、零填充三位（如 `TASK-001-`、`TASK-002-`、…… `TASK-999-`），单 phase 内不允许跳号或同号重复。
  - 合法示例：`tasks/TASK-001-环境搭建.md`、`tasks/TASK-002-用户登录接口.md`
  - 非法示例：`tasks/TASK-1-...`（未零填充）、`tasks/TASK-0001-...`（四位）、`tasks/task-001-...`（小写）、`tasks/001-...`（缺 `TASK-` 前缀）
- **序号连续性**：Phase 序号全局递增；Task 序号在所属 Phase 内从 001 起连续。上一 Phase 完成后，下一 Phase 序号 = 上一 Phase 序号 + 1。
- **描述部分**：用简短中文短语（建议 ≤ 12 字），单词之间用连字符 `-` 分隔，不允许空格、不允许中文标点。


## 模板路径
- Task 文件模板（只读）：`.templates/TASK.md`
- 全局快照模板（只读）：`.templates/STATE.json`
- 规格文档模板（只读）：`.templates/specs/`
- 参考索引模板（只读）：`.templates/references.yaml`


# Subagent 通用行为准则
## 事件上报
- 所有 Subagent 必须通过 `mcp__report-event__report_event` 上报事件。
- 参数: `event_type`, `agent_name`, `payload`
- payload 中的路径字段必须遵循：
  - `specs_folder` / `task_folder` / `task_path` 一律使用**相对项目根**的相对路径（Unix 风格正斜杠）
  - **禁止**出现 `task_folders` / `task_paths` 等复数键或列表
  - **禁止**使用绝对路径（以盘符 `E:\` / 根目录 `/` 开头）
  - 调用前若手里是绝对路径，必须用 `os.path.relpath(<abs>, <project_root>)` 化为相对路径

## 落盘前置门（Report-as-Gate）
- **先上报，后落盘**：所有终态事件（TDD_COMPLETED/FAILED、REVIEW_COMPLETED/FAILED、TEST_COMPLETED/FAILED）必须**先成功上报**，然后才允许在 Task 文件中追加 `## 实现摘要` / `## 审查报告` / `## 测试报告` 章节。

## 事件上报自检（通用重试规则）
每次调用 `mcp__report-event__report_event` 后，**必须检查返回值 `ok` 字段**：
- 若 `ok` 不为 `true`，视为本次上报失败，**自动重试**：间隔约 2 秒后重新调用同一 `report_event`，最多重试 3 次
- 若 3 次仍失败，在回复中明确说明"事件上报重试耗尽：<error 内容>"并**立即停止后续动作**（不落盘、不推进状态、不继续下一个 task）
- 此规则适用于所有事件类型（TDD_*/REVIEW_*/TEST_*/PHASE_PLAN_*），各 agent 无需在 workflow 中重复描述


# 开发环境可用工具
- **Node**: `node` 命令直接可用，无需查找路径或验证
- **Python**: `python` 命令直接可用（非 `python3`），无需查找路径或验证
- **Python依赖**：在项目文件夹中自行建立 `.venv`，并安装依赖
- **Docker**: `docker` 命令直接可用，无需查找路径或验证
- **Git**: `git` 命令直接可用，无需查找路径或验证
- **Playwright CLI**: 仅在需要**真实浏览器**端到端测试时使用 `Playwright CLI`，`playwright-cli` 命令直接可用，无需查找路径或验证；如需帮助查看 `skill:playwright-cli` 或运行命令 `playwright-cli --help`。`playwright-cli` 与 `npx playwright-cli` 等价，优先使用 `playwright-cli`
- **Searxng MCP Server**：优先使用 `Searxng` 进行 `web_search`