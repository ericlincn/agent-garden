---
author: eric.lin
version: 1.05
---

# 全局执行规范

## 核心流程
- 标准流程：用户需求 → Architect 产出计划 → Developer TDD 编码 → Reviewer 审查 → Tester 测试 → 用户验收
- 紧急流程：用户需求 → Developer TDD 编码 → Tester 测试 → 用户验收
- 插入任务：用户需求 → Architect 增量评估 → Developer TDD 编码 → Reviewer 审查 → Tester 测试 → 用户验收

## 流程规范
- **强制遵循核心流程**: 不可打乱流程顺序，不可跳过任一流程
- **用户验收必须等待**：Tester 完成后，Orchestrator **必须**向用户发送黑盒测试邀请（如"请进行黑盒测试验收，通过请回复'验收通过'，发现问题请描述"），并**阻塞等待用户输入**，不得自动结束 Phase。

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

## Task 文件状态流转
| 文件后缀 | 谁来变更后缀 | 后续动作 |
|:---|:---|:---|
| `.todo.md` | Architect 创建 | Orchestrator 派发路径给 Developer 开始编写任务 |
| `.doing.md` | Developer 开始编写任务时重命名 |  |
| `.done.md` | Developer 完成编写任务时重命名 | Orchestrator 派发路径给 Reviewer 开始验收 |
| `.blocked.md` | Reviewer 或 Tester 检验不通过时重命名 | Orchestrator 派发路径给 Developer 修复 |

## 规范文档
所有子 Agent 必须遵守以下规范，在执行任何操作前必须 Read 对应文件：
- 前端代码：`specs/frontend-rules.md`
- 后端代码：`specs/backend-rules.md`
- 数据库代码：`specs/database-rules.md`

## 日志规范
- 每个 Agent 执行时在 `logs/` 下创建以 Agent 名命名的日志文件（如 `orchestrator.log`）
- 日志格式：`[时间戳] [级别] [Agent名] 消息`
- 日志级别：INFO、WARN、ERROR、DEBUG
- 必须记录：Agent 被调用、关键决策点、任务状态变更、执行完成或失败

## 开发规范
- 项目必须按照核心流程逐步推进，步骤不允许跳过
- 项目目录结构必须严格按照路径规范创建
- 不改变默认开发环境，创建虚拟环境用于代码运行和测试
- Plan 文件、Task 文件、日志文件、quality-report 内容用中文书写
- **子Agent调用规则**：Orchestrator 调用任何子Agent时，必须在任务描述中明确引用对应的 `specs/` 规范文件路径

## 项目专属规范
所有子 Agent 必须遵守项目专属规范文件：`PROJECT-SPEC.md`。Orchestrator 在调用任何子 Agent 时，必须在任务描述中明确提示：“请先读取 `{project-root}/PROJECT-SPEC.md` 并遵守其中的环境配置。”