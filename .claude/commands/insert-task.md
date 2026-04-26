---
name: insert-task
description: 在已有 Phase 中插入新任务，触发架构师的增量讨论
disable-model-invocation: true
---

## 执行步骤
1. 你（Orchestrator）接收到 `/insert-task` 指令后，直接调用子Agent Architect，将用户描述的新需求完整传递。
2. Architect 与用户讨论增量需求，评估对现有计划的影响，更新 Plan 文件（`plan.md`）并生成新的 Task文件（`.todo.md`）。
3. Architect 工作完成后，你将计划展示给用户确认，确认后将新增任务纳入当前 Phase 的开发调度。