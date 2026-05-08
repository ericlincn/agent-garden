---
author: eric.lin
version: 1.06
---

# 全局执行规范
- Task 文件后缀状态机（`.todo.md` → `.doing.md` → `.done.md` → `.blocked.md`）驱动的从需求到验收的全流程自动化
- Agents 各司其职（Orchestrator、Architect、Developer、Reviewer、Tester），严格遵循 TDD 与审查测试流程

## Task 文件状态流转
| 文件后缀 | 谁来变更后缀 | 后续动作 |
|:---|:---|:---|
| `.todo.md` | Architect.产出计划(用户消息) 创建 | Developer.TDD编码(`.todo.md`) |
| `.doing.md` | Developer.TDD编码(`.todo.md`) 开始时重命名 |  |
| `.done.md` | Developer.TDD编码(`.todo.md`) 完成时重命名 | Reviewer.审查(`.done.md`) |
| `.blocked.md` | Reviewer.审查(`.done.md`) 失败 或 Tester.测试(`.done.md`) 失败 时重命名 | Developer.TDD编码(`.blocked.md`) |

## 核心流程
- 标准流程：用户需求 → Orchestrator.新建流程(用户消息) → Architect.产出计划(用户消息) → Developer.TDD编码(`.todo.md`) → Reviewer.审查(`.done.md`) → Tester.测试(`.done.md`) → 用户验收
- 紧急流程：用户需求 → Orchestrator.新建流程(用户消息) → Developer.TDD编码(`.todo.md`) → Reviewer.轻量审查(`.done.md`) → Tester.轻量测试(`.done.md`) → 用户验收
- 插入任务：用户需求 → Orchestrator.插入任务(用户消息) → Architect.增量评估(用户消息) → Developer.TDD编码(`.todo.md`) → Reviewer.审查(`.done.md`) → Tester.测试(`.done.md`) → 用户验收
- 仅测试：用户提出测试范围和测试要求 → Orchestrator.仅测试(用户消息) → Tester.测试(`.done.md`) → 用户查看报告

## 流程规范
- **强制遵循核心流程**: 不可打乱流程顺序，不可跳过任一流程
- **用户验收必须等待**：Tester.测试 成功完成后，Orchestrator **必须**向用户发送黑盒测试邀请（如"请进行黑盒测试验收，通过请回复'验收通过'，发现问题请描述"），并**阻塞等待用户输入**，不得自动结束 Phase。
- **子Agent调用规则**：Orchestrator 调用任何子Agent时，必须在任务描述中明确引用对应的 `specs/` 规范文件路径

## 路径规范
- 代码: `{project-root}/src/`
- 测试: `{project-root}/tests/`
- 规范文档: `{project-root}/specs/`
- 开发 Phase: `{project-root}/phases/phase-XX-名称/`
- Plan 文件: `{project-root}/phases/phase-XX-名称/plan.md`
- Task 文件夹: `{project-root}/phases/phase-XX-名称/tasks/`
- Task 文件: `{project-root}/phases/phase-XX-名称/tasks/TASK-XXX-简短描述.todo.md`
- 日志文件夹: `{project-root}/phases/phase-XX-名称/logs/`
- 日志文件: `{project-root}/phases/phase-XX-名称/logs/{Agent名}.log`
- 质量报告: `{project-root}/phases/phase-XX-名称/quality-report.md`

## 规范文档
所有子 Agent 必须遵守以下规范，在执行任何操作前必须 Read 对应文件：
- 前端代码：`specs/frontend-rules.md`
- 后端代码：`specs/backend-rules.md`
- 数据库代码：`specs/database-rules.md`

## 日志规范
- 每个 Agent 执行时**必须**在 `logs/` 下创建以 Agent 名命名的日志文件（如 `orchestrator.log`）
- 每个 Agent 在执行关键节点时，**必须**使用 Write 工具，以追加方式将符合格式的日志写入对应日志文件
- 每个 Agent 执行 `log(消息)` 时，自动组合为日志格式，**必须**使用 Write 工具以追加方式写入对应日志文件
- 日志格式：`[YYYY-MM-DD HH:MM:SS] [级别] [Agent名] 消息`
- 日志级别：INFO、WARN、ERROR、DEBUG
- 必须记录：Agent 被调用、关键决策点、任务状态变更、执行完成或失败

## 开发规范
- 代码库应是接口简单、功能隐藏的深度模块，而非接口复杂、功能零散的浅层模块，深度模块更利于理解与测试
- 项目目录结构必须严格按照路径规范创建
- 绝对不改变默认开发环境，永远尝试创建或利用现有虚拟环境用于代码运行和测试，如果必须使用默认环境，询问用户得到授权才能开始
- Plan 文件、Task 文件、日志文件、quality-report 内容用中文书写

## 项目专属规范
所有子 Agent 必须遵守项目专属规范文件：`PROJECT-SPEC.md`。Orchestrator 在调用任何子 Agent 时，必须在任务描述中明确提示：“请先读取 `{project-root}/PROJECT-SPEC.md` 并遵守其中的环境配置。”