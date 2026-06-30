---
name: knowledge-condenser
description: Use when a development phase has completed and you need to distill reusable patterns, anti-patterns, and decisions into a portable knowledge base before starting the next phase.
allowed-tools: mcp__memory__create_entities
---

## When to Use
- Phase 内所有 task 进入 `implementation: completed` 后跑一次
- 复盘会议前要快速汇总本 phase 教训
- 不适用于：项目刚启动无 phase、单 task 即整体、只想要 git log 摘要

## 两条输出路径的分工

| 输出 | 载体 | 目标读者 | 内容要求 |
|------|------|---------|---------|
| **KNOWLEDGE.md** | 项目仓库内文件 | 项目组成员 + AI | **项目级**：保留 Task ID、文件路径、具体接口名。用于当前项目新 task 开发时参考 |
| **MCP Memory** | 跨项目知识图谱 | 跨项目 AI agent | **跨项目级**：不含任何项目名、Task ID、文件路径。用于未来任意项目遇到相似问题时检索 |

---

## Execution Steps

### 0. Phase 状态预检
扫描 `phases/phase-XX-*/tasks/*.md` 的 frontmatter：
- 若全部 `implementation: pending` → 降级为"基于 plan.md 提炼预期设计"，**在 KNOWLEDGE.md 顶部标注 `[来源：规划阶段设计文档，非实战复盘]`**
- 若部分完成 → 仅基于已完成 task 提炼，注明哪些 task 还未实施
- 若全部完成 → 正常提炼

### 1. 扫描当前 Phase
- 定位当前 Phase 目录（由上下文或用户指定）
- 用 `Glob` 找出所有 `Task 文件`
- `Read` 这些文件，提取：
  - 完成摘要中的**设计模式 / 架构技巧**
  - 审查意见中**被多次打回的问题类型**（同一 Task 累计 retry ≥ 2）
  - 测试日志中**新增的边界条件或 Mock 策略**
  - 计划文件中记录的**技术选型理由**

### 2. 按输出路径分别提炼

#### 2A. 为 KNOWLEDGE.md 提炼（项目级）

保留项目上下文，让后续 task 能直接复用。**控制体量**：KNOWLEDGE.md 被 reviewer 在每轮审查时全量读取，体量膨胀会吃掉 agent 上下文预算。每个 phase 的 KNOWLEDGE.md 段落**总行数 ≤ 30 行**。

- ✅ **允许**出现 Task ID（`TASK-003`）、文件路径（`src/rate-limiter/middleware.go`）、具体接口名（`RateLimiterConfig`）
- **只保留两个维度**（其余维度如"模式""决策""测试策略"只写入 MCP Memory，不写入 KNOWLEDGE.md）：

| 维度 | 说明 | 行数预算 |
|:---|:---|:---|
| **反模式 / 常见陷阱** | 导致审查或测试多次失败的典型错误，附 Task ID 便于追溯。每条 ≤ 1 行（Task ID + 一句话），同 phase 内同类问题合并为一条 | ≤ 15 行 |
| **审查清单** | Reviewer 高频关注点，**直接包含项目内文件路径和命名约定**。每条 ≤ 1 行，去重后按重要性排序 | ≤ 15 行 |

> **删除维度说明**：原"模式""决策""测试策略"三个维度内容冗长（占行数 60%+），但对 reviewer 审查的实际帮助有限——reviewer 主要需要"什么会被打回"和"检查清单"。这三个维度仍写入 MCP Memory 供跨项目检索，不丢失。

#### 2B. 为 MCP Memory 提炼（跨项目级）

剥离项目上下文，只保留纯抽象经验。

- ❌ **禁止**出现：Task ID、文件路径、项目名、Phase 名、具体接口名、业务术语
- ✅ **允许**：通用术语（如"速率限制中间件"→「责任链模式应用于中间件管线」）
- 每条经验必须**可独立理解**，不依赖任何项目背景
- 每条经验正文 ≤ 300 字
- 按相同 5 维度整理（MCP Memory 仍保留全部维度），但描述方式完全不同：

| 维度 | KNOWLEDGE.md 写法（仅 2 维度） | MCP Memory 写法（全 5 维度） |
|:---|:---|---|
| 模式 | *(不写入 KNOWLEDGE.md)* | 「令牌桶算法 vs 漏桶算法选型指南」 |
| 反模式 | `TASK-003` 阶乘未做溢出检查 → 死循环 | 「大整数运算未做上界拦截 → 死循环」 |
| 决策 | *(不写入 KNOWLEDGE.md)* | 「框架选型三维度：生态 × 团队经验 × 性能需求」 |
| 测试策略 | *(不写入 KNOWLEDGE.md)* | 「Property-based 测试适用于数值边界验证」 |
| 审查清单 | `src/**/*.js` 文件超过 800 行需拆分 | 「模块边界检查：函数超 80 行 → 拆」 |

