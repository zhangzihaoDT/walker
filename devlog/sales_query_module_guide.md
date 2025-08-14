# 销量查询模块使用指南

## 概述

销量查询模块 (`SalesQueryModule`) 是专门为乘用车上险量数据设计的多维度查询分析模块。该模块支持灵活的SQL查询生成，能够处理各种复杂的销量数据查询需求。

## 功能特性

### 1. 多种查询类型
- **基本销量查询** (`basic_sales`): 按指定维度统计销量
- **时间趋势分析** (`time_trend`): 分析销量随时间的变化趋势
- **排行榜查询** (`ranking`): 生成销量排行榜
- **对比分析** (`comparison`): 不同维度间的销量对比

### 2. 支持的查询维度
- **品牌维度**: `brand`, `model_name`, `sub_model_name`
- **地域维度**: `province`, `city`, `city_tier`
- **车辆属性**: `body_style`, `fuel_type`, `fuel_type_group`
- **品牌属性**: `is_luxury_brand`, `is_new_energy_brand`
- **时间维度**: `date`
- **价格维度**: `tp_center`, `tp_avg`

### 3. 灵活的筛选条件
支持对任意字段进行筛选，包括：
- 字符串匹配
- 数值范围
- 列表包含
- 布尔值筛选
- 时间范围筛选

## 使用方法

### 基本用法

```python
from modules.sales_query_module import SalesQueryModule

# 创建模块实例
sales_module = SalesQueryModule()

# 定义查询参数
params = {
    "query_type": "basic_sales",
    "dimensions": ["brand"],
    "filters": {"fuel_type": "纯电动"},
    "limit": 10
}

# 执行查询
result = sales_module.execute(params)

# 处理结果
if result['success']:
    print(f"查询成功，共{len(result['data'])}条记录")
    print(f"总结: {result['summary']}")
else:
    print(f"查询失败: {result['error']}")
```

### 参数详解

#### 必需参数
- 无（所有参数都有默认值）

#### 可选参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `query_type` | string | "basic_sales" | 查询类型 |
| `dimensions` | array | [] | 查询维度列表 |
| `filters` | object | {} | 筛选条件 |
| `start_date` | string | null | 开始日期 (YYYY-MM-DD) |
| `end_date` | string | null | 结束日期 (YYYY-MM-DD) |
| `limit` | integer | null | 结果数量限制 |
| `order_by` | string | "total_sales DESC" | 排序方式 |
| `time_unit` | string | "month" | 时间聚合单位 |

## 查询示例

### 1. 品牌销量排行榜

```python
params = {
    "query_type": "ranking",
    "dimensions": ["brand"],
    "filters": {"fuel_type": "纯电动"},
    "limit": 5
}
```

### 2. 时间趋势分析

```python
params = {
    "query_type": "time_trend",
    "dimensions": ["date"],
    "filters": {"brand": "比亚迪"},
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
}
```

### 3. 多维度组合查询

```python
params = {
    "query_type": "basic_sales",
    "dimensions": ["brand", "fuel_type", "province"],
    "filters": {"city_tier": "一线城市"},
    "limit": 10
}
```

### 4. 地域销量分析

```python
params = {
    "query_type": "basic_sales",
    "dimensions": ["province"],
    "filters": {
        "fuel_type": "纯电动",
        "is_luxury_brand": True
    },
    "limit": 15
}
```

### 5. 车身类型对比

```python
params = {
    "query_type": "comparison",
    "dimensions": ["body_style"],
    "filters": {"brand": "比亚迪"},
    "compare_field": "body_style"
}
```

## 返回结果格式

```python
{
    "success": True,                    # 执行是否成功
    "module": "销量查询模块",            # 模块名称
    "parameters": {...},               # 使用的参数
    "data": [...],                     # 查询结果数据
    "analysis": {                       # 分析统计
        "record_count": 10,
        "sales_stats": {
            "total": 1000000,
            "mean": 100000,
            "median": 95000,
            "max": 200000,
            "min": 50000
        }
    },
    "insights": [...],                 # 关键洞察
    "summary": "查询总结文本",          # 文字总结
    "timestamp": "2024-12-19T...",     # 执行时间戳
    "visualization": {...}             # 可视化配置
}
```

## 数据字段说明

### 核心字段
- `sales_volume`: 销量数据（必需）
- `date`: 日期字段（必需）

### 维度字段
- `brand`: 品牌名称
- `model_name`: 车型名称
- `sub_model_name`: 子车型名称
- `province`: 省份
- `city`: 城市
- `city_tier`: 城市层级
- `body_style`: 车身类型
- `fuel_type`: 燃料类型
- `fuel_type_group`: 燃料类型分组
- `is_luxury_brand`: 是否豪华品牌
- `is_new_energy_brand`: 是否新能源品牌
- `tp_center`: 价格中位数
- `tp_avg`: 平均价格

## 错误处理

模块提供完善的错误处理机制：

1. **参数验证**: 自动验证输入参数的有效性
2. **SQL生成错误**: 捕获SQL模板渲染错误
3. **数据库查询错误**: 处理数据库连接和查询异常
4. **数据处理错误**: 处理结果数据转换异常

```python
# 参数验证示例
validation = sales_module.validate_parameters(params)
if not validation['valid']:
    print(f"参数错误: {validation['error']}")
```

## 性能优化建议

1. **合理使用limit**: 对于大数据集，建议设置合理的limit值
2. **精确筛选条件**: 使用具体的筛选条件减少数据扫描量
3. **避免过多维度**: 维度过多可能导致结果集过大
4. **时间范围控制**: 时间趋势分析时控制时间范围

## 集成使用

### 与意图解析器集成

```python
from agents.intent_parser import IntentParser
from modules.sales_query_module import SalesQueryModule

# 解析用户意图
intent_parser = IntentParser()
intent_result = intent_parser.parse_intent("查询比亚迪品牌销量")

# 构建查询参数
params = build_query_params_from_intent(intent_result)

# 执行查询
sales_module = SalesQueryModule()
result = sales_module.execute(params)
```

### 与模块执行器集成

```python
from agents.module_executor import ModuleExecutor

executor = ModuleExecutor()
result = executor.execute_module(
    module_id="sales_query",
    parameters=params,
    data_context=data_context
)
```

## 扩展开发

### 添加新的查询类型

1. 在 `query_templates` 中添加新的SQL模板
2. 在 `_parse_query_params` 中添加参数解析逻辑
3. 在 `validate_parameters` 中添加参数验证规则

### 添加新的分析维度

1. 确保数据源包含新字段
2. 在 `optional_fields` 中添加字段名
3. 在SQL模板中支持新字段的GROUP BY

## 注意事项

1. **数据源要求**: 确保数据源包含必需的 `sales_volume` 和 `date` 字段
2. **内存使用**: 大数据集查询时注意内存使用情况
3. **SQL注入防护**: 模块使用参数化查询，但仍需注意输入验证
4. **时区处理**: 日期字段默认使用数据源的时区设置

## 更新日志

- **v1.0.0** (2024-12-19): 初始版本发布
  - 支持基本销量查询
  - 支持时间趋势分析
  - 支持排行榜查询
  - 支持多维度组合查询
  - 集成Jinja2模板引擎
  - 完善的错误处理和参数验证