"""同比分析模块

用于进行年同比（Year-over-Year）分析，比较不同时期的数据变化。
支持多种时间粒度的同比分析，如年度、季度、月度等。
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base_module import BaseAnalysisModule


class YoYComparisonModule(BaseAnalysisModule):
    """同比分析模块
    
    进行年同比分析，计算同期数据的变化率、增长趋势等指标。
    支持按不同维度进行分组同比分析。
    """
    
    # 模块基本信息
    module_id = "yoy_comparison"
    module_name = "同比分析"
    description = "进行年同比分析，计算同期数据的变化率和增长趋势"
    
    # 数据库感知能力
    supported_databases = ['duckdb', 'sqlite', 'csv', 'excel']
    required_fields = ['date_field', 'value_field']  # 需要时间字段和数值字段
    optional_fields = ['category_field', 'region_field']  # 可选的分类字段
    
    def __init__(self):
        super().__init__()
    
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """准备数据
        
        Args:
            db_connector: 数据库连接器
            params: 参数字典
                - date_field: str 时间字段名
                - value_field: str 数值字段名
                - category_field: str 分类字段名（可选）
                - table_name: str 表名
                - comparison_periods: int 比较的年数（默认1年）
                - time_granularity: str 时间粒度 ('year', 'quarter', 'month')
                
        Returns:
            pd.DataFrame: 准备好的时间序列数据
        """
        date_field = params.get('date_field')
        value_field = params.get('value_field')
        category_field = params.get('category_field')
        table_name = params.get('table_name', 'data')
        comparison_periods = params.get('comparison_periods', 1)
        
        if not date_field or not value_field:
            raise ValueError("必须指定时间字段(date_field)和数值字段(value_field)")
        
        # 构建查询字段
        select_fields = [date_field, value_field]
        if category_field:
            select_fields.append(category_field)
        
        if hasattr(db_connector, 'execute'):
            # 数据库连接器
            query = f"SELECT {', '.join(select_fields)} FROM {table_name} ORDER BY {date_field}"
            
            result = db_connector.execute(query)
            if hasattr(result, 'df'):
                data = result.df()
            else:
                data = pd.DataFrame(result.fetchall())
        else:
            # 假设是DataFrame
            data = db_connector[select_fields].copy()
            data = data.sort_values(date_field)
        
        # 验证必需字段
        missing_fields = [field for field in [date_field, value_field] if field not in data.columns]
        if missing_fields:
            raise ValueError(f"数据中缺少必需字段: {missing_fields}")
        
        # 转换日期字段
        data[date_field] = pd.to_datetime(data[date_field])
        
        # 确保数值字段为数值类型
        data[value_field] = pd.to_numeric(data[value_field], errors='coerce')
        
        # 移除空值
        data = data.dropna(subset=[date_field, value_field])
        
        # 确保有足够的历史数据进行同比
        min_date = data[date_field].min()
        max_date = data[date_field].max()
        date_range = (max_date - min_date).days
        
        if date_range < comparison_periods * 365:
            print(f"警告：数据时间范围({date_range}天)可能不足以进行{comparison_periods}年同比分析")
        
        return data
    
    def run(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行同比分析
        
        Args:
            data: 时间序列数据
            params: 参数字典
                - date_field: str 时间字段名
                - value_field: str 数值字段名
                - category_field: str 分类字段名（可选）
                - comparison_periods: int 比较的年数（默认1年）
                - time_granularity: str 时间粒度 ('year', 'quarter', 'month')
                - aggregation_method: str 聚合方法 ('sum', 'mean', 'count')
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        date_field = params.get('date_field')
        value_field = params.get('value_field')
        category_field = params.get('category_field')
        comparison_periods = params.get('comparison_periods', 1)
        time_granularity = params.get('time_granularity', 'month')
        aggregation_method = params.get('aggregation_method', 'sum')
        
        results = {
            'data': [],
            'analysis': {},
            'visualization': {},
            'insights': []
        }
        
        if category_field and category_field in data.columns:
            # 按分类分别分析
            categories = data[category_field].unique()
            category_results = {}
            
            for category in categories:
                category_data = data[data[category_field] == category].copy()
                category_analysis = self._perform_yoy_analysis(
                    category_data, date_field, value_field,
                    comparison_periods, time_granularity, aggregation_method
                )
                category_results[str(category)] = category_analysis
            
            results['analysis']['by_category'] = category_results
            results['data'] = self._format_category_results(category_results)
        else:
            # 整体分析
            yoy_analysis = self._perform_yoy_analysis(
                data, date_field, value_field,
                comparison_periods, time_granularity, aggregation_method
            )
            results['analysis'] = yoy_analysis
            results['data'] = yoy_analysis.get('comparison_data', [])
        
        # 设置可视化配置
        results['visualization'] = {
            'type': 'yoy_comparison',
            'chart_type': 'bar',
            'x_field': 'period',
            'y_field': 'yoy_growth_rate',
            'comparison_chart': True
        }
        
        # 生成洞察
        results['insights'] = self._generate_insights(results['analysis'])
        
        return results
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成分析结果的文字解读
        
        Args:
            results: 分析结果字典
                
        Returns:
            str: 文字解读
        """
        analysis = results.get('analysis', {})
        
        summary = "同比分析结果：\n\n"
        
        if 'by_category' in analysis:
            # 分类同比分析
            category_results = analysis['by_category']
            summary += f"按分类进行同比分析，共分析了 {len(category_results)} 个类别：\n\n"
            
            for category, cat_analysis in category_results.items():
                avg_growth = cat_analysis.get('average_growth_rate', 0)
                latest_growth = cat_analysis.get('latest_growth_rate', 0)
                summary += f"- {category}: 平均同比增长 {avg_growth:.1f}%，最近期同比增长 {latest_growth:.1f}%\n"
        else:
            # 整体同比分析
            avg_growth = analysis.get('average_growth_rate', 0)
            latest_growth = analysis.get('latest_growth_rate', 0)
            total_periods = analysis.get('total_periods', 0)
            positive_periods = analysis.get('positive_growth_periods', 0)
            
            summary += f"整体平均同比增长率: {avg_growth:.1f}%\n"
            summary += f"最近期同比增长率: {latest_growth:.1f}%\n"
            summary += f"分析周期数: {total_periods}\n"
            summary += f"正增长周期数: {positive_periods} ({positive_periods/total_periods*100:.1f}%)\n\n"
            
            # 添加趋势描述
            if latest_growth > avg_growth + 5:
                summary += "近期增长表现优于历史平均水平\n"
            elif latest_growth < avg_growth - 5:
                summary += "近期增长表现低于历史平均水平\n"
            else:
                summary += "近期增长表现与历史平均水平基本一致\n"
        
        return summary
    
    def get_requirements(self) -> Dict[str, Any]:
        """声明所需数据字段和参数
        
        Returns:
            Dict[str, Any]: 需求声明
        """
        return {
            "data_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "parameters": [
                {
                    "name": "date_field",
                    "type": "string",
                    "required": True,
                    "description": "时间字段名",
                    "example": "date"
                },
                {
                    "name": "value_field",
                    "type": "string",
                    "required": True,
                    "description": "数值字段名",
                    "example": "sales"
                },
                {
                    "name": "category_field",
                    "type": "string",
                    "required": False,
                    "description": "分类字段名（可选）",
                    "example": "product_category"
                },
                {
                    "name": "comparison_periods",
                    "type": "integer",
                    "required": False,
                    "description": "比较的年数",
                    "default_value": 1
                },
                {
                    "name": "time_granularity",
                    "type": "string",
                    "required": False,
                    "description": "时间粒度",
                    "valid_values": ["year", "quarter", "month"],
                    "default_value": "month"
                },
                {
                    "name": "aggregation_method",
                    "type": "string",
                    "required": False,
                    "description": "聚合方法",
                    "valid_values": ["sum", "mean", "count"],
                    "default_value": "sum"
                }
            ],
            "databases": self.supported_databases,
            "module_type": "comparator"
        }
    
    def _perform_yoy_analysis(self, data: pd.DataFrame, date_field: str, value_field: str,
                             comparison_periods: int, time_granularity: str, 
                             aggregation_method: str) -> Dict[str, Any]:
        """执行同比分析
        
        Args:
            data: 时间序列数据
            date_field: 时间字段名
            value_field: 数值字段名
            comparison_periods: 比较年数
            time_granularity: 时间粒度
            aggregation_method: 聚合方法
            
        Returns:
            Dict[str, Any]: 同比分析结果
        """
        if len(data) == 0:
            return {
                'comparison_data': [],
                'average_growth_rate': 0,
                'latest_growth_rate': 0,
                'total_periods': 0,
                'positive_growth_periods': 0
            }
        
        # 根据时间粒度创建时间分组
        data_copy = data.copy()
        
        if time_granularity == 'year':
            data_copy['period'] = data_copy[date_field].dt.year
        elif time_granularity == 'quarter':
            data_copy['period'] = data_copy[date_field].dt.year.astype(str) + '-Q' + data_copy[date_field].dt.quarter.astype(str)
        elif time_granularity == 'month':
            data_copy['period'] = data_copy[date_field].dt.to_period('M')
        
        # 按时间周期聚合数据
        if aggregation_method == 'sum':
            aggregated = data_copy.groupby('period')[value_field].sum().reset_index()
        elif aggregation_method == 'mean':
            aggregated = data_copy.groupby('period')[value_field].mean().reset_index()
        elif aggregation_method == 'count':
            aggregated = data_copy.groupby('period')[value_field].count().reset_index()
        
        aggregated = aggregated.sort_values('period')
        
        # 计算同比增长率
        comparison_data = []
        growth_rates = []
        
        for i, row in aggregated.iterrows():
            current_period = row['period']
            current_value = row[value_field]
            
            # 寻找对应的历史同期数据
            if time_granularity == 'year':
                target_period = current_period - comparison_periods
            elif time_granularity == 'quarter':
                # 处理季度格式 "YYYY-QX"
                if isinstance(current_period, str) and '-Q' in current_period:
                    year, quarter = current_period.split('-Q')
                    target_year = int(year) - comparison_periods
                    target_period = f"{target_year}-Q{quarter}"
                else:
                    continue
            elif time_granularity == 'month':
                # 处理月度周期
                if hasattr(current_period, 'year'):
                    # 使用更兼容的方式计算目标周期
                    current_year = current_period.year
                    current_month = current_period.month
                    target_year = current_year - comparison_periods
                    target_period = pd.Period(year=target_year, month=current_month, freq='M')
                else:
                    continue
            
            # 查找历史同期数据
            historical_data = aggregated[aggregated['period'] == target_period]
            
            if not historical_data.empty:
                historical_value = historical_data[value_field].iloc[0]
                
                if historical_value != 0:
                    growth_rate = ((current_value - historical_value) / historical_value) * 100
                else:
                    growth_rate = 0 if current_value == 0 else float('inf')
                
                growth_rates.append(growth_rate)
                
                comparison_data.append({
                    'period': str(current_period),
                    'current_value': float(current_value),
                    'historical_value': float(historical_value),
                    'growth_rate': float(growth_rate) if growth_rate != float('inf') else None,
                    'growth_amount': float(current_value - historical_value)
                })
        
        # 计算统计指标
        valid_growth_rates = [gr for gr in growth_rates if gr != float('inf') and not pd.isna(gr)]
        
        if valid_growth_rates:
            average_growth_rate = np.mean(valid_growth_rates)
            latest_growth_rate = valid_growth_rates[-1] if valid_growth_rates else 0
            positive_growth_periods = sum(1 for gr in valid_growth_rates if gr > 0)
        else:
            average_growth_rate = 0
            latest_growth_rate = 0
            positive_growth_periods = 0
        
        return {
            'comparison_data': comparison_data,
            'average_growth_rate': float(average_growth_rate),
            'latest_growth_rate': float(latest_growth_rate),
            'total_periods': len(comparison_data),
            'positive_growth_periods': positive_growth_periods,
            'time_granularity': time_granularity,
            'comparison_periods': comparison_periods,
            'aggregation_method': aggregation_method
        }
    
    def _format_category_results(self, category_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化分类结果为统一格式"""
        formatted_data = []
        
        for category, analysis in category_results.items():
            formatted_data.append({
                'category': category,
                'average_growth_rate': analysis.get('average_growth_rate', 0),
                'latest_growth_rate': analysis.get('latest_growth_rate', 0),
                'total_periods': analysis.get('total_periods', 0),
                'positive_growth_periods': analysis.get('positive_growth_periods', 0)
            })
        
        return formatted_data
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成分析洞察"""
        insights = []
        
        if 'by_category' in analysis:
            # 分类分析洞察
            category_results = analysis['by_category']
            
            # 找出增长最快和最慢的类别
            best_category = None
            worst_category = None
            max_growth = float('-inf')
            min_growth = float('inf')
            
            for category, cat_analysis in category_results.items():
                avg_growth = cat_analysis.get('average_growth_rate', 0)
                if avg_growth > max_growth:
                    max_growth = avg_growth
                    best_category = category
                if avg_growth < min_growth:
                    min_growth = avg_growth
                    worst_category = category
            
            if best_category:
                insights.append(f"'{best_category}'类别表现最佳，平均同比增长{max_growth:.1f}%")
            if worst_category and worst_category != best_category:
                insights.append(f"'{worst_category}'类别表现最差，平均同比增长{min_growth:.1f}%")
            
            # 统计正增长类别数量
            positive_categories = sum(1 for cat_analysis in category_results.values() 
                                    if cat_analysis.get('average_growth_rate', 0) > 0)
            total_categories = len(category_results)
            
            insights.append(f"{positive_categories}/{total_categories}个类别实现正增长")
        
        else:
            # 整体分析洞察
            avg_growth = analysis.get('average_growth_rate', 0)
            latest_growth = analysis.get('latest_growth_rate', 0)
            positive_periods = analysis.get('positive_growth_periods', 0)
            total_periods = analysis.get('total_periods', 0)
            
            if avg_growth > 10:
                insights.append("整体呈现强劲增长态势")
            elif avg_growth > 0:
                insights.append("整体呈现稳定增长态势")
            elif avg_growth < -10:
                insights.append("整体呈现明显下降趋势")
            else:
                insights.append("整体增长相对平稳")
            
            if total_periods > 0:
                positive_ratio = positive_periods / total_periods
                if positive_ratio > 0.8:
                    insights.append("大部分时期都实现了正增长")
                elif positive_ratio < 0.3:
                    insights.append("多数时期出现负增长，需要关注")
            
            # 比较最近期与平均水平
            if abs(latest_growth - avg_growth) > 5:
                if latest_growth > avg_growth:
                    insights.append("最近期增长表现超出历史平均水平")
                else:
                    insights.append("最近期增长表现低于历史平均水平")
        
        return insights