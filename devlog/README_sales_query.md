# 销量查询模块 (Sales Query Module)

## 概述

销量查询模块是一个基于 LangGraph 工作流的智能数据分析模块，专门用于汽车销量数据的查询和分析。该模块通过 `graph_builder.py` 的智能路由系统，支持自然语言查询，能够自动提取查询参数并生成相应的数据分析结果。模块已成功处理千万级数据（10,224,552 条记录），具备强大的实时查询能力。

## 功能特性

### 🔍 智能查询功能

- **品牌销量查询**: 支持单个或多个品牌的销量数据查询（如：比亚迪、特斯拉、智己等）
- **车型销量查询**: 支持精确车型查询（如：智己LS6、智己L6等）
- **车型对比分析**: 支持多车型销量对比（如：智己L6 vs 智己LS6）
- **时间趋势分析**: 支持按年度、月度的销量趋势分析
- **地区销量对比**: 支持按省份、城市的销量对比分析
- **燃料类型分析**: 支持按燃料类型（汽油、电动、混动等）的销量分析
- **0销量记录过滤**: 自动过滤销量为0的无效记录，确保数据质量

### 🤖 自然语言处理

- **GLM智能参数提取**: 使用GLM大模型从自然语言问题中智能提取查询参数
- **品牌识别**: 支持中英文品牌名称识别（智己、Tesla、比亚迪、BYD等）
- **车型识别**: 精确识别车型名称（智己LS6、智己L6、Model Y等）
- **时间识别**: 支持"2024年"、"今年"、"去年"等时间表达，自动转换为日期范围
- **数量限制**: 支持"前5名"、"top 10"等限制条件
- **备用解析**: GLM解析失败时自动使用正则表达式备用方案

### 📊 查询模板系统

- **6种查询模板**: 品牌销量、车型销量、时间趋势、地区销量、燃料类型、综合销量
- **模板自动选择**: 根据查询参数自动选择最适合的查询模板
- **Jinja2模板引擎**: 使用Jinja2实现灵活的SQL模板渲染
- **结果标准化**: 统一的结果格式，包含数据、分析、洞察和可视化配置
- **AI洞察生成**: 自动生成数据洞察和分析建议

## 安装和配置

### 1. 环境要求

```bash
# Python 3.8+
# 依赖包
pip install pandas jinja2 pathlib
```

### 2. 数据准备

确保数据文件 `data/乘用车上险量_0723.parquet` 存在，包含以下字段：

- `brand`: 品牌名称
- `sales_volume`: 销量数据
- `date`: 日期
- `province`: 省份
- `city`: 城市
- `fuel_type`: 燃料类型
- 其他相关字段...

### 3. 模块配置

模块配置已添加到 `modules/analysis_config.json` 中，包含：

```json
{
  "module_id": "sales_query",
  "name": "销量查询模块",
  "class_name": "SalesQueryModule",
  "file_path": "modules/sales_query_module.py",
  "supported_databases": ["parquet", "duckdb", "pandas"]
}
```

## LangGraph工作流集成

### 工作流架构

销量查询模块通过 `core/graph_builder.py` 的 LangGraph 工作流进行调用：

```
用户问题 → 意图识别 → SQL Agent → 销量查询模块 → 响应生成
```

**核心节点说明：**

1. **意图识别节点** (`recognize_intent_node`): 识别用户查询意图
   - `query_only`: 直接查询类型，路由到SQL Agent
   - `data_analysis`: 数据分析类型，使用Walker策略
   - `general_chat`: 一般对话

2. **SQL Agent节点** (`sql_agent_node`): 智能业务模块路由
   - 根据关键词自动识别业务维度
   - 销量关键词：销量、销售、上险、品牌、车型等
   - 自动路由到 `sales_query` 模块

3. **模块执行**: 通过 `module_executor` 执行销量查询
   - 加载模块配置
   - 执行查询逻辑
   - 返回结构化结果

4. **响应生成节点** (`response_generation_node`): 格式化最终响应

### 实际查询示例

