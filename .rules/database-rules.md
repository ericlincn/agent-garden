# database-rules

## Schema

* 表名使用小写复数形式。
* 外键统一使用 `_id` 结尾。

## Query

* 禁止 `SELECT *`。
* 超过两个 JOIN、窗口函数、复杂子查询必须说明业务目的。

## Migration

* 一个 Migration 只做一件事。
* 文件名格式：

```text
YYYYMMDDHHMMSS_action_object.sql
```

例如：

```text
20250315123000_add_email_to_users.sql
```

* 必须提供回滚方案。