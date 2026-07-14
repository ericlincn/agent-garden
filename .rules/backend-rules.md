# backend-rules

## Architecture

* 严格遵循：

  ```text
  Controller → Service → Repository
  ```

* 禁止跨层调用。

* 每个文件保持单一职责。

## Error Handling

* 所有外部调用（数据库、API、文件、消息队列）必须处理异常。
* 错误日志必须包含：
  * 操作名称
  * 错误原因
  * 关键参数（脱敏后）
* 禁止裸 except / except Exception 且不 re-raise；捕获必须 log 并显式处理（re-raise / return error type / fallback with log）。
* 禁止 return None / return False / return {} 作为错误信号；错误必须通过异常或显式 error type 传递。
* 所有 catch 块必须 log，禁止空 catch 块（except: pass）。
* 外部 IO 的 catch 必须 log 原始异常（`exc_info=True` 或 `traceback.format_exc()`）。

## Logging

* logger 初始化：统一模块名（如 `__name__`），统一格式（时间 + 级别 + 模块 + 消息）。
* ERROR 级：需人工介入的异常。
* WARN 级：可降级处理的异常。
* INFO 级：关键业务操作（请求开始/结束、状态转换）。
* 禁止 print() 替代 logging。

## API

* API 错误响应统一格式：

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "timestamp": "ISO8601"
}
```

## Comments

仅对以下内容编写注释：

* 复杂业务规则
* 外部接口契约
* 非直观实现原因

禁止注释显而易见的代码。