### 3. 写入 `KNOWLEDGE.md`（项目级，先查重再追加）
- **查重**：grep `## \[YYYY-MM-DD\] Phase-XX 名称` 是否已存在
  - 存在 → 询问用户"已提炼过同 Phase，是否更新？"，**禁止静默追加**
  - 不存在 → 继续
- 若文件不存在则新建，编码 UTF-8
- 若步骤 0 触发降级，**先在文件顶部写来源声明**，再追加 phase 段
- 追加内容格式（**仅两个维度，总行数 ≤ 30 行**）：
  ```
  ## [YYYY-MM-DD] Phase-XX 名称
  ### 反模式 / 常见陷阱
  - <Task ID>：<一句话问题描述>（retry 次数）
  ### 审查清单
  - <具体检查项（含文件路径 / 命名约定）>
  ```

### 4. 存入知识图谱（跨项目级，抽象后写入）
为 **2B 中提炼的每条经验** 调用 `mcp__memory__create_entities`。

**实体命名规则**：
- ❌ BAD：`TASK-003-阶乘溢出`、`evaluator-evaluator.js的bug`、`项目A-选型`
- ✅ GOOD：`反模式-阶乘指数溢出未拦截`、`模式-三段式计算引擎分层`、`决策-框架选型三维度`

**entityType**：统一使用 `pattern`（不区分维度，由 tags 标记维度）

**observations 必须含 3 条**（按顺序）：

| 序 | 内容 | 示例 |
|:---:|:---|:---|
| 1 | 维度标注 | `dimension: 模式 / 反模式 / 决策 / 测试策略 / 审查清单` |
| 2 | 正文 | `<经验正文，≤300 字，纯抽象>` |
| 3 | **Meta（强制）** | `meta: project=<项目名> \| phase=<phase 名> \| date=<YYYY-MM-DD>` |

**Meta 三个字段全部必填**，缺一不写。
- 跨项目检索靠实体名（命名要自解释）
- 项目内溯源靠 `meta` 的 project + phase
- 维度筛选靠 observation[0] 的 `dimension:` 前缀

### 5. 完成报告
- 汇总本次提炼的维度、各维度条目数
- KNOWLEDGE.md：追加了多少行
- MCP Memory：创建了多少实体
- 若步骤 0 触发降级，必须显式声明"本轮为规划阶段提炼，非实战复盘"
- 输出简短总结（无需调用其他 Agent）

## Anti-Patterns (Rationalizations to Reject)
- ❌ "KNOWLEDGE.md 和 memory 写一样的内容就行了" → 两条路径目标读者不同，必须分别提炼
- ❌ "Phase 还没实施，plan 里能提炼的我先写了" → 必须先标注 [来源：规划阶段]
- ❌ "tags 接口不支持，那就别打了" → 嵌入 `observations` 第 1 条用 `dimension:` 前缀
- ❌ "MCP 写失败就跳过吧" → 写不出 entity 等于没提炼，停下来排查
- ❌ "已提炼过同 Phase 但忘了，再追加一遍" → 步骤 3 先 grep 查重
- ❌ "项目名 / phase 太长，meta 写不下" → 缩写或省略描述，但 meta 三个字段必填
- ❌ "MCP Memory 是跨项目的，不用写维度" → `dimension:` 是跨项目筛选的唯一依据
- ❌ "memory 的正文用项目内举例更方便" → 跨项目实体含项目细节会导致误召回
- ❌ "KNOWLEDGE.md 把模式/决策/测试策略也写进去更完整" → 这三维度只入 MCP Memory，KNOWLEDGE.md 仅保留反模式+审查清单，控制 ≤ 30 行/phase
- ❌ "审查清单和反模式有重叠，合并算了" → 两个维度语义不同：反模式是"过去犯过的错"，审查清单是"未来要检查的项"，分开保留

## Quick Reference

| 步骤 | 做什么 | 输出 |
|------|--------|------|
| 0 | Phase 状态预检 | 决定降级/正常模式 |
| 1 | 扫描 Task 文件 | 原始素材 |
| 2A | 为 KNOWLEDGE.md 提炼（仅反模式+审查清单，≤30 行） | 项目级经验 |
| 2B | 为 MCP Memory 提炼（全 5 维度，纯抽象） | 跨项目级经验 |
| 3 | 写入 KNOWLEDGE.md | 追加到项目仓库 |
| 4 | 存入 MCP Memory | 知识图谱实体 |

## Common Mistakes
- 实体名包含 TASK-XXX / 文件路径 / 业务术语
- KNOWLEDGE.md 写入了模式/决策/测试策略（应只保留反模式+审查清单）
- KNOWLEDGE.md 单个 phase 段落超过 30 行
- KNOWLEDGE.md 和 memory 写同一份内容
- KNOWLEDGE.md 重复追加同 Phase 段
- 写完后没在文件顶部标注来源（降级路径时）
- observation 漏写 dimension 或 meta 第 3 条
- 把"维度标注"和"正文"混进同一条 observation
- 跨项目实体使用了项目内举例或文件路径
