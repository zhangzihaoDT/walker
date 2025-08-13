"""参数细分模块

用于将数据按照指定维度进行切片分组，为后续分析模块提供细分后的数据。
这是Walker策略流程中的重要组件，负责数据的预处理和维度切分。
"""

from typing import Dict, Any, List
import pandas as pd
from .base_module import BaseAnalysisModule


class ParameterSegmenterModule(BaseAnalysisModule):
    """参数细分模块
    
    将原始数据按照指定的维度字段进行分组切片，
    输出结构化的分组数据供后续分析模块使用。
    """
    
    # 模块基本信息
    module_id = "param_segmenter"
    module_name = "参数细分器"
    description = "按指定维度对数据进行分组切片，为后续分析提供细分数据"
    
    # 数据库感知能力
    supported_databases = ['duckdb', 'sqlite', 'csv', 'excel']
    required_fields = []  # 不强制要求特定字段，根据参数动态确定
    optional_fields = []
    
    def __init__(self):
        super().__init__()
    
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """准备数据
        
        Args:
            db_connector: 数据库连接器
            params: 参数字典
                - segment_fields: List[str] 分组字段列表
                - filter_conditions: Dict 过滤条件（可选）
                - table_name: str 表名
                
        Returns:
            pd.DataFrame: 原始数据
        """
        segment_fields = params.get('segment_fields', [])
        filter_conditions = params.get('filter_conditions', {})
        table_name = params.get('table_name', 'data')
        
        if not segment_fields:
            raise ValueError("必须指定至少一个分组字段 segment_fields")
        
        # 构建查询
        if hasattr(db_connector, 'execute'):
            # 数据库连接器
            query = f"SELECT * FROM {table_name}"
            
            # 添加过滤条件
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    if isinstance(value, str):
                        conditions.append(f"{field} = '{value}'")
                    else:
                        conditions.append(f"{field} = {value}")
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            result = db_connector.execute(query)
            if hasattr(result, 'df'):
                data = result.df()
            else:
                data = pd.DataFrame(result.fetchall())
        else:
            # 假设是DataFrame
            data = db_connector
            
            # 应用过滤条件
            if filter_conditions:
                for field, value in filter_conditions.items():
                    if field in data.columns:
                        data = data[data[field] == value]
        
        # 验证分组字段是否存在
        missing_fields = [field for field in segment_fields if field not in data.columns]
        if missing_fields:
            raise ValueError(f"数据中缺少分组字段: {missing_fields}")
        
        return data
    
    def run(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行参数细分
        
        Args:
            data: 原始数据
            params: 参数字典
                - segment_fields: List[str] 分组字段列表
                - aggregation_method: str 聚合方法 ('count', 'sum', 'mean', 'none')
                - value_fields: List[str] 需要聚合的数值字段（当aggregation_method不为'none'时）
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        segment_fields = params.get('segment_fields', [])
        aggregation_method = params.get('aggregation_method', 'none')
        value_fields = params.get('value_fields', [])
        
        # 按分组字段进行分组
        grouped = data.groupby(segment_fields)
        
        segments = {}
        segment_stats = []
        
        if aggregation_method == 'none':
            # 不聚合，返回原始分组数据
            for group_key, group_data in grouped:
                if isinstance(group_key, tuple):
                    key_str = "_".join(str(k) for k in group_key)
                else:
                    key_str = str(group_key)
                
                segments[key_str] = {
                    'group_key': group_key,
                    'data': group_data,
                    'count': len(group_data)
                }
                
                segment_stats.append({
                    'segment': key_str,
                    'group_values': dict(zip(segment_fields, group_key if isinstance(group_key, tuple) else [group_key])),
                    'count': len(group_data)
                })
        else:
            # 进行聚合
            if not value_fields:
                # 如果没有指定数值字段，使用所有数值列
                value_fields = data.select_dtypes(include=['number']).columns.tolist()
            
            for group_key, group_data in grouped:
                if isinstance(group_key, tuple):
                    key_str = "_".join(str(k) for k in group_key)
                else:
                    key_str = str(group_key)
                
                # 计算聚合值
                agg_results = {}
                for field in value_fields:
                    if field in group_data.columns:
                        if aggregation_method == 'sum':
                            agg_results[field] = group_data[field].sum()
                        elif aggregation_method == 'mean':
                            agg_results[field] = group_data[field].mean()
                        elif aggregation_method == 'count':
                            agg_results[field] = group_data[field].count()
                
                segments[key_str] = {
                    'group_key': group_key,
                    'aggregated_data': agg_results,
                    'count': len(group_data)
                }
                
                segment_stats.append({
                    'segment': key_str,
                    'group_values': dict(zip(segment_fields, group_key if isinstance(group_key, tuple) else [group_key])),
                    'count': len(group_data),
                    'aggregated_values': agg_results
                })
        
        return {
            'data': segment_stats,
            'segments': segments,
            'analysis': {
                'total_segments': len(segments),
                'segment_fields': segment_fields,
                'aggregation_method': aggregation_method,
                'total_records': len(data)
            },
            'visualization': {
                'type': 'segmentation',
                'chart_type': 'bar',
                'x_field': segment_fields[0] if segment_fields else None,
                'y_field': 'count'
            },
            'insights': self._generate_insights(segments, segment_fields)
        }
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成分析结果的文字解读
        
        Args:
            results: 分析结果字典
                
        Returns:
            str: 文字解读
        """
        analysis = results.get('analysis', {})
        segments = results.get('segments', {})
        
        total_segments = analysis.get('total_segments', 0)
        segment_fields = analysis.get('segment_fields', [])
        total_records = analysis.get('total_records', 0)
        
        summary = f"数据细分分析完成。\n\n"
        summary += f"按照 {', '.join(segment_fields)} 字段进行分组，"
        summary += f"共生成 {total_segments} 个数据段，覆盖 {total_records} 条记录。\n\n"
        
        # 显示前几个最大的分组
        if segments:
            sorted_segments = sorted(segments.items(), key=lambda x: x[1]['count'], reverse=True)
            summary += "主要数据段：\n"
            for i, (segment_name, segment_info) in enumerate(sorted_segments[:5]):
                count = segment_info['count']
                percentage = (count / total_records) * 100 if total_records > 0 else 0
                summary += f"- {segment_name}: {count} 条记录 ({percentage:.1f}%)\n"
        
        return summary
    
    def get_requirements(self) -> Dict[str, Any]:
        """声明所需数据字段和参数
        
        Returns:
            Dict[str, Any]: 需求声明
        """
        return {
            "data_fields": [],  # 动态根据segment_fields确定
            "optional_fields": [],
            "parameters": [
                {
                    "name": "segment_fields",
                    "type": "list",
                    "required": True,
                    "description": "用于分组的字段列表",
                    "example": ["category", "region"]
                },
                {
                    "name": "aggregation_method",
                    "type": "string",
                    "required": False,
                    "description": "聚合方法",
                    "valid_values": ["none", "count", "sum", "mean"],
                    "default_value": "none"
                },
                {
                    "name": "value_fields",
                    "type": "list",
                    "required": False,
                    "description": "需要聚合的数值字段列表",
                    "example": ["sales", "quantity"]
                },
                {
                    "name": "filter_conditions",
                    "type": "dict",
                    "required": False,
                    "description": "数据过滤条件",
                    "example": {"status": "active"}
                }
            ],
            "databases": self.supported_databases,
            "module_type": "segmenter"
        }
    
    def _generate_insights(self, segments: Dict[str, Any], segment_fields: List[str]) -> List[str]:
        """生成分析洞察
        
        Args:
            segments: 分组结果
            segment_fields: 分组字段
            
        Returns:
            List[str]: 洞察列表
        """
        insights = []
        
        if not segments:
            return insights
        
        # 计算分组大小分布
        counts = [seg['count'] for seg in segments.values()]
        if counts:
            max_count = max(counts)
            min_count = min(counts)
            avg_count = sum(counts) / len(counts)
            
            insights.append(f"数据分布不均：最大分组有 {max_count} 条记录，最小分组有 {min_count} 条记录")
            
            if max_count > avg_count * 2:
                insights.append("存在明显的数据倾斜，某些分组的数据量显著高于平均水平")
            
            if len(segments) > 10:
                insights.append(f"分组数量较多（{len(segments)}个），建议考虑进一步合并相似分组")
        
        return insights