# 销量查询模块设计方案

## 背景分析

### 数据源分析

基于 `run_data_describe.py` 的分析结果，我们有以下三个数据源：

1. **乘用车上险量\_0723.parquet** (主要目标)

   - 行数: 10,224,552
   - 列数: 20
   - 关键字段: `sales_volume`(销量), `brand`(品牌), `model_name`(车型), `date`(日期), `province`(省份), `city`(城市), `fuel_type`(燃料类型), `body_style`(车身样式), `is_luxury_brand`(是否豪华品牌), `city_tier`(城市等级)

2. **business_daily_metrics.parquet**

   - 行数: 556
   - 业务指标数据

3. **order_observation_data.parquet**
   - 行数: 140,874
   - 订单观察数据

### 现有架构分析

1. **模块架构**: 基于 `BaseAnalysisModule` 的标准化模块系统
2. **意图识别**: 支持 `query_only`, `data_analysis`, `general_chat` 三种意图类型
3. **执行器**: `ModuleExecutor` 负责模块的加载和执行
4. **参数处理**: 支持 Jinja2 模板和参数映射

## 设计方案

### 1. 模块架构设计

#### 1.1 核心模块: SalesQueryModule

```python
class SalesQueryModule(BaseAnalysisModule):
    module_id = "sales_query"
    module_name = "销量查询模块"
    description = "基于乘用车上险量数据的多维度销量查询模块"

    # 数据库感知能力
    supported_databases = ["parquet", "duckdb"]
    required_fields = ["sales_volume", "date"]
    optional_fields = ["brand", "model_name", "province", "city", "fuel_type", "body_style", "is_luxury_brand", "city_tier"]
```

#### 1.2 查询模板系统

使用 Jinja2 模板引擎，支持以下查询类型：

1. **单维度查询**

   - 按品牌查询: `SELECT brand, SUM(sales_volume) as total_sales FROM table WHERE date >= '{{start_date}}' GROUP BY brand`
   - 按时间查询: `SELECT date, SUM(sales_volume) as total_sales FROM table WHERE date BETWEEN '{{start_date}}' AND '{{end_date}}' GROUP BY date`
   - 按地区查询: `SELECT province, SUM(sales_volume) as total_sales FROM table GROUP BY province`

2. **多维度查询**

   - 品牌+时间: `SELECT brand, date, SUM(sales_volume) as total_sales FROM table WHERE brand IN ({{brands}}) GROUP BY brand, date`
   - 地区+燃料类型: `SELECT province, fuel_type, SUM(sales_volume) as total_sales FROM table GROUP BY province, fuel_type`

3. **聚合查询**
   - TOP N 查询: `SELECT brand, SUM(sales_volume) as total_sales FROM table GROUP BY brand ORDER BY total_sales DESC LIMIT {{limit}}`
   - 趋势分析: `SELECT date, SUM(sales_volume) as total_sales FROM table GROUP BY date ORDER BY date`

### 2. 参数解析与映射

#### 2.1 意图解析增强

扩展 `IntentParser` 以支持查询参数提取：

```python
def extract_query_parameters(self, user_question: str) -> Dict[str, Any]:
    """
    从用户问题中提取查询参数

    支持的参数类型:
    - brands: 品牌列表
    - time_range: 时间范围
    - regions: 地区列表
    - fuel_types: 燃料类型
    - aggregation: 聚合方式 (sum, avg, count)
    - limit: 结果数量限制
    - order_by: 排序字段
    """
```

#### 2.2 参数映射规则

| 用户表达             | 参数名     | 示例值                                       |
| -------------------- | ---------- | -------------------------------------------- |
| "特斯拉", "Tesla"    | brands     | ["特斯拉"]                                   |
| "2024 年", "今年"    | time_range | {"start": "2024-01-01", "end": "2024-12-31"} |
| "北京", "上海"       | regions    | ["北京市", "上海市"]                         |
| "电动车", "纯电动"   | fuel_types | ["纯电动"]                                   |
| "前 10 名", "TOP 10" | limit      | 10                                           |

### 3. 查询模板库

#### 3.1 模板文件结构

```
modules/
├── sales_query_module.py
├── templates/
│   ├── sales_templates.json
│   └── query_patterns.py
└── utils/
    ├── parameter_extractor.py
    └── query_builder.py
```

#### 3.2 模板定义示例

```json
{
  "templates": {
    "brand_sales": {
      "name": "品牌销量查询",
      "description": "查询指定品牌的销量数据",
      "sql_template": "SELECT brand, SUM(sales_volume) as total_sales FROM {{table_name}} WHERE 1=1 {% if brands %}AND brand IN ({{brands|join(',', attribute='quote')}}){% endif %} {% if start_date %}AND date >= '{{start_date}}'{% endif %} {% if end_date %}AND date <= '{{end_date}}'{% endif %} GROUP BY brand ORDER BY total_sales DESC {% if limit %}LIMIT {{limit}}{% endif %}",
      "required_params": [],
      "optional_params": ["brands", "start_date", "end_date", "limit"],
      "result_columns": ["brand", "total_sales"]
    },
    "time_trend": {
      "name": "时间趋势查询",
      "description": "查询销量的时间趋势",
      "sql_template": "SELECT date, SUM(sales_volume) as total_sales FROM {{table_name}} WHERE 1=1 {% if brands %}AND brand IN ({{brands|join(',', attribute='quote')}}){% endif %} {% if start_date %}AND date >= '{{start_date}}'{% endif %} {% if end_date %}AND date <= '{{end_date}}'{% endif %} GROUP BY date ORDER BY date",
      "required_params": [],
      "optional_params": ["brands", "start_date", "end_date"],
      "result_columns": ["date", "total_sales"]
    }
  }
}
```

