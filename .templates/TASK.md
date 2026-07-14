---
task-id: TASK-NNN
description: <一句话说明做什么>
dependencies: ["phase-NN/TASK-NNN", ...]
  # dependencies：依赖的任务 ID 列表，无依赖留空数组。
  # 格式：无论同 phase 或跨 phase，一律写作 phase-NN/TASK-NNN。
  # 实现思路中引用了其他 task 产出的模块/接口/数据结构，必须在此列出。
---

## 实现思路
<简述关键步骤、技术方案、依赖与取舍。引用 specs/design.md 中的具体决策>

<!--
验收标准编写规则：
- 每条对应 specs 中至少一个 Scenario
- 使用可验证的表述，例如：
  - 正确："返回 200 + JSON body 含 order_id"
  - 错误："功能正常"
- 标注来源：spec_ref: <capability>/<requirement>/<scenario>（需求驱动）或 discovery_ref: DISC-NNN/<简短标识>（体验缺口驱动），两者可并存
- 每条验收标准必须可被测试断言
-->

## 验收标准
- <从 specs Scenario 的 WHEN/THEN 直接映射的可验证条件>
- <可验证的判定条件 2>

<!--
目标文件编写规则：
- 列出本 task 需要新增或修改的 src/ 和 tests/ 文件
- 路径必须与 specs/contracts/architecture.yaml 的 layout 一致
- 测试文件路径遵循 tests/ 镜像 src/ 结构
-->

## 目标文件
- `src/<路径>`
- `tests/<路径>`