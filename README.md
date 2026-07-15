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

<img width="1310" height="1706" alt="_E__projects_AI_workspace_260601_agent_garden_1_15_ bin_state-viewer html" src="https://github.com/user-attachments/assets/df09d135-9812-45ec-9aa1-1a9346fe65e9" />

---

## 许可证

MIT