### 4. 实现细节

#### 4.1 核心方法实现

```python
class SalesQueryModule(BaseAnalysisModule):
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """准备数据连接"""
        data_source = params.get('data_source', 'data/乘用车上险量_0723.parquet')
        return pd.read_parquet(data_source)

    def run(self, data: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行查询"""
        # 1. 选择合适的查询模板
        template = self._select_template(params)

        # 2. 构建SQL查询
        sql_query = self._build_query(template, params)

        # 3. 执行查询
        result_df = self._execute_query(data, sql_query)

        # 4. 格式化结果
        return self._format_results(result_df, template)

    def summarize(self, results: Dict[str, Any]) -> str:
        """生成查询结果摘要"""
        return self._generate_summary(results)
```

#### 4.2 查询模板选择逻辑

```python
def _select_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据参数选择最合适的查询模板

    选择逻辑:
    1. 如果有brands参数 -> brand_sales模板
    2. 如果有time_range参数 -> time_trend模板
    3. 如果有regions参数 -> region_sales模板
    4. 默认 -> general_sales模板
    """
```

### 5. 集成方案

#### 5.1 配置文件更新

在 `analysis_config.json` 中添加新模块配置：

```json
{
  "module_id": "sales_query",
  "module_name": "销量查询模块",
  "description": "基于乘用车上险量数据的多维度销量查询模块",
  "class_name": "SalesQueryModule",
  "file_path": "modules/sales_query_module.py",
  "supported_databases": ["parquet", "duckdb"],
  "required_fields": ["sales_volume", "date"],
  "optional_fields": ["brand", "model_name", "province", "city", "fuel_type"],
  "parameter_requirements": [
    {
      "name": "data_source",
      "type": "string",
      "required": true,
      "description": "数据源路径",
      "default_value": "data/乘用车上险量_0723.parquet"
    },
    {
      "name": "query_type",
      "type": "string",
      "required": false,
      "description": "查询类型",
      "default_value": "auto"
    }
  ]
}
```

#### 5.2 路由集成

在 `graph_builder.py` 的 `sql_agent_node` 中集成销量查询模块：

```python
def sql_agent_node(self, state: WorkflowState) -> WorkflowState:
    """SQL代理节点 - 处理query_only类型的问题"""
    user_question = state["user_question"]
    intent_result = state["intent_result"]

    # 使用销量查询模块处理查询
    from agents.module_executor import get_module_executor
    executor = get_module_executor()

    # 提取查询参数
    query_params = self._extract_query_parameters(user_question)

    # 执行销量查询模块
    result = executor.execute_module(
        module_id="sales_query",
        parameters=query_params,
        data_context={"type": "file_system", "path": "data/乘用车上险量_0723.parquet"}
    )

    state["sql_result"] = result
    return state
```

### 6. 测试方案

#### 6.1 单元测试

```python
# test/test_sales_query_module.py
class TestSalesQueryModule:
    def test_brand_query(self):
        """测试品牌查询"""

    def test_time_trend_query(self):
        """测试时间趋势查询"""

    def test_multi_dimension_query(self):
        """测试多维度查询"""
```

#### 6.2 集成测试

```python
# test/test_sales_query_integration.py
def test_query_only_intent():
    """测试query_only意图的完整流程"""
    questions = [
        "查询特斯拉2024年的销量",
        "比亚迪和蔚来哪个卖得更好？",
        "北京地区新能源车销量如何？"
    ]
```

### 7. 扩展计划

#### 7.1 短期扩展

1. 支持更复杂的查询条件组合
2. 添加数据可视化功能
3. 支持查询结果缓存

#### 7.2 长期扩展

1. 支持其他两个数据源的查询模块
2. 添加自然语言查询优化
3. 支持查询性能分析

## 实施步骤

1. **第一阶段**: 创建基础的 `SalesQueryModule` 类
2. **第二阶段**: 实现查询模板系统和参数提取
3. **第三阶段**: 集成到现有的路由系统
4. **第四阶段**: 添加测试和文档
5. **第五阶段**: 性能优化和扩展功能

## 预期效果

1. **查询效率**: 支持秒级响应的销量查询
2. **灵活性**: 支持多维度、多条件的复杂查询
3. **易用性**: 自然语言查询，无需 SQL 知识
4. **扩展性**: 模块化设计，易于扩展到其他数据源
5. **准确性**: 基于模板的 SQL 生成，减少错误

这个设计方案充分利用了现有的架构优势，通过模块化的方式实现了高效、灵活的销量查询功能。
