---
name: langfuse-eval-report
description: |
  Generate Langfuse-based evaluation reports with radar charts and HTML output. 触发词：评测报告、模型对比、benchmark、Langfuse评测、生成报告.
---

# Langfuse Evaluation Report Generator

Generate comprehensive evaluation reports for AI agents/models with visualization charts and HTML documentation.

## When to Use

Use this skill when:
- User provides evaluation metrics comparing different models/agents
- User has benchmark data with mean, std dev, or similar statistics
- User wants to create an evaluation summary report
- User mentions "评测报告", "模型对比", "benchmark", "evaluation metrics"
- User wants to fetch evaluation data from Langfuse with a time range

## Workflow

### Mode 1: Langfuse Data Source (Recommended)

When user specifies a time range and model names, fetch data from Langfuse:

**Input Format (supports precise time):**
```
生成评测报告:
- 时间范围: 2026-04-21 10:00:00 至 2026-04-21 18:30:00
- Dev模型: DeepSeek V3.2 (sys-user-dev)
- Test模型: Qwen3.5-Plus (sys-user-test)
```

Or simplified format:
```
生成评测报告: 2026-04-21 10:00:00 到 2026-04-22, dev是DeepSeek V3.2, test是Qwen3.5-Plus
```

**Steps:**

1. **Run the bundled script** `scripts/langfuse_ops.py` to fetch and aggregate data:
   ```bash
   python scripts/langfuse_ops.py \
     --from "2026-04-21 10:00:00" --to "2026-04-21 18:30:00" \
     --dev "DeepSeek V3.2" --test "Qwen3.5-Plus" \
     --dev-user "sys-user-dev" --test-user "sys-user-test" \
     -o eval_data.json
   ```

   Time format supports:
   - `YYYY-MM-DD` (full day)
   - `YYYY-MM-DD HH:MM:SS` (precise time)

2. **Parse the JSON output** which has this structure:
   ```json
   {
     "title": "DeepSeek V3.2 vs Qwen3.5-Plus 模型评测报告",
     "subtitle": "评测时间段: 2026-04-21 10:00:00 至 2026-04-21 18:30:00",
     "models": [
       {"id": "dev", "name": "DeepSeek V3.2"},
       {"id": "test", "name": "Qwen3.5-Plus"}
     ],
     "metrics": [
       {
         "name": "引导问题相关性",
         "data": {
           "dev": {"total": 150, "mean": 0.72, "std_dev": 0.26},
           "test": {"total": 150, "mean": 0.76, "std_dev": 0.24}
         }
       }
     ],
     "performance": {
       "dev": {
         "count": 150,
         "avg_latency": 16.82,
         "p50_latency": 15.32,
         "p95_latency": 32.02,
         "total_cost": 2.006191
       },
       "test": {
         "count": 150,
         "avg_latency": 7.79,
         "p50_latency": 6.18,
         "p95_latency": 14.59,
         "total_cost": 0.783922
       }
     }
   }
   ```

   **Performance Metrics Fields:**
   - `count`: Number of requests
   - `avg_latency`: Average latency in **seconds**
   - `p50_latency`: P50 (median) latency in **seconds**
   - `p95_latency`: P95 latency in **seconds**
   - `total_cost`: Total cost in **USD**

3. **Generate visualization charts** using `chart-visualization` skill

4. **Generate HTML report**

### Mode 2: Direct Data Input

When user directly provides evaluation data in natural language:

**Input Format:**
```
我有两个模型的评测数据：
模型A是GPT-4，模型B是Claude-3

评测指标如下：
- 代码生成能力：GPT-4 mean=0.85 std=0.15, Claude-3 mean=0.88 std=0.12
- 数学推理能力：GPT-4 mean=0.82 std=0.18, Claude-3 mean=0.86 std=0.14
...
```

**Steps:**

1. **Parse input data** to extract model names, metric names, mean values, standard deviations

2. **Structure the data** into the standard format

3. **Generate visualization and HTML report**

## Visualization Generation

Use `chart-visualization` skill to generate:

