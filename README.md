# Agent Garden

基于 [Claude Code](https://claude.ai/code) 的**多 Agent 协作式自动化软件开发工作流系统**。

通过 Task 文件后缀状态机、MCP Server 和 Skill 的组合，将“需求分析 → 计划 → 编码 → 审查 → 测试 → 验收”全流程自动化，各 Agent 各司其职，严格遵循 TDD，确保每一次代码提交都经过质量把关。

---

## 核心特性

- **多 Agent 协作**  
  `Orchestrator`、`Architect`、`Developer`、`Reviewer`、`Tester` 五个角色协同工作，每个角色只做自己最擅长的事。

- **文件后缀状态机**  
  `.todo.md` → `.doing.md` → `.done.md` → `.blocked.md`  
  任务文件的后缀即状态，不依赖外部数据库，文件系统就是 ground truth。

- **内置 TDD 闭环**  
  `Developer` 强制采用红-绿-重构循环；`Reviewer` 和 `Tester` 在每次编码完成后立即介入，失败的任务自动回到阻塞状态重试。

- **结构化状态管理（STATE.json）**  
  所有 Phase 和 Task 的进度、依赖、重试次数、事件历史集中存储在 `STATE.json`，可供 Orchestrator 快速决策，也方便随时查看全局进度。

- **可观测性与审计**  
  MCP Server 负责记录每一次事件（`agent-events.jsonl`），同步更新 `STATE.json`，并自动修正文件后缀。每一步都可追溯。

---

## 架构概览

```
用户需求
   ↓
Orchestrator (调度)
   ├─→ Architect (产出 plan.md + .todo.md)
   │         ↓
   │   STATE.json 初始化
   │
   ├─→ Developer (TDD 编码)
   │         ↓
   ├─→ Reviewer (代码审查)
   │         ↓
   └─→ Tester (自动化测试)
             ↓
         用户验收
```

所有状态变更都通过 `report-event` MCP 工具上报，MCP 负责：
- 修改 `.todo.md` 等文件后缀
- 写入结构化日志
- 更新 `STATE.json`

---

## 快速开始

### 1. 前置要求
- Claude Code 已安装并可用
- Python 3.10+，`mcp[cli]` 已安装

### 2. 配置 MCP Server
在 Claude Code 配置中注册 `report-event` MCP 服务器，指向 `report_event_server.py`。  
（具体配置方式请参考 [Claude Code MCP 文档](https://docs.claude.ai/code/mcp)）

### 3. 启动 Orchestrator
```bash
claude --agent orchestrator
```

### 4. 开始第一个需求
直接向 Orchestrator 说出你的需求：
```
我要做一个用户认证系统，包括注册、登录、JWT 鉴权。
```
Orchestrator 会自动调度 Architect 与你讨论、产出计划，然后进入开发循环。

---

## 目录结构

```
├── .claude/
│   ├── agents/                 # Agent 角色定义 (orchestrator, architect, developer, reviewer, tester)
│   ├── hooks/                  # Claude Code Hooks 定义
│   └── skills/                 # 流程 Skill 定义
├── docs/                       # 项目文档
├── converted/                  # MD 转换 HTML 输出
├── prototype/                  # 原型文件
├── specs/                      # 代码规范文档
│   ├── database-rules.md       # 数据库规范
│   └── visual-rules.md         # 视觉品味验证规则
├── src/                        # 项目源码
├── tests/                      # 测试代码
├── reports/                    # 测试报告
├── STATE.json                  # 全局开发进度快照
└── .claude-logs/               # 结构化事件日志
```

---

## 许可证

MIT
```

这样一份 README 能清晰地向访问者说明项目的意图、架构和用法，同时保持简洁。你可以根据需要进一步添加示例动画或链接。