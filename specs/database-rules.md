---
author: eric.lin
version: 1.03
---

# 数据库代码规范

## 核心原则：人类可读性优先

### 命名
- 表名使用小写复数形式（如 `users`、`orders`）
- 字段名使用小写，单词间用下划线（如 `created_at`）
- 外键字段以 `_id` 结尾（如 `user_id`）

### 查询
- SQL 关键字大写（`SELECT`、`WHERE`、`JOIN`）
- 复杂查询必须写注释说明其用途
- 禁止 `SELECT *`，显式列出需要的字段

### 迁移
- 每个迁移文件只做一件事
- 迁移文件名清晰描述操作（如 `add_email_to_users`）
- 必须包含回滚步骤的注释