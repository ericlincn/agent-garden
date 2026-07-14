---
id: DISC-NNN
phase: phase-03
severity: high          # critical / high / medium / low
category: UX            # UX / flow / error-handling / missing-feature
status: open            # open / converted / wontfix / fixed / verified / closed
personas: []            # 来源视角（如 [novice, abuser, power_user]）
---

<!--
字段说明：
- journey:            探索路径步骤，??? 表示旅程在此中断
- description:        问题描述
- expected:           期望行为
- actual:             实际行为
- blocked:            是否阻塞后续旅程探索
- screenshots:        截图路径列表
- playwright_trace:   playwright trace 路径
- log:                服务端日志片段列表
- created_at:         创建时间 ISO-8601
- converted_to_task:  修复此问题的 task_id（如 phase-01/TASK-005）
-->

journey:
  - Login
  - Create Project
  - Finish
  - ???

description: 创建完成后没有进入下一步入口
expected: 应该出现 Continue / Back to Dashboard / Create Another 按钮
actual: 页面停留，无后续操作入口
blocked: true

screenshots: []
playwright_trace: null
log: []

created_at: <ISO-8601>
converted_to_task: null