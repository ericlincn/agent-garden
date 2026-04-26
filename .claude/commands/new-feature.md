---
name: new-feature
description: 启动新功能的讨论与计划流程，由架构师引导用户产出原子化计划
disable-model-invocation: true
---

## 执行步骤
- 你（Orchestrator）接收到 `/new-feature` 指令后，检查用户消息中是否包含“马上/立刻/紧急”等字样。
   - 如果包含，走紧急流程
   - 否则，走标准流程