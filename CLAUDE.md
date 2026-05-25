---
author: eric.lin
version: 1.13
---

# 行为准则
- **先想后写**：不确定就提问，有多种解读就呈现出来，有更简单方案就说出来
- **简洁优先**：不写推测性代码、不为单次使用建抽象、不添加未要求的灵活性。200 行能变 50 行就重写
- **精准修改**：只改必须改的，不改相邻代码风格，不改没坏的东西。死代码提出来但别删。每行改动都要能追溯到需求
- **目标驱动**：任务转为可验证目标（"修复 bug" → "写复现测试" → "通过"），多步骤给出计划并逐步验证
- **对话语言**：中文

# Task 文件后缀状态机
`.todo.md` → `.doing.md` → `.done.md` → `.blocked.md`

## 路径规范
- 原型: `{project-root}/prototype/`
- 代码: `{project-root}/src/`
- 测试: `{project-root}/tests/`
- 代码规范文档: `{project-root}/specs/`
- 全局状态快照: `{project-root}/STATE.json`
- 开发 Phase: `{project-root}/phases/phase-XX-名称/`
- Plan 文件: `{project-root}/phases/phase-XX-名称/plan.md`
- Task 文件夹: `{project-root}/phases/phase-XX-名称/tasks/`
- Task 文件: `{project-root}/phases/phase-XX-名称/tasks/TASK-XXX-简短描述.todo.md`
- 质量报告: `{project-root}/phases/phase-XX-名称/quality-report.md`

## 质量报告格式规范
`quality-report.md` 由 Reviewer 和 Tester 共同维护，内容用中文书写，遵循以下模板：

```
### 测试环境
| 项目 | 信息 |
|:---|:---|
| 测试范围 | 全量回归 / 单元测试 / 指定模块 |
| 环境 | Node 20.x / Python 3.12 / 数据库版本等 |

### 结果汇总
| 总数 | 通过 | 失败 | 跳过 | 覆盖率 |
|:---|:---|:---|:---|:---|
| X | X | X | X | XX% |

### 失败用例
| 任务ID | 测试文件 | 行号 | 实际值 | 期望值 |
|:---|:---|:---|:---|:---|
| TASK-XXX | tests/xxx.test.ts | 42 | "error" | "ok" |

### 审查记录
| 任务ID | 结论 | 备注 |
|:---|:---|:---|
| TASK-XXX | 通过 | - |

### 边界条件
- 输入为空时的行为：已覆盖 / 未覆盖 / 不适用
- 超长字符串：...
- 并发场景：...

### 问题追踪
| ID | 关联任务 | 类型 | 描述 | 状态 |
|:---|:---|:---|:---|:---|
| Q-001 | TASK-XXX | 测试失败 | XXX | 待处理 |

### 建议
- 建议补充 XXX 场景的边界测试
```

## 开发规范
- 代码应是接口简单、功能隐藏的深度模块
- 项目目录结构必须严格按照路径规范创建
- `快照文件`、`Plan文件`、`Task文件`、`quality-report` 内容用中文书写

## 代码规范文档
- 前端代码：`{project-root}/specs/frontend-rules.md`
- 后端代码：`{project-root}/specs/backend-rules.md`
- 数据库代码：`{project-root}/specs/database-rules.md`

## 视觉品味验证规则
`specs/visual-rules.md`

# 项目专属规范文档
所有 Subagent 必须读取并遵守：`{project-root}/PROJECT-SPEC.md`

# 可复用经验文档
如果 `{project-root}/KNOWLEDGE.md` 存在，所有 Subagent 开始工作前需要读取