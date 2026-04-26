---
name: milestone
description: 定义项目里程碑，触发经验沉淀与进度快照
disable-model-invocation: true
---

## 执行步骤
1. 你（Orchestrator）接收到 `/milestone` 指令后，扫描当前所有 Phase 的 Task 状态，生成进度摘要。
2. 若 knowledge-condenser Skill 已配置，调用它从当前阶段提炼可复用经验，写入 `KNOWLEDGE.md`。
3. 将快照和沉淀的经验通过 `mcp__memory__create_entities` 持久化（若可用）。
4. 向用户汇报里程碑快照。