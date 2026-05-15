# 数据库代码规范

## 核心原则：人类可读性优先

### 命名

- 表名使用小写复数形式：`users`、`orders`、`order_items`。
- 字段名使用小写，单词之间用下划线分隔：`created_at`、`updated_by`、`is_active`。
- 外键字段必须以 `_id` 结尾：`user_id`、`product_id`。建议外键名称与引用表的主键名一致。

### 查询

- SQL 关键字统一使用大写：`SELECT`、`WHERE`、`JOIN`、`INSERT`、`UPDATE`、`DELETE`。
- 任何包含超过两个 `JOIN`、存在子查询、或使用了复杂条件（`CASE WHEN`、窗口函数等）的查询，必须在 SQL 语句上方写注释，说明该查询的业务目的和返回结果集的含义。
- **禁止使用 `SELECT *`**。必须显式列出所需字段，即使需要所有字段也要逐一列出（可使用代码生成器辅助）。这可以避免后续表结构变更导致的不可预期问题。

### 迁移

- 每个迁移文件（schema migration）只做一件事：一次只添加一张表、或只添加一个字段、或只修改一个约束。
- 迁移文件名必须清晰描述操作内容，格式为 `YYYYMMDDHHMMSS_动词_对象.sql`：
  - ✅ `20250315123000_add_email_to_users.sql`
  - ✅ `20250315130000_create_orders_table.sql`
  - ❌ `update.sql`
- 每个迁移文件必须包含回滚步骤的注释，说明如何撤销本次变更（例如使用 `DOWN` 部分或手动 SQL 示例）。