**Chart 1 - Radar Chart (评测综述):**
```json
{
  "tool": "generate_radar_chart",
  "args": {
    "title": "[Dev模型] vs [Test模型] 评测维度对比",
    "data": [
      {"name": "指标1", "value": 0.72, "group": "Dev模型"},
      {"name": "指标1", "value": 0.76, "group": "Test模型"},
      {"name": "指标2", "value": 0.85, "group": "Dev模型"},
      {"name": "指标2", "value": 0.88, "group": "Test模型"}
    ],
    "width": 700,
    "height": 500
  }
}
```

**Chart 2 - Mean Comparison:**
```json
{
  "tool": "generate_column_chart",
  "args": {
    "title": "模型各指标平均分对比",
    "axisXTitle": "评测指标",
    "axisYTitle": "平均分",
    "data": [
      {"category": "指标1", "value": 0.72, "group": "Dev模型"},
      {"category": "指标1", "value": 0.76, "group": "Test模型"}
    ],
    "group": true,
    "width": 800,
    "height": 450
  }
}
```

**Chart 3 - Std Dev Comparison:**
```json
{
  "tool": "generate_column_chart",
  "args": {
    "title": "模型各指标标准差对比",
    "axisXTitle": "评测指标",
    "axisYTitle": "标准差",
    "data": [...]
  }
}
```

**Chart 4 - Performance Comparison (if performance data exists):**
```json
{
  "tool": "generate_column_chart",
  "args": {
    "title": "模型延迟对比",
    "axisXTitle": "延迟指标",
    "axisYTitle": "延迟 (秒)",
    "data": [
      {"category": "平均延迟", "value": 16.82, "group": "DeepSeek"},
      {"category": "平均延迟", "value": 7.79, "group": "Qwen"},
      {"category": "P50延迟", "value": 15.32, "group": "DeepSeek"},
      {"category": "P50延迟", "value": 6.18, "group": "Qwen"},
      {"category": "P95延迟", "value": 32.02, "group": "DeepSeek"},
      {"category": "P95延迟", "value": 14.59, "group": "Qwen"}
    ],
    "group": true,
    "width": 700,
    "height": 400
  }
}
```

**Chart 5 - Cost Comparison (if performance data exists):**
```json
{
  "tool": "generate_column_chart",
  "args": {
    "title": "模型成本对比",
    "axisXTitle": "成本指标",
    "axisYTitle": "金额 (美元)",
    "data": [
      {"category": "总成本", "value": 2.01, "group": "DeepSeek"},
      {"category": "总成本", "value": 0.78, "group": "Qwen"},
      {"category": "单次成本", "value": 0.0134, "group": "DeepSeek"},
      {"category": "单次成本", "value": 0.0052, "group": "Qwen"}
    ],
    "group": true,
    "width": 600,
    "height": 400
  }
}
```

## HTML Report Generation

The skill includes a professional HTML template at `assets/template.html` with rich components:

**Template Components:**
- `.highlight-box` - 高亮提示框，用于核心发现
- `.info-box` - 信息提示框，用于补充说明
- `.cards-grid` + `.card` - 卡片网格布局，用于并列概念
- `.comparison-box` + `.comparison-item` - 对比框，用于模型对比
- `.method-badge` - 标签徽章，用于提升幅度标记
- `.figure-container` - 图片容器，用于图表展示

**Report Structure:**
1. **Header**: Title + subtitle (model comparison with time range)
2. **Overview Section**: Evaluation scope, models comparison box, evaluation dimensions cards grid, **radar chart**
3. **Metrics Detail Section**: Full data table with rowspan for metrics
4. **Comparison Analysis Section**: Performance table with badges, stability analysis in info-box
5. **Performance Section**: Latency & cost table (count, avg/p50/p95 latency, total cost, cost per request)
6. **Visualization Section**: Radar chart, Mean/Std Dev column charts, Performance bar charts
7. **Conclusion Section**: Cards grid for conclusions, recommendations list, final highlight-box

