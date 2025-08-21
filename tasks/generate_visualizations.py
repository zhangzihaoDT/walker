#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化生成脚本
生成analyze_business_metrics.py和analyze_intention_data.py各个模块的可视化
使用Plotly组件确保中文友好，前端使用Gradio选项卡布局
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import gradio as gr
from pathlib import Path
import sys
import numpy as np
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入分析模块
from tasks.analyze_business_metrics import (
    analyze_presale_post_launch_comparison
)
from datetime import datetime, timedelta

def load_business_data():
    """加载业务指标数据"""
    try:
        # 尝试多个可能的数据文件路径
        possible_paths = [
            project_root / "data" / "业务指标数据.parquet",
            project_root / "data" / "business_daily_metrics.parquet",  # 从analyze_business_metrics.py中找到的路径
            "/Users/zihao_/Documents/github/W33_utils_3/data/business_daily_metrics.parquet"
        ]
        
        print("\n=== 业务数据加载调试信息 ===")
        print(f"项目根目录: {project_root}")
        print(f"data目录存在: {(project_root / 'data').exists()}")
        
        for i, data_path in enumerate(possible_paths, 1):
            print(f"尝试路径 {i}: {data_path}")
            print(f"  文件存在: {Path(data_path).exists()}")
            
            if Path(data_path).exists():
                print(f"  ✓ 找到数据文件，开始加载...")
                # 直接使用pandas读取数据，而不是调用analyze_parquet_file
                df = pd.read_parquet(str(data_path))
                print(f"  ✓ 数据加载成功，形状: {df.shape}")
                return df
        
        print("  ✗ 所有路径都不存在数据文件")
        return None
        
    except Exception as e:
        print(f"加载业务指标数据失败: {e}")
        return None

def load_intention_data():
    """加载意向数据"""
    try:
        # 尝试多个可能的数据文件路径
        possible_paths = [
            project_root / "data" / "意向数据.xlsx",
            project_root / "data" / "intention_order_analysis.parquet",  # 从analyze_intention_data.py中找到的路径
            "/Users/zihao_/Documents/github/W33_utils_3/data/intention_order_analysis.parquet"
        ]
        
        print("\n=== 意向数据加载调试信息 ===")
        
        for i, data_path in enumerate(possible_paths, 1):
            print(f"尝试路径 {i}: {data_path}")
            print(f"  文件存在: {Path(data_path).exists()}")
            
            if Path(data_path).exists():
                print(f"  ✓ 找到数据文件，开始加载...")
                # 根据文件扩展名选择读取方式
                if str(data_path).endswith('.xlsx'):
                    df = pd.read_excel(str(data_path))
                else:
                    df = pd.read_parquet(str(data_path))
                print(f"  ✓ 数据加载成功，形状: {df.shape}")
                return df
        
        print("  ✗ 所有路径都不存在数据文件")
        return None
        
    except Exception as e:
        print(f"加载意向数据失败: {e}")
        return None

def analyze_post_launch_changes_for_viz(df, days_after_launch=3):
    """
    分析发布会后N日指标相对于前30日平均值的变化幅度（用于可视化）
    
    Args:
        df (pd.DataFrame): 业务指标数据
        days_after_launch (int): 发布会后分析的天数
    
    Returns:
        dict: 包含各发布会变化幅度数据的字典
    """
    # 定义发布会时间节点 - 只分析预售类发布会
    launch_events = {
        '2023-08-25': {'event': 'CM0预售', 'type': '预售'},
        '2024-04-08': {'event': 'DM0预售', 'type': '预售'},
        '2024-08-30': {'event': 'CM1预售', 'type': '预售'},
        '2025-04-18': {'event': 'DM1预售', 'type': '预售'},
        '2025-08-15': {'event': 'CM2预售', 'type': '预售'}
    }
    
    # 需要分析的指标
    metrics = [
        '小订数',
        '有效线索数', '抖音战队线索数', '下发线索数', '有效试驾数', '抖音线索占比',
        '本品牌人群总资产资产', '本品牌日新增', '本品牌日流失', '本品牌净增', '人群资产_相对30日最小值差值',
    ]
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    results = {}
    
    for date_str, event_info in launch_events.items():
        event_date = pd.to_datetime(date_str)
        
        # 前30日数据（用于计算基准平均值）
        pre_start_date = event_date - timedelta(days=30)
        pre_period_data = df[(df['date'] >= pre_start_date) & (df['date'] < event_date)]
        
        # 后N日数据
        post_end_date = event_date + timedelta(days=days_after_launch)
        post_period_data = df[(df['date'] >= event_date) & (df['date'] <= post_end_date)]
        
        if len(pre_period_data) == 0 or len(post_period_data) == 0:
            continue
            
        event_result = {
            'event': event_info['event'],
            'date': date_str,
            'type': event_info['type'],
            'metrics': {}
        }
        
        # 计算每个指标的变化幅度
        for metric in metrics:
            if metric in df.columns:
                pre_metric_data = pre_period_data[metric].dropna()
                post_metric_data = post_period_data[metric].dropna()
                
                if len(pre_metric_data) > 0 and len(post_metric_data) > 0:
                    pre_mean = pre_metric_data.mean()
                    post_mean = post_metric_data.mean()
                    
                    # 计算变化幅度（百分比）
                    if pre_mean != 0:
                        change_rate = ((post_mean - pre_mean) / pre_mean) * 100
                        change_abs = post_mean - pre_mean
                        
                        event_result['metrics'][metric] = {
                            'pre_mean': pre_mean,
                            'post_mean': post_mean,
                            'change_rate': change_rate,
                            'change_abs': change_abs
                        }
                    else:
                        event_result['metrics'][metric] = {
                            'pre_mean': 0,
                            'post_mean': post_mean,
                            'change_rate': None,
                            'change_abs': None
                        }
                else:
                    event_result['metrics'][metric] = {
                        'pre_mean': None,
                        'post_mean': None,
                        'change_rate': None,
                        'change_abs': None
                    }
        
        results[event_info['event']] = event_result
    
    return results

