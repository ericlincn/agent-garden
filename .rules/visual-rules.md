# visual-rules

## Fail Conditions

出现以下任意情况直接判定失败：

* CSS 未加载
* 页面布局错乱
* 关键组件不可见
* 大量资源加载失败
* 移动端严重错位
* 文本对比度低于 WCAG AA

## Scoring

| Score     | Result        |
| --------- | ------------- |
| < 0.70    | Fail          |
| 0.70-0.85 | Manual Review |
| > 0.85    | Pass          |

## Execution

根据项目的实际页面/路由清单确定检查范围。对每个页面分别执行视觉检查，至少覆盖以下交互类型（如项目中存在）：

* 登录/认证页
* 仪表盘/概览页
* 列表/表格页
* 表单/编辑页

若项目不包含上述某类页面，跳过即可，不视为缺失。

输出：

* Score
* Failed Rules
* Improvement Suggestions