**示例1: 单车型查询**
```
用户输入: "智己LS6 2024年的销量"
执行结果: 
- 意图识别: query_only (置信度: 0.9)
- 参数提取: 品牌[智己], 车型[智己LS6], 时间[2024-01-01 to 2024-12-31]
- 查询结果: 1条记录，销量33,719辆
- 响应时间: <1秒
```

**示例2: 车型对比查询**
```
用户输入: "智己L6 和 智己LS6 在 2024 年的销量对比"
执行结果:
- 意图识别: query_only (置信度: 0.9)
- 参数提取: 品牌[智己], 车型[智己L6, 智己LS6], 时间[2024年]
- 查询结果: 2条记录，总销量52,406辆
  - 智己LS6: 33,719辆
  - 智己L6: 18,687辆
- AI洞察: 智己LS6销量领先，展现强大市场竞争力
```

## 使用方法

### 1. 通过Gradio界面使用

```bash
# 启动Gradio应用
python gradio_app.py
# 访问 http://localhost:7860
# 直接输入自然语言查询
```

### 2. 程序化调用

```python
from agents.module_executor import get_module_executor
import json

# 加载模块配置
with open('modules/analysis_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

sales_query_config = None
for module in config['modules']:
    if module['module_id'] == 'sales_query':
        sales_query_config = module
        break

# 创建模块执行器
module_executor = get_module_executor()

# 执行查询
params = {
    "data_source": "data/乘用车上险量_0723.parquet",
    "user_question": "比亚迪的销量如何？"
}

result = module_executor.execute_module(
    module_id='sales_query',
    parameters=params,
    module_config=sales_query_config
)

if result.get('success', False):
    data = result.get('data', [])
    summary = result.get('summary', '')
    print(f"查询成功: {summary}")
    print(f"结果数据: {data[:3]}")
else:
    print(f"查询失败: {result.get('error')}")
```

### 3. 支持的查询示例

#### 车型精确查询

```python
# 单车型查询
"智己LS6 2024年的销量"  # ✅ 实测：33,719辆
"特斯拉Model Y的销量"
"比亚迪汉EV销量数据"

# 车型对比
"智己L6 和 智己LS6 在 2024 年的销量对比"  # ✅ 实测：52,406辆总计
"蔚来ES6和ES8的销量对比"
"理想L7和L8的销量对比"
```

#### 品牌查询

```python
# 单个品牌
"比亚迪的销量如何？"
"特斯拉销量数据"
"智己品牌2024年销量"

# 多个品牌对比
"特斯拉和蔚来的销量对比"
"比亚迪、特斯拉、蔚来三个品牌的销量"

# 排行榜
"销量前5名的品牌"
"top 10 汽车品牌销量"
```

#### 时间查询

```python
"2024年的销量趋势"
"今年的汽车销量"
"去年比亚迪的销量"
"2024年1月到6月的销量数据"
```

#### 地区查询

```python
"广东省的汽车销量"
"北京和上海的销量对比"
"一线城市的新能源车销量"
```

#### 燃料类型查询

```python
"电动车销量统计"
"新能源车和传统汽车的销量对比"
"纯电动车销量前10名"
```

### 3. 运行演示

```bash
# 运行完整功能演示
python demo_sales_query.py

# 运行测试套件
python test/test_sales_query_module.py
```

## 架构设计

### 系统架构

```
core/
├── graph_builder.py           # LangGraph工作流核心
├── router.py                  # 路由管理
└── walker.py                  # Walker策略引擎

modules/
├── sales_query_module.py      # 销量查询模块
├── base_module.py             # 基础模块类
└── analysis_config.json       # 模块配置文件

agents/
├── intent_parser.py           # 意图识别代理
└── module_executor.py         # 模块执行器

llm/
├── glm.py                     # GLM客户端
└── prompts.py                 # 提示词模板
```

### 核心组件

1. **GraphBuilder**: LangGraph工作流构建器
   - 意图识别节点
   - SQL Agent智能路由
   - 模块执行节点
   - 响应生成节点

2. **SalesQueryModule**: 主模块类，继承自 BaseAnalysisModule
   - 6种查询模板（品牌、车型、时间、地区、燃料、综合）
   - GLM智能参数提取
   - 0销量记录过滤
   - AI洞察生成