def create_module1_tables(days_after_launch=3):
    """
    创建Module 1的表格部分 - 发布会后指标变化幅度分析
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        plotly.graph_objects.Figure: 包含变化幅度对比表格的图表
    """
    df = load_business_data()
    if df is None:
        # 返回详细错误信息的图表
        fig = go.Figure()
        
        # 检查数据文件路径状态
        data_dir = Path("/Users/zihao_/Documents/github/W33_utils_3/data")
        error_text = "数据加载失败！\n\n"
        error_text += f"数据目录存在: {data_dir.exists()}\n"
        
        if data_dir.exists():
            files = list(data_dir.glob("*.parquet")) + list(data_dir.glob("*.xlsx"))
            error_text += f"数据目录中的文件: {len(files)}个\n"
            for file in files[:5]:  # 只显示前5个文件
                error_text += f"  - {file.name}\n"
        else:
            error_text += "数据目录不存在\n"
        
        error_text += "\n请检查.gitignore文件，数据文件可能被忽略"
        
        fig.add_annotation(
            text=error_text,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red"),
            align="left"
        )
        period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
        fig.update_layout(
            title=f"Module 1: 发布会{period_text}指标变化幅度分析 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=250
        )
        return fig
    
    # 获取Module 1的分析结果
    change_data = analyze_post_launch_changes_for_viz(df, days_after_launch)
    
    if not change_data:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="无法获取变化幅度分析数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
        fig.update_layout(
            title=f"Module 1: 发布会{period_text}指标变化幅度分析",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 使用核心指标
    core_metrics = [
        '有效线索数', '抖音战队线索数', '下发线索数', '抖音线索占比',
        '本品牌人群总资产资产', '本品牌日流失', '本品牌净增', '人群资产_相对30日最小值差值','有效试驾数',
    ]
    
    # 准备数据用于表格显示
    events = list(change_data.keys())
    
    # 只创建一个变化幅度表格
    period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日"
    table_data = []
    
    # 构建表格数据
    for metric in core_metrics:
        row_data = {'指标': metric}
        
        for event in events:
            if (event in change_data and 
                'metrics' in change_data[event] and 
                metric in change_data[event]['metrics'] and 
                change_data[event]['metrics'][metric]['change_rate'] is not None):
                
                value = change_data[event]['metrics'][metric]['change_rate']
                row_data[event] = f"{round(value, 2)}%" if isinstance(value, (int, float)) else 'N/A'
            else:
                row_data[event] = 'N/A'
        
        table_data.append(row_data)
    
    # 创建单个表格
    fig = go.Figure()
    
    if table_data:
        # 准备表格的列和数据
        columns = ['指标'] + events
        
        # 创建表格数据矩阵
        table_values = []
        for col_name in columns:
            col_values = []
            for row_data in table_data:
                col_values.append(str(row_data.get(col_name, 'N/A')))
            table_values.append(col_values)
        
        # 计算每行的最大值位置用于高亮
        fill_colors = []
        for col_idx, col_name in enumerate(columns):
            if col_name == '指标':
                fill_colors.append(['lightgray'] * len(table_data))
            else:
                col_colors = []
                for row_idx in range(len(table_data)):
                    # 找到该行数值列的最大增幅（正值最大）
                    max_col_idx = -1
                    max_value = float('-inf')
                    
                    for check_col_idx, check_col_name in enumerate(columns[1:], 1):  # 跳过'指标'列
                        try:
                            val_str = table_data[row_idx].get(check_col_name, '0%')
                            if val_str != 'N/A':
                                val = float(val_str.replace('%', ''))
                                # 只考虑正值增幅，找最大的正增长
                                if val > max_value:
                                    max_value = val
                                    max_col_idx = check_col_idx
                        except (ValueError, TypeError):
                            continue
                    
                    # 如果当前列是最大增幅列且增幅为正值，则高亮
                    if col_idx == max_col_idx and max_value > 0:
                        col_colors.append('lightgreen')  # 使用绿色表示正增长
                    else:
                        col_colors.append('white')
                
                fill_colors.append(col_colors)
        
        # 添加表格
        fig.add_trace(
            go.Table(
                header=dict(
                    values=columns,
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=table_values,
                    fill_color=fill_colors,
                    align='center',
                    font=dict(size=11, color='black')
                )
            )
        )
    
    # 更新布局
    period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
    
    fig.update_layout(
        title=dict(
            text=f"Module 1: 发布会{period_text}指标变化幅度分析 (%)",
            x=0.5,
            font=dict(size=16)
        ),
        height=400,  # 调整高度，只包含一个表格
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def create_module1_insights(days_after_launch=3):
    """
    创建Module 1的解释结论文本
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        str: 解释结论的文本内容
    """
    df = load_business_data()
    if df is None or df.empty:
        return "数据加载失败，无法生成解释结论。"
    
    try:
        # 调用分析函数
        change_data = analyze_post_launch_changes_for_viz(
            df, days_after_launch=days_after_launch
        )
        
        if not change_data:
            return "分析数据不足，无法生成解释结论。"
        
        # 定义核心指标
        core_metrics = [
            '有效线索数', '下发线索数', 
            '本品牌人群总资产资产', '本品牌日新增', 
        ]
        
        # 生成解释结论文本
        insights_text = generate_module1_insights(change_data, core_metrics, days_after_launch)
        return insights_text
        
    except Exception as e:
        return f"生成解释结论时发生错误: {str(e)}"

def generate_module1_insights(change_data, core_metrics, days_after_launch=3):
    """
    生成Module 1的解释结论文本
    
    Args:
        change_data: 变化幅度分析数据
        core_metrics: 核心指标列表
        days_after_launch: 发布会后分析的天数
    """
    insights = []
    
    # 检查CM2是否存在于数据中
    if 'CM2预售' in change_data:
        cm2_data = change_data['CM2预售']
        other_presale_events = ['CM0预售', 'CM1预售', 'DM0预售', 'DM1预售']
        
        # 分析CM2的整体表现
        cm2_advantages = []
        cm2_disadvantages = []
        
        # 动态生成标题
        period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日"
        insights.append(f"CM2预售与其他预售发布会指标变化幅度对比分析（基于发布会后{period_text}）:")
        insights.append("")
        
        for metric in core_metrics:
            if metric in cm2_data['metrics'] and cm2_data['metrics'][metric]['change_rate'] is not None:
                cm2_change_rate = cm2_data['metrics'][metric]['change_rate']
                
                # 计算CM2相对于其他预售发布会的平均表现
                other_change_rates = []
                for other_event in other_presale_events:
                    if other_event in change_data:
                        other_data = change_data[other_event]
                        if metric in other_data['metrics'] and other_data['metrics'][metric]['change_rate'] is not None:
                            other_change_rates.append(other_data['metrics'][metric]['change_rate'])
                
                if other_change_rates:
                    avg_other_change = sum(other_change_rates) / len(other_change_rates)
                    diff_to_avg = cm2_change_rate - avg_other_change
                    
                    if abs(diff_to_avg) > 10:  # 变化幅度差异超过10%
                        if diff_to_avg > 0:
                            cm2_advantages.append((metric, cm2_change_rate, avg_other_change, diff_to_avg))
                        else:
                            cm2_disadvantages.append((metric, cm2_change_rate, avg_other_change, diff_to_avg))
        
        # 输出优势分析
        if cm2_advantages:
            insights.append("1. CM2预售相对优势指标:")
            for metric, cm2_rate, avg_rate, diff in sorted(cm2_advantages, key=lambda x: x[3], reverse=True):
                insights.append(f"   • {metric}: CM2变化幅度{cm2_rate:.1f}%，其他预售平均{avg_rate:.1f}%，高出{diff:.1f}个百分点")
            insights.append("")
        
        # 输出劣势分析
        if cm2_disadvantages:
            insights.append("2. CM2预售相对劣势指标:")
            for metric, cm2_rate, avg_rate, diff in sorted(cm2_disadvantages, key=lambda x: x[3]):
                insights.append(f"   • {metric}: CM2变化幅度{cm2_rate:.1f}%，其他预售平均{avg_rate:.1f}%，低{abs(diff):.1f}个百分点")
            insights.append("")
        
        # 总体结论
        insights.append("3. 总体结论:")
        if len(cm2_advantages) > len(cm2_disadvantages):
            insights.append("   CM2预售在大多数关键指标的变化幅度上表现更优，显示出更强的市场响应能力。")
        elif len(cm2_advantages) < len(cm2_disadvantages):
            insights.append("   CM2预售在部分指标的变化幅度上仍有提升空间，需要优化发布会策略。")
        else:
            insights.append("   CM2预售整体变化幅度表现均衡，在不同指标上各有优劣。")
        
        # 添加具体数值对比
        insights.append("")
        insights.append("4. 详细数值对比:")
        for metric in core_metrics:
            if metric in cm2_data['metrics'] and cm2_data['metrics'][metric]['change_rate'] is not None:
                cm2_rate = cm2_data['metrics'][metric]['change_rate']
                insights.append(f"   • {metric}: CM2预售变化幅度为{cm2_rate:.2f}%")
    else:
        insights.append("警告: CM2预售数据不存在，无法进行对比分析")
    
    return '\n'.join(insights)

def create_module4_tables(days_after_launch=3):
    """创建Module 4的表格部分 - 预售发布会后指标对比分析
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        plotly.graph_objects.Figure: 包含两个对比表格的图表
    """
    df = load_business_data()
    if df is None:
        # 返回详细错误信息的图表
        fig = go.Figure()
        
        # 检查数据文件路径状态
        data_dir = Path("/Users/zihao_/Documents/github/W33_utils_3/data")
        error_text = "数据加载失败！\n\n"
        error_text += f"数据目录存在: {data_dir.exists()}\n"
        
        if data_dir.exists():
            files = list(data_dir.glob("*.parquet")) + list(data_dir.glob("*.xlsx"))
            error_text += f"数据目录中的文件: {len(files)}个\n"
            for file in files[:5]:  # 只显示前5个文件
                error_text += f"  - {file.name}\n"
        else:
            error_text += "数据目录不存在\n"
        
        error_text += "\n请检查.gitignore文件，数据文件可能被忽略"
        
        fig.add_annotation(
            text=error_text,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red"),
            align="left"
        )
        period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
        fig.update_layout(
            title=f"Module 4: 预售发布会{period_text}指标对比分析 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=250
        )
        return fig
    
    # 获取Module 4的分析结果
    comparison_data = analyze_presale_post_launch_comparison(df, days_after_launch)
    
    if not comparison_data:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="无法获取对比分析数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
        fig.update_layout(
            title=f"Module 4: 预售发布会{period_text}指标对比分析",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 使用与analyze_business_metrics.py保持一致的核心指标
    core_metrics = [
        '小订数',
        '有效线索数', '下发线索数', 
        '本品牌人群总资产资产', '本品牌日新增', 
    ]
    
    # 准备数据用于表格显示
    events = list(comparison_data.keys())
    
    # 创建两个表格：平均值、累计值
    period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日"
    tables_data = {
        'mean': {'title': f'{period_text}平均值对比表', 'data': []},
        'sum': {'title': f'{period_text}累计值对比表', 'data': []}
    }
    
    # 构建表格数据
    for metric in core_metrics:
        row_data = {'指标': metric}
        
        for stat_type in ['mean', 'sum']:
            for event in events:
                if (event in comparison_data and 
                    'metrics' in comparison_data[event] and 
                    metric in comparison_data[event]['metrics'] and 
                    comparison_data[event]['metrics'][metric][stat_type] is not None):
                    
                    value = comparison_data[event]['metrics'][metric][stat_type]
                    row_data[event] = round(value, 2) if isinstance(value, (int, float)) else value
                else:
                    row_data[event] = 'N/A'
            
            tables_data[stat_type]['data'].append(row_data.copy())
    
    # 创建垂直布局的子图 - 2行1列（2个表格）
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            tables_data['mean']['title'],
            tables_data['sum']['title']
        ],
        specs=[[{"type": "table"}],
               [{"type": "table"}]],
        vertical_spacing=0.12
    )
    
    # 为每个表格创建数据
    stat_types = ['mean', 'sum']
    
    for i, stat_type in enumerate(stat_types, 1):
        table_data = tables_data[stat_type]['data']
        
        if table_data:
            # 准备表格的列和数据
            columns = ['指标'] + events
            
            # 创建表格数据矩阵
            table_values = []
            for col_name in columns:
                col_values = []
                for row_data in table_data:
                    col_values.append(str(row_data.get(col_name, 'N/A')))
                table_values.append(col_values)
            
            # 计算每行的最大值位置用于高亮
            fill_colors = []
            for col_idx, col_name in enumerate(columns):
                if col_name == '指标':
                    fill_colors.append(['lightgray'] * len(table_data))
                else:
                    col_colors = []
                    for row_idx in range(len(table_data)):
                        # 找到该行数值列的最大值
                        max_col_idx = -1
                        max_value = float('-inf')
                        
                        for check_col_idx, check_col_name in enumerate(columns[1:], 1):  # 跳过'指标'列
                            try:
                                val = float(table_data[row_idx].get(check_col_name, 0))
                                if val > max_value:
                                    max_value = val
                                    max_col_idx = check_col_idx
                            except (ValueError, TypeError):
                                continue
                        
                        # 如果当前列是最大值列，则高亮
                        if col_idx == max_col_idx and max_value != float('-inf'):
                            col_colors.append('lightcoral')
                        else:
                            col_colors.append('white')
                    
                    fill_colors.append(col_colors)
            
            # 添加表格到子图
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=columns,
                        fill_color='lightblue',
                        align='center',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=table_values,
                        fill_color=fill_colors,
                        align='center',
                        font=dict(size=11, color='black')
                    )
                ),
                row=i, col=1
            )
    
    # 更新布局 - 只包含两个表格
    period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
    
    fig.update_layout(
        title=dict(
            text=f"Module 4: 预售发布会{period_text}指标对比分析 - 数据表格",
            x=0.5,
            font=dict(size=16)
        ),
        height=600,  # 固定高度，只包含两个表格
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig


def create_module4_insights(days_after_launch=3):
    """创建Module 4的解释结论文本
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        str: 解释结论的文本内容
    """
    df = load_business_data()
    if df is None or df.empty:
        return "数据加载失败，无法生成解释结论。"
    
    try:
        # 调用分析函数
        comparison_data = analyze_presale_post_launch_comparison(
            df, days_after_launch=days_after_launch
        )
        
        if not comparison_data:
            return "分析数据不足，无法生成解释结论。"
        
        # 定义核心指标
        core_metrics = [
            '小订数',
            '有效线索数', '下发线索数', 
            '本品牌人群总资产资产', '本品牌日新增', 
        ]
        
        # 生成解释结论文本
        insights_text = generate_module4_insights(comparison_data, core_metrics, days_after_launch)
        return insights_text
        
    except Exception as e:
        return f"生成解释结论时发生错误: {str(e)}"

def generate_module4_insights(comparison_data, core_metrics, days_after_launch=3):
    """生成Module 4的解释结论文本
    
    Args:
        comparison_data: 对比分析数据
        core_metrics: 核心指标列表
        days_after_launch: 发布会后分析的天数
    """
    insights = []
    
    # 检查CM2是否存在于数据中
    if 'CM2' in comparison_data:
        cm2_data = comparison_data['CM2']
        other_events = ['CM0', 'CM1', 'DM0', 'DM1']
        
        # 分析CM2的整体表现
        cm2_advantages = []
        cm2_disadvantages = []
        
        # 动态生成标题
        period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日累计值"
        insights.append(f"CM2与其他车型预售发布会指标对比分析（基于{period_text}）:")
        insights.append("")
        
        for metric in core_metrics:
            if metric in cm2_data['metrics'] and cm2_data['metrics'][metric]['sum'] is not None:
                cm2_value = cm2_data['metrics'][metric]['sum']
                
                # 计算CM2相对于其他车型的平均表现
                other_values = []
                for other_event in other_events:
                    if other_event in comparison_data:
                        other_data = comparison_data[other_event]
                        if metric in other_data['metrics'] and other_data['metrics'][metric]['sum'] is not None:
                            other_values.append(other_data['metrics'][metric]['sum'])
                
                if other_values:
                    avg_other = sum(other_values) / len(other_values)
                    ratio_to_avg = cm2_value / avg_other if avg_other != 0 else float('inf')
                    
                    if ratio_to_avg > 1.5:  # CM2显著优于平均水平
                        cm2_advantages.append((metric, ratio_to_avg))
                    elif ratio_to_avg < 0.8:  # CM2显著低于平均水平
                        cm2_disadvantages.append((metric, ratio_to_avg))
        
        # 输出优势分析
        if cm2_advantages:
            insights.append("1. CM2的优势指标:")
            for metric, ratio in sorted(cm2_advantages, key=lambda x: x[1], reverse=True):
                insights.append(f"   • {metric}: CM2表现比其他车型平均水平高{(ratio-1)*100:.1f}%")
            insights.append("")
        
        # 输出劣势分析
        if cm2_disadvantages:
            insights.append("2. CM2的劣势指标:")
            for metric, ratio in sorted(cm2_disadvantages, key=lambda x: x[1]):
                insights.append(f"   • {metric}: CM2表现比其他车型平均水平低{(1-ratio)*100:.1f}%")
            insights.append("")
        
        # 总体结论
        insights.append("3. 总体结论:")
        if len(cm2_advantages) > len(cm2_disadvantages):
            insights.append("   CM2在大多数关键指标上表现优异，显示出强劲的市场竞争力。")
        elif len(cm2_advantages) < len(cm2_disadvantages):
            insights.append("   CM2在部分指标上仍有提升空间，需要针对性优化营销策略。")
        else:
            insights.append("   CM2整体表现均衡，在不同指标上各有优劣。")
    else:
        insights.append("警告: CM2数据不存在，无法进行对比分析")
    
    return '\n'.join(insights)

def analyze_presale_daily_orders_for_viz(df):
    """
    分析每次预售发布会周期每天的小订订单数（用于可视化）
    
    Args:
        df (pd.DataFrame): 业务指标数据
    
    Returns:
        dict: 包含各预售周期数据的字典
    """
    # 定义预售发布会时间节点
    event_periods = [
        {"name": "CM0", "presale_start": "2023-08-25", "presale_end": "2023-10-12"},
        {"name": "DM0", "presale_start": "2024-04-08", "presale_end": "2024-05-13"},
        {"name": "CM1", "presale_start": "2024-08-30", "presale_end": "2024-09-26"},
        {"name": "DM1", "presale_start": "2025-04-18", "presale_end": "2025-05-13"},
        {"name": "CM2", "presale_start": "2025-08-15", "presale_end": "2025-09-10"}
    ]
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    results = {}
    max_daily_orders = 0  # 记录历史最大值
    max_cumulative_orders = 0  # 记录累计最大值
    
    for period in event_periods:
        event_date = pd.to_datetime(period['presale_start'])
        cycle_end_date = pd.to_datetime(period['presale_end'])
        
        # 计算完整的周期天数
        total_cycle_days = (cycle_end_date - event_date).days + 1
        
        # 筛选预售周期数据
        cycle_data = df[(df['date'] >= event_date) & (df['date'] <= cycle_end_date)]
        
        # 创建完整的日期范围
        full_date_range = pd.date_range(start=event_date, end=cycle_end_date, freq='D')
        
        # 准备数据 - 包含完整时间范围
        dates = []
        daily_orders = []
        cumulative_orders = []
        cumulative_sum = 0
        
        for date in full_date_range:
            dates.append(date)
            
            # 查找该日期的订单数据
            day_data = cycle_data[cycle_data['date'] == date]
            if len(day_data) > 0 and pd.notna(day_data['小订数'].iloc[0]):
                daily_order = day_data['小订数'].iloc[0]
                daily_orders.append(daily_order)
                cumulative_sum += daily_order
                # 更新历史最大值
                max_daily_orders = max(max_daily_orders, daily_order)
            else:
                # 没有数据的日期设为0或None（显示为空）
                daily_orders.append(0)
            
            cumulative_orders.append(cumulative_sum)
            max_cumulative_orders = max(max_cumulative_orders, cumulative_sum)
        
        results[period['name']] = {
            'event': f"{period['name']}预售",
            'dates': dates,
            'daily_orders': daily_orders,
            'cumulative_orders': cumulative_orders,
            'total_orders': cumulative_sum,
            'cycle_days': total_cycle_days,
            'actual_data_days': len([x for x in daily_orders if x > 0])
        }
    
    # 添加全局最大值信息
    for event_name in results:
        results[event_name]['max_daily_orders'] = max_daily_orders
        results[event_name]['max_cumulative_orders'] = max_cumulative_orders
    
    return results

def analyze_normalized_presale_model_for_viz(df):
    """
    分析预售发布会归一化数据模型（用于可视化）
    
    Args:
        df (pd.DataFrame): 业务指标数据
    
    Returns:
        dict: 包含归一化模型数据的字典
    """
    # 定义预售发布会时间节点
    event_periods = [
        {"name": "CM0", "presale_start": "2023-08-25", "presale_end": "2023-10-12"},
        {"name": "DM0", "presale_start": "2024-04-08", "presale_end": "2024-05-13"},
        {"name": "CM1", "presale_start": "2024-08-30", "presale_end": "2024-09-26"},
        {"name": "DM1", "presale_start": "2025-04-18", "presale_end": "2025-05-13"},
        {"name": "CM2", "presale_start": "2025-08-15", "presale_end": "2025-09-10"}
    ]
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 收集所有预售周期的归一化数据
    normalized_data = []
    
    for period in event_periods:
        event_date = pd.to_datetime(period['presale_start'])
        cycle_end_date = pd.to_datetime(period['presale_end'])
        cycle_data = df[(df['date'] >= event_date) & (df['date'] <= cycle_end_date)]
        
        if len(cycle_data) == 0 or '小订数' not in cycle_data.columns:
            continue
            
        valid_orders = cycle_data['小订数'].dropna()
        if len(valid_orders) == 0:
            continue
            
        # 计算归一化时间点
        total_days = len(valid_orders)
        total_orders = valid_orders.sum()
        
        if total_orders == 0:
            continue
            
        for i, daily_orders in enumerate(valid_orders):
            normalized_time = (i + 1) / total_days
            daily_percentage = daily_orders / total_orders
            
            normalized_data.append({
                'event': period['name'],
                'normalized_time': normalized_time,
                'daily_percentage': daily_percentage,
                'daily_orders': daily_orders,
                'total_days': total_days,
                'total_orders': total_orders
            })
    
    # 计算时间段模型
    time_segments = [
        {'name': '前10%时间', 'start': 0.0, 'end': 0.1},
        {'name': '10%-20%时间', 'start': 0.1, 'end': 0.2},
        {'name': '20%-30%时间', 'start': 0.2, 'end': 0.3},
        {'name': '30%-40%时间', 'start': 0.3, 'end': 0.4},
        {'name': '40%-50%时间', 'start': 0.4, 'end': 0.5},
        {'name': '50%-60%时间', 'start': 0.5, 'end': 0.6},
        {'name': '60%-70%时间', 'start': 0.6, 'end': 0.7},
        {'name': '70%-80%时间', 'start': 0.7, 'end': 0.8},
        {'name': '80%-90%时间', 'start': 0.8, 'end': 0.9},
        {'name': '后10%时间', 'start': 0.9, 'end': 1.0}
    ]
    
    segment_model = []
    norm_df = pd.DataFrame(normalized_data)
    
    for segment in time_segments:
        # 找到该时间段内的数据点
        segment_data = norm_df[
            (norm_df['normalized_time'] > segment['start']) & 
            (norm_df['normalized_time'] <= segment['end'])
        ]
        
        if len(segment_data) > 0:
            # 计算该时间段的日订单总和占比
            segment_orders = []
            for event in norm_df['event'].unique():
                event_data = segment_data[segment_data['event'] == event]
                if len(event_data) > 0:
                    segment_daily_orders = event_data['daily_orders'].sum()
                    total_orders = event_data['total_orders'].iloc[0]
                    segment_percentage = segment_daily_orders / total_orders
                    segment_orders.append(segment_percentage)
            
            if segment_orders:
                avg_orders_pct = np.mean(segment_orders) * 100
                std_orders_pct = np.std(segment_orders) * 100
                sample_count = len(segment_orders)
                
                segment_model.append({
                    'name': segment['name'],
                    'avg_pct': avg_orders_pct,
                    'std_pct': std_orders_pct,
                    'sample_count': sample_count
                })
    
    return {
        'normalized_data': norm_df,
        'segment_model': segment_model,
        'time_segments': time_segments
    }

def create_module3_charts():
    """
    创建Module 3的图表部分 - 预售日变化对比分析
    
    Returns:
        plotly.graph_objects.Figure: 包含预售周期小订数分析的复合图表
    """
    df = load_business_data()
    if df is None:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="数据加载失败，无法生成预售日变化对比分析",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        fig.update_layout(
            title="Module 3: 预售日变化对比分析 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=600
        )
        return fig
    
    # 获取预售周期数据
    presale_data = analyze_presale_daily_orders_for_viz(df)
    
    if not presale_data:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="无法获取预售周期数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        fig.update_layout(
            title="Module 3: 预售日变化对比分析",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 创建小多图布局 (2行3列)
    events = list(presale_data.keys())
    rows = 2
    cols = 3
    
    # 创建子图
    subplot_titles = [f"{event}预售周期" for event in events]
    # 补充空白标题以填满2x3布局
    while len(subplot_titles) < rows * cols:
        subplot_titles.append("")
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        specs=[[{"secondary_y": True} for _ in range(cols)] for _ in range(rows)],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # 颜色配置
    colors = ['#1f77b4', '#1f77b4', '#1f77b4', '#1f77b4', '#9467bd']
    
    # 获取全局最大值用于统一Y轴范围
    max_daily = max([data['max_daily_orders'] for data in presale_data.values()]) if presale_data else 1000
    max_cumulative = max([data['max_cumulative_orders'] for data in presale_data.values()]) if presale_data else 10000
    
    for i, (event, data) in enumerate(presale_data.items()):
        row = i // cols + 1
        col = i % cols + 1
        color = colors[i % len(colors)]
        
        # 添加柱状图（左轴）- 小订数
        fig.add_trace(
            go.Bar(
                x=list(range(1, len(data['daily_orders']) + 1)),
                y=data['daily_orders'],
                name=f"{event} 小订数",
                marker_color=color,
                opacity=0.7,
                showlegend=False
            ),
            row=row, col=col, secondary_y=False
        )
        
        # 添加折线图（右轴）- 累计小订数
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(data['cumulative_orders']) + 1)),
                y=data['cumulative_orders'],
                mode='lines+markers',
                name=f"{event} 累计小订数",
                line=dict(color='red', width=2),
                marker=dict(size=4),
                showlegend=False
            ),
            row=row, col=col, secondary_y=True
        )
        
        # 设置子图的轴标签和范围
        fig.update_xaxes(title_text="天数", row=row, col=col)
        fig.update_yaxes(title_text="小订数", row=row, col=col, secondary_y=False, range=[0, max_daily * 1.1])
        fig.update_yaxes(title_text="累计小订数", row=row, col=col, secondary_y=True, range=[0, max_cumulative * 1.1])
    
    # 获取归一化模型数据
    normalized_data = analyze_normalized_presale_model_for_viz(df)
    
    # 在第6个位置添加归一化模型图表
    if len(events) < 6:  # 如果预售事件少于6个，在最后一个位置添加归一化模型
        row = 2
        col = 3
        
        if normalized_data['segment_model']:
            segment_names = [seg['name'] for seg in normalized_data['segment_model']]
            avg_pcts = [seg['avg_pct'] for seg in normalized_data['segment_model']]
            std_pcts = [seg['std_pct'] for seg in normalized_data['segment_model']]
            
            # 计算Y轴范围，使左右轴同步
            max_avg = max(avg_pcts) if avg_pcts else 10
            max_std = max(std_pcts) if std_pcts else 5
            y_max = max(max_avg, max_std) * 1.2
            
            # 添加柱状图（左轴）- 平均订单占比
            fig.add_trace(
                go.Bar(
                    x=segment_names,
                    y=avg_pcts,
                    name="平均订单占比",
                    marker_color='lightblue',
                    opacity=0.7,
                    width=0.7,  # 设置柱子宽度为0.5
                    showlegend=False
                ),
                row=row, col=col, secondary_y=False
            )
            
            # 添加柱状图（右轴）- 标准差，改为柱状图
            fig.add_trace(
                go.Box(
                    x=segment_names,
                    y=std_pcts,
                    name="标准差",
                    marker_color='red',
                    opacity=0.6,
                    width=0.3,  # 设置柱子宽度为0.5
                    showlegend=False
                ),
                row=row, col=col, secondary_y=True
            )
            
            # 设置子图的轴标签和同步的Y轴范围
            fig.update_xaxes(title_text="时间段", row=row, col=col, tickangle=45)
            fig.update_yaxes(title_text="平均订单占比(%)", row=row, col=col, secondary_y=False, range=[0, y_max])
            fig.update_yaxes(title_text="标准差(%)", row=row, col=col, secondary_y=True, range=[0, y_max])
    
    # 更新整体布局
    fig.update_layout(
        title=dict(
            text="Module 3: 预售发布会周期小订数日变化分析",
            x=0.5,
            font=dict(size=16)
        ),
        height=800,
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def create_module3_insights():
    """
    创建Module 3的解释结论文本
    
    Returns:
        str: 解释结论的文本内容
    """
    df = load_business_data()
    if df is None or df.empty:
        return "数据加载失败，无法生成解释结论。"
    
    try:
        # 获取预售周期数据
        presale_data = analyze_presale_daily_orders_for_viz(df)
        normalized_data = analyze_normalized_presale_model_for_viz(df)
        
        if not presale_data:
            return "预售周期数据不足，无法生成解释结论。"
        
        # 生成解释结论文本
        insights_text = generate_module3_insights(presale_data, normalized_data)
        return insights_text
        
    except Exception as e:
        return f"生成解释结论时发生错误: {str(e)}"

def generate_module3_insights(presale_data, normalized_data):
    """
    生成Module 3的解释结论文本
    
    Args:
        presale_data: 预售周期数据
        normalized_data: 归一化模型数据
    """
    insights = []
    
    insights.append("预售发布会周期小订数分析结果:")
    insights.append("")
    
    # 1. 各预售周期基本统计
    insights.append("1. 各预售周期基本统计:")
    for event, data in presale_data.items():
        total_orders = data['total_orders']
        cycle_days = data['cycle_days']
        avg_daily = total_orders / cycle_days if cycle_days > 0 else 0
        max_daily = max(data['daily_orders']) if data['daily_orders'] else 0
        
        insights.append(f"   • {event}预售: 总订单{total_orders:.0f}个，周期{cycle_days}天，日均{avg_daily:.1f}个，最高日{max_daily:.0f}个")
    insights.append("")
    
    # 2. 预售表现对比
    insights.append("2. 预售表现对比:")
    if len(presale_data) > 1:
        # 按总订单数排序
        sorted_events = sorted(presale_data.items(), key=lambda x: x[1]['total_orders'], reverse=True)
        best_event = sorted_events[0]
        worst_event = sorted_events[-1]
        
        insights.append(f"   • 最佳表现: {best_event[0]}预售，总订单{best_event[1]['total_orders']:.0f}个")
        insights.append(f"   • 相对较弱: {worst_event[0]}预售，总订单{worst_event[1]['total_orders']:.0f}个")
        
        # 计算倍数差异
        if worst_event[1]['total_orders'] > 0:
            ratio = best_event[1]['total_orders'] / worst_event[1]['total_orders']
            insights.append(f"   • 表现差异: 最佳是最弱的{ratio:.1f}倍")
    insights.append("")
    
    # 3. 归一化模型分析
    if normalized_data['segment_model']:
        insights.append("3. 预售周期订单分布模型:")
        
        # 找到订单占比最高的时间段
        max_segment = max(normalized_data['segment_model'], key=lambda x: x['avg_pct'])
        min_segment = min(normalized_data['segment_model'], key=lambda x: x['avg_pct'])
        
        insights.append(f"   • 订单集中期: {max_segment['name']}，平均占比{max_segment['avg_pct']:.1f}%")
        insights.append(f"   • 订单低谷期: {min_segment['name']}，平均占比{min_segment['avg_pct']:.1f}%")
        
        # 分析前后期表现
        front_segments = [seg for seg in normalized_data['segment_model'] if '前' in seg['name'] or '10%-20%' in seg['name']]
        back_segments = [seg for seg in normalized_data['segment_model'] if '后' in seg['name'] or '80%-90%' in seg['name']]
        
        if front_segments and back_segments:
            front_avg = sum(seg['avg_pct'] for seg in front_segments) / len(front_segments)
            back_avg = sum(seg['avg_pct'] for seg in back_segments) / len(back_segments)
            
            if front_avg > back_avg:
                insights.append(f"   • 前期表现更强: 前期平均{front_avg:.1f}%，后期平均{back_avg:.1f}%")
            else:
                insights.append(f"   • 后期表现更强: 后期平均{back_avg:.1f}%，前期平均{front_avg:.1f}%")
        insights.append("")
    
    # 4. 预测模型应用示例
    insights.append("4. 预测模型应用示例:")
    insights.append("   基于归一化数据模型的预测功能:")
    
    # 实现预测函数
    def predict_total_orders(known_days, known_orders, total_cycle_days, segment_model, time_segments):
        """基于已知前N天的订单数预测整个周期的总订单数"""
        if known_days >= total_cycle_days:
            return known_orders
        
        # 计算已知时间的归一化比例
        known_time_ratio = known_days / total_cycle_days
        
        # 根据模型计算已知时间段应该占的订单比例
        expected_cumulative_ratio = 0
        for i, segment in enumerate(segment_model):
            if i < len(time_segments):
                segment_start = time_segments[i]['start']
                segment_end = time_segments[i]['end']
                
                if known_time_ratio > segment_end:
                    # 完全包含这个时间段
                    expected_cumulative_ratio += segment['avg_pct'] / 100
                elif known_time_ratio > segment_start:
                    # 部分包含这个时间段
                    partial_ratio = (known_time_ratio - segment_start) / (segment_end - segment_start)
                    expected_cumulative_ratio += (segment['avg_pct'] / 100) * partial_ratio
        
        if expected_cumulative_ratio > 0:
            predicted_total = known_orders / expected_cumulative_ratio
        else:
            # 如果模型无法预测，使用线性外推
            predicted_total = known_orders * (total_cycle_days / known_days)
        
        return predicted_total
    
    # 动态预测功能说明
    insights.append("   动态预测功能:")
    insights.append("   ------------------------------------------------------------")
    insights.append("   使用上方的动态预测功能，输入已知的前N天数据和订单数，")
    insights.append("   系统将基于归一化时间分布模型自动计算预测结果。")
    insights.append("")
    insights.append("   预测示例参考:")
    insights.append("   • 前1天订单5355个 → 预测总订单约69665个")
    insights.append("   • 前3天订单10742个 → 预测总订单约49688个")
    insights.append("")
    
    # 如果有CM2数据，显示验证信息
    if 'CM2' in presale_data and normalized_data['segment_model']:
        cm2_total = presale_data['CM2']['total_orders']
        cm2_days = presale_data['CM2']['cycle_days']
        cm2_daily_orders = [x for x in presale_data['CM2']['daily_orders'] if x > 0]  # 只取有效数据
        
        if len(cm2_daily_orders) >= 1:
            day1_orders = cm2_daily_orders[0]
            insights.append(f"   模型验证（基于CM2数据）:")
            insights.append(f"   • CM2首日订单: {day1_orders:.0f}个")
            insights.append(f"   • CM2实际总订单: {cm2_total:.0f}个")
            insights.append(f"   • 可使用动态预测功能验证模型准确性")
            insights.append("")
    
    # 5. 预测模型的实际应用价值
    insights.append("5. 预测模型的实际应用价值:")
    insights.append("   • 早期预警: 基于前1-3天数据快速评估预售表现")
    insights.append("   • 资源调配: 根据预测结果调整营销投入和库存准备")
    insights.append("   • 风险控制: 及时发现预售表现不佳的情况并采取措施")
    insights.append("   • 决策支持: 为后续产品发布提供数据驱动的决策依据")
    
    return '\n'.join(insights)

def create_dynamic_prediction(known_days, known_orders):
    """
    创建动态预测功能
    
    Args:
        known_days: 已知的前N天
        known_orders: 前N天的总订单数
    
    Returns:
        str: 预测结果文本
    """
    try:
        # 加载数据
        df = load_business_data()
        if df is None or df.empty:
            return "数据加载失败，无法进行预测。"
        
        # 获取归一化模型数据
        normalized_data = analyze_normalized_presale_model_for_viz(df)
        
        if not normalized_data['segment_model']:
            return "归一化模型数据不足，无法进行预测。"
        
        # 预测函数
        def predict_total_orders(known_days, known_orders, total_cycle_days, segment_model, time_segments):
            """基于已知前N天的订单数预测整个周期的总订单数"""
            if known_days >= total_cycle_days:
                return known_orders
            
            # 计算已知时间的归一化比例
            known_time_ratio = known_days / total_cycle_days
            
            # 根据模型计算已知时间段应该占的订单比例
            expected_cumulative_ratio = 0
            for i, segment in enumerate(segment_model):
                if i < len(time_segments):
                    segment_start = time_segments[i]['start']
                    segment_end = time_segments[i]['end']
                    
                    if known_time_ratio > segment_end:
                        # 完全包含这个时间段
                        expected_cumulative_ratio += segment['avg_pct'] / 100
                    elif known_time_ratio > segment_start:
                        # 部分包含这个时间段
                        partial_ratio = (known_time_ratio - segment_start) / (segment_end - segment_start)
                        expected_cumulative_ratio += (segment['avg_pct'] / 100) * partial_ratio
            
            if expected_cumulative_ratio > 0:
                predicted_total = known_orders / expected_cumulative_ratio
            else:
                # 如果模型无法预测，使用线性外推
                predicted_total = known_orders * (total_cycle_days / known_days)
            
            return predicted_total
        
        # 使用27天作为标准预售周期
        total_cycle_days = 27
        
        # 进行预测
        predicted_total = predict_total_orders(
            known_days, 
            known_orders, 
            total_cycle_days, 
            normalized_data['segment_model'], 
            normalized_data['time_segments']
        )
        
        # 计算预期占比
        expected_ratio = (known_days / total_cycle_days) * 100
        
        # 格式化结果
        result = []
        result.append(f"预测结果:")
        result.append(f"")
        result.append(f"输入参数:")
        result.append(f"• 已知前{known_days}天订单数: {known_orders:.0f}个")
        result.append(f"• 预售周期总天数: {total_cycle_days}天")
        result.append(f"")
        result.append(f"预测输出:")
        result.append(f"• 预测总订单数: {predicted_total:.0f}个")
        result.append(f"• 已知时间占比: {expected_ratio:.1f}%")
        result.append(f"• 剩余预期订单: {predicted_total - known_orders:.0f}个")
        
        # 添加模型说明
        result.append(f"")
        result.append(f"模型说明:")
        result.append(f"基于历史预售周期的归一化时间分布模型进行预测")
        
        return '\n'.join(result)
        
    except Exception as e:
        return f"预测过程中发生错误: {str(e)}"

def load_intention_data():
    """
    加载意向数据
    
    Returns:
        DataFrame: 意向数据，如果加载失败返回None
    """
    try:
        # 尝试加载意向数据文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, 'data')
        
        # 尝试多个可能的文件名
        possible_files = [
            'intention_order_analysis.parquet',
            'intention_data.parquet',
            '意向数据.xlsx'
        ]
        
        for filename in possible_files:
            file_path = os.path.join(data_dir, filename)
            if os.path.exists(file_path):
                if filename.endswith('.parquet'):
                    df = pd.read_parquet(file_path)
                elif filename.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                else:
                    continue
                print(f"成功加载意向数据: {filename}，形状: {df.shape}")
                return df
        
        print(f"意向数据文件不存在，尝试的路径: {[os.path.join(data_dir, f) for f in possible_files]}")
        return None
    except Exception as e:
        print(f"加载意向数据时发生错误: {str(e)}")
        return None

def analyze_by_demographics_modified(df, days_after_launch=3):
    """
    修改后的人口统计学特征分析函数，筛选指定车型并返回表格数据
    
    Args:
        df (DataFrame): 包含锁单指标的数据
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        dict: 包含6个表格数据的字典
    """
    # 定义发布会时间节点
    launch_events = {
        '2023-08-25': 'CM0预售',
        '2024-04-08': 'DM0预售', 
        '2024-08-30': 'CM1预售',
        '2025-04-18': 'DM1预售',
        '2025-08-15': 'CM2预售'
    }
    
    # 确保Intention_Payment_Time列是datetime类型
    if 'Intention_Payment_Time' in df.columns:
        df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
        
        # 根据days_after_launch筛选数据
        if days_after_launch >= 0:
            # 计算所有发布会后N天的时间范围
            filtered_data_list = []
            
            for date_str in launch_events.keys():
                event_date = pd.to_datetime(date_str)
                end_date = event_date + timedelta(days=days_after_launch)
                
                # 筛选该发布会后N天的数据
                event_data = df[(df['Intention_Payment_Time'] >= event_date) & (df['Intention_Payment_Time'] <= end_date)]
                if not event_data.empty:
                    filtered_data_list.append(event_data)
            
            # 合并所有发布会后的数据
            if filtered_data_list:
                df = pd.concat(filtered_data_list, ignore_index=True)
            else:
                # 如果没有发布会后的数据，返回空结果
                return None
    
    # 筛选指定的5个车型
    target_vehicles = ['CM0', 'CM1', 'CM2', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    if df_filtered.empty:
        return None
    
    # 创建年龄分组
    df_filtered['age_group'] = pd.cut(df_filtered['buyer_age'], 
                                    bins=[0, 25, 35, 45, 55, 100], 
                                    labels=['25岁以下', '25-35岁', '35-45岁', '45-55岁', '55岁以上'],
                                    include_lowest=True)
    
    results = {}
    
    # 1. 年龄组×车型交叉表
    age_analysis = df_filtered.groupby(['age_group', '车型分组'], observed=False).size().unstack(fill_value=0)
    # 只保留目标车型列
    age_analysis = age_analysis.reindex(columns=target_vehicles, fill_value=0)
    results['age_vehicle_cross'] = age_analysis
    
    # 2. 年龄组×车型占比表(%)
    # 修改计算逻辑：基于车型维度计算百分比（每个车型内各年龄组的占比）
    age_vehicle_pct = age_analysis.div(age_analysis.sum(axis=0), axis=1) * 100
    age_vehicle_pct = age_vehicle_pct.fillna(0)
    results['age_vehicle_pct'] = age_vehicle_pct
    
    # 3. 性别×车型交叉表
    gender_analysis = df_filtered.groupby(['order_gender', '车型分组'], observed=False).size().unstack(fill_value=0)
    # 只保留目标车型列
    gender_analysis = gender_analysis.reindex(columns=target_vehicles, fill_value=0)
    results['gender_vehicle_cross'] = gender_analysis
    
    # 4. 性别×车型占比表(%)
    # 修改计算逻辑：基于车型维度计算百分比（每个车型内各性别的占比）
    gender_vehicle_pct = gender_analysis.div(gender_analysis.sum(axis=0), axis=1) * 100
    gender_vehicle_pct = gender_vehicle_pct.fillna(0)
    results['gender_vehicle_pct'] = gender_vehicle_pct
    
    # 5. CM2车型年龄结构差异
    if 'CM2' in df_filtered['车型分组'].unique():
        cm2_data = df_filtered[df_filtered['车型分组'] == 'CM2']
        other_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
        other_data = df_filtered[df_filtered['车型分组'].isin(other_vehicles)]
        
        if not cm2_data.empty and not other_data.empty:
            # CM2年龄分布
            cm2_age_dist = cm2_data.groupby('age_group', observed=False).size()
            cm2_age_pct = (cm2_age_dist / cm2_age_dist.sum() * 100).round(2)
            
            # 其他车型年龄分布
            other_age_dist = other_data.groupby('age_group', observed=False).size()
            other_age_pct = (other_age_dist / other_age_dist.sum() * 100).round(2)
            
            # 对比分析
            age_comparison = pd.DataFrame({
                'CM2占比(%)': cm2_age_pct,
                '其他车型占比(%)': other_age_pct
            }).fillna(0)
            age_comparison['差异(百分点)'] = (age_comparison['CM2占比(%)'] - age_comparison['其他车型占比(%)']).round(2)
            
            results['cm2_age_diff'] = age_comparison
        else:
            results['cm2_age_diff'] = None
    else:
        results['cm2_age_diff'] = None
    
    # 6. CM2车型性别结构差异
    if 'CM2' in df_filtered['车型分组'].unique():
        cm2_data = df_filtered[df_filtered['车型分组'] == 'CM2']
        other_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
        other_data = df_filtered[df_filtered['车型分组'].isin(other_vehicles)]
        
        if not cm2_data.empty and not other_data.empty:
            # CM2性别分布
            cm2_gender_dist = cm2_data.groupby('order_gender', observed=False).size()
            cm2_gender_pct = (cm2_gender_dist / cm2_gender_dist.sum() * 100).round(2)
            
            # 其他车型性别分布
            other_gender_dist = other_data.groupby('order_gender', observed=False).size()
            other_gender_pct = (other_gender_dist / other_gender_dist.sum() * 100).round(2)
            
            # 对比分析
            gender_comparison = pd.DataFrame({
                'CM2占比(%)': cm2_gender_pct,
                '其他车型占比(%)': other_gender_pct
            }).fillna(0)
            gender_comparison['差异(百分点)'] = (gender_comparison['CM2占比(%)'] - gender_comparison['其他车型占比(%)']).round(2)
            
            results['cm2_gender_diff'] = gender_comparison
        else:
            results['cm2_gender_diff'] = None
    else:
        results['cm2_gender_diff'] = None
    
    # 7. 车型平均年龄对比分析（18-70岁）
    # 筛选18-70岁的数据，排除异常值
    age_filtered_df = df_filtered[(df_filtered['buyer_age'] >= 18) & (df_filtered['buyer_age'] <= 70)]
    
    if len(age_filtered_df) > 0:
        # 计算每个车型的平均年龄
        vehicle_age_stats = age_filtered_df.groupby('车型分组').agg({
            'buyer_age': ['mean', 'median', 'std', 'count']
        }).round(2)
        
        # 重命名列
        vehicle_age_stats.columns = ['平均年龄', '中位数年龄', '年龄标准差', '样本数量']
        
        # 按平均年龄排序
        vehicle_age_stats = vehicle_age_stats.sort_values('平均年龄', ascending=False)
        
        # 只保留目标车型
        vehicle_age_stats = vehicle_age_stats.reindex(target_vehicles).dropna()
        
        # 计算整体平均年龄
        overall_mean_age = age_filtered_df['buyer_age'].mean()
        
        # 分析各车型与整体平均年龄的差异
        age_diff_analysis = pd.DataFrame({
            '车型': vehicle_age_stats.index,
            '平均年龄': vehicle_age_stats['平均年龄'],
            '中位数年龄': vehicle_age_stats['中位数年龄'],
            '年龄标准差': vehicle_age_stats['年龄标准差'],
            '样本数量': vehicle_age_stats['样本数量'].astype(int),
            '与整体差异': (vehicle_age_stats['平均年龄'] - overall_mean_age).round(2)
        })
        
        # 重置索引，使车型成为普通列
        age_diff_analysis = age_diff_analysis.reset_index(drop=True)
        
        results['vehicle_age_comparison'] = age_diff_analysis
    else:
        results['vehicle_age_comparison'] = None
    
    return results

def analyze_by_geography_modified(df, days_after_launch=3):
    """
    修改后的地理分布分析函数，返回结构化数据用于可视化
    
    Args:
        df (DataFrame): 包含锁单指标的数据
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        dict: 包含地理分布分析数据的字典
    """
    # 定义发布会时间节点
    launch_events = {
        '2023-08-25': 'CM0预售',
        '2024-04-08': 'DM0预售', 
        '2024-08-30': 'CM1预售',
        '2025-04-18': 'DM1预售',
        '2025-08-15': 'CM2预售'
    }
    
    # 确保Intention_Payment_Time列是datetime类型
    if 'Intention_Payment_Time' in df.columns:
        df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
        
        # 根据days_after_launch筛选数据
        if days_after_launch >= 0:
            # 计算所有发布会后N天的时间范围
            filtered_data_list = []
            
            for date_str in launch_events.keys():
                event_date = pd.to_datetime(date_str)
                end_date = event_date + timedelta(days=days_after_launch)
                
                # 筛选该发布会后N天的数据
                event_data = df[(df['Intention_Payment_Time'] >= event_date) & (df['Intention_Payment_Time'] <= end_date)]
                if not event_data.empty:
                    filtered_data_list.append(event_data)
            
            # 合并所有发布会后的数据
            if filtered_data_list:
                df = pd.concat(filtered_data_list, ignore_index=True)
            else:
                # 如果没有发布会后的数据，返回空结果
                return None
    
    # 筛选掉LS7和L7车型
    df_filtered = df[~df['车型分组'].isin(['LS7', 'L7'])].copy()
    
    if df_filtered.empty:
        return None
    
    results = {}
    
    # 1. 城市等级分析
    city_level_vehicle = df_filtered.groupby(['license_city_level', '车型分组'], observed=False).size().unstack(fill_value=0)
    results['city_level_vehicle_count'] = city_level_vehicle
    
    # 修改百分比计算逻辑：按车型计算百分比（每个车型在不同城市等级的分布）
    city_level_vehicle_pct = city_level_vehicle.div(city_level_vehicle.sum(axis=0), axis=1) * 100
    city_level_vehicle_pct = city_level_vehicle_pct.fillna(0)
    results['city_level_vehicle_pct'] = city_level_vehicle_pct
    
    # 2. CM2对比分析
    if 'CM2' in df_filtered['车型分组'].unique():
        cm2_city_level = df_filtered[df_filtered['车型分组'] == 'CM2'].groupby('license_city_level', observed=False).size()
        cm2_city_level_pct = (cm2_city_level / cm2_city_level.sum() * 100).round(2)
        
        target_vehicles = ['CM0', 'CM1', 'DM1']
        available_vehicles = [v for v in target_vehicles if v in df_filtered['车型分组'].unique()]
        
        for vehicle in available_vehicles:
            other_city_level = df_filtered[df_filtered['车型分组'] == vehicle].groupby('license_city_level', observed=False).size()
            other_city_level_pct = (other_city_level / other_city_level.sum() * 100).round(2)
            
            # 计算差异
            comparison = pd.DataFrame({
                f'CM2占比(%)': cm2_city_level_pct,
                f'{vehicle}占比(%)': other_city_level_pct
            }).fillna(0)
            comparison['差异(百分点)'] = (comparison[f'CM2占比(%)'] - comparison[f'{vehicle}占比(%)']).round(2)
            
            results[f'cm2_vs_{vehicle.lower()}_comparison'] = comparison
    
    # 3. TOP10城市分析数据
    if 'License City' in df_filtered.columns:
        city_vehicle = df_filtered.groupby(['License City', '车型分组'], observed=False).size().unstack(fill_value=0)
        
        top10_cities_data = {}
        for vehicle in city_vehicle.columns:
            if city_vehicle[vehicle].sum() > 0:
                top_cities = city_vehicle[vehicle].sort_values(ascending=False).head(10)
                top_cities_pct = (top_cities / city_vehicle[vehicle].sum() * 100).round(2)
                
                # 计算各城市的锁单率
                lock_rates = []
                for city in top_cities.index:
                    city_data = df_filtered[(df_filtered['车型分组'] == vehicle) & (df_filtered['License City'] == city)]
                    lock_rate = city_data['has_lock'].mean() * 100 if len(city_data) > 0 else 0
                    lock_rates.append(round(lock_rate, 2))
                
                top10_cities_data[vehicle] = pd.DataFrame({
                    '订单数': top_cities,
                    '占该车型比例(%)': top_cities_pct,
                    '锁单率(%)': lock_rates
                })
        
        results['top10_cities_data'] = top10_cities_data
    
    return results

def create_demographics_analysis(days_after_launch=3):
    """
    创建人口统计学特征分析可视化
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="意向数据加载失败！请检查数据文件是否存在",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        fig.update_layout(
            title="人口统计学特征分析 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 添加锁单指标
    df['has_lock'] = ~df['Lock_Time'].isnull() if 'Lock_Time' in df.columns else False
    
    # 调用修改后的分析函数
    analysis_results = analyze_by_demographics_modified(df, days_after_launch)
    
    if analysis_results is None:
        fig = go.Figure()
        fig.add_annotation(
            text="指定车型数据不足，无法生成分析图表",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="orange")
        )
        fig.update_layout(
            title="人口统计学特征分析 - 数据不足",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 创建包含7个表格的子图 - 4行2列布局
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=[
            "车型平均年龄对比分析（18-70岁）",
            "CM2车型年龄结构差异",
            "CM2车型性别结构差异",
            "年龄组×车型交叉表",
            "年龄组×车型占比表(%)",
            "性别×车型交叉表",
            "性别×车型占比表(%)",
            ""
        ],
        specs=[[{"type": "table", "colspan": 2}, None],
               [{"type": "table"}, {"type": "table"}],
               [{"type": "table"}, {"type": "table"}],
               [{"type": "table"}, {"type": "table"}]],
        vertical_spacing=0.08,
        horizontal_spacing=0.05
    )
    
    # 1. 车型平均年龄对比分析（18-70岁）(第1行，跨两列)
    if analysis_results.get('vehicle_age_comparison') is not None:
        table_data = analysis_results['vehicle_age_comparison']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(table_data.columns),
                    fill_color='lightsteelblue',
                    align='center',
                    font=dict(size=12, color='darkblue')
                ),
                cells=dict(
                    values=[table_data[col] for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=11)
                )
            ),
            row=1, col=1
        )
    
    # 2. CM2车型年龄结构差异 (第2行第1列)
    if analysis_results.get('cm2_age_diff') is not None:
        table_data = analysis_results['cm2_age_diff']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['年龄组'] + list(table_data.columns),
                    fill_color='lightpink',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col].round(2) for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=2, col=1
        )
    
    # 3. CM2车型性别结构差异 (第2行第2列)
    if analysis_results.get('cm2_gender_diff') is not None:
        table_data = analysis_results['cm2_gender_diff']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['性别'] + list(table_data.columns),
                    fill_color='lightcyan',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col].round(2) for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=2, col=2
        )
    
    # 4. 年龄组×车型交叉表 (第3行第1列)
    if 'age_vehicle_cross' in analysis_results:
        table_data = analysis_results['age_vehicle_cross']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['年龄组'] + list(table_data.columns),
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col] for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=3, col=1
        )
    
    # 5. 年龄组×车型占比表(%) (第3行第2列)
    if 'age_vehicle_pct' in analysis_results:
        table_data = analysis_results['age_vehicle_pct']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['年龄组'] + list(table_data.columns),
                    fill_color='lightgreen',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col].round(2) for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=3, col=2
        )
    
    # 6. 性别×车型交叉表 (第4行第1列)
    if 'gender_vehicle_cross' in analysis_results:
        table_data = analysis_results['gender_vehicle_cross']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['性别'] + list(table_data.columns),
                    fill_color='lightcoral',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col] for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=4, col=1
        )
    
    # 7. 性别×车型占比表(%) (第4行第2列)
    if 'gender_vehicle_pct' in analysis_results:
        table_data = analysis_results['gender_vehicle_pct']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['性别'] + list(table_data.columns),
                    fill_color='lightyellow',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[table_data.index] + [table_data[col].round(2) for col in table_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=4, col=2
        )
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text="人口统计学特征分析 - CM0/CM1/CM2/DM0/DM1车型对比",
            x=0.5,
            font=dict(size=16)
        ),
        height=1000,  # 调整高度适应4行2列布局
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def create_geography_analysis(days_after_launch=3):
    """
    创建地理分布分析可视化
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="意向数据加载失败！请检查数据文件是否存在",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        fig.update_layout(
            title="地理分布分析 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 添加锁单指标
    df['has_lock'] = ~df['Lock_Time'].isnull() if 'Lock_Time' in df.columns else False
    
    # 调用修改后的分析函数
    analysis_results = analyze_by_geography_modified(df, days_after_launch)
    
    if analysis_results is None:
        fig = go.Figure()
        fig.add_annotation(
            text="地理分布数据不足，无法生成分析图表",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="orange")
        )
        fig.update_layout(
            title="地理分布分析 - 数据不足",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 创建包含5个表格的子图 - 5行1列垂直布局
    fig = make_subplots(
        rows=5, cols=1,
        subplot_titles=[
            "各车型在不同城市等级的订单数量",
            "各车型在不同城市等级的占比(%)",
            "CM2 vs CM0 城市等级分布对比",
            "CM2 vs CM1 城市等级分布对比",
            "CM2 vs DM1 城市等级分布对比"
        ],
        specs=[[{"type": "table"}],
               [{"type": "table"}],
               [{"type": "table"}],
               [{"type": "table"}],
               [{"type": "table"}]],
        vertical_spacing=0.04
    )
    
    # 1. 各车型在不同城市等级的订单数量 (第1行)
    if 'city_level_vehicle_count' in analysis_results:
        table_data = analysis_results['city_level_vehicle_count']
        # 筛选车型：只保留CM0、CM1、CM2、DM0、DM1
        target_vehicles = ['CM0', 'CM1', 'CM2', 'DM0', 'DM1']
        filtered_columns = [col for col in table_data.columns if col in target_vehicles]
        filtered_data = table_data[filtered_columns]
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['城市等级'] + list(filtered_data.columns),
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[filtered_data.index] + [filtered_data[col] for col in filtered_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=1, col=1
        )
    
    # 2. 各车型在不同城市等级的占比(%) (第2行)
    if 'city_level_vehicle_pct' in analysis_results:
        table_data = analysis_results['city_level_vehicle_pct']
        # 筛选车型：只保留CM0、CM1、CM2、DM0、DM1
        target_vehicles = ['CM0', 'CM1', 'CM2', 'DM0', 'DM1']
        filtered_columns = [col for col in table_data.columns if col in target_vehicles]
        filtered_data = table_data[filtered_columns]
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['城市等级'] + list(filtered_data.columns),
                    fill_color='lightgreen',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[filtered_data.index] + [filtered_data[col].round(2) for col in filtered_data.columns],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=2, col=1
        )
    
    # 3. CM2 vs CM0 城市等级分布对比 (第3行)
    if 'cm2_vs_cm0_comparison' in analysis_results:
        table_data = analysis_results['cm2_vs_cm0_comparison']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['城市等级', 'CM2占比(%)', 'CM0占比(%)', '差异(百分点)'],
                    fill_color='lightcoral',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[
                        table_data.index,
                        table_data['CM2占比(%)'],
                        table_data['CM0占比(%)'],
                        table_data['差异(百分点)']
                    ],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=3, col=1
        )
    
    # 4. CM2 vs CM1 城市等级分布对比 (第4行)
    if 'cm2_vs_cm1_comparison' in analysis_results:
        table_data = analysis_results['cm2_vs_cm1_comparison']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['城市等级', 'CM2占比(%)', 'CM1占比(%)', '差异(百分点)'],
                    fill_color='lightyellow',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[
                        table_data.index,
                        table_data['CM2占比(%)'],
                        table_data['CM1占比(%)'],
                        table_data['差异(百分点)']
                    ],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=4, col=1
        )
    
    # 5. CM2 vs DM1 城市等级分布对比 (第5行)
    if 'cm2_vs_dm1_comparison' in analysis_results:
        table_data = analysis_results['cm2_vs_dm1_comparison']
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['城市等级', 'CM2占比(%)', 'DM1占比(%)', '差异(百分点)'],
                    fill_color='lightsteelblue',
                    align='center',
                    font=dict(size=11)
                ),
                cells=dict(
                    values=[
                        table_data.index,
                        table_data['CM2占比(%)'],
                        table_data['DM1占比(%)'],
                        table_data['差异(百分点)']
                    ],
                    fill_color='white',
                    align='center',
                    font=dict(size=10)
                )
            ),
            row=5, col=1
        )
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text="地理分布分析 - 城市等级分布及CM2车型对比",
            x=0.5,
            font=dict(size=16)
        ),
        height=1200,  # 调整高度适应5行垂直布局
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def create_top10_cities_analysis(selected_vehicle="CM2"):
    """
    创建TOP10城市分析表格
    
    Args:
        selected_vehicle (str): 选择的车型
    
    Returns:
        DataFrame: TOP10城市分析数据
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        return pd.DataFrame(columns=['License City', '订单数', '占该车型比例(%)', '锁单率(%)'])
    
    # 添加锁单指标
    df['has_lock'] = ~df['Lock_Time'].isnull() if 'Lock_Time' in df.columns else False
    
    # 调用修改后的分析函数
    analysis_results = analyze_by_geography_modified(df)
    
    if analysis_results is None or 'top10_cities_data' not in analysis_results:
        return pd.DataFrame(columns=['License City', '订单数', '占该车型比例(%)', '锁单率(%)'])
    
    top10_data = analysis_results['top10_cities_data']
    
    if selected_vehicle in top10_data:
        result_df = top10_data[selected_vehicle].copy()
        result_df.reset_index(inplace=True)
        result_df.rename(columns={'License City': 'License City'}, inplace=True)
        return result_df
    else:
        return pd.DataFrame(columns=['License City', '订单数', '占该车型比例(%)', '锁单率(%)'])

def analyze_by_channel_modified(df, days_after_launch=3):
    """
    修改版渠道分析函数，专门用于可视化
    
    Args:
        df (DataFrame): 包含锁单指标的数据
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        dict: 包含渠道分析结果的字典
    """
    # 定义发布会时间节点
    launch_events = {
        '2023-08-25': 'CM0预售',
        '2024-04-08': 'DM0预售', 
        '2024-08-30': 'CM1预售',
        '2025-04-18': 'DM1预售',
        '2025-08-15': 'CM2预售'
    }
    
    # 确保Intention_Payment_Time列是datetime类型
    if 'Intention_Payment_Time' in df.columns:
        df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
        
        # 根据days_after_launch筛选数据
        if days_after_launch >= 0:
            # 计算所有发布会后N天的时间范围
            filtered_data_list = []
            
            for date_str in launch_events.keys():
                event_date = pd.to_datetime(date_str)
                end_date = event_date + timedelta(days=days_after_launch)
                
                # 筛选该发布会后N天的数据
                event_data = df[(df['Intention_Payment_Time'] >= event_date) & (df['Intention_Payment_Time'] <= end_date)]
                if not event_data.empty:
                    filtered_data_list.append(event_data)
            
            # 合并所有发布会后的数据
            if filtered_data_list:
                df = pd.concat(filtered_data_list, ignore_index=True)
            else:
                # 如果没有发布会后的数据，返回空结果
                return None
    
    # 检查必要字段
    if 'first_middle_channel_name' not in df.columns or '车型分组' not in df.columns:
        return None
    
    # 筛选车型：只保留CM0、CM1、CM2、DM0、DM1
    target_vehicles = ['CM0', 'CM1', 'CM2', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    if df_filtered.empty:
        return None
    
    # 按车型和渠道分组分析
    channel_vehicle_analysis = df_filtered.groupby(['车型分组', 'first_middle_channel_name'], observed=False).agg({
        'Order Number': 'count'
    }).reset_index()
    channel_vehicle_analysis.rename(columns={'Order Number': 'quantity'}, inplace=True)
    
    # 计算每个车型的总订单数
    vehicle_totals = df_filtered.groupby('车型分组', observed=False)['Order Number'].count().to_dict()
    
    # 为每个车型计算占比
    channel_vehicle_analysis['proportion'] = channel_vehicle_analysis.apply(
        lambda row: (row['quantity'] / vehicle_totals[row['车型分组']] * 100) if vehicle_totals[row['车型分组']] > 0 else 0, 
        axis=1
    )
    
    # 创建渠道×车型占比表格（按车型维度计算百分比）
    channel_vehicle_pivot = channel_vehicle_analysis.pivot(index='first_middle_channel_name', columns='车型分组', values='proportion')
    channel_vehicle_pivot = channel_vehicle_pivot.fillna(0)
    
    # 确保所有目标车型都在列中
    for vehicle in target_vehicles:
        if vehicle not in channel_vehicle_pivot.columns:
            channel_vehicle_pivot[vehicle] = 0
    
    # 按目标车型顺序排列列
    channel_vehicle_pivot = channel_vehicle_pivot[target_vehicles]
    
    # 按CM2车型的占比降序排列渠道
    if 'CM2' in channel_vehicle_pivot.columns:
        channel_vehicle_pivot = channel_vehicle_pivot.sort_values('CM2', ascending=False)
    
    # 创建渠道×车型订单数表格
    channel_vehicle_count = channel_vehicle_analysis.pivot(index='first_middle_channel_name', columns='车型分组', values='quantity')
    channel_vehicle_count = channel_vehicle_count.fillna(0).astype(int)
    
    # 确保所有目标车型都在列中
    for vehicle in target_vehicles:
        if vehicle not in channel_vehicle_count.columns:
            channel_vehicle_count[vehicle] = 0
    
    # 按目标车型顺序排列列
    channel_vehicle_count = channel_vehicle_count[target_vehicles]
    
    # 按CM2车型的订单数降序排列渠道
    if 'CM2' in channel_vehicle_count.columns:
        channel_vehicle_count = channel_vehicle_count.sort_values('CM2', ascending=False)
    
    # 找出每个渠道占比最大的车型（用于高亮显示）
    max_vehicle_per_channel = {}
    for channel in channel_vehicle_pivot.index:
        row_data = channel_vehicle_pivot.loc[channel]
        max_vehicle = row_data.idxmax() if row_data.max() > 0 else None
        max_vehicle_per_channel[channel] = max_vehicle
    
    return {
        'channel_vehicle_count': channel_vehicle_count,
        'channel_vehicle_pct': channel_vehicle_pivot,
        'max_vehicle_per_channel': max_vehicle_per_channel,
        'vehicle_totals': vehicle_totals
    }

def create_channel_analysis(days_after_launch=3):
    """
    创建渠道结构分析可视化
    
    Args:
        days_after_launch (int): 发布会后分析的天数，默认为3天
    
    Returns:
        plotly.graph_objects.Figure: 包含渠道分析表格的图表
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        fig = go.Figure()
        fig.add_annotation(
            text="无法加载意向数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # 添加锁单指标
    df['has_lock'] = ~df['Lock_Time'].isnull() if 'Lock_Time' in df.columns else False
    
    # 调用修改后的渠道分析函数
    analysis_results = analyze_by_channel_modified(df, days_after_launch)
    
    if analysis_results is None:
        fig = go.Figure()
        fig.add_annotation(
            text="渠道分析数据不足",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # 获取分析结果
    channel_count = analysis_results['channel_vehicle_count']
    channel_pct = analysis_results['channel_vehicle_pct']
    max_vehicle_per_channel = analysis_results['max_vehicle_per_channel']
    
    # 创建子图布局：2行1列
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            "各渠道在不同车型的订单数量",
            "各渠道在不同车型的占比(%) - 高亮最大占比"
        ],
        vertical_spacing=0.15,
        specs=[[{"type": "table"}], [{"type": "table"}]]
    )
    
    # 表格1：订单数量
    count_values = []
    count_values.append(list(channel_count.index))  # 渠道名称
    for col in channel_count.columns:
        count_values.append(list(channel_count[col]))
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=["渠道"] + list(channel_count.columns),
                fill_color='lightblue',
                align='center',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=count_values,
                fill_color='white',
                align='center',
                font=dict(size=11)
            )
        ),
        row=1, col=1
    )
    
    # 表格2：占比（带高亮）
    pct_values = []
    pct_values.append(list(channel_pct.index))  # 渠道名称
    
    # 准备占比数据和颜色
    pct_colors = [['white'] * len(channel_pct.index)]  # 渠道名称列
    
    for col in channel_pct.columns:
        col_values = []
        col_colors = []
        for idx, channel in enumerate(channel_pct.index):
            value = channel_pct.loc[channel, col]
            col_values.append(f"{value:.1f}%")
            
            # 如果这个渠道在这个车型上有最大占比，则高亮显示
            if max_vehicle_per_channel.get(channel) == col:
                col_colors.append('lightgreen')  # 高亮颜色
            else:
                col_colors.append('white')
        
        pct_values.append(col_values)
        pct_colors.append(col_colors)
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=["渠道"] + list(channel_pct.columns),
                fill_color='lightblue',
                align='center',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=pct_values,
                fill_color=pct_colors,
                align='center',
                font=dict(size=11)
            )
        ),
        row=2, col=1
    )
    
    # 更新布局
    fig.update_layout(
        height=1000,
        title_text="渠道结构分析",
        title_x=0.5,
        showlegend=False,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig

def analyze_order_date_features_modified(df):
    """
    修改版下订日期特征分析函数，专门用于可视化
    
    Args:
        df (DataFrame): 包含锁单指标的数据
    
    Returns:
        dict: 包含下订日期分析结果的字典
    """
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    # 检查必要字段
    if 'Intention_Payment_Time' not in df.columns or '车型分组' not in df.columns:
        return None
    
    # 确保时间字段为datetime类型
    df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
    
    # 筛选出CM0、CM1、DM0、DM1车型
    target_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    if df_filtered.empty:
        return None
    
    date_analysis_results = {}
    summary_text = ""
    
    for vehicle in target_vehicles:
        if vehicle not in presale_periods:
            continue
            
        vehicle_data = df_filtered[df_filtered['车型分组'] == vehicle].copy()
        
        if len(vehicle_data) == 0:
            continue
            
        # 获取预售时间范围
        presale_start = pd.to_datetime(presale_periods[vehicle]['start'])
        presale_end = pd.to_datetime(presale_periods[vehicle]['end'])
        total_days = (presale_end - presale_start).days + 1
        
        # 筛选预售期间的订单
        presale_orders = vehicle_data[
            (vehicle_data['Intention_Payment_Time'] >= presale_start) & 
            (vehicle_data['Intention_Payment_Time'] <= presale_end)
        ].copy()
        
        if len(presale_orders) == 0:
            continue
            
        # 计算每天相对于预售开始的天数
        presale_orders['days_from_start'] = (presale_orders['Intention_Payment_Time'] - presale_start).dt.days
        
        # 按日期分组统计
        daily_stats = presale_orders.groupby('Intention_Payment_Time', observed=False).agg({
            'Order Number': 'count',
            'has_lock': ['sum', 'mean']
        }).round(4)
        
        daily_stats.columns = ['订单数', '锁单数', '锁单率']
        daily_stats['锁单率'] = daily_stats['锁单率'] * 100
        daily_stats = daily_stats.reset_index()
        daily_stats['相对天数'] = (daily_stats['Intention_Payment_Time'] - presale_start).dt.days
        
        # 计算前10%和后10%的数据
        front_10_threshold = total_days * 0.1
        back_10_threshold = total_days * 0.9
        
        front_10_orders = presale_orders[presale_orders['days_from_start'] <= front_10_threshold]
        back_10_orders = presale_orders[presale_orders['days_from_start'] >= back_10_threshold]
        
        # 统计前10%和后10%的指标
        front_10_count = len(front_10_orders)
        front_10_lock_rate = front_10_orders['has_lock'].mean() * 100 if len(front_10_orders) > 0 else 0
        
        back_10_count = len(back_10_orders)
        back_10_lock_rate = back_10_orders['has_lock'].mean() * 100 if len(back_10_orders) > 0 else 0
        
        total_presale_orders = len(presale_orders)
        
        # 保存分析结果
        date_analysis_results[vehicle] = {
            'total_days': total_days,
            'total_orders': total_presale_orders,
            'front_10_orders': front_10_count,
            'front_10_lock_rate': front_10_lock_rate,
            'back_10_orders': back_10_count,
            'back_10_lock_rate': back_10_lock_rate,
            'daily_stats': daily_stats,
            'presale_start': presale_start,
            'presale_end': presale_end
        }
    
    # 生成跨车型对比分析文本
    if len(date_analysis_results) > 1:
        summary_text += "跨车型下订日期特征对比分析\n"
        summary_text += "=" * 50 + "\n\n"
        
        summary_text += "各车型预售期订单分布对比:\n"
        summary_text += f"{'车型':<8} {'预售天数':<10} {'总订单':<10} {'前10%订单':<12} {'前10%锁单率':<15} {'后10%订单':<12} {'后10%锁单率':<15}\n"
        summary_text += "-" * 90 + "\n"
        
        front_order_ratios = []
        back_order_ratios = []
        front_lock_rates = []
        back_lock_rates = []
        
        for vehicle, data in date_analysis_results.items():
            front_ratio = (data['front_10_orders'] / data['total_orders']) * 100
            back_ratio = (data['back_10_orders'] / data['total_orders']) * 100
            
            front_order_ratios.append(front_ratio)
            back_order_ratios.append(back_ratio)
            front_lock_rates.append(data['front_10_lock_rate'])
            back_lock_rates.append(data['back_10_lock_rate'])
            
            summary_text += f"{vehicle:<8} {data['total_days']:<10} {data['total_orders']:<10} {data['front_10_orders']:<12} {data['front_10_lock_rate']:<15.2f} {data['back_10_orders']:<12} {data['back_10_lock_rate']:<15.2f}\n"
        
        # 计算平均值
        avg_front_ratio = np.mean(front_order_ratios)
        avg_back_ratio = np.mean(back_order_ratios)
        avg_front_lock = np.mean(front_lock_rates)
        avg_back_lock = np.mean(back_lock_rates)
        
        summary_text += "\n下订日期特征规律分析:\n"
        summary_text += "-" * 50 + "\n"
        summary_text += f"• 前10%时间段平均订单占比: {avg_front_ratio:.2f}%\n"
        summary_text += f"• 后10%时间段平均订单占比: {avg_back_ratio:.2f}%\n"
        summary_text += f"• 前10%时间段平均锁单率: {avg_front_lock:.2f}%\n"
        summary_text += f"• 后10%时间段平均锁单率: {avg_back_lock:.2f}%\n\n"
        
        # 发现规律
        if avg_front_ratio > avg_back_ratio:
            summary_text += f"• 规律发现: 预售前期订单集中度更高 (前期{avg_front_ratio:.1f}% vs 后期{avg_back_ratio:.1f}%)\n"
        else:
            summary_text += f"• 规律发现: 预售后期订单集中度更高 (后期{avg_back_ratio:.1f}% vs 前期{avg_front_ratio:.1f}%)\n"
            
        if avg_front_lock > avg_back_lock:
            summary_text += f"• 规律发现: 预售前期锁单率更高 (前期{avg_front_lock:.1f}% vs 后期{avg_back_lock:.1f}%)\n"
        else:
            summary_text += f"• 规律发现: 预售后期锁单率更高 (后期{avg_back_lock:.1f}% vs 前期{avg_front_lock:.1f}%)\n"
    
    return {
        'date_analysis_results': date_analysis_results,
        'summary_text': summary_text
    }

def create_order_date_analysis():
    """
    创建下订日期特征分析可视化
    
    Returns:
        tuple: (plotly.graph_objects.Figure, str) 包含图表和结论文本
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        fig = go.Figure()
        fig.add_annotation(
            text="无法加载意向数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, "无法加载数据"
    
    # 添加锁单指标
    df['has_lock'] = ~df['Lock_Time'].isnull() if 'Lock_Time' in df.columns else False
    
    # 调用修改后的下订日期分析函数
    analysis_results = analyze_order_date_features_modified(df)
    
    if analysis_results is None or not analysis_results['date_analysis_results']:
        fig = go.Figure()
        fig.add_annotation(
            text="下订日期分析数据不足",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, "数据不足"
    
    # 获取分析结果
    date_results = analysis_results['date_analysis_results']
    summary_text = analysis_results['summary_text']
    
    # 创建小多图布局：2行2列
    vehicles = list(date_results.keys())
    n_vehicles = len(vehicles)
    
    if n_vehicles == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="无有效车型数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, "无有效数据"
    
    # 计算子图布局
    rows = 2
    cols = 2
    
    # 创建子图标题
    subplot_titles = []
    for i, vehicle in enumerate(vehicles[:4]):  # 最多显示4个车型
        data = date_results[vehicle]
        start_date = data['presale_start'].strftime('%Y-%m-%d')
        end_date = data['presale_end'].strftime('%Y-%m-%d')
        subplot_titles.append(f"{vehicle}车型预售期 ({start_date} 至 {end_date})")
    
    # 补齐子图标题
    while len(subplot_titles) < 4:
        subplot_titles.append("")
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # 为每个车型创建双轴图表
    for i, vehicle in enumerate(vehicles[:4]):  # 最多显示4个车型
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        data = date_results[vehicle]
        daily_stats = data['daily_stats']
        
        if daily_stats.empty:
            continue
        
        # 将相对天数转换为时间段
        total_days = data['total_days']
        time_periods = []
        period_orders = []
        period_lock_rates = []
        
        # 定义10个时间段：前10%，10%-20%，...，90%-100%
        for period_idx in range(10):
            start_pct = period_idx * 10
            end_pct = (period_idx + 1) * 10
            period_label = f"{start_pct}%-{end_pct}%时间"
            
            # 计算该时间段对应的天数范围
            start_day = int(total_days * start_pct / 100)
            end_day = int(total_days * end_pct / 100)
            
            # 筛选该时间段的数据
            period_data = daily_stats[
                (daily_stats['相对天数'] >= start_day) & 
                (daily_stats['相对天数'] < end_day)
            ]
            
            if not period_data.empty:
                # 汇总该时间段的订单数和锁单率
                total_orders = period_data['订单数'].sum()
                avg_lock_rate = period_data['锁单率'].mean()
                
                time_periods.append(period_label)
                period_orders.append(total_orders)
                period_lock_rates.append(avg_lock_rate)
        
        # 左Y轴：订单数柱状图
        fig.add_trace(
            go.Bar(
                x=time_periods,
                y=period_orders,
                name=f"{vehicle} 订单数",
                marker_color='lightblue',
                opacity=0.7,
                showlegend=(i == 0),  # 只在第一个图显示图例
                legendgroup="orders"
            ),
            row=row, col=col, secondary_y=False
        )
        
        # 右Y轴：锁单率折线图
        fig.add_trace(
            go.Scatter(
                x=time_periods,
                y=period_lock_rates,
                mode='lines+markers',
                name=f"{vehicle} 锁单率",
                line=dict(color='red', width=2),
                marker=dict(size=4),
                showlegend=(i == 0),  # 只在第一个图显示图例
                legendgroup="lock_rate"
            ),
            row=row, col=col, secondary_y=True
        )
        
        # 设置X轴标题和样式
        fig.update_xaxes(
            title_text="预售时间段" if row == 2 else "",
            tickangle=45,  # 倾斜标签以避免重叠
            row=row, col=col
        )
        
        # 设置左Y轴标题（订单数）
        fig.update_yaxes(
            title_text="订单数" if col == 1 else "",
            row=row, col=col, secondary_y=False
        )
        
        # 设置右Y轴标题（锁单率）
        fig.update_yaxes(
            title_text="锁单率(%)" if col == 2 else "",
            row=row, col=col, secondary_y=True
        )
    
    # 更新整体布局
    fig.update_layout(
        height=800,
        title_text="各车型预售期下订日期特征分析",
        title_x=0.5,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig, summary_text

def analyze_order_hour_features_modified(df):
    """
    修改版的下订时间（小时）特征分析函数，用于可视化
    
    Args:
        df (DataFrame): 包含订单数据的DataFrame
    """
    # 筛选出CM0、CM1、DM0、DM1车型
    target_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    # 检查是否有Intention Payment Time 小时字段
    if 'Intention Payment Time 小时' not in df_filtered.columns:
        return {}, "错误: 未找到'Intention Payment Time 小时'字段"
    
    # 添加锁单指标
    df_filtered['has_lock'] = (~df_filtered['Lock_Time'].isnull()).astype(int)
    
    hour_analysis_results = {}
    
    for vehicle in target_vehicles:
        vehicle_data = df_filtered[df_filtered['车型分组'] == vehicle].copy()
        
        if len(vehicle_data) == 0:
            continue
        
        # 按小时分组统计
        hourly_stats = vehicle_data.groupby('Intention Payment Time 小时', observed=False).agg({
            'Order Number': 'count',
            'has_lock': ['sum', 'mean']
        }).round(4)
        
        hourly_stats.columns = ['订单数', '锁单数', '锁单率']
        hourly_stats['锁单率'] = hourly_stats['锁单率'] * 100
        hourly_stats = hourly_stats.reset_index()
        hourly_stats['订单占比(%)'] = (hourly_stats['订单数'] / hourly_stats['订单数'].sum() * 100).round(2)
        
        # 确保所有24小时都有数据（填充0）
        all_hours = pd.DataFrame({'Intention Payment Time 小时': range(24)})
        hourly_stats = all_hours.merge(hourly_stats, on='Intention Payment Time 小时', how='left').fillna(0)
        
        # 分析高峰时段
        top_hours = hourly_stats.nlargest(5, '订单数')
        
        # 分析锁单率高峰时段
        high_lock_hours = hourly_stats[hourly_stats['订单数'] > 0].nlargest(5, '锁单率')
        
        # 保存分析结果
        hour_analysis_results[vehicle] = {
            'hourly_stats': hourly_stats,
            'total_orders': int(hourly_stats['订单数'].sum()),
            'peak_hours': top_hours['Intention Payment Time 小时'].tolist(),
            'high_lock_hours': high_lock_hours['Intention Payment Time 小时'].tolist()
        }
    
    # 生成跨车型对比分析文本
    analysis_text = "跨车型24小时下订时间特征规律性深度解读\n\n"
    
    # 定义时段
    time_periods = {
        '深夜时段(0-6时)': list(range(0, 6)),
        '早晨时段(6-9时)': list(range(6, 9)),
        '上午时段(9-12时)': list(range(9, 12)),
        '下午时段(12-18时)': list(range(12, 18)),
        '晚上时段(18-22时)': list(range(18, 22)),
        '夜间时段(22-24时)': list(range(22, 24))
    }
    
    analysis_text += "1. 时段订单分布一致性分析:\n"
    analysis_text += "-" * 50 + "\n"
    
    period_analysis = {}
    period_consistency = {}
    
    for period_name, hours in time_periods.items():
        period_stats = []
        
        for vehicle, data in hour_analysis_results.items():
            period_data = data['hourly_stats'][data['hourly_stats']['Intention Payment Time 小时'].isin(hours)]
            period_orders = period_data['订单数'].sum()
            period_lock_rate = (period_data['锁单数'].sum() / period_orders * 100) if period_orders > 0 else 0
            period_ratio = (period_orders / data['total_orders'] * 100) if data['total_orders'] > 0 else 0
            
            period_stats.append({
                'vehicle': vehicle,
                'orders': period_orders,
                'lock_rate': period_lock_rate,
                'ratio': period_ratio
            })
        
        # 计算该时段的平均表现和一致性
        vehicle_ratios = [s['ratio'] for s in period_stats]
        ratio_std = np.std(vehicle_ratios)
        ratio_avg = np.mean(vehicle_ratios)
        
        period_consistency[period_name] = {
            'avg': ratio_avg,
            'std': ratio_std,
            'consistent': ratio_std < 3.0  # 3%标准差阈值
        }
        
        analysis_text += f"• {period_name}: {ratio_avg:.1f}% ± {ratio_std:.1f}% (标准差)\n"
        
        period_analysis[period_name] = {
            'avg_orders': np.mean([s['orders'] for s in period_stats]),
            'avg_lock_rate': np.mean([s['lock_rate'] for s in period_stats if s['orders'] > 0]),
            'avg_ratio': ratio_avg,
            'vehicle_stats': period_stats
        }
    
    # 识别一致性时段
    consistent_periods = [name for name, data in period_consistency.items() if data['consistent']]
    
    if len(consistent_periods) >= 4:
        analysis_text += f"\n• 规律性发现: {len(consistent_periods)}/6个时段具有高度一致性\n"
        analysis_text += f"• 一致时段: {', '.join(consistent_periods)}\n"
        analysis_text += f"• 可预测性: 强 - 24小时分布规律稳定，可作为CM2预测的可靠特征\n"
    elif len(consistent_periods) >= 2:
        analysis_text += f"\n• 规律性发现: {len(consistent_periods)}/6个时段具有一致性\n"
        analysis_text += f"• 一致时段: {', '.join(consistent_periods)}\n"
        analysis_text += f"• 可预测性: 中等 - 部分时段规律稳定\n"
    else:
        analysis_text += f"\n• 规律性发现: 各车型24小时订单分布存在较大差异\n"
        analysis_text += f"• 可预测性: 较低 - 需结合其他特征进行CM2预测\n"
    
    # 分析峰值时段一致性
    analysis_text += "\n2. 订单峰值时段一致性分析:\n"
    analysis_text += "-" * 50 + "\n"
    
    # 找出各车型的峰值时段
    vehicle_peak_periods = {}
    for vehicle, data in hour_analysis_results.items():
        vehicle_period_ratios = {}
        for period_name, period_data in period_analysis.items():
            vehicle_stat = next((s for s in period_data['vehicle_stats'] if s['vehicle'] == vehicle), None)
            if vehicle_stat:
                vehicle_period_ratios[period_name] = vehicle_stat['ratio']
        
        # 找出该车型的峰值时段（订单占比最高的时段）
        if vehicle_period_ratios:
            peak_period = max(vehicle_period_ratios.items(), key=lambda x: x[1])
            vehicle_peak_periods[vehicle] = peak_period[0]
    
    analysis_text += f"• 各车型峰值时段:\n"
    for vehicle, peak_period in vehicle_peak_periods.items():
        analysis_text += f"  {vehicle}: {peak_period}\n"
    
    # 统计峰值时段频率
    from collections import Counter
    peak_period_counts = Counter(vehicle_peak_periods.values())
    common_peak_periods = [period for period, count in peak_period_counts.items() if count >= 2]
    
    if len(common_peak_periods) >= 1:
        analysis_text += f"\n• 共同峰值时段: {', '.join(common_peak_periods)} (出现在2个以上车型中)\n"
        analysis_text += f"• 峰值规律性: 强 - 存在明显的共同峰值时段\n"
    else:
        analysis_text += f"\n• 共同峰值时段: 无\n"
        analysis_text += f"• 峰值规律性: 弱 - 各车型峰值时段差异较大\n"
    
    # 分析锁单率时间分布一致性
    analysis_text += "\n3. 时段锁单率分布一致性分析:\n"
    analysis_text += "-" * 50 + "\n"
    
    lock_rate_consistency = {}
    for period_name, data in period_analysis.items():
        vehicle_lock_rates = [stat['lock_rate'] for stat in data['vehicle_stats'] if stat['orders'] > 0]
        if vehicle_lock_rates:
            lock_std = np.std(vehicle_lock_rates)
            lock_avg = np.mean(vehicle_lock_rates)
            
            lock_rate_consistency[period_name] = {
                'avg': lock_avg,
                'std': lock_std,
                'consistent': lock_std < 8.0  # 8%标准差阈值
            }
            analysis_text += f"• {period_name}锁单率: {lock_avg:.1f}% ± {lock_std:.1f}% (标准差)\n"
    
    consistent_lock_periods = [name for name, data in lock_rate_consistency.items() if data['consistent']]
    
    if len(consistent_lock_periods) >= 3:
        analysis_text += f"\n• 锁单率规律性: 强 - {len(consistent_lock_periods)}/6个时段锁单率分布一致\n"
        analysis_text += f"• 一致时段: {', '.join(consistent_lock_periods)}\n"
    else:
        analysis_text += f"\n• 锁单率规律性: 中等 - 各车型锁单率时间分布存在差异\n"
    
    # 工作时间vs非工作时间规律分析
    analysis_text += "\n4. 工作时间vs非工作时间订单规律分析:\n"
    analysis_text += "-" * 50 + "\n"
    
    work_periods = ['早晨时段(6-9时)', '上午时段(9-12时)', '下午时段(12-18时)']
    non_work_periods = ['深夜时段(0-6时)', '晚上时段(18-22时)', '夜间时段(22-24时)']
    
    work_vs_nonwork_patterns = {}
    for vehicle, data in hour_analysis_results.items():
        work_ratio = sum(period_analysis[period]['vehicle_stats'][i]['ratio'] 
                       for period in work_periods 
                       for i, stat in enumerate(period_analysis[period]['vehicle_stats']) 
                       if stat['vehicle'] == vehicle)
        
        non_work_ratio = sum(period_analysis[period]['vehicle_stats'][i]['ratio'] 
                           for period in non_work_periods 
                           for i, stat in enumerate(period_analysis[period]['vehicle_stats']) 
                           if stat['vehicle'] == vehicle)
        
        work_vs_nonwork_patterns[vehicle] = {
            'work_ratio': work_ratio,
            'non_work_ratio': non_work_ratio,
            'work_dominant': work_ratio > non_work_ratio
        }
    
    work_dominant_count = sum(1 for data in work_vs_nonwork_patterns.values() if data['work_dominant'])
    total_vehicles = len(work_vs_nonwork_patterns)
    
    analysis_text += f"• 各车型工作时间vs非工作时间订单分布:\n"
    for vehicle, data in work_vs_nonwork_patterns.items():
        dominant = "工作时间" if data['work_dominant'] else "非工作时间"
        analysis_text += f"  {vehicle}: 工作时间{data['work_ratio']:.1f}% vs 非工作时间{data['non_work_ratio']:.1f}% (偏好{dominant})\n"
    
    if work_dominant_count == total_vehicles:
        analysis_text += f"\n• 时间偏好规律: 所有车型均偏好工作时间下单\n"
        analysis_text += f"• 规律一致性: 强 - 可作为CM2预测的稳定特征\n"
    elif work_dominant_count == 0:
        analysis_text += f"\n• 时间偏好规律: 所有车型均偏好非工作时间下单\n"
        analysis_text += f"• 规律一致性: 强 - 可作为CM2预测的稳定特征\n"
    else:
        analysis_text += f"\n• 时间偏好规律: {work_dominant_count}/{total_vehicles}车型偏好工作时间\n"
        analysis_text += f"• 规律一致性: 中等 - 存在车型差异\n"
    
    # CM2预测的关键时间规律总结
    analysis_text += "\n5. CM2预测关键时间规律总结:\n"
    analysis_text += "-" * 50 + "\n"
    
    time_patterns = []
    
    if len(consistent_periods) >= 4:
        time_patterns.append(f"24小时分布规律高度稳定({len(consistent_periods)}/6时段一致)")
    elif len(consistent_periods) >= 2:
        time_patterns.append(f"24小时分布规律部分稳定({len(consistent_periods)}/6时段一致)")
    
    if len(common_peak_periods) >= 1:
        time_patterns.append(f"存在共同峰值时段({', '.join(common_peak_periods)})")
    
    if len(consistent_lock_periods) >= 3:
        time_patterns.append(f"锁单率时间分布规律稳定({len(consistent_lock_periods)}/6时段一致)")
    
    if work_dominant_count == total_vehicles or work_dominant_count == 0:
        preference = "工作时间" if work_dominant_count == total_vehicles else "非工作时间"
        time_patterns.append(f"统一偏好{preference}下单")
    
    if time_patterns:
        analysis_text += "• 可用于CM2预测的稳定时间规律:\n"
        for i, pattern in enumerate(time_patterns, 1):
            analysis_text += f"  {i}. {pattern}\n"
        
        reliability_score = len(time_patterns)
        if reliability_score >= 3:
            reliability = "高"
        elif reliability_score >= 2:
            reliability = "中等"
        else:
            reliability = "较低"
        
        analysis_text += f"\n• 时间特征预测可信度: {reliability}\n"
        
        if reliability in ["高", "中等"]:
            analysis_text += f"• CM2营销建议: 可基于历史时间规律制定精准的时段营销策略\n"
            if len(common_peak_periods) >= 1:
                analysis_text += f"• 重点时段: 优先在{', '.join(common_peak_periods)}投入营销资源\n"
        else:
            analysis_text += f"• CM2营销建议: 建议结合其他特征维度，避免过度依赖时间规律\n"
    else:
        analysis_text += "• 各车型24小时订单特征差异较大，时间维度预测价值有限\n"
        analysis_text += "• 建议重点关注其他特征维度进行CM2预测\n"
    
    return hour_analysis_results, analysis_text

def create_order_hour_analysis():
    """
    创建下订时间（小时）特征分析可视化
    
    Returns:
        tuple: (plotly.graph_objects.Figure, str) 包含图表和结论文本
    """
    # 加载意向数据
    df = load_intention_data()
    if df is None:
        fig = go.Figure()
        fig.add_annotation(
            text="无法加载意向数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, "无法加载数据"
    
    # 调用修改后的下订时间（小时）分析函数
    hour_results, analysis_text = analyze_order_hour_features_modified(df)
    
    if not hour_results:
        fig = go.Figure()
        fig.add_annotation(
            text="下订时间（小时）分析数据不足",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, analysis_text
    
    # 创建小多图布局：2行2列
    vehicles = list(hour_results.keys())
    n_vehicles = len(vehicles)
    
    if n_vehicles == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="无有效车型数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig, analysis_text
    
    # 计算子图布局
    rows = 2
    cols = 2
    
    # 创建子图标题
    subplot_titles = [f"{vehicle}车型24小时订单分布" for vehicle in vehicles]
    
    # 创建子图
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 颜色配置
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, vehicle in enumerate(vehicles):
        row = (i // cols) + 1
        col = (i % cols) + 1
        
        data = hour_results[vehicle]
        hourly_stats = data['hourly_stats']
        
        # 添加订单数柱状图（左Y轴）
        fig.add_trace(
            go.Bar(
                x=hourly_stats['Intention Payment Time 小时'],
                y=hourly_stats['订单数'],
                name=f"{vehicle} 订单数",
                marker_color='lightblue',
                opacity=0.7,
                showlegend=(i == 0),
                legendgroup="orders"
            ),
            row=row, col=col, secondary_y=False
        )
        
        # 添加锁单率折线图（右Y轴）
        fig.add_trace(
            go.Scatter(
                x=hourly_stats['Intention Payment Time 小时'],
                y=hourly_stats['锁单率'],
                mode='lines+markers',
                name=f"{vehicle} 锁单率",
                line=dict(color='red', width=2),
                marker=dict(size=4),
                showlegend=(i == 0),
                legendgroup="lock_rate"
            ),
            row=row, col=col, secondary_y=True
        )
        
        # 设置Y轴标题
        fig.update_yaxes(title_text="订单数", row=row, col=col, secondary_y=False)
        fig.update_yaxes(title_text="锁单率(%)", row=row, col=col, secondary_y=True)
        
        # 设置X轴标题
        fig.update_xaxes(title_text="小时", row=row, col=col)
    
    # 更新整体布局
    fig.update_layout(
        title={
            'text': "CM0、CM1、DM0、DM1车型24小时下订时间特征分析",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig, analysis_text

def create_cm2_mg4_comparison():
    """创建CM2与MG4小订数对比可视化"""
    df = load_business_data()
    if df is None:
        # 返回错误信息的图表
        fig = go.Figure()
        fig.add_annotation(
            text="数据加载失败！请检查数据文件是否存在",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red")
        )
        fig.update_layout(
            title="小订数与MG4对比 - 数据加载失败",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 定义预售周期
    cm2_presale_start = pd.to_datetime('2025-08-15')
    cm2_presale_end = pd.to_datetime('2025-09-10')
    mg4_presale_start = pd.to_datetime('2025-08-05')
    mg4_presale_end = pd.to_datetime('2025-08-29')
    
    # 筛选CM2预售期间数据
    cm2_data = df[(df['date'] >= cm2_presale_start) & (df['date'] <= cm2_presale_end)].copy()
    
    # 筛选MG4预售期间数据
    mg4_data = df[(df['date'] >= mg4_presale_start) & (df['date'] <= mg4_presale_end)].copy()
    
    if cm2_data.empty and mg4_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="预售期间数据不足，无法生成对比图表",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="orange")
        )
        fig.update_layout(
            title="小订数与MG4对比 - 数据不足",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # 创建对齐的天数列（从第0天开始）
    if not cm2_data.empty:
        cm2_data['days_from_start'] = (cm2_data['date'] - cm2_presale_start).dt.days
    
    if not mg4_data.empty:
        mg4_data['days_from_start'] = (mg4_data['date'] - mg4_presale_start).dt.days
    
    # 创建图表
    fig = go.Figure()
    
    # 添加CM2小订数折线
    if not cm2_data.empty and '小订数' in cm2_data.columns:
        cm2_valid_data = cm2_data.dropna(subset=['小订数'])
        if not cm2_valid_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=cm2_valid_data['days_from_start'],
                    y=cm2_valid_data['小订数'],
                    mode='lines+markers',
                    name='CM2小订数',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>CM2</b><br>' +
                                '第%{x}天<br>' +
                                '小订数: %{y}<br>' +
                                '<extra></extra>'
                )
            )
    
    # 添加MG4小订数折线
    if not mg4_data.empty and 'MG4小订数' in mg4_data.columns:
        mg4_valid_data = mg4_data.dropna(subset=['MG4小订数'])
        if not mg4_valid_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=mg4_valid_data['days_from_start'],
                    y=mg4_valid_data['MG4小订数'],
                    mode='lines+markers',
                    name='MG4小订数',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>MG4</b><br>' +
                                '第%{x}天<br>' +
                                '小订数: %{y}<br>' +
                                '<extra></extra>'
                )
            )
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text="CM2与MG4预售期间小订数对比",
            x=0.5,
            font=dict(size=18)
        ),
        xaxis=dict(
            title="预售天数（第0天为预售开始日）",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            tickmode='linear',
            tick0=0,
            dtick=1
        ),
        yaxis=dict(
            title="小订数",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        hovermode='x unified',
        height=450,
        font=dict(family="Arial, sans-serif"),
        plot_bgcolor='white'
    )
    
    return fig

def create_placeholder_tab(tab_name):
    """创建占位符标签页"""
    fig = go.Figure()
    fig.add_annotation(
        text=f"{tab_name} - 待实现",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=20)
    )
    fig.update_layout(
        title=f"{tab_name}",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig

def create_gradio_interface():
    """创建Gradio界面"""
    
    with gr.Blocks(title="业务分析可视化", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 业务分析可视化平台")
        gr.Markdown("基于analyze_business_metrics.py和analyze_intention_data.py的可视化展示")
        
        with gr.Tabs():
            # Module 4 - 预售发布会后指标对比分析
            with gr.TabItem("Module 4: 预售发布会指标对比"):
                with gr.Row():
                    days_input = gr.Number(
                        value=3,
                        minimum=0,
                        maximum=30,
                        step=1,
                        label="发布会后分析天数",
                        info="输入发布会后要分析的天数（0=当日，1=后1日，以此类推，最大30天）"
                    )
                    refresh_btn = gr.Button("刷新数据", variant="primary")
                
                # 数据表格部分
                module4_plot = gr.Plot(
                    value=create_module4_tables(3),
                    label="预售发布会后指标对比分析 - 数据表格"
                )
                
                # 解释结论部分
                module4_insights = gr.Textbox(
                    value=create_module4_insights(3),
                    label="解释结论",
                    lines=10,
                    max_lines=20,
                    interactive=False,
                    show_copy_button=True
                )
                
                # 绑定事件：输入框变化时更新图表和结论
                days_input.change(
                    fn=lambda days: [create_module4_tables(days), create_module4_insights(days)],
                    inputs=days_input,
                    outputs=[module4_plot, module4_insights]
                )
                
                # 绑定事件：刷新按钮点击时更新图表和结论
                refresh_btn.click(
                    fn=lambda days: [create_module4_tables(days), create_module4_insights(days)],
                    inputs=days_input,
                    outputs=[module4_plot, module4_insights]
                )
            
            # Module 1 - 发布会后指标变化幅度分析
            with gr.TabItem("Module 1: 发布会后指标变化幅度分析"):
                with gr.Row():
                    days_input_m1 = gr.Number(
                        value=3,
                        minimum=0,
                        maximum=30,
                        step=1,
                        label="发布会后指标变化幅度分析",
                        info="输入发布会后要分析的天数（0=当日，1=后1日，以此类推，最大30天）"
                    )
                    refresh_btn_m1 = gr.Button("刷新数据", variant="primary")
                
                # 数据表格部分
                module1_plot = gr.Plot(
                    value=create_module1_tables(3),
                    label="发布会后指标变化幅度分析 - 数据表格"
                )
                
                # 解释结论部分
                module1_insights = gr.Textbox(
                    value=create_module1_insights(3),
                    label="解释结论",
                    lines=10,
                    max_lines=20,
                    interactive=False,
                    show_copy_button=True
                )
                
                # 绑定事件：输入框变化时更新图表和结论
                days_input_m1.change(
                    fn=lambda days: [create_module1_tables(days), create_module1_insights(days)],
                    inputs=days_input_m1,
                    outputs=[module1_plot, module1_insights]
                )
                
                # 绑定事件：刷新按钮点击时更新图表和结论
                refresh_btn_m1.click(
                    fn=lambda days: [create_module1_tables(days), create_module1_insights(days)],
                    inputs=days_input_m1,
                    outputs=[module1_plot, module1_insights]
                )
            
            with gr.TabItem("Module 3: 预售日变化对比"):
                # 预售周期小订数分析图表
                module3_plot = gr.Plot(
                    value=create_module3_charts(),
                    label="预售发布会周期小订数日变化分析"
                )
                
                # 动态预测功能
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 动态预测功能")
                        days_input_m3 = gr.Number(
                            value=1,
                            minimum=1,
                            maximum=27,
                            step=1,
                            label="前N天",
                            info="输入已知的前N天数据（1-27天）"
                        )
                        orders_input_m3 = gr.Number(
                            value=5355,
                            minimum=0,
                            step=1,
                            label="订单数",
                            info="输入前N天的总订单数"
                        )
                        predict_btn_m3 = gr.Button("预测总订单数", variant="primary")
                    
                    with gr.Column(scale=2):
                        prediction_result_m3 = gr.Textbox(
                            value="",
                            label="预测结果",
                            lines=5,
                            interactive=False,
                            show_copy_button=True
                        )
                
                # 解释结论部分
                module3_insights = gr.Textbox(
                    value=create_module3_insights(),
                    label="解释结论",
                    lines=15,
                    max_lines=25,
                    interactive=False,
                    show_copy_button=True
                )
                
                # 绑定预测按钮事件
                predict_btn_m3.click(
                    fn=lambda days, orders: create_dynamic_prediction(days, orders),
                    inputs=[days_input_m3, orders_input_m3],
                    outputs=prediction_result_m3
                )
            
            with gr.TabItem("小订数与 MG4 对比"):
                gr.Plot(
                    value=create_cm2_mg4_comparison(),
                    label="小订数与 MG4 对比"
                )

            with gr.TabItem("人口统计学特征分析"):
                with gr.Row():
                    days_input_demo = gr.Number(
                        value=3,
                        minimum=0,
                        maximum=30,
                        step=1,
                        label="发布会后分析天数",
                        info="输入发布会后要分析的天数（0=当日，1=后1日，以此类推，最大30天）"
                    )
                    refresh_btn_demo = gr.Button("刷新数据", variant="primary")
                
                demographics_plot = gr.Plot(
                    value=create_demographics_analysis(3),
                    label="人口统计学特征分析"
                )
                
                # 绑定事件：输入框变化时更新图表
                days_input_demo.change(
                    fn=lambda days: create_demographics_analysis(days),
                    inputs=days_input_demo,
                    outputs=demographics_plot
                )
                
                # 绑定事件：刷新按钮点击时更新图表
                refresh_btn_demo.click(
                    fn=lambda days: create_demographics_analysis(days),
                    inputs=days_input_demo,
                    outputs=demographics_plot
                )

            with gr.TabItem("地理分布分析"):
                with gr.Row():
                    days_input_geo = gr.Number(
                        value=3,
                        minimum=0,
                        maximum=30,
                        step=1,
                        label="发布会后分析天数",
                        info="输入发布会后要分析的天数（0=当日，1=后1日，以此类推，最大30天）"
                    )
                    refresh_btn_geo = gr.Button("刷新数据", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 地理分布分析")
                        geography_plot = gr.Plot(
                            value=create_geography_analysis(3),
                            label="地理分布分析"
                        )
                        
                        # 绑定事件：输入框变化时更新图表
                        days_input_geo.change(
                            fn=lambda days: create_geography_analysis(days),
                            inputs=days_input_geo,
                            outputs=geography_plot
                        )
                        
                        # 绑定事件：刷新按钮点击时更新图表
                        refresh_btn_geo.click(
                            fn=lambda days: create_geography_analysis(days),
                            inputs=days_input_geo,
                            outputs=geography_plot
                        )
                        
                        gr.Markdown("### TOP10城市分析")
                        with gr.Row():
                            vehicle_dropdown = gr.Dropdown(
                                choices=["CM0", "CM1", "CM2", "DM0", "DM1"],
                                value="CM2",
                                label="选择车型"
                            )
                        
                        top10_table = gr.Dataframe(
                            value=create_top10_cities_analysis("CM2"),
                            label="TOP10城市分析",
                            interactive=False
                        )
                        
                        # 添加车型选择的交互功能
                        vehicle_dropdown.change(
                            fn=create_top10_cities_analysis,
                            inputs=[vehicle_dropdown],
                            outputs=[top10_table]
                        )

            with gr.TabItem("渠道结构分析"):
                with gr.Row():
                    days_input_channel = gr.Number(
                        value=3,
                        minimum=0,
                        maximum=30,
                        step=1,
                        label="发布会后分析天数",
                        info="输入发布会后要分析的天数（0=当日，1=后1日，以此类推，最大30天）"
                    )
                    refresh_btn_channel = gr.Button("刷新数据", variant="primary")
                
                channel_plot = gr.Plot(
                    value=create_channel_analysis(3),
                    label="渠道结构分析"
                )
                
                # 绑定事件：输入框变化时更新图表
                days_input_channel.change(
                    fn=lambda days: create_channel_analysis(days),
                    inputs=days_input_channel,
                    outputs=channel_plot
                )
                
                # 绑定事件：刷新按钮点击时更新图表
                refresh_btn_channel.click(
                    fn=lambda days: create_channel_analysis(days),
                    inputs=days_input_channel,
                    outputs=channel_plot
                )

            with gr.TabItem("下订日期特征分析"):
                # 创建下订日期特征分析
                order_date_fig, order_date_text = create_order_date_analysis()
                
                gr.Plot(
                    value=order_date_fig,
                    label="各车型预售期下订日期特征分析"
                )
                
                gr.Textbox(
                    value=order_date_text,
                    label="分析结论",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )

            with gr.TabItem("下订时间（小时）特征分析"):
                hour_plot, hour_text = create_order_hour_analysis()
                gr.Plot(
                    value=hour_plot,
                    label="下订时间（小时）特征分析"
                )
                gr.Textbox(
                    value=hour_text,
                    label="分析结论",
                    lines=30,
                    max_lines=50,
                    interactive=False
                )
    return demo

def main():
    """主函数"""
    print("启动数据分析可视化平台...")
    
    # 创建并启动Gradio界面
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()