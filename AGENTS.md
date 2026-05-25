---
author: eric.lin
version: 1.13
---

# 项目索引入口

## Agents 清单
| Agent | 文件 | 职责 |
|:---|:---|:---|
| Architect | `.claude/agents/architect.md` | 需求讨论，产出计划 |
| Orchestrator | `.claude/agents/orchestrator.md` | 调度 |
| Developer | `.claude/agents/developer.md` | 按 TDD 编码 |
| Reviewer | `.claude/agents/reviewer.md` | 审查代码 |
| Tester | `.claude/agents/tester.md` | 自动化测试 |

## 规范文档
- 前端代码规范: `specs/frontend-rules.md`
- 后端代码规范: `specs/backend-rules.md`
- 数据库代码规范: `specs/database-rules.md`
- 视觉品味验证规则: `specs/visual-rules.md`

## 路径
- Subagent logs：`.claude-logs/`
- 报告：`reports/`
- 文档：`docs/`
- md转换html：`converted/`
- 临时文件/备份文件：`.tmp/`

## Hooks & MCP
- Hooks 定义 & 基础权限：`.claude/settings.json`
- Logger：`.claude/hooks/log-writer.py`
- 根据事件播放音乐：`.claude/hooks/play-sound.py`
- 事件流转 MCP：`.claude/hooks/report-event-server.py`
- MCP 定义：`.mcp.json`

# 流程机制
- Architect 深度对话产出 PRD 和 开发计划
- Orchestrator 调用 Subagent，任务完成调用 MCP → MCP 生成标准事件块 → Orchestrator 根据事件继续其他任务