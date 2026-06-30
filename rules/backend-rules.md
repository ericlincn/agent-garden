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
  * 关键参数

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