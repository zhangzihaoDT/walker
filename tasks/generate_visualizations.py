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
            
            with gr.TabItem("Module 2: 发布会后变化"):
                gr.Plot(
                    value=create_placeholder_tab("Module 2: 发布会后变化"),
                    label="发布会后变化分析"
                )
            
            with gr.TabItem("Module 3: 预售比值对比"):
                gr.Plot(
                    value=create_placeholder_tab("Module 3: 预售比值对比"),
                    label="预售比值对比分析"
                )
            
            with gr.TabItem("意向数据分析"):
                gr.Plot(
                    value=create_placeholder_tab("意向数据分析"),
                    label="意向数据分析"
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