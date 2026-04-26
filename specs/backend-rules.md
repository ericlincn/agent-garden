---
author: eric.lin
version: 1.03
---

# 后端代码规范

## 核心原则：人类可读性优先

### 命名
- 函数、变量、类名必须自解释，禁止无意义缩写
- 控制器方法名对应 HTTP 动词：`getUser`、`createOrder`、`updateProduct`
- 数据库查询函数以 `find`/`create`/`update`/`delete` 开头

### 结构
- 遵循清晰分层：Controller → Service → Repository
- 单个文件不超过 400 行（建议）
- 函数不超过 50 行（建议）

### 错误处理
- 每个外部调用（数据库、API）必须有错误处理
- 错误信息必须包含足够的上下文，便于定位

### 注释
- 复杂算法和业务规则必须注释
- API 端点必须有一行描述其功能
- 显而易见的代码不注释