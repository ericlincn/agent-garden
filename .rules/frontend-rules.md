# frontend-rules

## Structure

组件按以下顺序组织：

1. imports
2. types/interfaces
3. hooks
4. event handlers
5. render helpers
6. JSX

## Components

* JSX 嵌套超过 4 层时拆分组件。
* 复杂业务逻辑不得直接写在 JSX 中。

## Routing & Response Convention (Web App)

> 本节适用于**前后端不分离的 web 应用**（如 Flask + Jinja2 / Rails + ERB）。纯 API 项目忽略本节。

### 强制 PRG 模式（Post-Redirect-Get）
- **POST / DELETE / PATCH 表单提交成功后必须返回 `redirect()`（302 或 303）**，跳转到结果页或原页面刷新。**禁止**返回纯 JSON 给浏览器。
- 仅以下例外允许返回 JSON：
  1. 路由显式标注为 API 端点（URL 前缀含 `/api/`，或 `@bp.route` 注释含 `API:`）
  2. AJAX/fetch 请求（请求头含 `X-Requested-With: XMLHttpRequest` 或 `Accept: application/json`）
  3. SSE 流式端点
- **GET 请求必须返回 `render_template()` 或 `redirect()`**，不得返回纯 JSON 给浏览器（API 端点除外）。

### 首页路由
- 应用必须定义 `/` 根路由：
  - 已登录用户 → `redirect('/dashboard')`（或项目主功能页）
  - 未登录用户 → `redirect('/auth/login')`
- `/` 不得返回 404 或 JSON。

## Comments

仅对以下内容编写注释：

* 权限逻辑
* 数据转换规则
* 复杂业务规则

## Formatting

生成代码后执行：

```bash
npx prettier --write <file>
```