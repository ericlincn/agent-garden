---
name: knowledge-condenser
description: 从当前 Phase 中提炼可复用经验，写入 KNOWLEDGE.md
---

## 执行步骤
1. 扫描当前 Phase 下所有 `*.done.md` 和 `*.blocked.md` 中的完成摘要、审查意见、测试日志。
2. 提炼以下内容写入 `{project-root}/KNOWLEDGE.md`（若不存在则新建）：
   - **模式**：本次开发中复用的成功设计模式或代码结构
   - **教训**：Reviewer 打回超过 1 次的问题类型，Tester 发现的边界条件遗漏
   - **决策**：关键的技术选型理由（如为什么选 A 库而非 B 库）
3. 不在 `{project-root}/KNOWLEDGE.md` 中记录具体代码，只记录抽象经验和决策理由。
4. 每次写入追加而非覆盖，格式：`## [日期] Phase-XX 名称` + 提炼内容。