# 前端代码规范

## 核心原则：人类可读性优先

### 命名

- 组件文件名、组件名（函数名/类名）、变量名必须自解释。禁止使用无意义缩写（如 `btn`、`usr`、`hdr`）。
- 事件处理函数以 `handle` 开头，后接触发事件的元素/事件名：
  - `handleSubmit`、`handleInputChange`、`handleClickDelete`
- 布尔值变量以 `is`/`has`/`can` 开头：
  - `isLoading`、`hasError`、`canEdit`

### 结构

- 组件逻辑按以下顺序清晰分层（使用空行分隔）：
  1. 外部导入（imports）
  2. 类型/接口定义（types/interfaces）
  3. Props 解构与默认值
  4. Hooks 调用（useState、useEffect、自定义 hooks）
  5. 事件处理函数定义
  6. 辅助渲染逻辑（如条件判断、数据转换）
  7. JSX 返回语句
- 避免 JSX 嵌套深度超过 4 层。如果超过，应拆分子组件。

### 注释

- 任何包含复杂业务规则的代码（如价格计算、权限判断、数据格式化）必须写注释，说明输入来源、输出格式以及边界情况。
- 禁止注释显而易见的代码（如 `const visible = true; // 设置为可见`）。
- 注释语言可以全部使用中文或全部使用英文，但在同一个项目中必须保持一致。

### 格式一致性

- 必须使用 Prettier 的默认配置（不作自定义）。Claude Code 在生成代码后应自动运行 `npx prettier --write <文件>` 以保证格式统一。