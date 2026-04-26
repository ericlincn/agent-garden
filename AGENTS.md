---
author: eric.lin
version: 1.05
---

# 项目索引入口

## Agent 清单
| Agent | 文件 | 职责 |
|:---|:---|:---|
| Orchestrator | `.claude/agents/orchestrator.md` | 解析意图，调度团队，管理生命周期 |
| Architect | `.claude/agents/architect.md` | 需求讨论，产出原子化计划 |
| Developer | `.claude/agents/developer.md` | 按 TDD 编码 |
| Reviewer | `.claude/agents/reviewer.md` | 审查代码可读性与规范 |
| Tester | `.claude/agents/tester.md` | 自动化测试与黑盒反馈回流 |

## 用户命令
- 启动新功能讨论: `/new-feature`
- 定义里程碑，触发经验沉淀: `/milestone`
- 在现有 Phase 中插入新任务: `/insert-task`

## 规范文档
- 前端代码规范: `specs/frontend-rules.md`
- 后端代码规范: `specs/backend-rules.md`
- 数据库代码规范: `specs/database-rules.md`

## Skills
- 提炼可复用经验: `knowledge-condenser`