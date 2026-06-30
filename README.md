# Agent Garden

基于 [opencode](https://opencode.ai) 的**多 Agent 协作式自动化软件开发工作流系统**。

通过 Agent 角色定义、MCP Server 和 Skill 的组合，将"需求分析 → 计划 → 编码 → 审查 → 测试 → 验收"全流程自动化。各 Agent 各司其职，严格遵循 TDD，确保每一次代码提交都经过质量把关。

---

## 核心特性

- **多 Agent 协作**  
  `Orchestrator`、`Planner`、`Developer`、`Reviewer`、`Tester` 五个角色协同工作，每个角色只做自己最擅长的事。

- **宪法级 Specs 先行**  
  用户手动调用 `/produce-specs` skill，与 AI 讨论需求后生成 `specs/` 规格文档（proposal.md + design.md + capability spec.md + contracts），作为项目"宪法"贯穿始终。

- **事件驱动状态管理**  
  所有状态变更通过 `report-event` MCP Server 上报，写入结构化日志（`.agent-logs/agent-events.jsonl`），自动从事件日志推导 `STATE.json`，无需手动维护。

- **内置 TDD 闭环**  
  `Developer` 强制采用红-绿-重构循环；`Reviewer` 和 `Tester` 在每次编码完成后立即介入，失败的任务自动回到阻塞状态重试。

- **Phase + Task 原子化拆分**  
  `Planner` 根据 specs 自动拆分为多个 Phase（纵向切片），每个 Phase 包含多个原子化 Task。Task 间支持同/跨 Phase 依赖，由 `task_graph.json` 管理。

- **可观测性与审计**  
  MCP Server 记录每一次事件到 `agent-events.jsonl`，`report-event-server.py` 负责路径规范化、复数数组字段拆分、并发安全写入。每一步都可追溯。

- **经验沉淀**  
  每个 Phase 完成后，`knowledge-condenser` 自动将反模式、审查清单提炼到 `KNOWLEDGE.md`（项目级）和 MCP Memory（跨项目图谱）。

---

## 架构概览

```
用户手动 /produce-specs  →  specs/ (proposal + design + spec + contracts)
                                    ↓
                          Orchestrator (调度器)
                            ├─→ Planner (拆分 Phase + Task)
                            │         ↓
                            │   PHASE_PLAN_COMPLETED 事件
                            │
                            ├─→ Developer (TDD 编码)
                            │         ↓
                            ├─→ Reviewer (代码审查)
                            │         ↓
                            └─→ Tester (自动化测试)
                                      ↓
                                  用户验收
```

核心流程：
1. **用户手动**调用 `/produce-specs` skill → 生成 `specs/` 规格文档
2. **Orchestrator** 检测 specs 变更 → 调度 **Planner** 根据 specs 生成 Phase/Task 文件
3. **Orchestrator** 读取 `STATE.json` + `task_graph.json`，按依赖并行调度 Agent
4. 每个 Task 经历 Developer → Reviewer → Tester 线性闭环
5. 所有状态变更通过 `report-event` MCP 上报 → 事件日志 → `STATE.json` 自动推导

---

## 快速开始

### 1. 前置要求
- opencode CLI 已安装并可用
- Python 3.10+

### 2. 配置 MCP Server
`opencode.json` 已注册 `report-event` MCP 服务器，指向 `.bin/report-event-server.py`。

### 3. 生成 Specs
手动调用 produce-specs skill：
```
/skill produce-specs
```
与 AI 讨论需求后，生成 `specs/` 规格文档。

### 4. 启动 Orchestrator
```bash
opencode --agent orchestrator
```
Orchestrator 检测到 specs 后，自动调度 Planner 拆分 Phase/Task，进入开发循环。

---

## 目录结构

```
├── .opencode/
│   ├── agents/                 # Agent 角色定义 (orchestrator, planner, developer, reviewer, tester)
│   ├── skills/                 # 流程 Skill 定义 (produce-specs, knowledge-condenser, cross-analysis...)
│   └── plugins/                # opencode 插件 (sound-bridge.ts)
├── .bin/                       # 工具脚本
│   ├── report-event-server.py  # 事件报告 MCP Server
│   ├── build_state.py          # 从事件日志重建 STATE.json
│   ├── build_task_graph.py     # 从 Task 文件生成依赖图
│   ├── refresh_state.py        # 合并刷新 STATE.json + task_graph.json
│   ├── check_specs_hash.py     # specs 变更检测
│   └── _common.py              # 共享路径/正则工具
├── .templates/                 # 模板文件
│   ├── TASK.md                 # Task 文件模板
│   ├── STATE.json              # 状态快照模板
│   └── specs/                  # 规格文档模板 (proposal, design, spec, contracts)
├── rules/                      # 开发规范
│   ├── backend-rules.md        # 后端规范 (Controller → Service → Repository)
│   ├── frontend-rules.md       # 前端规范 (组件结构, PRG 模式)
│   ├── database-rules.md       # 数据库规范 (命名, 迁移)
│   └── visual-rules.md         # 视觉检查规范
├── AGENTS.md                   # Agent 行为准则 (路径/命名/事件上报规则)
├── opencode.json               # opencode 配置
├── STATE.json                  # 全局开发进度快照 (由 .bin/build_state.py 自动生成)
└── task_graph.json             # Task 依赖关系图 (由 .bin/build_task_graph.py 自动生成)
```

---

## Agent 角色说明

| 角色 | 职责 | 触发条件 |
|------|------|----------|
| **Orchestrator** | 调度器：检测 specs 变更、刷新状态、按依赖并行调度 sub-agent | 用户指令或 sub-agent 返回 |
| **Planner** | 根据 specs 自动拆分 Phase/Task 文件（不与用户对话） | specs 变更检测 |
| **Developer** | 按 Task 文件 TDD 编码（红-绿-重构） | Task implementation pending/failed |
| **Reviewer** | 代码质量审查（规范、安全、架构一致性） | Task 编码完成 |
| **Tester** | 执行测试验证 | 审查通过 |

---

## 许可证

MIT