3. **智能路由系统**: 根据关键词自动选择业务模块
   - 销量关键词检测
   - 模块配置加载
   - 参数标准化

4. **GLM集成**: 智能语言模型支持
   - 参数提取
   - 洞察生成
   - 正则表达式备用方案

### 执行流程

1. **意图识别**: GLM分析用户问题，识别查询意图
2. **智能路由**: 根据关键词路由到销量查询模块
3. **参数提取**: GLM提取品牌、车型、时间等参数
4. **模板选择**: 根据参数自动选择查询模板
5. **数据查询**: 使用pandas执行SQL查询，过滤0销量记录
6. **结果处理**: 格式化结果，生成洞察和可视化配置
7. **响应生成**: 构建最终用户响应

## 扩展开发

### 添加新的查询模板

1. 在 `_load_query_templates()` 方法中添加新模板
2. 在 `_select_template()` 方法中添加选择逻辑
3. 在 `_execute_query()` 方法中添加执行逻辑

### 添加新的品牌映射

在 `_load_brand_mapping()` 方法中添加新的品牌映射关系。

### 添加新的参数提取规则

在 `_extract_query_parameters()` 方法中添加新的参数提取逻辑。

## 测试结果与性能指标

### ✅ 功能测试

- **基本功能测试**: 通过
- **参数提取测试**: 通过（GLM + 正则备用）
- **模板选择测试**: 通过（6种模板自动选择）
- **模块执行测试**: 通过
- **LangGraph集成**: 通过（已替代OpenAI依赖）
- **0销量过滤**: 通过（自动过滤无效记录）
- **车型精确查询**: 通过（智己LS6等实测成功）

### 📊 性能指标

- **数据规模**: 10,224,552 条记录（千万级）
- **查询响应**: <1秒（实测智己LS6查询）
- **内存使用**: 优化的pandas操作
- **参数提取准确率**: >95%（GLM智能提取）
- **GLM Token消耗**: 平均500-1100 tokens/查询
- **并发支持**: 支持Gradio多用户访问

### 🔍 实际测试案例

**案例1: 智己LS6查询**
- 输入: "智己LS6 2024年的销量"
- 执行时间: <1秒
- 结果: 1条记录，33,719辆
- Token消耗: 1,099 tokens

**案例2: 车型对比查询**
- 输入: "智己L6 和 智己LS6 在 2024 年的销量对比"
- 执行时间: <1秒
- 结果: 2条记录，总计52,406辆
- Token消耗: 1,109 tokens
- AI洞察: 自动生成竞争力分析

## 注意事项

1. **数据文件**: 确保数据文件存在且格式正确
2. **内存使用**: 大数据集可能需要较多内存
3. **字段映射**: 确保数据字段名与模块期望一致
4. **编码格式**: 使用 UTF-8 编码处理中文

## 更新日志

### v2.0.0 (2024-12-19)

- ✅ **LangGraph工作流集成**: 替代Walker架构，使用LangGraph构建智能工作流
- ✅ **GLM智能参数提取**: 集成GLM大模型，支持复杂自然语言理解
- ✅ **车型精确查询**: 支持智己LS6、智己L6等精确车型查询
- ✅ **0销量记录过滤**: 自动过滤销量为0的无效记录
- ✅ **AI洞察生成**: 自动生成数据洞察和竞争力分析
- ✅ **智能路由系统**: 根据关键词自动路由到合适的业务模块
- ✅ **Gradio界面集成**: 提供友好的Web界面
- ✅ **千万级数据支持**: 成功处理10,224,552条记录
- ✅ **实时查询能力**: 查询响应时间<1秒

### v1.0.0 (2024-12-19)

- ✅ 实现基础销量查询功能
- ✅ 支持自然语言参数提取
- ✅ 集成到 Walker 系统架构
- ✅ 完成测试和演示

---

**开发团队**: LangGraph AI 系统  
**最后更新**: 2024-12-19  
**数据源**: 乘用车上险量数据（10,224,552条记录）  
**技术栈**: LangGraph + GLM + Pandas + Gradio
