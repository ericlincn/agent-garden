---
name: milestone
description: 定义项目里程碑，触发经验沉淀与进度快照
disable-model-invocation: true
---

## 执行步骤
- 接收到 `/milestone` 指令后，执行 Orchestrator.里程碑()
   - 若 knowledge-condenser Skill 已配置，调用它从当前阶段提炼可复用经验