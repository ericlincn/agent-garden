# Agent Garden

基于 [opencode](https://opencode.ai) 的**多 Agent 协作式自动化软件开发工作流系统**。

通过 Agent 角色定义、MCP Server 和 Skill 的组合，将"需求定义 → 规格评审 → 计划 → 编码 → 审查 → 测试 → 体验探索 → 复盘"全流程自动化。各 Agent 各司其职，严格遵循 TDD，确保每一次代码提交都经过质量把关。

---

## 核心特性

- **多 Agent 协作**  
  `Orchestrator`、`Planner`、`Developer`、`Reviewer`、`Tester`、`Explorer` 六个角色协同工作，每个角色只做自己最擅长的事。

- **事实来源驱动**  
  用户手动在 `.source/` 中编写项目需求、资源、灵感、用户体验流程，作为项目一切决策的事实来源。

- **宪法级 Specs 先行**  
  用户调用 `skills:/produce-specs`，基于 `.source/` 内容生成 `specs/` 规格文档（proposal.md + design.md + capability spec.md + contracts），作为项目"宪法"贯穿始终。

- **Requirement Council 三方审查**  
  `produce-specs` 自动并行调度 Builder（功能完整性）、Breaker（异常路径）、Operator（长期运维）三个视角审查 specs，由 Merge Agent 合并去重冲突检测后写入，确保规格无遗漏。

- **事件驱动状态管理**  
  所有状态变更通过 `report-event` MCP Server 上报，写入结构化日志（`.agent-logs/agent-events.jsonl`），自动从事件日志推导 `STATE.json`，无需手动维护。

- **内置 TDD 闭环**  
  `Developer` 强制采用红-绿-重构循环；`Reviewer` 和 `Tester` 在每次编码完成后立即介入，失败的任务自动回到阻塞状态重试。

- **UX 旅程探索**  
  每 Phase 任务完成后，`Explorer` 以 Novice / Abuser / Power User 三轮视角真实浏览 web 应用，发现规格未覆盖的体验缺口，写入 `discoveries/`。

- **Phase + Task 原子化拆分**  
  `Planner` 根据 specs 自动拆分为多个 Phase（纵向切片），每个 Phase 包含多个原子化 Task。Task 间支持同/跨 Phase 依赖，由 `task_graph.json` 管理。

- **可观测性与审计**  
  MCP Server 记录每一次事件到 `agent-events.jsonl`，`report_event_server.py` 负责路径规范化、并发安全写入。每一步都可追溯。

- **经验沉淀**  
  每 Phase 完成后，`knowledge-condenser` 自动将反模式、审查清单提炼到 `KNOWLEDGE.md`（项目级）和 MCP Memory（跨项目图谱）。

---

## 使用流程

```
User 写 .source/  (需求/资源/灵感/用户体验流程)
        ↓
User 调用 skills:/produce-specs  (自动含 Requirement Council 三方审查)
        ↓
User 对 orchestrator 说 "开始执行" / "继续执行"
        ↓
Orchestrator 运行 schedule.py
    ├─→ Planner (拆分 Phase + Task)
    ├─→ Developer (TDD 编码)
    ├─→ Reviewer (代码审查)
    ├─→ Tester (自动化测试)
    └─→ Explorer (UX 旅程探索)
              ↓
         knowledge-condenser (复盘沉淀)
              ↓
         下一 Phase 或 全部完成
```

核心流程：
1. **用户**在 `.source/` 中编写项目需求、资源、灵感、UX 旅程
2. **用户**调用 `skills:/produce-specs` → skill 读取 `.source/` 生成 `specs/` 规格文档，自动触发 Requirement Council（Builder + Breaker + Operator）三方审查
3. **用户**对 orchestrator 说"开始执行"或"继续执行"
4. **Orchestrator** 运行 `.bin/schedule.py` 获取调度决策，按依赖并行调度 Agent
5. 每 Task 经历 Developer → Reviewer → Tester 线性闭环
6. 每 Phase 全部 Task 完成后，**Explorer** 启动三轮 UX 旅程探索，发现体验缺口
7. Exploration 通过后，**knowledge-condenser** 复盘沉淀经验
8. 所有状态变更通过 `report-event` MCP 上报 → 事件日志 → `STATE.json` 自动推导

---

## 快速开始

### 1. 前置要求
- opencode CLI 已安装并可用
- Python 3.10+

### 2. 配置 MCP Server
`opencode.json` 已注册 `report-event` MCP 服务器，指向 `.bin/report_event_server.py`。

### 3. 编写需求
在 `.source/` 中编写项目需求、资源、灵感、用户体验流程（支持 `.md`、`.txt`、`.yaml`、`.json`、`.pdf`）。

### 4. 生成 Specs
调用 produce-specs skill：

```
/skill produce-specs
```

skill 自动读取 `.source/` 内容，与用户讨论后生成 `specs/` 规格文档，并自动执行 Requirement Council 三方审查。

### 5. 启动 Orchestrator

```
opencode --agent orchestrator
```

Orchestrator 运行 `.bin/schedule.py`，自动调度 Planner → Developer → Reviewer → Tester → Explorer → knowledge-condenser 全流程。

---

## 目录结构

```
├── .opencode/
│   ├── agents/                    # Agent 角色定义
│   │   ├── orchestrator.md        # 调度器
│   │   ├── planner.md             # 计划拆分
│   │   ├── developer.md           # TDD 编码
│   │   ├── reviewer.md            # 代码审查
│   │   ├── tester.md              # 测试验证
│   │   ├── explorer.md            # UX 旅程探索
│   │   ├── architect-breaker.md   # Requirement Council 异常路径视角
│   │   ├── architect-builder.md   # Requirement Council 功能完整性视角
│   │   ├── architect-operator.md  # Requirement Council 长期运维视角
│   │   └── architect-merge.md     # Requirement Council 合并去重
│   ├── skills/
│   │   ├── produce-specs/         # 规格文档生成 Skill
│   │   └── knowledge-condenser/   # 经验沉淀 Skill
│   └── plugins/
├── .bin/                          # 工具脚本
│   ├── schedule.py                # 调度决策引擎
│   ├── report_event_server.py     # 事件报告 MCP Server
│   ├── build_state.py             # 从事件日志重建 STATE.json
│   ├── build_task_graph.py        # 从 Task 文件生成依赖图
│   ├── refresh_state.py           # 合并刷新 STATE.json + task_graph.json
│   ├── check_content_changed.py   # specs/discoveries 变更检测
│   ├── check_specs_existed.py     # specs 存在性检测
│   ├── check_spec_scenario_coverage.py
│   ├── check_phases_existed.py
│   ├── check_task_dependencies.py
│   ├── get_discoveries_count.py
│   ├── get_discoveries_list.py
│   ├── play_sound.py
│   └── _common.py                 # 共享路径/正则工具
├── .source/                       # 事实来源（需求/资源/灵感/UX）
├── .templates/                    # 模板文件
│   ├── TASK.md                    # Task 文件模板
│   ├── STATE.json                 # 状态快照模板
│   ├── discovery.md               # Discovery 文件模板
│   └── specs/                     # 规格文档模板
├── .rules/                        # 开发规范
├── AGENTS.md                      # Agent 行为准则
├── opencode.json                  # opencode 配置
├── STATE.json                     # 全局开发进度快照
└── task_graph.json                # Task 依赖关系图
```

---

## Agent 角色说明

| 角色 | 职责 | 触发条件 |
|------|------|----------|
| **Orchestrator** | 调度器：运行 `schedule.py`，按决策并行调度 sub-agent | 用户指令含"执行/开发/开始/继续" |
| **Planner** | 根据 specs 自动拆分 Phase/Task 文件 | specs/discoveries 变更检测 |
| **Developer** | 按 Task 文件 TDD 编码（红-绿-重构） | Task implementation pending/failed |
| **Reviewer** | 代码质量审查（规范、安全、架构一致性） | Task 编码完成 |
| **Tester** | 执行测试验证 | 审查通过 |
| **Explorer** | 以 Novice / Abuser / Power User 三轮视角探索 web 应用 | Phase 内全部 Task completed |
| **architect-builder** | Requirement Council 成员 — 功能完整性视角 | produce-specs skill 调用 |
| **architect-breaker** | Requirement Council 成员 — 异常路径视角 | produce-specs skill 调用 |
| **architect-operator** | Requirement Council 成员 — 长期运维视角 | produce-specs skill 调用 |
| **architect-merge** | Requirement Council 合并去重冲突检测 | 三方审查完成后 |

---

## 许可证

MIT
