---
name: test-only
description: 对现有项目进行仅测试，不修改任何代码，输出测试报告
disable-model-invocation: true
---

## 执行步骤
- 接收到 `/test-only` 指令后，将用户消息作为参数，执行 Orchestrator.仅测试(用户消息)