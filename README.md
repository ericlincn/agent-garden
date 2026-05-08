# 🌱 Agent Garden

> 一个基于 Claude Code 的工程化多智能体开发工作流，用文件后缀状态机驱动从需求到验收的全流程自动化。

## ✨ 核心理念

- **文件即状态**：通过 `.todo.md` → `.doing.md` → `.done.md` → `.blocked.md` 的文件重命名，无需任何外部工具即可可视化管理项目进度。
- **Agent 专业化**：五位角色各司其职（总指挥、架构师、开发者、审查员、测试员），严格遵循 TDD 与审查流程。
- **工程化而非提示词堆砌**：流程、规范、接口定义在 Markdown 文件中，可版本控制、可审计、可共享。

## 🚀 快速开始

### 1. 前置条件
- 安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
- 拥有 Anthropic API 密钥或已登录

### 2. 克隆或下载本仓库

### 3. 启动 Claude Code

首次启动会自动加载 `.claude/agents/` 下的子智能体定义。输入 `/new-feature` 即可开始第一个功能开发。

## 📂 目录结构
```
.
├── .claude/
│   ├── agents/                # 五个 Agent 定义
│   │   ├── orchestrator.md
│   │   ├── architect.md
│   │   ├── developer.md
│   │   ├── reviewer.md
│   │   └── tester.md
│   ├── commands/              # 用户命令
│   │   ├── new-feature.md
│   │   ├── insert-task.md
│   │   └── milestone.md
│   └── skills/
│       └── knowledge-condenser/SKILL.md   # 经验沉淀
├── specs/                     # 代码规范
│   ├── frontend-rules.md
│   ├── backend-rules.md
│   └── database-rules.md
├── AGENTS.md                  # 项目导航索引
├── CLAUDE.md                  # 全局执行规范
├── PROJECT-SPEC.md            # (可选) 项目专属环境配置
└── README.md
```

运行时产生的所有 Phase 数据均在 `phases/` 目录下，不会污染其他配置。

## 🧠 Agent 角色

| Agent | 职责 | 关键动作 |
|:---|:---|:---|
| **Orchestrator** | 总指挥、流程调度 | 解析用户意图、派发任务、管理 Phase 生命周期 |
| **Architect** | 系统架构师 | 与用户讨论需求、产出原子化计划和 `.todo.md` 任务文件 |
| **Developer** | 开发者 | 严格遵循 TDD 编写代码和测试，维护文件状态流转 |
| **Reviewer** | 代码审查员 | 对照 `specs/` 规范审查代码，不通过则打回 `.blocked.md` |
| **Tester** | 测试员 | 执行单元/集成/回归测试，处理用户黑盒反馈回流 |

## 🔄 工作流

### 标准开发流程
输入 `/new-feature`
```
用户需求 → Architect 产出计划 → 用户确认 → Developer TDD 编码 → Reviewer 审查 → Tester 测试 → 用户验收
```
所有任务文件通过后缀自动可视化当前状态。

### 紧急修复流程
输入 `/new-feature` + “紧急！修某个 Bug”：
```
跳过 Architect → Orchestrator 补写简要计划 → Developer TDD  → 轻量测试 → 用户验收
```

### 插入任务
使用 `/insert-task` 在已有 Phase 中插入新需求。

### 里程碑
使用 `/milestone` 生成进度快照并沉淀经验到 `KNOWLEDGE.md`。

## 🛠 自定义规范

- 编辑 `specs/` 下的三个规范文件，定制代码审查标准。当前规范极度精简，仅强调人类可读性。
- 通过 `PROJECT-SPEC.md` 指定私有库等本地配置。

## 📜 许可
MIT License
