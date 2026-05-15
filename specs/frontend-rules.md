# 前端代码规范

## 1. HTML 规范

### 结构要求

- 使用 HTML5 语义化标签
- 按钮使用 `<button>` 标签
- 主容器使用 `<main>` 或 `<div id="app">`
- 显示屏使用 `<output>` 或 `<div>` 配合 role

### 标签规范

```html
<!-- 正确示例 -->
<main id="calculator">
  <output id="display" role="status" aria-live="polite"></output>
  <div id="keypad">
    <button type="button" data-action="digit" data-value="7">7</button>
  </div>
</main>

<!-- 错误示例 -->
<div id="calc">
  <div id="screen"></div>
  <span onclick="clickBtn(7)">7</span>
</div>
```

### 属性规范

- 所有按键必须有 `data-*` 属性标识功能类型
- 使用 `aria-label` 为图标按钮提供文本说明
- 使用 `title` 属性提供工具提示

## 2. CSS 规范

### 命名规范

- 使用 BEM 命名法：`block__element--modifier`
- 类名全部小写，使用连字符分隔
- 避免使用内联样式

### 样式组织

```css
/* BEM 示例 */
.calculator__display { }
.calculator__key { }
.calculator__key--operator { }
.calculator__key--scientific { }
```

### 拟物风格实现

```css
/* 立体按键 */
.calculator__key {
  /* 渐变背景模拟高光 */
  background: linear-gradient(180deg, #f5f5f5 0%, #e0e0e0 50%, #d0d0d0 100%);

  /* 多层阴影实现立体感 */
  box-shadow:
    0 1px 0 #666,        /* 底部硬边 */
    0 2px 4px rgba(0,0,0,0.3),  /* 柔和阴影 */
    inset 0 1px 0 rgba(255,255,255,0.8); /* 顶部高光 */
}

/* 按下状态 */
.calculator__key:active {
  box-shadow:
    0 1px 0 #666,
    inset 0 2px 4px rgba(0,0,0,0.2);
  transform: translateY(2px);
}
```

### 过渡动画

```css
/* 按键反馈 */
.calculator__key {
  transition: all 0.1s ease;
}

/* 显示屏数字变化 */
.calculator__display {
  transition: background-color 0.2s ease;
}
```

## 3. JavaScript 规范

### 模块化

```javascript
// calculator.js - 计算器核心逻辑
export class CalculatorEngine {
  // ...
}

// app.js - 应用入口
import { CalculatorEngine } from './calculator.js';
import { KeyboardHandler } from './keyboard.js';
import { DisplayManager } from './display.js';
```

### 命名规范

| 类型 | 规范 | 示例 |
|:---|:---|:---|
| 类 | PascalCase | `CalculatorEngine` |
| 方法 | camelCase | `appendDigit()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_FACTORIAL` |
| 私有属性 | _prefix | `_currentExpression` |

### 函数设计

```javascript
/**
 * 计算数学表达式
 * @param {string} expression - 数学表达式字符串
 * @returns {number|string} 计算结果或错误信息
 * @throws {RangeError} 表达式格式错误
 */
evaluate(expression) {
  // 实现
}
```

### 错误处理

```javascript
// 统一错误返回值
evaluate(expression) {
  try {
    const result = this.parseAndCalculate(expression);
    return isNaN(result) ? 'Error' : result;
  } catch (e) {
    return 'Error';
  }
}
```

### 事件处理

```javascript
// 事件绑定（使用事件委托）
document.getElementById('keypad').addEventListener('click', (e) => {
  const button = e.target.closest('[data-action]');
  if (!button) return;

  const action = button.dataset.action;
  const value = button.dataset.value;

  this.handleInput(action, value);
});
```

## 4. 文件组织

```
src/
├── index.html           # 主页面
├── styles/
│   └── calculator.css   # 所有样式
└── scripts/
    ├── app.js           # 应用入口
    ├── calculator.js    # 计算器核心
    ├── display.js       # 显示屏管理
    ├── keyboard.js      # 键盘处理
    └── utils.js         # 工具函数
```

## 5. 测试要求

### 单元测试

```javascript
// tests/calculator.test.js
describe('CalculatorEngine', () => {
  it('should add two numbers', () => {
    const calc = new CalculatorEngine();
    calc.appendDigit('1');
    calc.appendOperator('+');
    calc.appendDigit('2');
    expect(calc.evaluate()).toBe(3);
  });
});
```

### 测试覆盖

- 四则运算：100%
- 科学函数：100%
- 进制转换：100%
- 边界条件：全覆盖
