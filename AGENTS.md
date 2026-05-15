---
author: eric.lin
version: 1.12
---

# 项目索引入口

## Agents 清单
| Agent | 文件 | 职责 |
|:---|:---|:---|
| Orchestrator | `.claude/agents/orchestrator.md` | 调度 |
| Architect | `.claude/agents/architect.md` | 需求讨论，产出计划 |
| Developer | `.claude/agents/developer.md` | 按 TDD 编码 |
| Reviewer | `.claude/agents/reviewer.md` | 审查代码 |
| Tester | `.claude/agents/tester.md` | 自动化测试 |

## 规范文档
- 前端代码规范: `specs/frontend-rules.md`
- 后端代码规范: `specs/backend-rules.md`
- 数据库代码规范: `specs/database-rules.md`
- 视觉品味验证规则: `specs/visual-rules.md`

## Skills
- 生成图片或提示词：`/gpt-image-2`
- 本地知识库检索：`/kb-retriever`
- 前端工程师：`/web-design-engineer`
- 产出适合视频输出的网页ppt：`/web-video-presentation`
---
- Web 体验测试：`/playwright-cli`
- 知识沉淀输出文档：`/knowledge-condenser`
- 交叉分析输出报告：`/cross-analysis`
- 产出PRD：`/produce-prd`
- 反推PRD：`/reverse-prd`

## 路径
- Subagent logs：`.claude-logs/`
- 报告：`reports/`
- 文档：`dcos/`

## Hooks & MCP
- Hooks 定义 & 基础权限：`.claude/settings.json`
- Logger：`.claude/hooks/log-writer.py`
- 根据事件播放音乐：`.claude/hooks/play-sound.py`
- 事件流转 MCP：`.claude/hooks/report-event-server.py`
- MCP 定义：`.mcp.json`

# 流程机制
Orchestrator 调用 Subagent，任务完成调用 MCP → MCP 生成标准事件块 → Orchestrator 根据事件继续其他任务

## 流程设计思想
| 环节类型 | 谁负责处理 |
|:---|:---|
| 流程 / 策略 / 应对 | `Skill` / `Agent` |
| 机制 / 协议 / 状态 | `MCP` |

## 项目启动方法（为了支持 Event 流转机制）
1. 桌面快捷方式运行 Anaconda Powershell Prompt (miniconda3)
> %windir%\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& 'D:\miniconda3\shell\condabin\conda-hook.ps1' ; conda activate 'D:\miniconda3' "
2. 切换虚拟环境 conda activate ai-env-xxx
   - 如果没有虚拟环境：conda create --name xxx python=3.10，pip install mcp[cli]
3. cd 到项目路径运行 claude --agent orchestrator