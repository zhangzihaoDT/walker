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
    optional_fields = []  # 所有字段都是可选的
    
    def __init__(self):
        """初始化模块"""
        super().__init__()
        self.analyzer = None
    
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
        
        # 如果是文件路径
        if isinstance(data_source, str) and ('/' in data_source or '\\' in data_source or data_source.endswith(('.csv', '.parquet', '.duckdb', '.db'))):
            file_path = Path(data_source)
            if not file_path.is_absolute():
                # 相对路径，从项目根目录开始
                project_root = Path(__file__).parent.parent
                file_path = project_root / data_source
            
            if not file_path.exists():
                raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
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
            'insights': []
        }
        
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
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成分析结果的文字解读
        
        Args:
            results: 分析结果字典
                
        Returns:
            str: 文字解读
        """
        analysis = results.get('analysis', {})
        insights = results.get('insights', [])
        
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
        else:
            # 单表分析总结
            if 'error' in analysis:
                return f"数据分析失败: {analysis['error']}"
            
            summary_parts = [
                f"数据集 {analysis['数据集名称']} 包含 {analysis['行数']} 行和 {analysis['列数']} 列。",
                f"内存使用: {analysis['内存使用']}。"
            ]
            
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