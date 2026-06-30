# <项目名称>

## Why

<一句话：为什么做这个项目，解决什么问题>

## User Stories

### <角色1>
- 作为<角色>，我希望<功能>，以便<价值>

### <角色2>
- 作为<角色>，我希望<功能>，以便<价值>

> 每条用户故事对应的验收标准见 specs/<capability>/spec.md，整体验收条件见 contracts/acceptance.yaml

## What

<功能范围描述，子模块拆分。用 SHALL 语气描述系统必须做什么>

> **Web 应用强制项**：若项目类型为 web，必须包含首页路由 `/`：已登录 → redirect 到主功能页（如 `/dashboard`）；未登录 → redirect 到登录页。`/` 不得返回 404 或纯 JSON。此条须在第一个涉及路由的 phase 中实现。

## Impact

<对现有系统的影响：新建项目 / 影响哪些已有模块 / 涉及的外部依赖>

## Out of Scope

明确**不做**的事，避免 scope creep：

- <不做的功能 1>
- <不做的功能 2>

## Acceptance

<整体验收标准摘要（高层级），详细逐条验收条件见 contracts/acceptance.yaml>