**Performance Section Template:**
```html
<section id="performance">
    <h2>四、性能对比</h2>

    <h3>延迟与成本指标</h3>
    <table>
        <thead>
            <tr>
                <th>指标</th>
                <th>[Dev模型]</th>
                <th>[Test模型]</th>
                <th>对比</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>请求数</td>
                <td>[dev_count]</td>
                <td>[test_count]</td>
                <td>[相同/差异]</td>
            </tr>
            <tr>
                <td>平均延迟</td>
                <td>[dev_avg]s</td>
                <td>[test_avg]s</td>
                <td><span class="method-badge style-c">快 [X]%</span></td>
            </tr>
            <tr>
                <td>P50延迟</td>
                <td>[dev_p50]s</td>
                <td>[test_p50]s</td>
                <td><span class="method-badge style-c">快 [X]%</span></td>
            </tr>
            <tr>
                <td>P95延迟</td>
                <td>[dev_p95]s</td>
                <td>[test_p95]s</td>
                <td><span class="method-badge style-c">快 [X]%</span></td>
            </tr>
            <tr>
                <td>总成本</td>
                <td>$[dev_cost]</td>
                <td>$[test_cost]</td>
                <td><span class="method-badge style-c">节省 [X]%</span></td>
            </tr>
            <tr>
                <td>单次请求成本</td>
                <td>$[dev_cost_per_req]</td>
                <td>$[test_cost_per_req]</td>
                <td><span class="method-badge style-c">节省 [X]%</span></td>
            </tr>
        </tbody>
    </table>

    <div class="highlight-box">
        <strong>性能总结：</strong>[Test模型]模型在延迟和成本上均显著优于[Dev模型]...
    </div>

    <div class="info-box">
        <strong>说明：</strong>延迟数据来自Langfuse的trace统计，时间单位为秒。成本数据为API调用费用，单位为美元。单次请求成本 = 总成本 / 请求数。
    </div>
</section>
```

**Template Variables:**
| Variable | Description |
|----------|-------------|
| `{{TITLE}}` | 页面标题 (用于 `<title>`) |
| `{{HEADER_TITLE}}` | 主标题 |
| `{{HEADER_SUBTITLE}}` | 副标题 |
| `{{NAV_ITEMS}}` | 导航项 |
| `{{TOC_ITEMS}}` | 目录项 (中文数字格式) |
| `{{SECTIONS}}` | 内容章节 |

## Analysis Calculations

**Performance Difference:**
```
difference = test_mean - dev_mean
improvement_pct = (difference / dev_mean) * 100
```

**Stability Improvement:**
```
stability_improvement = ((dev_std - test_std) / dev_std) * 100
```

**Latency Improvement (if performance data exists):**
```
latency_improvement = ((dev_latency - test_latency) / dev_latency) * 100
```

**Cost Savings (if performance data exists):**
```
cost_savings = ((dev_cost - test_cost) / dev_cost) * 100
cost_per_request = total_cost / count
```

## Output Files

| File | Description |
|------|-------------|
| `[标题]评测报告.html` | Formatted HTML report |
| `[标题]评测报告.md` | Markdown version |
| `eval_data.json` | Raw data from Langfuse |

## Example Usage

**Example 1 - Langfuse with precise time:**
```
生成评测报告:
- 时间范围: 2026-04-21 09:00:00 至 2026-04-21 17:30:00
- Dev模型: DeepSeek V3.2
- Test模型: Qwen3.5-Plus
```

**Example 2 - Langfuse with daily range:**
```
生成评测报告: 2026-04-21 到 2026-04-22, dev是DeepSeek V3.2, test是Qwen3.5-Plus
```

**Example 3 - Direct input:**
```
帮我生成评测报告：
模型A是GPT-4，模型B是Claude-3
代码生成能力：GPT-4 mean=0.85 std=0.15, Claude-3 mean=0.88 std=0.12
```

## Tips

- The bundled script `scripts/langfuse_ops.py` handles Langfuse data fetching
- Time format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`
- Default user IDs: `sys-user-dev` and `sys-user-test`
- Always include actionable recommendations
