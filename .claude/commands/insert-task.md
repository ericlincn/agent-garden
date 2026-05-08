---
name: insert-task
description: 在已有 Phase 中插入新任务，触发架构师的增量讨论
disable-model-invocation: true
---

## 执行步骤
- 接收到 `/insert-task` 指令后，执行 Orchestrator.插入任务(用户消息)