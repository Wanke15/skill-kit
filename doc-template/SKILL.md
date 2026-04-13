---
name: doc-template
description: |
  将结构化内容转换为美观的HTML文档。当用户需要生成文档、报告、技术文档、或任何需要美观排版的HTML输出时使用此skill。支持导航栏、卡片、时间线等多种组件，响应式设计，适配中文排版。触发词：生成文档、创建报告、HTML文档、技术文档、文档模板。
---

# 文档模板 Skill

将结构化内容转换为美观的HTML文档，支持导航栏、卡片布局、时间线等多种组件。

## 工作流程

1. 接收用户提供的标题和结构化内容（markdown或章节描述）
2. 读取模板文件 `assets/template.html`
3. 替换模板变量，生成完整HTML文档
4. 输出HTML文件供用户保存

## 模板变量

替换模板中的以下占位符：

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{TITLE}}` | 文档标题（用于 `<title>` 标签） | `API设计最佳实践` |
| `{{HEADER_TITLE}}` | 主标题 | `API设计最佳实践` |
| `{{HEADER_SUBTITLE}}` | 副标题/描述 | `构建优雅、可维护的API接口` |
| `{{NAV_ITEMS}}` | 导航项 | `<li><a href="#intro">引言</a></li>` |
| `{{TOC_ITEMS}}` | 目录项（中文数字） | `<li><a href="#intro">一、引言</a></li>` |
| `{{SECTIONS}}` | 内容章节 | `<section id="intro"><h2>一、引言</h2>...</section>` |

## 中文数字格式

目录和章节标题使用中文数字：

```
一、二、三、四、五、六、七、八、九、十
```

示例：
- 目录项：`<li><a href="#intro">一、引言</a></li>`
- 章节标题：`<h2>一、引言</h2>`

## 可用组件

### highlight-box
高亮提示框，用于核心观点或重要提示：

```html
<div class="highlight-box">
    <strong>核心观点：</strong>内容...
</div>
```

### info-box
信息提示框，用于补充说明：

```html
<div class="info-box">
    <strong>提示：</strong>内容...
</div>
```

### cards-grid
卡片网格布局，用于并列概念或分类展示：

```html
<div class="cards-grid">
    <div class="card">
        <h4><span class="card-icon">📊</span>标题</h4>
        <p>描述内容</p>
    </div>
</div>
```

### definition-list
定义列表，用于术语解释：

```html
<div class="definition-list">
    <div class="definition-item">
        <dt>术语</dt>
        <dd>定义说明</dd>
    </div>
</div>
```

### step-list
步骤列表，用于操作流程：

```html
<ol class="step-list">
    <li><strong>步骤标题</strong>详细说明</li>
</ol>
```

### timeline
时间线，用于发展历程或阶段说明：

```html
<div class="timeline">
    <div class="timeline-item">
        <strong>事件标题</strong>
        <p>事件描述</p>
    </div>
</div>
```

### comparison-box
对比框，用于方案比较：

```html
<div class="comparison-box">
    <div class="comparison-item style-a">
        <h4>方案A</h4>
        <p>详情</p>
    </div>
    <div class="comparison-item style-b">
        <h4>方案B</h4>
        <p>详情</p>
    </div>
</div>
```

### method-badge
方法标签，用于技术分类：

```html
<span class="method-badge style-a">标签1</span>
<span class="method-badge style-b">标签2</span>
<span class="method-badge style-c">标签3</span>
```

### figure-container
图片容器，用于图表展示：

```html
<div class="figure-container">
    <img src="url" alt="描述">
    <p class="figure-caption">图片说明</p>
</div>
```

### code-block
代码块，深色主题，支持语法高亮。

**单行代码：**
```html
<div class="code-block"><pre><code><span class="keyword">const</span> x = <span class="string">'value'</span>;</code></pre></div>
```

**多行代码（必须使用 `<pre><code>` 包裹）：**
```html
<div class="code-block"><pre><code><span class="keyword">from</span> agentkit <span class="keyword">import</span> AgentkitSimpleApp

app = AgentkitSimpleApp()

<span class="keyword">async def</span> run():
    <span class="keyword">return</span> <span class="string">"ok"</span></code></pre></div>
```

**语法高亮类名：**
| 类名 | 用途 | 颜色 |
|------|------|------|
| `.keyword` | 关键字 | 紫色 |
| `.string` | 字符串 | 绿色 |
| `.comment` | 注释 | 灰色 |
| `.function` | 函数名 | 蓝色 |
| `.number` | 数字 | 橙色 |
| `.operator` | 操作符 | 青色 |

**重要：** 多行代码块必须使用 `<pre><code>` 标签包裹，否则换行符会被 HTML 忽略导致所有代码挤在一行。

## 使用指南

1. 为每个章节创建 `id` 属性（小写、连字符格式）
2. 根据内容类型选择合适的组件
3. 保持中文排版习惯
4. 输出完整的HTML文件内容

## 示例

**输入：**
```
标题：API设计最佳实践
章节：
1. 引言 - 为什么API设计很重要
2. 核心原则 - RESTful、版本控制、错误处理
3. 安全考虑 - 认证、授权、数据保护
```

**输出：**
完整的HTML文档，包含样式、粘性导航栏、目录和结构化内容。
