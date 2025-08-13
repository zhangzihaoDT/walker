"""趋势分析模块

用于分析时间序列数据的趋势变化，识别上升、下降、平稳等趋势模式。
支持多种趋势检测算法和可视化展示。
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base_module import BaseAnalysisModule


class TrendAnalysisModule(BaseAnalysisModule):
    """趋势分析模块
    
    分析时间序列数据的趋势变化，提供趋势方向、强度、
    拐点检测等功能。
    """
    
    # 模块基本信息
    module_id = "trend_analysis"
    module_name = "趋势分析"
    description = "分析时间序列数据的趋势变化，识别趋势方向和强度"
    
    # 数据库感知能力
    supported_databases = ['duckdb', 'sqlite', 'csv', 'excel']
    required_fields = ['date_field', 'value_field']  # 需要时间字段和数值字段
    optional_fields = ['category_field']  # 可选的分类字段
    
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
                - start_date: str 开始日期（可选）
                - end_date: str 结束日期（可选）
                
        Returns:
            pd.DataFrame: 准备好的时间序列数据
        """
        date_field = params.get('date_field')
        value_field = params.get('value_field')
        category_field = params.get('category_field')
        table_name = params.get('table_name', 'data')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        if not date_field or not value_field:
            raise ValueError("必须指定时间字段(date_field)和数值字段(value_field)")
        
        # 构建查询
        select_fields = [date_field, value_field]
        if category_field:
            select_fields.append(category_field)
        
        if hasattr(db_connector, 'execute'):
            # 数据库连接器
            query = f"SELECT {', '.join(select_fields)} FROM {table_name}"
            
            # 添加时间范围过滤
            conditions = []
            if start_date:
                conditions.append(f"{date_field} >= '{start_date}'")
            if end_date:
                conditions.append(f"{date_field} <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY {date_field}"
            
            result = db_connector.execute(query)
            if hasattr(result, 'df'):
                data = result.df()
            else:
                data = pd.DataFrame(result.fetchall())
        else:
            # 假设是DataFrame
            data = db_connector[select_fields].copy()
            
            # 应用时间范围过滤
            if start_date:
                data = data[data[date_field] >= start_date]
            if end_date:
                data = data[data[date_field] <= end_date]
            
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
        
        return data
    
    def run(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行趋势分析
        
        Args:
            data: 时间序列数据
            params: 参数字典
                - date_field: str 时间字段名
                - value_field: str 数值字段名
                - category_field: str 分类字段名（可选）
                - trend_method: str 趋势检测方法 ('linear', 'moving_average', 'polynomial')
                - window_size: int 移动平均窗口大小
                - polynomial_degree: int 多项式拟合度数
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        date_field = params.get('date_field')
        value_field = params.get('value_field')
        category_field = params.get('category_field')
        trend_method = params.get('trend_method', 'linear')
        window_size = params.get('window_size', 7)
        polynomial_degree = params.get('polynomial_degree', 2)
        
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
                category_analysis = self._analyze_trend(
                    category_data, date_field, value_field, 
                    trend_method, window_size, polynomial_degree
                )
                category_results[str(category)] = category_analysis
            
            results['analysis']['by_category'] = category_results
            results['data'] = self._format_category_results(category_results)
        else:
            # 整体分析
            trend_analysis = self._analyze_trend(
                data, date_field, value_field, 
                trend_method, window_size, polynomial_degree
            )
            results['analysis'] = trend_analysis
            results['data'] = trend_analysis.get('trend_data', [])
        
        # 设置可视化配置
        results['visualization'] = {
            'type': 'trend',
            'chart_type': 'line',
            'x_field': date_field,
            'y_field': value_field,
            'trend_line': True
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
        
        summary = "趋势分析结果：\n\n"
        
        if 'by_category' in analysis:
            # 分类趋势分析
            category_results = analysis['by_category']
            summary += f"按分类进行趋势分析，共分析了 {len(category_results)} 个类别：\n\n"
            
            for category, cat_analysis in category_results.items():
                trend_direction = cat_analysis.get('trend_direction', '未知')
                trend_strength = cat_analysis.get('trend_strength', 0)
                summary += f"- {category}: {trend_direction}趋势，强度 {trend_strength:.2f}\n"
        else:
            # 整体趋势分析
            trend_direction = analysis.get('trend_direction', '未知')
            trend_strength = analysis.get('trend_strength', 0)
            slope = analysis.get('slope', 0)
            
            summary += f"整体趋势方向: {trend_direction}\n"
            summary += f"趋势强度: {trend_strength:.2f}\n"
            summary += f"变化率: {slope:.4f}\n\n"
            
            # 添加拐点信息
            turning_points = analysis.get('turning_points', [])
            if turning_points:
                summary += f"检测到 {len(turning_points)} 个趋势拐点\n"
        
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
                    "name": "trend_method",
                    "type": "string",
                    "required": False,
                    "description": "趋势检测方法",
                    "valid_values": ["linear", "moving_average", "polynomial"],
                    "default_value": "linear"
                },
                {
                    "name": "window_size",
                    "type": "integer",
                    "required": False,
                    "description": "移动平均窗口大小",
                    "default_value": 7
                },
                {
                    "name": "start_date",
                    "type": "string",
                    "required": False,
                    "description": "分析开始日期",
                    "example": "2023-01-01"
                },
                {
                    "name": "end_date",
                    "type": "string",
                    "required": False,
                    "description": "分析结束日期",
                    "example": "2023-12-31"
                }
            ],
            "databases": self.supported_databases,
            "module_type": "analyzer"
        }
    
    def _analyze_trend(self, data: pd.DataFrame, date_field: str, value_field: str, 
                      method: str, window_size: int, polynomial_degree: int) -> Dict[str, Any]:
        """分析单个时间序列的趋势
        
        Args:
            data: 时间序列数据
            date_field: 时间字段名
            value_field: 数值字段名
            method: 趋势检测方法
            window_size: 移动平均窗口大小
            polynomial_degree: 多项式度数
            
        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        if len(data) < 2:
            return {
                'trend_direction': '数据不足',
                'trend_strength': 0,
                'slope': 0,
                'trend_data': []
            }
        
        # 准备数据
        data_sorted = data.sort_values(date_field).copy()
        dates = data_sorted[date_field]
        values = data_sorted[value_field]
        
        # 创建数值型时间索引用于计算
        time_numeric = np.arange(len(values))
        
        # 根据方法计算趋势
        if method == 'linear':
            # 线性回归
            slope, intercept = np.polyfit(time_numeric, values, 1)
            trend_values = slope * time_numeric + intercept
            
        elif method == 'moving_average':
            # 移动平均
            trend_values = values.rolling(window=window_size, center=True).mean()
            slope = self._calculate_slope(trend_values.dropna())
            
        elif method == 'polynomial':
            # 多项式拟合
            coeffs = np.polyfit(time_numeric, values, polynomial_degree)
            trend_values = np.polyval(coeffs, time_numeric)
            slope = self._calculate_slope(trend_values)
        
        # 计算趋势强度（R²）
        if len(trend_values) > 0:
            correlation = np.corrcoef(values, trend_values)[0, 1]
            trend_strength = correlation ** 2 if not np.isnan(correlation) else 0
        else:
            trend_strength = 0
        
        # 确定趋势方向
        if slope > 0.01:
            trend_direction = '上升'
        elif slope < -0.01:
            trend_direction = '下降'
        else:
            trend_direction = '平稳'
        
        # 检测拐点
        turning_points = self._detect_turning_points(values, dates)
        
        # 格式化趋势数据
        trend_data = []
        for i, (date, original, trend) in enumerate(zip(dates, values, trend_values)):
            trend_data.append({
                'date': date.isoformat() if hasattr(date, 'isoformat') else str(date),
                'original_value': float(original) if not pd.isna(original) else None,
                'trend_value': float(trend) if not pd.isna(trend) else None,
                'index': i
            })
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': float(trend_strength),
            'slope': float(slope),
            'method': method,
            'turning_points': turning_points,
            'trend_data': trend_data,
            'data_points': len(data),
            'date_range': {
                'start': dates.min().isoformat() if hasattr(dates.min(), 'isoformat') else str(dates.min()),
                'end': dates.max().isoformat() if hasattr(dates.max(), 'isoformat') else str(dates.max())
            }
        }
    
    def _calculate_slope(self, values: pd.Series) -> float:
        """计算数值序列的斜率"""
        if len(values) < 2:
            return 0
        
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope
    
    def _detect_turning_points(self, values: pd.Series, dates: pd.Series) -> List[Dict[str, Any]]:
        """检测趋势拐点"""
        if len(values) < 3:
            return []
        
        turning_points = []
        
        # 计算一阶和二阶差分
        diff1 = values.diff()
        diff2 = diff1.diff()
        
        # 寻找二阶差分的符号变化点
        for i in range(2, len(values) - 1):
            if abs(diff2.iloc[i]) > diff2.std():  # 显著变化
                turning_points.append({
                    'date': dates.iloc[i].isoformat() if hasattr(dates.iloc[i], 'isoformat') else str(dates.iloc[i]),
                    'value': float(values.iloc[i]),
                    'index': i,
                    'type': 'peak' if diff2.iloc[i] < 0 else 'valley'
                })
        
        return turning_points
    
    def _format_category_results(self, category_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化分类结果为统一格式"""
        formatted_data = []
        
        for category, analysis in category_results.items():
            formatted_data.append({
                'category': category,
                'trend_direction': analysis.get('trend_direction', '未知'),
                'trend_strength': analysis.get('trend_strength', 0),
                'slope': analysis.get('slope', 0),
                'data_points': analysis.get('data_points', 0)
            })
        
        return formatted_data
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成分析洞察"""
        insights = []
        
        if 'by_category' in analysis:
            # 分类分析洞察
            category_results = analysis['by_category']
            
            # 统计各趋势方向的数量
            trend_counts = {}
            for cat_analysis in category_results.values():
                direction = cat_analysis.get('trend_direction', '未知')
                trend_counts[direction] = trend_counts.get(direction, 0) + 1
            
            if trend_counts:
                dominant_trend = max(trend_counts, key=trend_counts.get)
                insights.append(f"大多数类别呈现{dominant_trend}趋势（{trend_counts[dominant_trend]}个类别）")
            
            # 找出趋势最强的类别
            strongest_category = None
            max_strength = 0
            for category, cat_analysis in category_results.items():
                strength = cat_analysis.get('trend_strength', 0)
                if strength > max_strength:
                    max_strength = strength
                    strongest_category = category
            
            if strongest_category:
                insights.append(f"'{strongest_category}'类别的趋势最为明显（强度: {max_strength:.2f}）")
        
        else:
            # 整体分析洞察
            trend_strength = analysis.get('trend_strength', 0)
            trend_direction = analysis.get('trend_direction', '未知')
            
            if trend_strength > 0.8:
                insights.append(f"数据呈现非常明显的{trend_direction}趋势")
            elif trend_strength > 0.5:
                insights.append(f"数据呈现较为明显的{trend_direction}趋势")
            elif trend_strength < 0.2:
                insights.append("数据趋势不明显，可能存在较大波动")
            
            turning_points = analysis.get('turning_points', [])
            if len(turning_points) > 3:
                insights.append(f"检测到{len(turning_points)}个拐点，数据波动较大")
        
        return insights