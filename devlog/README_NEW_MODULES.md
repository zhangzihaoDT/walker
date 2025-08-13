# 新增分析模块说明

本文档介绍了为实现Walker策略流程而新增的三个分析模块，它们都继承自升级后的 `BaseAnalysisModule`，实现了统一的接口标准。

## 模块概览

### 1. ParameterSegmenterModule (参数细分器)
- **模块ID**: `param_segmenter`
- **功能**: 按指定维度对数据进行分组切片，为后续分析提供细分数据
- **模块类型**: `segmenter`
- **支持数据库**: DuckDB, SQLite, CSV, Excel

### 2. TrendAnalysisModule (趋势分析器)
- **模块ID**: `trend_analysis`
- **功能**: 分析时间序列数据的趋势变化，识别趋势方向和强度
- **模块类型**: `analyzer`
- **支持数据库**: DuckDB, SQLite, CSV, Excel

### 3. YoYComparisonModule (同比分析器)
- **模块ID**: `yoy_comparison`
- **功能**: 进行年同比分析，计算同期数据的变化率和增长趋势
- **模块类型**: `comparator`
- **支持数据库**: DuckDB, SQLite, CSV, Excel

## BaseAnalysisModule 升级

### 新增接口

根据 README.md 中的建议，为 `BaseAnalysisModule` 添加了新的标准接口：

```python
@abstractmethod
def get_requirements(self) -> Dict[str, Any]:
    """声明所需数据字段和参数（Walker流程标准接口）
    
    Returns:
        Dict[str, Any]: 需求声明
        {
            "data_fields": List[str],     # 必需的数据字段
            "optional_fields": List[str], # 可选的数据字段
            "parameters": List[dict],     # 参数要求
            "databases": List[str],       # 支持的数据库类型
            "module_type": str            # 模块类型
        }
    """
```

这个接口确保了不管模块是做分析还是做切片，都能在Walker流程里稳定运行。

## Walker策略流程示例

以下是一个完整的Walker策略流程示例，展示了如何串联使用这些模块：

```python
# 步骤1: 参数细分 - 按类别分组
segmenter = ParameterSegmenterModule()
segment_params = {
    'segment_fields': ['category'],
    'aggregation_method': 'none'
}
segment_results = segmenter.execute(segment_params, data_context)

# 步骤2: 趋势分析 - 对每个分组执行趋势分析
trend_analyzer = TrendAnalysisModule()
for segment_name, segment_data in segment_results['segments'].items():
    trend_params = {
        'date_field': 'date',
        'value_field': 'sales',
        'trend_method': 'linear'
    }
    trend_result = trend_analyzer.execute(trend_params, segment_data)

# 步骤3: 同比分析
yoy_analyzer = YoYComparisonModule()
yoy_params = {
    'date_field': 'date',
    'value_field': 'sales',
    'category_field': 'category',
    'comparison_periods': 1,
    'time_granularity': 'month'
}
yoy_results = yoy_analyzer.execute(yoy_params, data_context)

# 步骤4: 综合洞察生成
# 结合各模块结果生成综合分析报告
```

## 详细功能说明

### ParameterSegmenterModule

**主要参数**:
- `segment_fields`: 用于分组的字段列表
- `aggregation_method`: 聚合方法 ('none', 'count', 'sum', 'mean')
- `value_fields`: 需要聚合的数值字段列表
- `filter_conditions`: 数据过滤条件

**输出结果**:
- 分组统计信息
- 各分组的数据或聚合结果
- 分组分布洞察

**使用场景**:
- 按产品类别、地区、时间等维度切分数据
- 为后续分析模块提供细分数据
- 数据探索和分布分析

### TrendAnalysisModule

**主要参数**:
- `date_field`: 时间字段名
- `value_field`: 数值字段名
- `category_field`: 分类字段名（可选）
- `trend_method`: 趋势检测方法 ('linear', 'moving_average', 'polynomial')
- `window_size`: 移动平均窗口大小

**输出结果**:
- 趋势方向（上升/下降/平稳）
- 趋势强度（R²值）
- 趋势斜率
- 拐点检测
- 趋势数据点

**使用场景**:
- 销售趋势分析
- 用户增长趋势
- 业务指标变化趋势
- 季节性模式识别

### YoYComparisonModule

**主要参数**:
- `date_field`: 时间字段名
- `value_field`: 数值字段名
- `category_field`: 分类字段名（可选）
- `comparison_periods`: 比较的年数
- `time_granularity`: 时间粒度 ('year', 'quarter', 'month')
- `aggregation_method`: 聚合方法 ('sum', 'mean', 'count')

**输出结果**:
- 同比增长率
- 平均增长率
- 正增长周期数
- 增长趋势分析
- 同比对比数据

**使用场景**:
- 年度业绩对比
- 季度增长分析
- 月度同比分析
- 业务增长评估

## 测试和验证

运行测试脚本验证模块功能：

```bash
python test/test_new_modules.py
```

测试包括：
1. 各模块的基本功能测试
2. Walker策略流程的串联执行测试
3. 模块接口兼容性测试
4. 数据处理和结果生成测试

## 集成说明

这些模块已经集成到 `modules/__init__.py` 中，可以直接导入使用：

```python
from modules import ParameterSegmenterModule, TrendAnalysisModule, YoYComparisonModule
```

所有模块都实现了：
- 统一的 `execute()` 接口
- 新的 `get_requirements()` 接口
- 标准的错误处理
- 数据库兼容性检查
- 结果序列化支持

## 未来扩展

基于这个架构，可以轻松添加更多分析模块：

1. **相关性分析模块**: 分析变量间的相关关系
2. **异常检测模块**: 识别数据中的异常值和模式
3. **预测分析模块**: 基于历史数据进行预测
4. **聚类分析模块**: 对数据进行聚类分组
5. **统计检验模块**: 进行各种统计假设检验

每个新模块只需要：
1. 继承 `BaseAnalysisModule`
2. 实现必需的抽象方法
3. 定义模块特定的参数和逻辑
4. 添加到 `modules/__init__.py`

这样就能无缝集成到Walker策略流程中。