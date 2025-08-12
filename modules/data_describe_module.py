#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据描述分析模块

基于BaseAnalysisModule实现的数据描述性统计分析模块
支持CSV、Parquet、DuckDB等多种数据格式
"""

import os
import pandas as pd
import duckdb
from pathlib import Path
from typing import Dict, Any, List
import warnings
from .base_module import BaseAnalysisModule
from .run_data_describe import DataAnalyzer

warnings.filterwarnings('ignore')


class DataDescribeModule(BaseAnalysisModule):
    """数据描述分析模块
    
    继承BaseAnalysisModule，提供数据描述性统计分析功能
    """
    
    # 模块基本信息
    module_id = "data_describe"
    module_name = "数据描述分析模块"
    description = "对数据进行基本的描述性统计分析，包括数据形状、类型、缺失值、统计摘要等"
    
    # 数据库感知能力
    supported_databases = ["csv", "parquet", "duckdb", "sqlite"]
    required_fields = []  # 不要求特定字段，可以分析任何数据
    optional_fields = []  # 所有字段都是可选的，会动态检测
    
    def __init__(self):
        """初始化模块"""
        super().__init__()
        self.analyzer = None
        self._detected_fields = []  # 动态检测到的字段
    
    def check_database_compatibility(self, database_type: str, available_fields: List[str]) -> Dict[str, Any]:
        """检查与指定数据库的兼容性
        
        重写基类方法，支持动态字段检测
        
        Args:
            database_type: 数据库类型
            available_fields: 数据库中可用的字段列表
            
        Returns:
            Dict[str, Any]: 兼容性检查结果
        """
        # 检查数据库类型支持
        if self.supported_databases and database_type not in self.supported_databases:
            return {
                "compatible": False,
                "missing_fields": [],
                "available_fields": available_fields,
                "score": 0.0,
                "reason": f"不支持数据库类型: {database_type}"
            }
        
        # 数据描述模块不要求特定字段，任何字段都可以分析
        # 动态更新检测到的字段
        self._detected_fields = available_fields
        
        # 计算兼容性评分
        # 基于可用字段数量给分
        if available_fields:
            # 有字段就兼容，字段越多分数越高
            base_score = 0.8  # 基础分
            field_bonus = min(0.2, len(available_fields) * 0.01)  # 字段数量奖励
            score = base_score + field_bonus
        else:
            score = 0.5  # 即使没有字段信息也可以尝试分析
        
        return {
            "compatible": True,
            "missing_fields": [],
            "available_fields": available_fields,
            "detected_fields": self._detected_fields,
            "score": min(score, 1.0),
            "reason": f"可分析 {len(available_fields)} 个字段的数据"
        }
    
    def get_detected_fields(self) -> List[str]:
        """获取动态检测到的字段列表
        
        Returns:
            List[str]: 检测到的字段列表
        """
        return self._detected_fields.copy()
    
    def get_module_info(self) -> Dict[str, Any]:
        """获取模块信息
        
        重写基类方法，包含动态检测的字段信息
        
        Returns:
            Dict[str, Any]: 模块信息
        """
        base_info = super().get_module_info()
        
        # 添加动态字段信息
        base_info.update({
            "detected_fields": self._detected_fields,
            "field_detection": "dynamic",
            "supports_any_fields": True,
            "field_analysis_capabilities": {
                "field_types": ["numeric", "text", "datetime"],
                "field_statistics": ["count", "null_count", "unique_count", "data_type"],
                "missing_value_analysis": True,
                "data_type_detection": True
            }
        })
        
        return base_info
    
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """根据数据库连接器和参数准备数据
        
        Args:
            db_connector: 数据库连接器对象
            params: 分析参数字典
                - data_source: 数据源路径或表名
                
        Returns:
            Any: 准备好的数据对象（DataFrame或字典）
        """
        data_source = params.get('data_source')
        if not data_source:
            raise ValueError("缺少必需参数: data_source")
        
        # 如果是文件路径或目录路径
        if isinstance(data_source, str):
            file_path = Path(data_source)
            if not file_path.is_absolute():
                # 相对路径，从项目根目录开始
                project_root = Path(__file__).parent.parent
                file_path = project_root / data_source
            
            if not file_path.exists():
                raise FileNotFoundError(f"数据源不存在: {file_path}")
            
            # 如果是目录，分析目录中的所有数据文件
            if file_path.is_dir():
                self.analyzer = DataAnalyzer(str(file_path))
                data_files = self.analyzer.get_data_files()
                if not data_files:
                    raise ValueError(f"目录中没有找到支持的数据文件: {file_path}")
                
                # 读取所有数据文件
                all_data = {}
                for data_file in data_files:
                    if data_file.suffix.lower() == '.csv':
                        df = self.analyzer.read_csv_file(data_file)
                        if df is not None:
                            all_data[data_file.name] = df
                    elif data_file.suffix.lower() == '.parquet':
                        df = self.analyzer.read_parquet_file(data_file)
                        if df is not None:
                            all_data[data_file.name] = df
                    elif data_file.suffix.lower() in ['.duckdb', '.db']:
                        tables_data = self.analyzer.read_duckdb_file(data_file)
                        for table_name, df in tables_data.items():
                            all_data[f"{data_file.name}.{table_name}"] = df
                
                if not all_data:
                    raise ValueError(f"无法读取目录中的任何数据文件: {file_path}")
                
                return {'type': 'tables', 'data': all_data, 'name': file_path.name}
            
            # 如果是文件，按原逻辑处理
            elif file_path.is_file():
                # 根据文件类型读取数据
                if file_path.suffix.lower() == '.csv':
                    self.analyzer = DataAnalyzer()
                    df = self.analyzer.read_csv_file(file_path)
                    if df is None:
                        raise ValueError(f"无法读取CSV文件: {file_path}")
                    return {'type': 'dataframe', 'data': df, 'name': file_path.name}
                
                elif file_path.suffix.lower() == '.parquet':
                    self.analyzer = DataAnalyzer()
                    df = self.analyzer.read_parquet_file(file_path)
                    if df is None:
                        raise ValueError(f"无法读取Parquet文件: {file_path}")
                    return {'type': 'dataframe', 'data': df, 'name': file_path.name}
                
                elif file_path.suffix.lower() in ['.duckdb', '.db']:
                    self.analyzer = DataAnalyzer()
                    tables_data = self.analyzer.read_duckdb_file(file_path)
                    if not tables_data:
                        raise ValueError(f"无法读取DuckDB文件或文件为空: {file_path}")
                    return {'type': 'tables', 'data': tables_data, 'name': file_path.name}
                
                else:
                    raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            else:
                raise ValueError(f"数据源既不是文件也不是目录: {file_path}")
        
        # 如果是数据库表名且有连接器
        elif db_connector:
            try:
                # 尝试从数据库读取表
                if hasattr(db_connector, 'execute'):
                    df = db_connector.execute(f"SELECT * FROM {data_source}").df()
                elif hasattr(db_connector, 'query'):
                    df = db_connector.query(f"SELECT * FROM {data_source}")
                else:
                    raise ValueError("不支持的数据库连接器类型")
                
                return {'type': 'dataframe', 'data': df, 'name': data_source}
            except Exception as e:
                raise ValueError(f"无法从数据库读取表 {data_source}: {str(e)}")
        
        else:
            raise ValueError("无效的数据源或缺少数据库连接器")
    
    def run(self, data: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析逻辑
        
        Args:
            data: 准备好的数据
            params: 分析参数字典
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not self.analyzer:
            self.analyzer = DataAnalyzer()
        
        results = {
            'data': [],
            'analysis': {},
            'visualization': {},
            'insights': [],
            'field_info': {},
            'available_fields': []
        }
        
        # 获取字段信息
        field_info = self.get_field_info(data)
        available_fields = self.get_available_fields(data)
        results['field_info'] = field_info
        results['available_fields'] = available_fields
        
        if data['type'] == 'dataframe':
            # 单个DataFrame分析
            df = data['data']
            name = data['name']
            description = self.analyzer.describe_dataframe(df, name)
            
            results['data'] = [description]
            results['analysis'] = description
            
            # 生成洞察
            insights = self._generate_insights(description)
            results['insights'] = insights
            
            # 生成可视化配置
            if params.get('include_visualization', True):
                viz_config = self._generate_visualization_config(df, description)
                results['visualization'] = viz_config
        
        elif data['type'] == 'tables':
            # 多个表分析
            tables_data = data['data']
            all_descriptions = []
            
            for table_name, df in tables_data.items():
                description = self.analyzer.describe_dataframe(df, f"{data['name']}.{table_name}")
                all_descriptions.append(description)
            
            results['data'] = all_descriptions
            results['analysis'] = {
                'total_tables': len(all_descriptions),
                'tables': all_descriptions
            }
            
            # 生成综合洞察
            insights = self._generate_multi_table_insights(all_descriptions)
            results['insights'] = insights
        
        return results
    
    def get_available_fields(self, data: Any) -> List[str]:
        """获取数据中可用的字段列表
        
        Args:
            data: 准备好的数据对象
            
        Returns:
            List[str]: 可用字段列表
        """
        fields = []
        
        if data['type'] == 'dataframe':
            # 单个DataFrame的字段
            df = data['data']
            fields = list(df.columns)
        elif data['type'] == 'tables':
            # 多个表的字段，合并所有唯一字段
            all_fields = set()
            for table_name, df in data['data'].items():
                all_fields.update(df.columns)
            fields = list(all_fields)
        
        return fields
    
    def get_field_info(self, data: Any) -> Dict[str, Any]:
        """获取详细的字段信息
        
        Args:
            data: 准备好的数据对象
            
        Returns:
            Dict[str, Any]: 字段信息字典
        """
        field_info = {
            'total_fields': 0,
            'field_details': {},
            'field_types': {},
            'numeric_fields': [],
            'text_fields': [],
            'datetime_fields': []
        }
        
        if data['type'] == 'dataframe':
            df = data['data']
            field_info['total_fields'] = len(df.columns)
            
            for col in df.columns:
                dtype = str(df[col].dtype)
                field_info['field_details'][col] = {
                    'type': dtype,
                    'non_null_count': df[col].count(),
                    'null_count': df[col].isnull().sum(),
                    'unique_count': df[col].nunique()
                }
                field_info['field_types'][col] = dtype
                
                # 分类字段类型
                if 'int' in dtype or 'float' in dtype:
                    field_info['numeric_fields'].append(col)
                elif 'datetime' in dtype:
                    field_info['datetime_fields'].append(col)
                else:
                    field_info['text_fields'].append(col)
        
        elif data['type'] == 'tables':
            all_fields = {}
            for table_name, df in data['data'].items():
                for col in df.columns:
                    if col not in all_fields:
                        dtype = str(df[col].dtype)
                        all_fields[col] = {
                            'type': dtype,
                            'tables': [table_name],
                            'non_null_count': df[col].count(),
                            'null_count': df[col].isnull().sum(),
                            'unique_count': df[col].nunique()
                        }
                        
                        # 分类字段类型
                        if 'int' in dtype or 'float' in dtype:
                            if col not in field_info['numeric_fields']:
                                field_info['numeric_fields'].append(col)
                        elif 'datetime' in dtype:
                            if col not in field_info['datetime_fields']:
                                field_info['datetime_fields'].append(col)
                        else:
                            if col not in field_info['text_fields']:
                                field_info['text_fields'].append(col)
                    else:
                        all_fields[col]['tables'].append(table_name)
            
            field_info['total_fields'] = len(all_fields)
            field_info['field_details'] = all_fields
            field_info['field_types'] = {k: v['type'] for k, v in all_fields.items()}
        
        return field_info
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成分析结果的文字解读
        
        Args:
            results: 分析结果字典
                
        Returns:
            str: 文字解读
        """
        analysis = results.get('analysis', {})
        insights = results.get('insights', [])
        field_info = results.get('field_info', {})
        
        if 'total_tables' in analysis:
            # 多表分析总结
            summary_parts = [
                f"数据库包含 {analysis['total_tables']} 个表。"
            ]
            
            for table_desc in analysis['tables']:
                if 'error' not in table_desc:
                    summary_parts.append(
                        f"表 {table_desc['数据集名称']}: {table_desc['行数']} 行 × {table_desc['列数']} 列，"
                        f"内存使用 {table_desc['内存使用']}。"
                    )
            
            # 添加字段信息
            if field_info:
                summary_parts.append(
                    f"共发现 {field_info.get('total_fields', 0)} 个不同字段："
                    f"{len(field_info.get('numeric_fields', []))} 个数值字段、"
                    f"{len(field_info.get('text_fields', []))} 个文本字段、"
                    f"{len(field_info.get('datetime_fields', []))} 个日期时间字段。"
                )
                
                # 列出主要字段名称
                if field_info.get('numeric_fields'):
                    numeric_sample = field_info['numeric_fields'][:5]
                    summary_parts.append(f"主要数值字段: {', '.join(numeric_sample)}{'等' if len(field_info['numeric_fields']) > 5 else ''}。")
                
                if field_info.get('text_fields'):
                    text_sample = field_info['text_fields'][:5]
                    summary_parts.append(f"主要文本字段: {', '.join(text_sample)}{'等' if len(field_info['text_fields']) > 5 else ''}。")
        else:
            # 单表分析总结
            if 'error' in analysis:
                return f"数据分析失败: {analysis['error']}"
            
            summary_parts = [
                f"数据集 {analysis['数据集名称']} 包含 {analysis['行数']} 行和 {analysis['列数']} 列。",
                f"内存使用: {analysis['内存使用']}。"
            ]
            
            # 添加字段详细信息
            if '列名' in analysis:
                column_names = analysis['列名']
                summary_parts.append(f"字段列表: {', '.join(column_names[:10])}{'等' if len(column_names) > 10 else ''}。")
            
            # 添加数据类型信息
            if '数据类型' in analysis:
                numeric_cols = sum(1 for dtype in analysis['数据类型'].values() 
                                 if 'int' in str(dtype) or 'float' in str(dtype))
                text_cols = analysis['列数'] - numeric_cols
                summary_parts.append(f"包含 {numeric_cols} 个数值列和 {text_cols} 个文本列。")
            
            # 添加缺失值信息
            if '缺失值统计' in analysis:
                total_missing = sum(analysis['缺失值统计'].values())
                if total_missing > 0:
                    missing_pct = (total_missing / (analysis['行数'] * analysis['列数'])) * 100
                    summary_parts.append(f"总缺失值: {total_missing} ({missing_pct:.1f}%)。")
                else:
                    summary_parts.append("数据完整，无缺失值。")
        
        # 添加洞察
        if insights:
            summary_parts.append("\n主要发现:")
            for insight in insights[:3]:  # 只显示前3个洞察
                summary_parts.append(f"• {insight}")
        
        return " ".join(summary_parts)
    
    def _generate_insights(self, description: Dict[str, Any]) -> List[str]:
        """生成数据洞察"""
        insights = []
        
        if 'error' in description:
            return [f"数据处理错误: {description['error']}"]
        
        # 数据规模洞察
        rows, cols = description['数据形状']
        if rows > 100000:
            insights.append(f"大型数据集，包含 {rows:,} 行数据")
        elif rows < 100:
            insights.append(f"小型数据集，仅包含 {rows} 行数据")
        
        # 缺失值洞察
        if '缺失值统计' in description:
            missing_stats = description['缺失值统计']
            total_missing = sum(missing_stats.values())
            if total_missing > 0:
                missing_cols = [col for col, count in missing_stats.items() if count > 0]
                if len(missing_cols) > cols * 0.5:
                    insights.append(f"数据质量问题：超过一半的列({len(missing_cols)}/{cols})存在缺失值")
                elif total_missing > rows * cols * 0.1:
                    insights.append(f"缺失值较多：总缺失率达到 {(total_missing/(rows*cols)*100):.1f}%")
        
        # 数据类型洞察
        if '数据类型' in description:
            dtypes = description['数据类型']
            numeric_count = sum(1 for dtype in dtypes.values() if 'int' in str(dtype) or 'float' in str(dtype))
            if numeric_count == 0:
                insights.append("纯文本数据集，不包含数值列")
            elif numeric_count == len(dtypes):
                insights.append("纯数值数据集，适合统计分析")
        
        return insights
    
    def _generate_multi_table_insights(self, descriptions: List[Dict[str, Any]]) -> List[str]:
        """生成多表洞察"""
        insights = []
        
        total_rows = sum(desc.get('行数', 0) for desc in descriptions if 'error' not in desc)
        total_cols = sum(desc.get('列数', 0) for desc in descriptions if 'error' not in desc)
        
        insights.append(f"数据库总计包含 {total_rows:,} 行数据，分布在 {len(descriptions)} 个表中")
        
        # 找出最大的表
        largest_table = max(descriptions, key=lambda x: x.get('行数', 0) if 'error' not in x else 0)
        if 'error' not in largest_table:
            insights.append(f"最大表 {largest_table['数据集名称']} 包含 {largest_table['行数']:,} 行")
        
        return insights
    
    def _generate_visualization_config(self, df: pd.DataFrame, description: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化配置"""
        viz_config = {
            'charts': [],
            'recommended_plots': []
        }
        
        # 数值列的分布图
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            viz_config['charts'].append({
                'type': 'histogram',
                'title': '数值列分布',
                'columns': numeric_cols[:5],  # 最多5列
                'description': '显示数值列的分布情况'
            })
            
            if len(numeric_cols) >= 2:
                viz_config['charts'].append({
                    'type': 'correlation_matrix',
                    'title': '相关性矩阵',
                    'columns': numeric_cols,
                    'description': '显示数值列之间的相关性'
                })
        
        # 文本列的频次图
        text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        categorical_cols = [col for col in text_cols if df[col].nunique() <= 20]  # 类别数少于20的列
        
        if categorical_cols:
            viz_config['charts'].append({
                'type': 'bar_chart',
                'title': '类别分布',
                'columns': categorical_cols[:3],  # 最多3列
                'description': '显示类别变量的分布'
            })
        
        # 缺失值热力图
        if description.get('缺失值统计') and sum(description['缺失值统计'].values()) > 0:
            viz_config['charts'].append({
                'type': 'missing_heatmap',
                'title': '缺失值分布',
                'description': '显示各列的缺失值模式'
            })
        
        return viz_config