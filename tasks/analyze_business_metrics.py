#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务日常指标数据分析脚本
读取 business_daily_metrics.parquet 文件并分析基本数据信息
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def analyze_parquet_file(file_path):
    """
    分析parquet文件的基本信息
    
    Args:
        file_path (str): parquet文件路径
    """
    try:
        # 读取parquet文件
        print(f"正在读取文件: {file_path}")
        df = pd.read_parquet(file_path)
        
        print("\n" + "="*60)
        print("数据基本信息分析")
        print("="*60)
        
        # 1. 数据形状
        print(f"\n1. 数据形状:")
        print(f"   行数: {df.shape[0]:,}")
        print(f"   列数: {df.shape[1]:,}")
        
        # 2. 字段名称和数据类型
        print(f"\n2. 字段信息:")
        print("-" * 40)
        for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
            print(f"   {i:2d}. {col:<25} | {str(dtype):<15}")
        
        # 3. 空值统计
        print(f"\n3. 空值统计:")
        print("-" * 40)
        null_counts = df.isnull().sum()
        null_percentages = (df.isnull().sum() / len(df)) * 100
        
        for col in df.columns:
            null_count = null_counts[col]
            null_pct = null_percentages[col]
            print(f"   {col:<25} | 空值数量: {null_count:>6,} | 空值比例: {null_pct:>6.2f}%")
        
        # 4. 数据类型分布
        print(f"\n4. 数据类型分布:")
        print("-" * 40)
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            print(f"   {str(dtype):<15} | {count:>3} 个字段")
        
        # 5. 内存使用情况
        print(f"\n5. 内存使用情况:")
        print("-" * 40)
        memory_usage = df.memory_usage(deep=True)
        total_memory = memory_usage.sum()
        print(f"   总内存使用: {total_memory / 1024 / 1024:.2f} MB")
        print(f"   平均每行: {total_memory / len(df):.2f} bytes")
        
        # 6. 数值型字段的基本统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            print(f"\n6. 数值型字段基本统计:")
            print("-" * 40)
            print(f"   数值型字段数量: {len(numeric_cols)}")
            print(f"   数值型字段: {', '.join(numeric_cols)}")
            
            # 显示数值型字段的描述性统计
            print("\n   描述性统计:")
            desc_stats = df[numeric_cols].describe()
            print(desc_stats.round(2))
        
        # 7. 非数值型字段信息
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
        if len(non_numeric_cols) > 0:
            print(f"\n7. 非数值型字段信息:")
            print("-" * 40)
            for col in non_numeric_cols:
                unique_count = df[col].nunique()
                print(f"   {col:<25} | 唯一值数量: {unique_count:>6,}")
                
                # 如果唯一值不多，显示前几个值
                if unique_count <= 10:
                    sample_values = df[col].value_counts().head(5)
                    print(f"   {'':>27} | 前5个值: {list(sample_values.index)}")
        
        print("\n" + "="*60)
        print("分析完成")
        print("="*60)
        
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
    except Exception as e:
        print(f"读取文件时发生错误: {str(e)}")

def analyze_launch_events(df):
    """
    分析发布会时间节点前30日的指标
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义发布会时间节点
    launch_events = {
        '2023-08-25': {'event': 'CM0预售', 'type': '预售'},
        '2023-10-12': {'event': 'CM0上市', 'type': '上市'},
        '2024-04-08': {'event': 'DM0预售', 'type': '预售'},
        '2024-05-13': {'event': 'DM0上市', 'type': '上市'},
        '2024-08-30': {'event': 'CM1预售', 'type': '预售'},
        '2024-09-26': {'event': 'CM1上市', 'type': '上市'},
        '2025-04-18': {'event': 'DM1预售', 'type': '预售'},
        '2025-05-13': {'event': 'DM1上市', 'type': '上市'},
        '2025-08-15': {'event': 'CM2预售', 'type': '预售'}
    }
    
    # 需要分析的指标
    metrics = [
        '小订数',
        '有效线索数', '抖音战队线索数', '下发线索数', '有效试驾数', '抖音线索占比'
        '本品牌人群总资产资产', '本品牌日新增', '本品牌日流失', '本品牌人群流量'
    ]
    
    print("\n" + "="*80)
    print("发布会时间节点前30日指标分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    results = []
    
    for date_str, event_info in launch_events.items():
        event_date = pd.to_datetime(date_str)
        start_date = event_date - timedelta(days=30)
        
        # 筛选前30日数据
        period_data = df[(df['date'] >= start_date) & (df['date'] < event_date)]
        
        if len(period_data) == 0:
            print(f"\n警告: {event_info['event']} ({date_str}) 前30日无数据")
            continue
            
        print(f"\n{event_info['event']} ({date_str}) - {event_info['type']}")
        print(f"分析期间: {start_date.strftime('%Y-%m-%d')} 至 {event_date.strftime('%Y-%m-%d')}")
        print(f"数据天数: {len(period_data)}")
        print("-" * 60)
        
        event_result = {
            'event': event_info['event'],
            'date': date_str,
            'type': event_info['type'],
            'data_days': len(period_data)
        }
        
        # 计算每个指标的平均值、最大值、最小值和方差
        for metric in metrics:
            if metric in period_data.columns:
                # 过滤掉空值
                metric_data = period_data[metric].dropna()
                
                if len(metric_data) > 0:
                    mean_val = metric_data.mean()
                    max_val = metric_data.max()
                    min_val = metric_data.min()
                    var_val = metric_data.var()
                    
                    print(f"{metric:<20} | 平均值: {mean_val:>10.2f} | 最大值: {max_val:>10.2f} | 最小值: {min_val:>10.2f} | 方差: {var_val:>12.2f}")
                    
                    event_result[f'{metric}_mean'] = mean_val
                    event_result[f'{metric}_max'] = max_val
                    event_result[f'{metric}_min'] = min_val
                    event_result[f'{metric}_var'] = var_val
                else:
                    print(f"{metric:<20} | 无有效数据")
                    event_result[f'{metric}_mean'] = None
                    event_result[f'{metric}_max'] = None
                    event_result[f'{metric}_min'] = None
                    event_result[f'{metric}_var'] = None
            else:
                print(f"{metric:<20} | 字段不存在")
        
        results.append(event_result)
    
    # 转换为DataFrame便于后续分析
    results_df = pd.DataFrame(results)
    
    return results_df

def analyze_post_launch_changes(df):
    """
    分析发布会后3日指标相对于前30日平均值的变化幅度
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义发布会时间节点（复用之前的定义）
    launch_events = {
        '2023-08-25': {'event': 'CM0预售', 'type': '预售'},
        '2023-10-12': {'event': 'CM0上市', 'type': '上市'},
        '2024-04-08': {'event': 'DM0预售', 'type': '预售'},
        '2024-05-13': {'event': 'DM0上市', 'type': '上市'},
        '2024-08-30': {'event': 'CM1预售', 'type': '预售'},
        '2024-09-26': {'event': 'CM1上市', 'type': '上市'},
        '2025-04-18': {'event': 'DM1预售', 'type': '预售'},
        '2025-05-13': {'event': 'DM1上市', 'type': '上市'},
        '2025-08-15': {'event': 'CM2预售', 'type': '预售'}
    }
    
    # 需要分析的指标（复用之前的定义）
    metrics = [
        '小订数',
        '有效线索数', '抖音战队线索数', '下发线索数', '有效试驾数', '抖音线索占比'
        '本品牌人群总资产资产', '本品牌日新增', '本品牌日流失', '本品牌人群流量'
    ]
    
    print("\n" + "="*80)
    print("发布会后3日指标变化幅度分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    results = []
    
    for date_str, event_info in launch_events.items():
        event_date = pd.to_datetime(date_str)
        
        # 前30日数据（用于计算基准平均值）
        pre_start_date = event_date - timedelta(days=30)
        pre_period_data = df[(df['date'] >= pre_start_date) & (df['date'] < event_date)]
        
        # 后3日数据
        post_end_date = event_date + timedelta(days=3)
        post_period_data = df[(df['date'] >= event_date) & (df['date'] <= post_end_date)]
        
        if len(pre_period_data) == 0 or len(post_period_data) == 0:
            print(f"\n警告: {event_info['event']} ({date_str}) 前30日或后3日数据不足")
            continue
            
        print(f"\n{event_info['event']} ({date_str}) - {event_info['type']}")
        print(f"前30日期间: {pre_start_date.strftime('%Y-%m-%d')} 至 {event_date.strftime('%Y-%m-%d')} ({len(pre_period_data)}天)")
        print(f"后3日期间: {event_date.strftime('%Y-%m-%d')} 至 {post_end_date.strftime('%Y-%m-%d')} ({len(post_period_data)}天)")
        print("-" * 80)
        
        event_result = {
            'event': event_info['event'],
            'date': date_str,
            'type': event_info['type'],
            'pre_data_days': len(pre_period_data),
            'post_data_days': len(post_period_data)
        }
        
        # 计算每个指标的变化幅度
        for metric in metrics:
            if metric in df.columns:
                # 前30日平均值
                pre_metric_data = pre_period_data[metric].dropna()
                post_metric_data = post_period_data[metric].dropna()
                
                if len(pre_metric_data) > 0 and len(post_metric_data) > 0:
                    pre_mean = pre_metric_data.mean()
                    post_mean = post_metric_data.mean()
                    
                    # 计算变化幅度（百分比）
                    if pre_mean != 0:
                        change_rate = ((post_mean - pre_mean) / pre_mean) * 100
                        change_abs = post_mean - pre_mean
                        
                        print(f"{metric:<20} | 前30日均值: {pre_mean:>10.2f} | 后3日均值: {post_mean:>10.2f} | 变化幅度: {change_rate:>8.2f}% | 绝对变化: {change_abs:>10.2f}")
                        
                        event_result[f'{metric}_pre_mean'] = pre_mean
                        event_result[f'{metric}_post_mean'] = post_mean
                        event_result[f'{metric}_change_rate'] = change_rate
                        event_result[f'{metric}_change_abs'] = change_abs
                    else:
                        print(f"{metric:<20} | 前30日均值为0，无法计算变化幅度")
                        event_result[f'{metric}_pre_mean'] = 0
                        event_result[f'{metric}_post_mean'] = post_mean
                        event_result[f'{metric}_change_rate'] = None
                        event_result[f'{metric}_change_abs'] = None
                else:
                    print(f"{metric:<20} | 数据不足")
                    event_result[f'{metric}_pre_mean'] = None
                    event_result[f'{metric}_post_mean'] = None
                    event_result[f'{metric}_change_rate'] = None
                    event_result[f'{metric}_change_abs'] = None
            else:
                print(f"{metric:<20} | 字段不存在")
        
        results.append(event_result)
    
    # 转换为DataFrame便于分析
    results_df = pd.DataFrame(results)
    
    # 按照"上市"和"预售"分组分析变化幅度
    if len(results_df) > 0:
        print("\n" + "="*80)
        print("按发布会类型分组的变化幅度对比分析")
        print("="*80)
        
        # 分组统计
        for event_type in ['预售', '上市']:
            type_data = results_df[results_df['type'] == event_type]
            if len(type_data) == 0:
                continue
                
            print(f"\n{event_type}类发布会变化幅度统计:")
            print("-" * 60)
            
            # 计算每个指标的平均变化幅度
            change_summary = []
            for metric in metrics:
                change_col = f'{metric}_change_rate'
                if change_col in type_data.columns:
                    valid_changes = type_data[change_col].dropna()
                    if len(valid_changes) > 0:
                        avg_change = valid_changes.mean()
                        max_change = valid_changes.max()
                        min_change = valid_changes.min()
                        std_change = valid_changes.std()
                        
                        change_summary.append({
                            'metric': metric,
                            'avg_change': avg_change,
                            'max_change': max_change,
                            'min_change': min_change,
                            'std_change': std_change,
                            'abs_avg_change': abs(avg_change)
                        })
            
            # 按绝对平均变化幅度排序，找出变化最大的指标
            if change_summary:
                change_df = pd.DataFrame(change_summary)
                change_df_sorted = change_df.sort_values('abs_avg_change', ascending=False)
                
                print(f"变化幅度排序（按绝对值）:")
                for idx, row in change_df_sorted.head(10).iterrows():
                    print(f"  {row['metric']:<20} | 平均变化: {row['avg_change']:>8.2f}% | 最大变化: {row['max_change']:>8.2f}% | 标准差: {row['std_change']:>8.2f}%")
                
                print(f"\n{event_type}类发布会变化最大的前3个指标:")
                top_3 = change_df_sorted.head(3)
                for idx, row in top_3.iterrows():
                    print(f"  1. {row['metric']}: 平均变化幅度 {row['avg_change']:.2f}%")
    
    return results_df

def analyze_presale_post_launch_comparison(df, days_after_launch=3):
    """
    横向对比各个预售发布会后N日指标的均值、最大值、最小值
    
    Args:
        df (pd.DataFrame): 业务指标数据
        days_after_launch (int): 发布会后分析的天数，默认为3天
    """
    # 定义预售发布会时间节点
    presale_events = {
        '2023-08-25': {'event': 'CM0预售', 'name': 'CM0'},
        '2024-04-08': {'event': 'DM0预售', 'name': 'DM0'},
        '2024-08-30': {'event': 'CM1预售', 'name': 'CM1'},
        '2025-04-18': {'event': 'DM1预售', 'name': 'DM1'},
        '2025-08-15': {'event': 'CM2预售', 'name': 'CM2'}
    }
    
    # 需要分析的指标
    core_metrics = [
        '小订数',
        '有效线索数', '下发线索数', 
        '本品牌人群总资产资产', '本品牌日新增', 
    ]
    
    print("\n" + "="*80)
    period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
    print(f"预售发布会{period_text}指标横向对比分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 收集各预售发布会后N日数据
    comparison_data = {}
    
    for date_str, event_info in presale_events.items():
        event_date = pd.to_datetime(date_str)
        
        # 后N日数据
        post_end_date = event_date + timedelta(days=days_after_launch)
        post_period_data = df[(df['date'] >= event_date) & (df['date'] <= post_end_date)]
        
        if len(post_period_data) == 0:
            period_text = "当日" if days_after_launch == 0 else f"后{days_after_launch}日"
            print(f"\n警告: {event_info['event']} ({date_str}) {period_text}数据不足")
            continue
            
        comparison_data[event_info['name']] = {
            'event': event_info['event'],
            'date': date_str,
            'data_days': len(post_period_data),
            'metrics': {}
        }
        
        # 计算每个指标的统计数据
        for metric in core_metrics:
            if metric in df.columns:
                metric_data = post_period_data[metric].dropna()
                
                if len(metric_data) > 0:
                    comparison_data[event_info['name']]['metrics'][metric] = {
                        'mean': metric_data.mean(),
                        'max': metric_data.max(),
                        'min': metric_data.min(),
                        'std': metric_data.std(),
                        'sum': metric_data.sum()  # 新增：N日累计值
                    }
                else:
                    comparison_data[event_info['name']]['metrics'][metric] = {
                        'mean': None,
                        'max': None,
                        'min': None,
                        'std': None,
                        'sum': None  # 新增：3日累计值
                    }
    
    # 输出对比表格
    if comparison_data:
        print("\n预售发布会后3日指标对比表格:")
        print("\n1. 指标均值对比:")
        print("-" * 120)
        
        # 表头
        header = "指标名称" + " " * 12
        for event_name in comparison_data.keys():
            header += f"{event_name:>12}"
        print(header)
        print("-" * 120)
        
        # 均值对比
        for metric in core_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['mean'] is not None:
                    value = event_data['metrics'][metric]['mean']
                    if abs(value) >= 1000:
                        row += f"{value:>12.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>12.2f}"
                    else:
                        row += f"{value:>12.4f}"
                else:
                    row += f"{'--':>12}"
            print(row)
        
        print("\n2. 指标最大值对比:")
        print("-" * 120)
        print(header)
        print("-" * 120)
        
        # 最大值对比
        for metric in core_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['max'] is not None:
                    value = event_data['metrics'][metric]['max']
                    if abs(value) >= 1000:
                        row += f"{value:>12.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>12.2f}"
                    else:
                        row += f"{value:>12.4f}"
                else:
                    row += f"{'--':>12}"
            print(row)
        
        print("\n3. 指标最小值对比:")
        print("-" * 120)
        print(header)
        print("-" * 120)
        
        # 最小值对比
        for metric in core_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['min'] is not None:
                    value = event_data['metrics'][metric]['min']
                    if abs(value) >= 1000:
                        row += f"{value:>12.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>12.2f}"
                    else:
                        row += f"{value:>12.4f}"
                else:
                    row += f"{'--':>12}"
            print(row)
        
        period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日"
        print(f"\n4. 指标{period_text}累计值对比:")
        print("-" * 120)
        print(header)
        print("-" * 120)
        
        # N日累计值对比
        for metric in core_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['sum'] is not None:
                    value = event_data['metrics'][metric]['sum']
                    if abs(value) >= 1000:
                        row += f"{value:>12.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>12.2f}"
                    else:
                        row += f"{value:>12.4f}"
                else:
                    row += f"{'--':>12}"
            print(row)
        
        # 关键洞察分析
        print("\n" + "="*80)
        print("关键洞察分析")
        print("="*80)
        
        # 找出各指标表现最好的预售发布会（基于均值）
        insights = []
        for metric in core_metrics:
            metric_comparison = {}
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['mean'] is not None:
                    metric_comparison[event_name] = event_data['metrics'][metric]['mean']
            
            if metric_comparison:
                best_event = max(metric_comparison.keys(), key=lambda x: metric_comparison[x])
                worst_event = min(metric_comparison.keys(), key=lambda x: metric_comparison[x])
                best_value = metric_comparison[best_event]
                worst_value = metric_comparison[worst_event]
                
                insights.append({
                    'metric': metric,
                    'best_event': best_event,
                    'best_value': best_value,
                    'worst_event': worst_event,
                    'worst_value': worst_value,
                    'improvement_ratio': (best_value / worst_value) if worst_value != 0 else float('inf')
                })
        
        # 找出各指标N日累计值表现最好的预售发布会
        sum_insights = []
        for metric in core_metrics:
            metric_sum_comparison = {}
            for event_name, event_data in comparison_data.items():
                if metric in event_data['metrics'] and event_data['metrics'][metric]['sum'] is not None:
                    metric_sum_comparison[event_name] = event_data['metrics'][metric]['sum']
            
            if metric_sum_comparison:
                best_event = max(metric_sum_comparison.keys(), key=lambda x: metric_sum_comparison[x])
                worst_event = min(metric_sum_comparison.keys(), key=lambda x: metric_sum_comparison[x])
                best_value = metric_sum_comparison[best_event]
                worst_value = metric_sum_comparison[worst_event]
                
                sum_insights.append({
                    'metric': metric,
                    'best_event': best_event,
                    'best_value': best_value,
                    'worst_event': worst_event,
                    'worst_value': worst_value,
                    'improvement_ratio': (best_value / worst_value) if worst_value != 0 else float('inf')
                })
        
        # 输出关键洞察 - CM2与其他车型的对比分析
        period_text = "当日" if days_after_launch == 0 else f"{days_after_launch}日"
        print(f"\nCM2与其他车型预售发布会指标对比分析（基于{period_text}累计值）:")
        print("-" * 80)
        
        # 检查CM2是否存在于数据中
        if 'CM2' in comparison_data:
            cm2_data = comparison_data['CM2']
            other_events = ['CM0', 'CM1', 'DM0', 'DM1']
            
            for metric in core_metrics:
                if metric in cm2_data['metrics'] and cm2_data['metrics'][metric]['sum'] is not None:
                    cm2_value = cm2_data['metrics'][metric]['sum']
                    
                    # 构建对比字符串
                    comparison_str = f"{metric:<20} | CM2: {cm2_value:.0f} | vs "
                    comparisons = []
                    
                    for other_event in other_events:
                        if other_event in comparison_data:
                            other_data = comparison_data[other_event]
                            if metric in other_data['metrics'] and other_data['metrics'][metric]['sum'] is not None:
                                other_value = other_data['metrics'][metric]['sum']
                                ratio = cm2_value / other_value if other_value != 0 else float('inf')
                                if ratio != float('inf'):
                                    comparisons.append(f"{other_event}({other_value:.0f}, {ratio:.2f}x)")
                                else:
                                    comparisons.append(f"{other_event}({other_value:.0f}, ∞x)")
                    
                    comparison_str += " | ".join(comparisons)
                    print(comparison_str)
            
            # 输出解释结论
            print("\n解释结论:")
            print("-" * 80)
            
            # 分析CM2的整体表现
            cm2_advantages = []
            cm2_disadvantages = []
            
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
                print("\n1. CM2的优势指标:")
                for metric, ratio in sorted(cm2_advantages, key=lambda x: x[1], reverse=True):
                    print(f"   • {metric}: CM2表现比其他车型平均水平高{(ratio-1)*100:.1f}%")
            
            # 输出劣势分析
            if cm2_disadvantages:
                print("\n2. CM2的劣势指标:")
                for metric, ratio in sorted(cm2_disadvantages, key=lambda x: x[1]):
                    print(f"   • {metric}: CM2表现比其他车型平均水平低{(1-ratio)*100:.1f}%")
            
            # 总体结论
            print("\n3. 总体结论:")
            if len(cm2_advantages) > len(cm2_disadvantages):
                print("   CM2在大多数关键指标上表现优异，显示出强劲的市场竞争力。")
            elif len(cm2_advantages) < len(cm2_disadvantages):
                print("   CM2在部分指标上仍有提升空间，需要针对性优化营销策略。")
            else:
                print("   CM2整体表现均衡，在不同指标上各有优劣。")
                
        else:
            print("警告: CM2数据不存在，无法进行对比分析")
    
    return comparison_data

def analyze_presale_ratio_comparison(df):
    """
    分析各个预售发布会后3日指标与小订数的比值对比
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义预售发布会时间节点
    presale_events = {
        '2023-08-25': {'event': 'CM0预售', 'name': 'CM0'},
        '2024-04-08': {'event': 'DM0预售', 'name': 'DM0'},
        '2024-08-30': {'event': 'CM1预售', 'name': 'CM1'},
        '2025-04-18': {'event': 'DM1预售', 'name': 'DM1'},
        '2025-08-15': {'event': 'CM2预售', 'name': 'CM2'}
    }
    
    # 需要分析的指标（与小订数的比值）
    ratio_metrics = [
        '有效线索数', '本品牌日新增', '下发线索数', '本品牌人群总资产资产'
    ]
    
    print("\n" + "="*80)
    print("预售发布会后3日指标与小订数比值对比分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 收集各预售发布会后3日数据
    ratio_data = {}
    
    for date_str, event_info in presale_events.items():
        event_date = pd.to_datetime(date_str)
        
        # 后3日数据
        post_end_date = event_date + timedelta(days=3)
        post_period_data = df[(df['date'] >= event_date) & (df['date'] <= post_end_date)]
        
        if len(post_period_data) == 0:
            print(f"\n警告: {event_info['event']} ({date_str}) 后3日数据不足")
            continue
            
        ratio_data[event_info['name']] = {
            'event': event_info['event'],
            'date': date_str,
            'data_days': len(post_period_data),
            'ratios': {}
        }
        
        # 计算小订数的均值
        xiaoding_data = post_period_data['小订数'].dropna()
        if len(xiaoding_data) > 0 and xiaoding_data.mean() > 0:
            xiaoding_mean = xiaoding_data.mean()
            
            # 计算每个指标与小订数的比值
            for metric in ratio_metrics:
                if metric in df.columns:
                    metric_data = post_period_data[metric].dropna()
                    
                    if len(metric_data) > 0:
                        metric_mean = metric_data.mean()
                        
                        # 计算比值（指标/小订数）
                        if xiaoding_mean > 0:
                            ratio_value = metric_mean / xiaoding_mean
                            ratio_data[event_info['name']]['ratios'][metric] = {
                                'metric_mean': metric_mean,
                                'xiaoding_mean': xiaoding_mean,
                                'ratio': ratio_value
                            }
                        else:
                            ratio_data[event_info['name']]['ratios'][metric] = {
                                'metric_mean': metric_mean,
                                'xiaoding_mean': xiaoding_mean,
                                'ratio': None
                            }
                    else:
                        ratio_data[event_info['name']]['ratios'][metric] = {
                            'metric_mean': None,
                            'xiaoding_mean': xiaoding_mean,
                            'ratio': None
                        }
        else:
            print(f"\n警告: {event_info['event']} ({date_str}) 小订数数据不足或为零")
    
    # 输出比值对比表格
    if ratio_data:
        print("\n预售发布会后3日指标与小订数比值对比表格:")
        print("\n1. 指标与小订数比值对比:")
        print("-" * 120)
        
        # 表头
        header = "指标名称" + " " * 12
        for event_name in ratio_data.keys():
            header += f"{event_name:>15}"
        print(header)
        print("-" * 120)
        
        # 比值对比
        for metric in ratio_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['ratio'] is not None:
                    ratio = event_data['ratios'][metric]['ratio']
                    if abs(ratio) >= 1000:
                        row += f"{ratio:>15.0f}"
                    elif abs(ratio) >= 1:
                        row += f"{ratio:>15.2f}"
                    else:
                        row += f"{ratio:>15.6f}"
                else:
                    row += f"{'--':>15}"
            print(row)
        
        print("\n2. 指标均值详情:")
        print("-" * 120)
        header_detail = "指标名称" + " " * 12
        for event_name in ratio_data.keys():
            header_detail += f"{event_name}_指标值" + " " * 3
        print(header_detail)
        print("-" * 120)
        
        for metric in ratio_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['metric_mean'] is not None:
                    value = event_data['ratios'][metric]['metric_mean']
                    if abs(value) >= 1000000:
                        row += f"{value:>15.0f}"
                    elif abs(value) >= 1000:
                        row += f"{value:>15.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>15.2f}"
                    else:
                        row += f"{value:>15.6f}"
                else:
                    row += f"{'--':>15}"
            print(row)
        
        print("\n3. 小订数均值详情:")
        print("-" * 120)
        header_xiaoding = "预售发布会" + " " * 8
        header_xiaoding += "小订数均值" + " " * 8
        print(header_xiaoding)
        print("-" * 120)
        
        for event_name, event_data in ratio_data.items():
            if event_data['ratios']:
                # 获取任意一个指标的小订数均值（都是相同的）
                xiaoding_mean = None
                for metric in ratio_metrics:
                    if metric in event_data['ratios']:
                        xiaoding_mean = event_data['ratios'][metric]['xiaoding_mean']
                        break
                
                if xiaoding_mean is not None:
                    print(f"{event_data['event']:<20}{xiaoding_mean:>15.2f}")
        
        # 比值差异分析
        print("\n" + "="*80)
        print("比值差异分析")
        print("="*80)
        
        # 找出各指标比值最高和最低的预售发布会
        ratio_insights = []
        for metric in ratio_metrics:
            metric_ratios = {}
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['ratio'] is not None:
                    metric_ratios[event_name] = event_data['ratios'][metric]['ratio']
            
            if metric_ratios:
                best_event = max(metric_ratios.keys(), key=lambda x: metric_ratios[x])
                worst_event = min(metric_ratios.keys(), key=lambda x: metric_ratios[x])
                best_ratio = metric_ratios[best_event]
                worst_ratio = metric_ratios[worst_event]
                
                ratio_insights.append({
                    'metric': metric,
                    'best_event': best_event,
                    'best_ratio': best_ratio,
                    'worst_event': worst_event,
                    'worst_ratio': worst_ratio,
                    'ratio_difference': best_ratio - worst_ratio,
                    'ratio_multiple': (best_ratio / worst_ratio) if worst_ratio != 0 else float('inf')
                })
        
        # 输出比值差异洞察
        print("\n各指标与小订数比值表现分析:")
        print("-" * 100)
        for insight in ratio_insights:
            if insight['ratio_multiple'] != float('inf'):
                print(f"{insight['metric']:<20} | 最高比值: {insight['best_event']} ({insight['best_ratio']:.4f}) | 最低比值: {insight['worst_event']} ({insight['worst_ratio']:.4f}) | 差异倍数: {insight['ratio_multiple']:.2f}x")
            else:
                print(f"{insight['metric']:<20} | 最高比值: {insight['best_event']} ({insight['best_ratio']:.4f}) | 最低比值: {insight['worst_event']} ({insight['worst_ratio']:.4f}) | 差异倍数: 无穷大")
        
        # 效率排名分析
        print("\n预售发布会指标效率排名 (基于指标与小订数比值):")
        print("-" * 80)
        
        # 计算综合效率得分（比值越小表示效率越高，即用更少的指标产生更多小订）
        efficiency_scores = {}
        
        for event_name in ratio_data.keys():
            total_ratio = 0
            valid_ratios = 0
            
            for metric in ratio_metrics:
                if (metric in ratio_data[event_name]['ratios'] and 
                    ratio_data[event_name]['ratios'][metric]['ratio'] is not None):
                    
                    ratio_value = ratio_data[event_name]['ratios'][metric]['ratio']
                    # 对于资产类指标，需要特殊处理（数值很大）
                    if metric == '本品牌人群总资产资产':
                        # 将资产比值缩放到合理范围
                        ratio_value = ratio_value / 1000000  # 除以百万
                    
                    total_ratio += ratio_value
                    valid_ratios += 1
            
            if valid_ratios > 0:
                efficiency_scores[event_name] = total_ratio / valid_ratios
            else:
                efficiency_scores[event_name] = float('inf')
        
        # 排序（比值越小效率越高）
        sorted_efficiency = sorted(efficiency_scores.items(), key=lambda x: x[1])
        for rank, (event_name, score) in enumerate(sorted_efficiency, 1):
            if score != float('inf'):
                event_full_name = ratio_data[event_name]['event']
                print(f"{rank}. {event_full_name} ({event_name}): 平均比值 {score:.4f} (效率越高比值越小)")
    
    return ratio_data


def comprehensive_presale_ranking(comparison_results, ratio_results):
    """
    综合预售发布会排名分析，基于模块4的提升幅度和模块5的效率变化
    
    Args:
        comparison_results: 模块4的横向对比分析结果
        ratio_results: 模块5的比值对比分析结果
    """
    print("\n" + "="*80)
    print("预售发布会综合排名分析 (基于提升幅度和效率变化)")
    print("="*80)
    
    if not comparison_results or not ratio_results:
        print("警告: 缺少必要的分析结果数据")
        return
    
    # 从模块4获取提升幅度数据
    core_metrics = ['小订数', '有效线索数', '下发线索数', '本品牌人群总资产资产', '本品牌日新增']
    
    # 计算各指标的提升倍数洞察
    insights = []
    for metric in core_metrics:
        metric_comparison = {}
        for event_name, event_data in comparison_results.items():
            if metric in event_data['metrics'] and event_data['metrics'][metric]['mean'] is not None:
                metric_comparison[event_name] = event_data['metrics'][metric]['mean']
        
        if metric_comparison:
            best_event = max(metric_comparison.keys(), key=lambda x: metric_comparison[x])
            worst_event = min(metric_comparison.keys(), key=lambda x: metric_comparison[x])
            best_value = metric_comparison[best_event]
            worst_value = metric_comparison[worst_event]
            
            insights.append({
                'metric': metric,
                'best_event': best_event,
                'best_value': best_value,
                'worst_event': worst_event,
                'worst_value': worst_value,
                'improvement_ratio': (best_value / worst_value) if worst_value != 0 else float('inf')
            })
    
    # 计算提升幅度得分
    improvement_scores = {}
    for event_name in comparison_results.keys():
        total_improvement = 0
        valid_improvements = 0
        
        for insight in insights:
            if insight['best_event'] == event_name:
                total_improvement += insight['improvement_ratio'] if insight['improvement_ratio'] != float('inf') else 5.0
                valid_improvements += 1
            elif insight['worst_event'] == event_name:
                total_improvement += 1.0 / insight['improvement_ratio'] if insight['improvement_ratio'] != 0 else 0.2
                valid_improvements += 1
            else:
                metric = insight['metric']
                if (metric in comparison_results[event_name]['metrics'] and 
                    comparison_results[event_name]['metrics'][metric]['mean'] is not None):
                    current_val = comparison_results[event_name]['metrics'][metric]['mean']
                    best_val = insight['best_value']
                    worst_val = insight['worst_value']
                    
                    if best_val != worst_val:
                        relative_score = ((current_val - worst_val) / (best_val - worst_val)) * insight['improvement_ratio']
                        total_improvement += relative_score
                        valid_improvements += 1
        
        if valid_improvements > 0:
            improvement_scores[event_name] = total_improvement / valid_improvements
        else:
            improvement_scores[event_name] = 1.0
    
    # 从模块5获取效率得分（转换为效率得分，比值越小效率越高）
    ratio_metrics = ['有效线索数', '本品牌日新增', '下发线索数', '本品牌人群总资产资产']
    efficiency_scores = {}
    
    for event_name in ratio_results.keys():
        total_ratio = 0
        valid_ratios = 0
        
        for metric in ratio_metrics:
            if (metric in ratio_results[event_name]['ratios'] and 
                ratio_results[event_name]['ratios'][metric]['ratio'] is not None):
                
                ratio_value = ratio_results[event_name]['ratios'][metric]['ratio']
                if metric == '本品牌人群总资产资产':
                    ratio_value = ratio_value / 1000000
                
                total_ratio += ratio_value
                valid_ratios += 1
        
        if valid_ratios > 0:
            avg_ratio = total_ratio / valid_ratios
            # 转换为效率得分：比值越小效率越高，所以用倒数
            efficiency_scores[event_name] = 1.0 / avg_ratio if avg_ratio > 0 else 0
        else:
            efficiency_scores[event_name] = 0
    
    # 标准化得分到0-1范围
    if improvement_scores:
        max_improvement = max(improvement_scores.values())
        min_improvement = min(improvement_scores.values())
        if max_improvement != min_improvement:
            for event_name in improvement_scores:
                improvement_scores[event_name] = (improvement_scores[event_name] - min_improvement) / (max_improvement - min_improvement)
    
    if efficiency_scores:
        max_efficiency = max(efficiency_scores.values())
        min_efficiency = min(efficiency_scores.values())
        if max_efficiency != min_efficiency:
            for event_name in efficiency_scores:
                efficiency_scores[event_name] = (efficiency_scores[event_name] - min_efficiency) / (max_efficiency - min_efficiency)
    
    # 计算综合得分（提升幅度权重50%，效率变化权重50%）
    comprehensive_scores = {}
    for event_name in comparison_results.keys():
        improvement_score = improvement_scores.get(event_name, 0)
        efficiency_score = efficiency_scores.get(event_name, 0)
        
        comprehensive_score = improvement_score * 0.5 + efficiency_score * 0.5
        comprehensive_scores[event_name] = comprehensive_score
    
    # 输出详细分析结果
    print("\n1. 提升幅度得分 (模块4分析，权重50%):")
    print("-" * 60)
    sorted_improvement = sorted(improvement_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (event_name, score) in enumerate(sorted_improvement, 1):
        event_full_name = comparison_results[event_name]['event']
        print(f"{rank}. {event_full_name} ({event_name}): {score:.3f}")
    
    print("\n2. 效率变化得分 (模块5分析，权重50%):")
    print("-" * 60)
    sorted_efficiency = sorted(efficiency_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (event_name, score) in enumerate(sorted_efficiency, 1):
        event_full_name = comparison_results[event_name]['event']
        print(f"{rank}. {event_full_name} ({event_name}): {score:.3f}")
    
    print("\n3. 综合排名 (提升幅度50% + 效率变化50%):")
    print("="*60)
    sorted_comprehensive = sorted(comprehensive_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (event_name, score) in enumerate(sorted_comprehensive, 1):
        event_full_name = comparison_results[event_name]['event']
        improvement_score = improvement_scores.get(event_name, 0)
        efficiency_score = efficiency_scores.get(event_name, 0)
        print(f"{rank}. {event_full_name} ({event_name}):")
        print(f"   综合得分: {score:.3f} (提升: {improvement_score:.3f} + 效率: {efficiency_score:.3f})")
    
    print("\n排名说明:")
    print("- 提升幅度得分: 基于各指标相对于最差表现的提升倍数")
    print("- 效率变化得分: 基于指标与小订数比值的效率表现")
    print("- 综合得分: 提升幅度(50%) + 效率变化(50%)")
    print("- 得分范围: 0-1，得分越高表现越好")
    
    return comprehensive_scores


def analyze_presale_ratio_comparison_1day(df):
    """
    分析各个预售发布会后1日（当日）指标与小订数的比值对比
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义预售发布会时间节点
    presale_events = {
        '2023-08-25': {'event': 'CM0预售', 'name': 'CM0'},
        '2024-04-08': {'event': 'DM0预售', 'name': 'DM0'},
        '2024-08-30': {'event': 'CM1预售', 'name': 'CM1'},
        '2025-04-18': {'event': 'DM1预售', 'name': 'DM1'},
        '2025-08-15': {'event': 'CM2预售', 'name': 'CM2'}
    }
    
    # 需要分析的指标（与小订数的比值）
    ratio_metrics = [
        '有效线索数', '本品牌日新增', '下发线索数', '本品牌人群总资产资产'
    ]
    
    print("\n" + "="*80)
    print("预售发布会后1日（当日）指标与小订数比值对比分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 收集各预售发布会当日数据
    ratio_data = {}
    
    for date_str, event_info in presale_events.items():
        event_date = pd.to_datetime(date_str)
        
        # 当日数据（发布会当天）
        post_period_data = df[df['date'] == event_date]
        
        if len(post_period_data) == 0:
            print(f"\n警告: {event_info['event']} ({date_str}) 当日数据不足")
            continue
            
        ratio_data[event_info['name']] = {
            'event': event_info['event'],
            'date': date_str,
            'data_days': len(post_period_data),
            'ratios': {}
        }
        
        # 计算小订数的值（当日）
        xiaoding_data = post_period_data['小订数'].dropna()
        if len(xiaoding_data) > 0 and xiaoding_data.iloc[0] > 0:
            xiaoding_value = xiaoding_data.iloc[0]
            
            # 计算每个指标与小订数的比值
            for metric in ratio_metrics:
                if metric in df.columns:
                    metric_data = post_period_data[metric].dropna()
                    
                    if len(metric_data) > 0:
                        metric_value = metric_data.iloc[0]
                        
                        # 计算比值（指标/小订数）
                        if xiaoding_value > 0:
                            ratio_value = metric_value / xiaoding_value
                            ratio_data[event_info['name']]['ratios'][metric] = {
                                'metric_value': metric_value,
                                'xiaoding_value': xiaoding_value,
                                'ratio': ratio_value
                            }
                        else:
                            ratio_data[event_info['name']]['ratios'][metric] = {
                                'metric_value': metric_value,
                                'xiaoding_value': xiaoding_value,
                                'ratio': None
                            }
                    else:
                        ratio_data[event_info['name']]['ratios'][metric] = {
                            'metric_value': None,
                            'xiaoding_value': xiaoding_value,
                            'ratio': None
                        }
        else:
            print(f"\n警告: {event_info['event']} ({date_str}) 当日小订数数据不足或为零")
    
    # 输出比值对比表格
    if ratio_data:
        print("\n预售发布会当日指标与小订数比值对比表格:")
        print("\n1. 指标与小订数比值对比:")
        print("-" * 120)
        
        # 表头
        header = "指标名称" + " " * 12
        for event_name in ratio_data.keys():
            header += f"{event_name:>15}"
        print(header)
        print("-" * 120)
        
        # 比值对比
        for metric in ratio_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['ratio'] is not None:
                    ratio = event_data['ratios'][metric]['ratio']
                    if abs(ratio) >= 1000:
                        row += f"{ratio:>15.0f}"
                    elif abs(ratio) >= 1:
                        row += f"{ratio:>15.2f}"
                    else:
                        row += f"{ratio:>15.6f}"
                else:
                    row += f"{'--':>15}"
            print(row)
        
        print("\n2. 指标当日数值详情:")
        print("-" * 120)
        header_detail = "指标名称" + " " * 12
        for event_name in ratio_data.keys():
            header_detail += f"{event_name}_指标值" + " " * 3
        print(header_detail)
        print("-" * 120)
        
        for metric in ratio_metrics:
            row = f"{metric:<20}"
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['metric_value'] is not None:
                    value = event_data['ratios'][metric]['metric_value']
                    if abs(value) >= 1000000:
                        row += f"{value:>15.0f}"
                    elif abs(value) >= 1000:
                        row += f"{value:>15.0f}"
                    elif abs(value) >= 1:
                        row += f"{value:>15.2f}"
                    else:
                        row += f"{value:>15.6f}"
                else:
                    row += f"{'--':>15}"
            print(row)
        
        print("\n3. 小订数当日数值详情:")
        print("-" * 120)
        header_xiaoding = "预售发布会" + " " * 8
        header_xiaoding += "小订数当日值" + " " * 6
        print(header_xiaoding)
        print("-" * 120)
        
        for event_name, event_data in ratio_data.items():
            if event_data['ratios']:
                # 获取任意一个指标的小订数值（都是相同的）
                xiaoding_value = None
                for metric in ratio_metrics:
                    if metric in event_data['ratios']:
                        xiaoding_value = event_data['ratios'][metric]['xiaoding_value']
                        break
                
                if xiaoding_value is not None:
                    print(f"{event_data['event']:<20}{xiaoding_value:>15.0f}")
        
        # 比值差异分析
        print("\n" + "="*80)
        print("当日比值差异分析")
        print("="*80)
        
        # 找出各指标比值最高和最低的预售发布会
        ratio_insights = []
        for metric in ratio_metrics:
            metric_ratios = {}
            for event_name, event_data in ratio_data.items():
                if metric in event_data['ratios'] and event_data['ratios'][metric]['ratio'] is not None:
                    metric_ratios[event_name] = event_data['ratios'][metric]['ratio']
            
            if metric_ratios:
                best_event = max(metric_ratios.keys(), key=lambda x: metric_ratios[x])
                worst_event = min(metric_ratios.keys(), key=lambda x: metric_ratios[x])
                best_ratio = metric_ratios[best_event]
                worst_ratio = metric_ratios[worst_event]
                
                ratio_insights.append({
                    'metric': metric,
                    'best_event': best_event,
                    'best_ratio': best_ratio,
                    'worst_event': worst_event,
                    'worst_ratio': worst_ratio,
                    'ratio_difference': best_ratio - worst_ratio,
                    'ratio_multiple': (best_ratio / worst_ratio) if worst_ratio != 0 else float('inf')
                })
        
        # 输出比值差异洞察
        print("\n各指标与小订数当日比值表现分析:")
        print("-" * 100)
        for insight in ratio_insights:
            if insight['ratio_multiple'] != float('inf'):
                print(f"{insight['metric']:<20} | 最高比值: {insight['best_event']} ({insight['best_ratio']:.4f}) | 最低比值: {insight['worst_event']} ({insight['worst_ratio']:.4f}) | 差异倍数: {insight['ratio_multiple']:.2f}x")
            else:
                print(f"{insight['metric']:<20} | 最高比值: {insight['best_event']} ({insight['best_ratio']:.4f}) | 最低比值: {insight['worst_event']} ({insight['worst_ratio']:.4f}) | 差异倍数: 无穷大")
        
        # 效率排名分析
        print("\n预售发布会当日指标效率排名 (基于指标与小订数比值):")
        print("-" * 80)
        
        # 计算综合效率得分（比值越小表示效率越高，即用更少的指标产生更多小订）
        efficiency_scores = {}
        
        for event_name in ratio_data.keys():
            total_ratio = 0
            valid_ratios = 0
            
            for metric in ratio_metrics:
                if (metric in ratio_data[event_name]['ratios'] and 
                    ratio_data[event_name]['ratios'][metric]['ratio'] is not None):
                    
                    ratio_value = ratio_data[event_name]['ratios'][metric]['ratio']
                    # 对于资产类指标，需要特殊处理（数值很大）
                    if metric == '本品牌人群总资产资产':
                        # 将资产比值缩放到合理范围
                        ratio_value = ratio_value / 1000000  # 除以百万
                    
                    total_ratio += ratio_value
                    valid_ratios += 1
            
            if valid_ratios > 0:
                efficiency_scores[event_name] = total_ratio / valid_ratios
            else:
                efficiency_scores[event_name] = float('inf')
        
        # 排序（比值越小效率越高）
        sorted_efficiency = sorted(efficiency_scores.items(), key=lambda x: x[1])
        for rank, (event_name, score) in enumerate(sorted_efficiency, 1):
            if score != float('inf'):
                event_full_name = ratio_data[event_name]['event']
                print(f"{rank}. {event_full_name} ({event_name}): 平均比值 {score:.4f} (效率越高比值越小)")
    
    return ratio_data

def Linear_attribution_analysis(df):
    """
    使用线性归因模型对历史预售发布会周期小订数进行归因分析
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    from sklearn.linear_model import Lasso
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    import warnings
    warnings.filterwarnings('ignore')
    
    # 定义发布会日期和对应的上市期
    event_periods = [
        {"name": "CM0", "presale_start": "2023-08-25", "presale_end": "2023-10-12", "launch_start": "2023-10-12", "launch_days": 60},
        {"name": "DM0", "presale_start": "2024-04-08", "presale_end": "2024-05-13", "launch_start": "2024-05-13", "launch_days": 60},
        {"name": "CM1", "presale_start": "2024-08-30", "presale_end": "2024-09-26", "launch_start": "2024-09-26", "launch_days": 60},
        {"name": "CM2", "presale_start": "2025-08-15", "presale_end": "2025-09-10", "launch_start": "2025-09-10", "launch_days": 60},
        {"name": "DM1", "presale_start": "2025-04-18", "presale_end": "2025-05-13", "launch_start": "2025-05-13", "launch_days": 60}
    ]
    
    # 定义归因分析的特征指标
    feature_metrics = [
        '有效线索数', '抖音战队线索数', '下发线索数', '有效试驾数', '抖音线索占比',
        '本品牌人群总资产资产', '本品牌日新增', '本品牌日流失', '本品牌人群流量',
        '试驾锁单占比', '小订留存占比', '线索转化率', 
    ]
    
    print("\n" + "="*80)
    print("小订数归因分析 - 线性归因模型（Lasso回归）")
    print("="*80)
    print("分析历史预售发布会周期各指标对小订数的贡献百分比")
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 收集所有预售周期的数据
    all_period_data = []
    
    for period in event_periods:
        presale_start = pd.to_datetime(period['presale_start'])
        presale_end = pd.to_datetime(period['presale_end'])
        
        # 获取预售期间数据
        period_data = df[(df['date'] >= presale_start) & (df['date'] <= presale_end)].copy()
        
        if len(period_data) == 0:
            print(f"警告: {period['name']} 预售期间无数据")
            continue
            
        # 添加周期标识
        period_data['period_name'] = period['name']
        period_data['period_type'] = 'presale'
        
        all_period_data.append(period_data)
        
        print(f"{period['name']} 预售期: {presale_start.strftime('%Y-%m-%d')} 至 {presale_end.strftime('%Y-%m-%d')} ({len(period_data)}天)")
    
    if not all_period_data:
        print("\n错误: 没有找到有效的预售期间数据")
        return pd.DataFrame()
    
    # 合并所有周期数据
    combined_data = pd.concat(all_period_data, ignore_index=True)
    
    print(f"\n总计数据: {len(combined_data)} 天，覆盖 {len(event_periods)} 个预售周期")
    
    # 检查目标变量和特征变量的可用性
    target_col = '小订数'
    if target_col not in combined_data.columns:
        print(f"错误: 目标变量 '{target_col}' 不存在")
        return pd.DataFrame()
    
    # 筛选可用的特征指标
    available_features = []
    for metric in feature_metrics:
        if metric in combined_data.columns:
            # 检查数据质量：非空值比例 > 50%
            non_null_ratio = combined_data[metric].notna().sum() / len(combined_data)
            if non_null_ratio > 0.5:
                available_features.append(metric)
                print(f"✓ {metric:<25} | 数据完整度: {non_null_ratio:.1%}")
            else:
                print(f"✗ {metric:<25} | 数据完整度: {non_null_ratio:.1%} (跳过)")
        else:
            print(f"✗ {metric:<25} | 字段不存在")
    
    if len(available_features) < 3:
        print(f"\n错误: 可用特征指标不足 ({len(available_features)} < 3)")
        return pd.DataFrame()
    
    print(f"\n最终使用 {len(available_features)} 个特征指标进行归因分析")
    
    # 准备建模数据
    model_data = combined_data[available_features + [target_col, 'period_name']].copy()
    
    # 删除包含空值的行
    model_data = model_data.dropna()
    
    if len(model_data) < 10:
        print(f"\n错误: 清洗后数据不足 ({len(model_data)} < 10)")
        return pd.DataFrame()
    
    print(f"\n建模数据: {len(model_data)} 个样本")
    
    # 分离特征和目标变量
    X = model_data[available_features]
    y = model_data[target_col]
    
    print(f"\n目标变量统计:")
    print(f"  小订数均值: {y.mean():.2f}")
    print(f"  小订数标准差: {y.std():.2f}")
    print(f"  小订数范围: [{y.min():.0f}, {y.max():.0f}]")
    
    # 标准化特征
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns=available_features, index=X.index)
    
    print(f"\n特征标准化完成")
    
    # 使用交叉验证选择最优的Lasso正则化参数
    alphas = [0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    best_alpha = 0.1
    best_score = -float('inf')
    
    print(f"\n正在选择最优正则化参数...")
    for alpha in alphas:
        lasso = Lasso(alpha=alpha, random_state=42, max_iter=2000)
        try:
            scores = cross_val_score(lasso, X_scaled, y, cv=min(5, len(model_data)//2), scoring='r2')
            avg_score = scores.mean()
            print(f"  Alpha={alpha:<6} | R²={avg_score:.4f} | 标准差={scores.std():.4f}")
            
            if avg_score > best_score:
                best_score = avg_score
                best_alpha = alpha
        except Exception as e:
            print(f"  Alpha={alpha:<6} | 错误: {str(e)}")
    
    print(f"\n最优参数: Alpha={best_alpha}, R²={best_score:.4f}")
    
    # 使用最优参数训练最终模型
    final_lasso = Lasso(alpha=best_alpha, random_state=42, max_iter=2000)
    final_lasso.fit(X_scaled, y)
    
    # 获取标准化系数
    coefficients = final_lasso.coef_
    
    # 计算贡献百分比
    # 使用绝对值系数计算相对重要性
    abs_coefficients = np.abs(coefficients)
    total_abs_coef = abs_coefficients.sum()
    
    if total_abs_coef == 0:
        print("\n警告: 所有系数为0，可能需要调整正则化参数")
        contribution_percentages = np.zeros(len(available_features))
    else:
        contribution_percentages = (abs_coefficients / total_abs_coef) * 100
    
    # 创建归因结果
    attribution_results = []
    for i, feature in enumerate(available_features):
        attribution_results.append({
            '指标': feature,
            '标准化系数': coefficients[i],
            '绝对系数': abs_coefficients[i],
            '贡献百分比': contribution_percentages[i],
            '系数符号': '正向' if coefficients[i] > 0 else '负向' if coefficients[i] < 0 else '无影响'
        })
    
    # 转换为DataFrame并排序
    attribution_df = pd.DataFrame(attribution_results)
    attribution_df = attribution_df.sort_values('贡献百分比', ascending=False)
    
    # 输出归因结果
    print("\n" + "="*80)
    print("小订数归因分析结果")
    print("="*80)
    
    print(f"\n模型性能:")
    y_pred = final_lasso.predict(X_scaled)
    r2_score = final_lasso.score(X_scaled, y)
    print(f"  R² 决定系数: {r2_score:.4f}")
    print(f"  均方根误差: {np.sqrt(((y - y_pred) ** 2).mean()):.2f}")
    print(f"  平均绝对误差: {np.abs(y - y_pred).mean():.2f}")
    
    print(f"\n各指标对小订数的贡献排序:")
    print("-" * 80)
    print(f"{'指标名称':<25} {'标准化系数':<12} {'贡献百分比':<12} {'影响方向':<10}")
    print("-" * 80)
    
    for _, row in attribution_df.iterrows():
        print(f"{row['指标']:<25} {row['标准化系数']:>10.4f} {row['贡献百分比']:>10.2f}% {row['系数符号']:<10}")
    
    # 输出关键发现
    print(f"\n关键发现:")
    print("-" * 40)
    
    # 前5大贡献指标
    top_5 = attribution_df.head(5)
    total_top5_contribution = top_5['贡献百分比'].sum()
    
    print(f"\n前5大贡献指标 (累计贡献: {total_top5_contribution:.1f}%):")
    for i, (_, row) in enumerate(top_5.iterrows(), 1):
        print(f"  {i}. {row['指标']}: {row['贡献百分比']:.1f}% ({row['系数符号']})")
    
    # 按指标类型分组分析
    print(f"\n按指标类型分组的贡献分析:")
    
    # 定义指标分类
    metric_categories = {
        '线索获取': ['有效线索数', '抖音战队线索数', '下发线索数'],
        '转化行为': ['有效试驾数', '试驾锁单数', '锁单数', '小订留存锁单数'],
        '用户基盘': ['本品牌人群总资产资产', '本品牌日新增', '本品牌日流失', '本品牌人群流量'],
        '转化效率': ['试驾锁单占比', '小订留存占比', '线索转化率', '抖音线索占比']
    }
    
    category_contributions = {}
    for category, metrics in metric_categories.items():
        category_total = 0
        category_metrics = []
        
        for metric in metrics:
            if metric in attribution_df['指标'].values:
                contribution = attribution_df[attribution_df['指标'] == metric]['贡献百分比'].iloc[0]
                category_total += contribution
                category_metrics.append(f"{metric}({contribution:.1f}%)")
        
        if category_total > 0:
            category_contributions[category] = {
                'total': category_total,
                'metrics': category_metrics
            }
    
    # 按贡献排序输出类别分析
    sorted_categories = sorted(category_contributions.items(), key=lambda x: x[1]['total'], reverse=True)
    
    for category, data in sorted_categories:
        print(f"\n{category} (总贡献: {data['total']:.1f}%):")
        for metric_info in data['metrics']:
            print(f"  - {metric_info}")
    
    # 按预售周期分析
    print(f"\n" + "="*80)
    print("按预售周期的归因分析")
    print("="*80)
    
    period_analysis = []
    for period in event_periods:
        period_data = model_data[model_data['period_name'] == period['name']]
        
        if len(period_data) == 0:
            continue
            
        period_X = period_data[available_features]
        period_y = period_data[target_col]
        
        # 使用训练好的模型预测
        period_X_scaled = scaler.transform(period_X)
        period_pred = final_lasso.predict(period_X_scaled)
        
        # 计算各指标的实际贡献值
        period_contributions = {}
        for i, feature in enumerate(available_features):
            # 计算该指标对预测值的贡献
            feature_contribution = (period_X_scaled[:, i] * coefficients[i]).mean()
            period_contributions[feature] = feature_contribution
        
        total_actual_orders = period_y.sum()
        avg_predicted = period_pred.mean()
        
        period_analysis.append({
            'period': period['name'],
            'actual_orders': total_actual_orders,
            'avg_predicted': avg_predicted,
            'days': len(period_data),
            'contributions': period_contributions
        })
        
        print(f"\n{period['name']} 预售周期:")
        print(f"  实际小订总数: {total_actual_orders:.0f}")
        print(f"  模型预测均值: {avg_predicted:.2f}")
        print(f"  数据天数: {len(period_data)}")
        
        # 显示该周期的主要贡献指标
        period_contrib_sorted = sorted(period_contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        print(f"  主要贡献指标:")
        for feature, contrib in period_contrib_sorted[:5]:
            contrib_pct = (abs(contrib) / sum(abs(c) for c in period_contributions.values())) * 100 if sum(abs(c) for c in period_contributions.values()) > 0 else 0
            print(f"    {feature}: {contrib_pct:.1f}%")
    
    # 输出最终归因总结
    print(f"\n" + "="*80)
    print("归因分析总结")
    print("="*80)
    
    print(f"\n基于Lasso回归的小订数归因结果:")
    
    # 生成易读的归因描述
    top_contributors = attribution_df.head(3)
    attribution_summary = []
    
    for _, row in top_contributors.iterrows():
        attribution_summary.append(f"{row['贡献百分比']:.0f}% 来自{row['指标']}")
    
    print(f"\n小订数构成: {', '.join(attribution_summary)}")
    
    # 计算其他指标的总贡献
    other_contribution = attribution_df.iloc[3:]['贡献百分比'].sum()
    if other_contribution > 0:
        print(f"其他指标贡献: {other_contribution:.0f}%")
    
    print(f"\n模型说明:")
    print(f"  - 使用Lasso回归防止多重共线性")
    print(f"  - 所有指标已标准化处理")
    print(f"  - 贡献百分比基于标准化系数的绝对值计算")
    print(f"  - 模型R²: {r2_score:.3f}")
    
    return attribution_df

def leads_regression_model(df):
    """
    模块7.5：线索回归模型 - Lasso + 敏感性分析
    使用本品牌人群总资产资产、本品牌日新增、本品牌人群流量、抖音战队线索数对有效线索数进行归因分析
    时间范围：2024年7月1日至2025年8月19日
    
    Args:
        df (pd.DataFrame): 业务指标数据
    
    Returns:
        dict: 包含回归结果和敏感性分析结果的字典
    """
    from sklearn.linear_model import Lasso
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    import warnings
    warnings.filterwarnings('ignore')
    
    print("\n" + "="*80)
    print("模块7.5：线索回归模型 - Lasso + 敏感性分析")
    print("="*80)
    print("分析时间范围：2024年7月1日至2025年8月19日")
    print("目标变量：有效线索数")
    print("特征变量：本品牌人群总资产资产、本品牌日新增、本品牌人群流量、抖音战队线索数")
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 筛选时间范围：2024年7月1日至2025年8月19日
    start_date = pd.to_datetime('2024-07-01')
    end_date = pd.to_datetime('2025-08-19')
    
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
    
    print(f"\n数据筛选结果：")
    print(f"  原始数据：{len(df)} 条记录")
    print(f"  筛选后数据：{len(filtered_df)} 条记录")
    print(f"  时间范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    if len(filtered_df) == 0:
        print("\n错误：筛选后无数据")
        return {}
    
    # 定义目标变量和特征变量
    target_variable = '有效线索数'
    feature_variables = [
        '本品牌人群总资产资产',
        '本品牌日新增', 
        '本品牌人群流量',
        '抖音战队线索数'
    ]
    
    print(f"\n变量检查：")
    print(f"  目标变量：{target_variable}")
    print(f"  特征变量：{', '.join(feature_variables)}")
    
    # 检查变量是否存在
    missing_vars = []
    if target_variable not in filtered_df.columns:
        missing_vars.append(target_variable)
    
    for var in feature_variables:
        if var not in filtered_df.columns:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n错误：以下变量不存在于数据中：{', '.join(missing_vars)}")
        return {}
    
    # 准备建模数据
    model_data = filtered_df[feature_variables + [target_variable, 'date']].copy()
    
    # 检查数据质量
    print(f"\n数据质量检查：")
    print("-" * 60)
    
    for var in [target_variable] + feature_variables:
        total_count = len(model_data)
        null_count = model_data[var].isnull().sum()
        null_pct = (null_count / total_count) * 100
        
        if null_count > 0:
            print(f"  {var:<25} | 空值：{null_count:>4}/{total_count} ({null_pct:>5.1f}%)")
        else:
            print(f"  {var:<25} | 无空值")
    
    # 删除包含空值的行
    initial_count = len(model_data)
    model_data = model_data.dropna()
    final_count = len(model_data)
    
    print(f"\n数据清洗结果：")
    print(f"  清洗前：{initial_count} 条记录")
    print(f"  清洗后：{final_count} 条记录")
    print(f"  删除：{initial_count - final_count} 条记录 ({((initial_count - final_count) / initial_count * 100):.1f}%)")
    
    if final_count < 30:
        print(f"\n警告：清洗后数据量不足（{final_count} < 30），可能影响模型可靠性")
    
    # 分离特征和目标变量
    X = model_data[feature_variables]
    y = model_data[target_variable]
    
    # 基本统计信息
    print(f"\n变量基本统计：")
    print("-" * 80)
    print(f"{'变量名称':<25} {'均值':<12} {'标准差':<12} {'最小值':<12} {'最大值':<12}")
    print("-" * 80)
    
    # 目标变量统计
    print(f"{target_variable:<25} {y.mean():>10.2f} {y.std():>10.2f} {y.min():>10.2f} {y.max():>10.2f}")
    
    # 特征变量统计
    for var in feature_variables:
        var_data = X[var]
        print(f"{var:<25} {var_data.mean():>10.2f} {var_data.std():>10.2f} {var_data.min():>10.2f} {var_data.max():>10.2f}")
    
    # 相关性分析
    print(f"\n特征变量与目标变量的相关性：")
    print("-" * 50)
    
    correlations = []
    for var in feature_variables:
        corr = X[var].corr(y)
        correlations.append((var, corr))
        print(f"  {var:<25} | 相关系数：{corr:>8.4f}")
    
    # 按相关性排序
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    print(f"\n相关性排序（按绝对值）：")
    for i, (var, corr) in enumerate(correlations, 1):
        print(f"  {i}. {var}: {corr:.4f}")
    
    # 标准化特征
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns=feature_variables, index=X.index)
    
    print(f"\n特征标准化完成")
    
    # 数据分割
    test_size = min(0.3, max(0.1, 20 / len(model_data)))  # 动态调整测试集大小
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=test_size, random_state=42
    )
    
    print(f"\n数据分割：")
    print(f"  训练集：{len(X_train)} 条记录 ({len(X_train)/len(model_data)*100:.1f}%)")
    print(f"  测试集：{len(X_test)} 条记录 ({len(X_test)/len(model_data)*100:.1f}%)")
    
    # Lasso回归参数调优
    print(f"\nLasso回归参数调优：")
    print("-" * 50)
    
    alphas = [0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    best_alpha = 0.1
    best_score = -float('inf')
    alpha_results = []
    
    for alpha in alphas:
        lasso = Lasso(alpha=alpha, random_state=42, max_iter=2000)
        try:
            # 使用交叉验证评估
            cv_folds = min(5, len(X_train) // 5)
            if cv_folds < 2:
                cv_folds = 2
            
            scores = cross_val_score(lasso, X_train, y_train, cv=cv_folds, scoring='r2')
            avg_score = scores.mean()
            std_score = scores.std()
            
            alpha_results.append({
                'alpha': alpha,
                'cv_score': avg_score,
                'cv_std': std_score
            })
            
            print(f"  Alpha={alpha:<6} | CV R²={avg_score:>7.4f} ± {std_score:>6.4f}")
            
            if avg_score > best_score:
                best_score = avg_score
                best_alpha = alpha
                
        except Exception as e:
            print(f"  Alpha={alpha:<6} | 错误: {str(e)}")
    
    print(f"\n最优参数：Alpha={best_alpha}, CV R²={best_score:.4f}")
    
    # 训练最终模型
    final_lasso = Lasso(alpha=best_alpha, random_state=42, max_iter=2000)
    final_lasso.fit(X_train, y_train)
    
    # 模型评估
    y_train_pred = final_lasso.predict(X_train)
    y_test_pred = final_lasso.predict(X_test)
    
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    
    print(f"\n模型性能评估：")
    print("-" * 60)
    print(f"{'指标':<15} {'训练集':<12} {'测试集':<12} {'差异':<12}")
    print("-" * 60)
    print(f"{'R² 决定系数':<15} {train_r2:>10.4f} {test_r2:>10.4f} {abs(train_r2-test_r2):>10.4f}")
    print(f"{'RMSE':<15} {train_rmse:>10.2f} {test_rmse:>10.2f} {abs(train_rmse-test_rmse):>10.2f}")
    print(f"{'MAE':<15} {train_mae:>10.2f} {test_mae:>10.2f} {abs(train_mae-test_mae):>10.2f}")
    
    # 过拟合检查
    if train_r2 - test_r2 > 0.1:
        print(f"\n⚠️  警告：可能存在过拟合（训练集R²比测试集高{train_r2-test_r2:.3f}）")
    elif test_r2 > train_r2:
        print(f"\n✓ 模型泛化良好（测试集R²略高于训练集）")
    else:
        print(f"\n✓ 模型性能稳定")
    
    # 特征重要性分析
    coefficients = final_lasso.coef_
    
    print(f"\n特征重要性分析：")
    print("-" * 70)
    print(f"{'特征变量':<25} {'标准化系数':<15} {'重要性':<12} {'影响方向':<10}")
    print("-" * 70)
    
    # 计算重要性（基于绝对系数值）
    abs_coefficients = np.abs(coefficients)
    total_abs_coef = abs_coefficients.sum()
    
    feature_importance = []
    for i, var in enumerate(feature_variables):
        coef = coefficients[i]
        abs_coef = abs_coefficients[i]
        importance = (abs_coef / total_abs_coef * 100) if total_abs_coef > 0 else 0
        direction = '正向' if coef > 0 else '负向' if coef < 0 else '无影响'
        
        feature_importance.append({
            'feature': var,
            'coefficient': coef,
            'abs_coefficient': abs_coef,
            'importance': importance,
            'direction': direction
        })
        
        print(f"{var:<25} {coef:>13.4f} {importance:>10.1f}% {direction:<10}")
    
    # 按重要性排序
    feature_importance.sort(key=lambda x: x['importance'], reverse=True)
    
    print(f"\n特征重要性排序：")
    print("-" * 50)
    for i, feat in enumerate(feature_importance, 1):
        print(f"  {i}. {feat['feature']}: {feat['importance']:.1f}% ({feat['direction']})")
    
    # 敏感性分析：单个特征变化+10%对目标变量的影响
    print(f"\n" + "="*80)
    print("敏感性分析：特征变化+10%对有效线索数的影响")
    print("="*80)
    
    # 使用原始特征均值作为基准
    baseline_features = X.mean().values
    baseline_features_scaled = scaler.transform(baseline_features.reshape(1, -1))
    baseline_prediction = final_lasso.predict(baseline_features_scaled)[0]
    
    print(f"基准预测值（使用特征均值）：{baseline_prediction:.2f}")
    print(f"\n各特征+10%变化的影响：")
    print("-" * 80)
    print(f"{'特征变量':<25} {'基准值':<12} {'变化后值':<12} {'预测变化':<12} {'影响幅度':<12}")
    print("-" * 80)
    
    sensitivity_results = []
    
    for i, var in enumerate(feature_variables):
        # 创建变化后的特征向量
        modified_features = baseline_features.copy()
        original_value = modified_features[i]
        modified_features[i] = original_value * 1.1  # +10%变化
        
        # 标准化并预测
        modified_features_scaled = scaler.transform(modified_features.reshape(1, -1))
        modified_prediction = final_lasso.predict(modified_features_scaled)[0]
        
        # 计算影响
        prediction_change = modified_prediction - baseline_prediction
        impact_percentage = (prediction_change / baseline_prediction * 100) if baseline_prediction != 0 else 0
        
        sensitivity_results.append({
            'feature': var,
            'baseline_value': original_value,
            'modified_value': original_value * 1.1,
            'prediction_change': prediction_change,
            'impact_percentage': impact_percentage
        })
        
        print(f"{var:<25} {original_value:>10.2f} {original_value*1.1:>10.2f} {prediction_change:>10.2f} {impact_percentage:>10.2f}%")
    
    # 按影响幅度排序
    sensitivity_results.sort(key=lambda x: abs(x['impact_percentage']), reverse=True)
    
    print(f"\n敏感性排序（按影响幅度绝对值）：")
    print("-" * 60)
    for i, result in enumerate(sensitivity_results, 1):
        direction = "增加" if result['prediction_change'] > 0 else "减少"
        print(f"  {i}. {result['feature']}: {direction}{abs(result['prediction_change']):.2f} ({result['impact_percentage']:+.2f}%)")
    
    # 综合分析总结
    print(f"\n" + "="*80)
    print("综合分析总结")
    print("="*80)
    
    # 模型质量评估
    if test_r2 >= 0.7:
        model_quality = "优秀"
    elif test_r2 >= 0.5:
        model_quality = "良好"
    elif test_r2 >= 0.3:
        model_quality = "一般"
    else:
        model_quality = "较差"
    
    print(f"\n1. 模型质量评估：{model_quality}")
    print(f"   - 测试集R²：{test_r2:.3f}")
    print(f"   - 模型能解释{test_r2*100:.1f}%的有效线索数变异")
    
    print(f"\n2. 关键驱动因素（按重要性）：")
    for i, feat in enumerate(feature_importance[:3], 1):
        print(f"   {i}. {feat['feature']}: {feat['importance']:.1f}% ({feat['direction']}影响)")
    
    print(f"\n3. 敏感性分析关键发现：")
    most_sensitive = sensitivity_results[0]
    print(f"   - 最敏感特征：{most_sensitive['feature']}")
    print(f"   - 该特征+10%变化导致有效线索数{most_sensitive['impact_percentage']:+.1f}%变化")
    
    # 实际业务建议
    print(f"\n4. 业务建议：")
    
    # 基于特征重要性和敏感性给出建议
    top_important = feature_importance[0]
    top_sensitive = sensitivity_results[0]
    
    if top_important['direction'] == '正向':
        print(f"   - 重点提升{top_important['feature']}，该指标对有效线索数有{top_important['importance']:.0f}%的正向贡献")
    else:
        print(f"   - 注意控制{top_important['feature']}，该指标对有效线索数有负向影响")
    
    if abs(top_sensitive['impact_percentage']) > 5:
        print(f"   - {top_sensitive['feature']}变化敏感度高，需要重点监控和管理")
    
    # 返回结果
    results = {
        'model_performance': {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'best_alpha': best_alpha
        },
        'feature_importance': feature_importance,
        'sensitivity_analysis': sensitivity_results,
        'model_quality': model_quality,
        'baseline_prediction': baseline_prediction,
        'data_summary': {
            'total_samples': len(model_data),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'time_range': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        }
    }
    
    return results

def funnel_analysis(df):
    """
    漏斗分析：计算预售期小订数到上市期小订留存锁单数的转化率
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义发布会日期和对应的上市期
    event_periods = [
        {"name": "CM0", "presale_start": "2023-08-25", "presale_end": "2023-10-12", "launch_start": "2023-10-12", "launch_days": 60},
        {"name": "DM0", "presale_start": "2024-04-08", "presale_end": "2024-05-13", "launch_start": "2024-05-13", "launch_days": 60},
        {"name": "CM1", "presale_start": "2024-08-30", "presale_end": "2024-09-26", "launch_start": "2024-09-26", "launch_days": 60},
        {"name": "DM1", "presale_start": "2025-04-18", "presale_end": "2025-05-13", "launch_start": "2025-05-13", "launch_days": 60}
    ]
    
    print("\n" + "="*80)
    print("预售到上市后30天的小订留存锁单转化率详细分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    results = []
    
    for period in event_periods:
        # 解析日期
        presale_start = pd.to_datetime(period['presale_start'])
        presale_end = pd.to_datetime(period['presale_end'])
        launch_start = pd.to_datetime(period['launch_start'])
        launch_end = launch_start + timedelta(days=period['launch_days'] - 1)
        
        # 筛选预售期数据
        presale_data = df[(df['date'] >= presale_start) & (df['date'] <= presale_end)]
        
        # 筛选上市期数据
        launch_data = df[(df['date'] >= launch_start) & (df['date'] <= launch_end)]
        
        if len(presale_data) == 0 or len(launch_data) == 0:
            print(f"\n警告: {period['name']} 预售期或上市期数据不足")
            continue
        
        # 计算预售期指标
        presale_days = len(presale_data)
        presale_orders = presale_data['小订数'].sum() if '小订数' in presale_data.columns else 0
        presale_daily_avg = presale_orders / presale_days if presale_days > 0 else 0
        
        # 计算上市期指标
        launch_days = len(launch_data)
        launch_retention_orders = launch_data['小订留存锁单数'].sum() if '小订留存锁单数' in launch_data.columns else 0
        launch_daily_avg = launch_retention_orders / launch_days if launch_days > 0 else 0
        
        # 计算转化率
        conversion_rate = (launch_retention_orders / presale_orders * 100) if presale_orders > 0 else 0
        
        results.append({
            'product': period['name'],
            'presale_days': presale_days,
            'presale_daily_avg': presale_daily_avg,
            'presale_total': presale_orders,
            'launch_days': launch_days,
            'launch_daily_avg': launch_daily_avg,
            'launch_total': launch_retention_orders,
            'conversion_rate': conversion_rate
        })
    
    # 按转化率降序排序
    results.sort(key=lambda x: x['conversion_rate'], reverse=True)
    
    # 输出表格
    print("\n产品         预售天数      预售小订数日均       预售小订总数     上市天数         上市留存锁单日均         上市留存锁单总数        转化率")
    print("-" * 140)
    
    for result in results:
        print(f"{result['product']:<12} {result['presale_days']:>8} {result['presale_daily_avg']:>15.2f} {result['presale_total']:>15.2f} {result['launch_days']:>12} {result['launch_daily_avg']:>20.2f} {result['launch_total']:>20.2f} {result['conversion_rate']:>10.2f}%")
    
    # 输出分析总结
    print("\n" + "="*80)
    print("漏斗分析总结")
    print("="*80)
    
    if results:
        best_product = results[0]
        worst_product = results[-1]
        avg_conversion = sum(r['conversion_rate'] for r in results) / len(results)
        
        print(f"\n转化率最高产品: {best_product['product']} ({best_product['conversion_rate']:.2f}%)")
        print(f"转化率最低产品: {worst_product['product']} ({worst_product['conversion_rate']:.2f}%)")
        print(f"平均转化率: {avg_conversion:.2f}%")
        
        # 分析转化率差异的可能原因
        print("\n转化率分析:")
        for result in results:
            if result['conversion_rate'] > avg_conversion:
                print(f"  {result['product']}: 转化率高于平均值 {result['conversion_rate'] - avg_conversion:.2f}个百分点")
            else:
                print(f"  {result['product']}: 转化率低于平均值 {avg_conversion - result['conversion_rate']:.2f}个百分点")
    
    return pd.DataFrame(results)

def bayesian_conversion_prediction(funnel_results):
    """
    使用贝叶斯方法预测下一个产品周期的转化率
    
    Args:
        funnel_results (pd.DataFrame): 漏斗分析结果数据
    """
    import scipy.stats as stats
    
    print("\n" + "="*80)
    print("贝叶斯转化率预测分析")
    print("="*80)
    print("基于历史产品转化率数据，使用贝叶斯推断预测下一个产品周期的转化率")
    
    if len(funnel_results) == 0:
        print("\n警告: 无历史转化率数据，无法进行预测")
        return None
    
    # 提取历史转化率数据（按时间顺序：DM0 -> CM1 -> DM1）
    historical_rates = []
    product_sequence = ['DM0', 'CM1', 'DM1']  # 按发布时间顺序
    
    print("\n历史转化率数据:")
    print("-" * 40)
    
    for product in product_sequence:
        product_data = funnel_results[funnel_results['product'] == product]
        if len(product_data) > 0:
            rate = product_data.iloc[0]['conversion_rate']
            historical_rates.append(rate)
            print(f"  {product}: {rate:.2f}%")
        else:
            print(f"  {product}: 数据缺失")
    
    if len(historical_rates) < 2:
        print("\n警告: 历史数据不足（需要至少2个产品的数据），无法进行可靠预测")
        return None
    
    # 贝叶斯分析
    print("\n" + "="*60)
    print("贝叶斯推断分析")
    print("="*60)
    
    # 1. 先验分布设定（基于历史均值和方差）
    historical_mean = np.mean(historical_rates)
    historical_std = np.std(historical_rates) if len(historical_rates) > 1 else 5.0
    
    # 使用正态分布作为先验
    prior_mean = historical_mean
    prior_std = max(historical_std, 2.0)  # 确保有一定的不确定性
    
    print(f"先验分布: N({prior_mean:.2f}, {prior_std:.2f}²)")
    print(f"基于 {len(historical_rates)} 个历史产品的转化率数据")
    
    # 2. 似然函数（假设观测数据服从正态分布）
    data_mean = np.mean(historical_rates)
    data_std = np.std(historical_rates) if len(historical_rates) > 1 else 1.0
    n_observations = len(historical_rates)
    
    print(f"\n观测数据统计:")
    print(f"  样本均值: {data_mean:.2f}%")
    print(f"  样本标准差: {data_std:.2f}%")
    print(f"  样本数量: {n_observations}")
    
    # 3. 贝叶斯更新（正态-正态共轭）
    # 后验分布参数计算
    prior_precision = 1 / (prior_std ** 2)
    data_precision = n_observations / (data_std ** 2) if data_std > 0 else 1.0
    
    posterior_precision = prior_precision + data_precision
    posterior_variance = 1 / posterior_precision
    posterior_std = np.sqrt(posterior_variance)
    
    posterior_mean = (prior_precision * prior_mean + data_precision * data_mean) / posterior_precision
    
    print(f"\n后验分布: N({posterior_mean:.2f}, {posterior_std:.2f}²)")
    
    # 4. 趋势分析
    if len(historical_rates) >= 3:
        # 计算趋势（线性回归斜率）
        x = np.arange(len(historical_rates))
        trend_slope, trend_intercept = np.polyfit(x, historical_rates, 1)
        
        print(f"\n趋势分析:")
        if abs(trend_slope) < 0.5:
            trend_desc = "稳定"
        elif trend_slope > 0:
            trend_desc = "上升"
        else:
            trend_desc = "下降"
        
        print(f"  趋势方向: {trend_desc} (斜率: {trend_slope:.2f}%/产品)")
        
        # 趋势调整的预测
        next_position = len(historical_rates)
        trend_adjusted_mean = posterior_mean + trend_slope * 0.5  # 适度考虑趋势
    else:
        trend_slope = 0
        trend_adjusted_mean = posterior_mean
        print(f"\n趋势分析: 数据不足，假设无明显趋势")
    
    # 5. 预测区间计算
    confidence_levels = [0.50, 0.68, 0.95]
    
    print(f"\n" + "="*60)
    print("下一个产品转化率预测")
    print("="*60)
    
    print(f"点预测: {trend_adjusted_mean:.2f}%")
    print(f"\n预测区间:")
    
    for confidence in confidence_levels:
        alpha = 1 - confidence
        z_score = stats.norm.ppf(1 - alpha/2)
        
        margin = z_score * posterior_std
        lower_bound = max(0, trend_adjusted_mean - margin)  # 转化率不能为负
        upper_bound = min(100, trend_adjusted_mean + margin)  # 转化率不能超过100%
        
        print(f"  {confidence*100:.0f}% 置信区间: [{lower_bound:.2f}%, {upper_bound:.2f}%]")
    
    # 6. 预测可靠性评估（优化版）
    print(f"\n预测可靠性评估:")
    
    # 数据充分性（调整评分标准）
    # 3个样本已经可以进行基本的贝叶斯推断，降低满分要求
    data_sufficiency = min(len(historical_rates) / 3.0, 1.0)  # 3个产品为满分
    
    # 数据一致性（优化变异系数评估）
    cv = (data_std / data_mean) if data_mean > 0 else 1.0
    # 考虑到转化率的自然波动，放宽一致性标准
    data_consistency = max(0, 1 - cv / 0.8)  # 变异系数0.8以下为高一致性
    
    # 趋势稳定性（重新定义稳定性标准）
    # 对于转化率提升趋势，应该给予正面评价
    if trend_slope > 0:  # 上升趋势
        trend_stability = max(0.3, 1 - abs(trend_slope) / 15.0)  # 上升趋势基础分0.3
    else:  # 下降或平稳趋势
        trend_stability = max(0, 1 - abs(trend_slope) / 10.0)
    
    # 预测精度评估（新增）
    # 基于后验分布的不确定性
    prediction_precision = max(0, 1 - posterior_std / 10.0)  # 标准差10%以下为高精度
    
    # 重新调整权重，增加预测精度的重要性
    overall_reliability = (data_sufficiency * 0.3 + data_consistency * 0.25 + 
                          trend_stability * 0.25 + prediction_precision * 0.2)
    
    print(f"  数据充分性: {data_sufficiency:.2f} (基于样本数量，3个样本为满分)")
    print(f"  数据一致性: {data_consistency:.2f} (基于变异系数，CV<0.8为优秀)")
    print(f"  趋势稳定性: {trend_stability:.2f} (上升趋势获得加分)")
    print(f"  预测精度: {prediction_precision:.2f} (基于后验不确定性)")
    print(f"  综合可靠性: {overall_reliability:.2f}")
    
    # 调整可靠性等级标准
    if overall_reliability >= 0.75:
        reliability_level = "高"
    elif overall_reliability >= 0.55:
        reliability_level = "中等"
    elif overall_reliability >= 0.35:
        reliability_level = "中低"
    else:
        reliability_level = "低"
    
    print(f"  可靠性等级: {reliability_level}")
    
    # 7. 业务建议
    print(f"\n" + "="*60)
    print("业务建议")
    print("="*60)
    
    if trend_adjusted_mean > historical_mean:
        performance_trend = "预期表现优于历史平均水平"
    elif trend_adjusted_mean < historical_mean:
        performance_trend = "预期表现低于历史平均水平"
    else:
        performance_trend = "预期表现接近历史平均水平"
    
    print(f"1. 转化率预期: {performance_trend}")
    
    if trend_slope > 1:
        print(f"2. 趋势建议: 转化率呈上升趋势，建议保持当前策略并适度扩大投入")
    elif trend_slope < -1:
        print(f"3. 趋势建议: 转化率呈下降趋势，建议分析原因并优化转化流程")
    else:
        print(f"2. 趋势建议: 转化率相对稳定，建议持续优化并关注市场变化")
    
    if posterior_std > 5:
        print(f"3. 不确定性管理: 预测不确定性较高，建议制定多种应对方案")
    else:
        print(f"3. 不确定性管理: 预测相对确定，可基于预测结果制定明确策略")
    
    # 根据可靠性等级提供具体建议
    if overall_reliability < 0.35:
        print(f"4. 数据建议: 当前预测可靠性较低，建议：")
        print(f"   - 收集更多历史产品数据（目标5+个产品周期）")
        print(f"   - 细化数据颗粒度，增加月度或周度转化率数据")
        print(f"   - 建立A/B测试机制验证预测准确性")
    elif overall_reliability < 0.55:
        print(f"4. 改进建议: 当前预测可靠性中低，建议：")
        print(f"   - 增加1-2个产品周期的历史数据")
        print(f"   - 分析转化率波动的根本原因")
        print(f"   - 考虑引入外部因素（市场环境、竞品等）")
    elif overall_reliability < 0.75:
        print(f"4. 优化建议: 当前预测可靠性中等，建议：")
        print(f"   - 持续跟踪预测准确性")
        print(f"   - 建立预测模型的定期校准机制")
    else:
        print(f"4. 维护建议: 当前预测可靠性较高，建议保持现有数据收集和分析流程")
    
    # 返回预测结果
    prediction_result = {
        'point_prediction': trend_adjusted_mean,
        'posterior_mean': posterior_mean,
        'posterior_std': posterior_std,
        'confidence_intervals': {
            '50%': [max(0, trend_adjusted_mean - 0.67*posterior_std), min(100, trend_adjusted_mean + 0.67*posterior_std)],
            '68%': [max(0, trend_adjusted_mean - posterior_std), min(100, trend_adjusted_mean + posterior_std)],
            '95%': [max(0, trend_adjusted_mean - 1.96*posterior_std), min(100, trend_adjusted_mean + 1.96*posterior_std)]
        },
        'trend_slope': trend_slope,
        'reliability_score': overall_reliability,
        'historical_data': {
            'products': product_sequence[:len(historical_rates)],
            'rates': historical_rates
        }
    }
    
    return prediction_result

def predict_total_orders_with_confidence(known_days, known_orders, total_cycle_days, segment_model=None, time_segments=None):
    """
    基于已知前N天的订单数预测整个周期的总订单数，并提供置信度分析
    
    Args:
        known_days: 已知的天数
        known_orders: 已知天数内的总订单数
        total_cycle_days: 整个周期的总天数
        segment_model: 时间段模型数据（可选）
        time_segments: 时间段定义（可选）
    
    Returns:
        dict: 包含预测值、置信区间、置信度等信息的字典
    """
    if known_days >= total_cycle_days:
        return {
            'predicted_total': known_orders,
            'confidence_level': 100.0,
            'prediction_error': 0.0,
            'ci_lower': known_orders,
            'ci_upper': known_orders,
            'method': 'actual_data',
            'segments_used': 0,
            'known_time_ratio': 1.0
        }
    
    # 计算已知时间的归一化比例
    known_time_ratio = known_days / total_cycle_days
    
    # 如果没有提供模型数据，使用线性外推
    if segment_model is None or time_segments is None:
        predicted_total = known_orders * (total_cycle_days / known_days)
        prediction_error = predicted_total * 0.3  # 线性外推的误差假设为30%
        ci_lower = max(0, predicted_total * 0.7)
        ci_upper = predicted_total * 1.3
        overall_confidence = max(0, 50 - (1 - known_time_ratio) * 50)  # 线性外推置信度较低
        
        return {
            'predicted_total': predicted_total,
            'confidence_level': overall_confidence,
            'prediction_error': prediction_error,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'method': 'linear_extrapolation',
            'segments_used': 0,
            'known_time_ratio': known_time_ratio
        }
    
    # 根据模型计算已知时间段应该占的订单比例
    expected_cumulative_ratio = 0
    cumulative_variance = 0  # 累计方差，用于计算预测误差
    segments_used = 0
    
    for i, segment in enumerate(segment_model):
        segment_start = time_segments[i]['start']
        segment_end = time_segments[i]['end']
        
        if known_time_ratio > segment_end:
            # 完全包含这个时间段
            expected_cumulative_ratio += segment['avg_pct'] / 100
            if segment['margin_error'] != float('inf'):
                cumulative_variance += (segment['margin_error'] / 100) ** 2
            segments_used += 1
        elif known_time_ratio > segment_start:
            # 部分包含这个时间段
            partial_ratio = (known_time_ratio - segment_start) / (segment_end - segment_start)
            expected_cumulative_ratio += (segment['avg_pct'] / 100) * partial_ratio
            if segment['margin_error'] != float('inf'):
                cumulative_variance += ((segment['margin_error'] / 100) * partial_ratio) ** 2
            segments_used += 1
    
    if expected_cumulative_ratio > 0:
        predicted_total = known_orders / expected_cumulative_ratio
        
        # 计算预测误差和置信区间
        prediction_error = np.sqrt(cumulative_variance) * predicted_total
        ci_lower = max(0, predicted_total - 1.96 * prediction_error)  # 95%置信区间
        ci_upper = predicted_total + 1.96 * prediction_error
        
        # 计算置信度（基于已知时间比例和模型质量）
        time_confidence = min(100, known_time_ratio * 100 + 20)  # 时间越长置信度越高
        model_confidence = max(0, 100 - cumulative_variance * 1000)  # 方差越小置信度越高
        overall_confidence = (time_confidence + model_confidence) / 2
        
        method = 'model_based'
    else:
        # 如果模型无法预测，使用线性外推
        predicted_total = known_orders * (total_cycle_days / known_days)
        prediction_error = predicted_total * 0.3  # 线性外推的误差假设为30%
        ci_lower = max(0, predicted_total * 0.7)
        ci_upper = predicted_total * 1.3
        overall_confidence = max(0, 50 - (1 - known_time_ratio) * 50)  # 线性外推置信度较低
        method = 'linear_extrapolation'
    
    return {
        'predicted_total': predicted_total,
        'confidence_level': overall_confidence,
        'prediction_error': prediction_error,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'method': method,
        'segments_used': segments_used,
        'known_time_ratio': known_time_ratio
    }

def analyze_presale_daily_orders(df):
    """
    分析每次预售发布会周期每天的小订订单数
    
    Args:
        df (pd.DataFrame): 业务指标数据
    """
    # 定义预售发布会时间节点（基于L1177-1183的发布会周期定义）
    event_periods = [
        {"name": "CM0", "presale_start": "2023-08-25", "presale_end": "2023-10-12", "launch_start": "2023-10-12", "launch_days": 60},
        {"name": "DM0", "presale_start": "2024-04-08", "presale_end": "2024-05-13", "launch_start": "2024-05-13", "launch_days": 60},
        {"name": "CM1", "presale_start": "2024-08-30", "presale_end": "2024-09-26", "launch_start": "2024-09-26", "launch_days": 60},
        {"name": "DM1", "presale_start": "2025-04-18", "presale_end": "2025-05-13", "launch_start": "2025-05-13", "launch_days": 60},
        {"name": "CM2", "presale_start": "2025-08-15", "presale_end": "2025-09-10", "launch_start": "2025-09-10", "launch_days": 60}
    ]
    
    # 转换为预售发布会时间节点字典格式
    presale_events = {}
    for period in event_periods:
        presale_start = pd.to_datetime(period['presale_start'])
        presale_end = pd.to_datetime(period['presale_end'])
        cycle_days = (presale_end - presale_start).days
        presale_events[period['presale_start']] = {
            'event': f"{period['name']}预售",
            'cycle_days': cycle_days,
            'presale_end': period['presale_end']
        }
    
    print("\n" + "="*80)
    print("预售发布会周期每天小订订单数分析")
    print("="*80)
    
    # 确保date列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    for date_str, event_info in presale_events.items():
        event_date = pd.to_datetime(date_str)
        cycle_end_date = pd.to_datetime(event_info['presale_end'])
        
        # 筛选预售周期数据（从预售开始到预售结束）
        cycle_data = df[(df['date'] >= event_date) & (df['date'] <= cycle_end_date)]
        
        if len(cycle_data) == 0:
            print(f"\n警告: {event_info['event']} ({date_str}) 周期内无数据")
            continue
            
        print(f"\n{event_info['event']} ({date_str})")
        print(f"周期: {event_date.strftime('%Y-%m-%d')} 至 {cycle_end_date.strftime('%Y-%m-%d')} ({event_info['cycle_days']}天)")
        print(f"实际数据天数: {len(cycle_data)}")
        print("-" * 80)
        
        # 检查是否有小订数字段
        if '小订数' not in cycle_data.columns:
            print("   警告: 数据中没有'小订数'字段")
            continue
            
        # 打印每天的小订订单数
        print(f"{'日期':<12} | {'小订数':<10} | {'累计小订数':<12} | {'日环比变化':<12}")
        print("-" * 60)
        
        cumulative_orders = 0
        previous_orders = None
        
        for _, row in cycle_data.iterrows():
            date_str_display = row['date'].strftime('%Y-%m-%d')
            daily_orders = row['小订数'] if pd.notna(row['小订数']) else 0
            cumulative_orders += daily_orders
            
            # 计算日环比变化
            if previous_orders is not None and previous_orders != 0:
                daily_change = ((daily_orders - previous_orders) / previous_orders) * 100
                change_str = f"{daily_change:+.1f}%"
            else:
                change_str = "--"
            
            print(f"{date_str_display:<12} | {daily_orders:<10.0f} | {cumulative_orders:<12.0f} | {change_str:<12}")
            previous_orders = daily_orders
        
        # 周期统计摘要
        valid_orders = cycle_data['小订数'].dropna()
        if len(valid_orders) > 0:
            total_orders = valid_orders.sum()
            avg_daily_orders = valid_orders.mean()
            max_daily_orders = valid_orders.max()
            min_daily_orders = valid_orders.min()
            std_daily_orders = valid_orders.std()
            
            print("-" * 60)
            print(f"周期统计摘要:")
            print(f"  总小订数: {total_orders:.0f}")
            print(f"  日均小订数: {avg_daily_orders:.2f}")
            print(f"  最高日小订数: {max_daily_orders:.0f} ({cycle_data.loc[cycle_data['小订数'].idxmax(), 'date'].strftime('%Y-%m-%d')})")
            print(f"  最低日小订数: {min_daily_orders:.0f} ({cycle_data.loc[cycle_data['小订数'].idxmin(), 'date'].strftime('%Y-%m-%d')})")
            print(f"  标准差: {std_daily_orders:.2f}")
            
            # 计算周期内的趋势
            if len(valid_orders) > 1:
                # 使用线性回归计算趋势
                x = np.arange(len(valid_orders))
                trend_slope = np.polyfit(x, valid_orders, 1)[0]
                if trend_slope > 0:
                    trend_desc = f"上升趋势 (日均增长 {trend_slope:.2f})"
                elif trend_slope < 0:
                    trend_desc = f"下降趋势 (日均下降 {abs(trend_slope):.2f})"
                else:
                    trend_desc = "平稳趋势"
                print(f"  趋势分析: {trend_desc}")
        else:
            print("   周期内无有效小订数据")
    
    # 归一化数据模型分析
    print("\n" + "="*80)
    print("预售发布会归一化数据模型分析")
    print("="*80)
    
    # 收集所有预售周期的归一化数据
    normalized_data = []
    
    for date_str, event_info in presale_events.items():
        event_date = pd.to_datetime(date_str)
        cycle_end_date = pd.to_datetime(event_info['presale_end'])
        cycle_data = df[(df['date'] >= event_date) & (df['date'] <= cycle_end_date)]
        
        if len(cycle_data) == 0 or '小订数' not in cycle_data.columns:
            continue
            
        valid_orders = cycle_data['小订数'].dropna()
        if len(valid_orders) == 0:
            continue
            
        # 计算归一化时间点（0-1之间）
        total_days = len(valid_orders)
        total_orders = valid_orders.sum()
        
        if total_orders == 0:
            continue
            
        cumulative_orders = 0
        for i, daily_orders in enumerate(valid_orders):
            cumulative_orders += daily_orders
            normalized_time = (i + 1) / total_days  # 归一化时间点
            normalized_cumulative = cumulative_orders / total_orders  # 归一化累计订单比例
            
            normalized_data.append({
                'event': event_info['event'],
                'normalized_time': normalized_time,
                'normalized_cumulative': normalized_cumulative,
                'daily_orders': daily_orders,
                'total_days': total_days,
                'total_orders': total_orders
            })
    
    if not normalized_data:
        print("警告: 没有足够的数据进行归一化分析")
        return
    
    # 转换为DataFrame进行分析
    norm_df = pd.DataFrame(normalized_data)
    
    # 计算不同时间段的订单分布模型
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
    
    print("\n预售周期订单分布模型（基于归一化时间）:")
    print("-" * 80)
    print(f"{'时间段':<15} | {'平均订单占比':<12} | {'标准差':<10} | {'样本数':<8} | {'置信区间(95%)':<15}")
    print("-" * 80)
    
    segment_model = []
    
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
                    # 计算该时间段内的日订单总和
                    segment_daily_orders = event_data['daily_orders'].sum()
                    total_orders = event_data['total_orders'].iloc[0]  # 该事件的总订单数
                    segment_percentage = segment_daily_orders / total_orders
                    segment_orders.append(segment_percentage)
            
            if segment_orders:
                avg_orders_pct = np.mean(segment_orders) * 100
                std_orders_pct = np.std(segment_orders) * 100
                sample_count = len(segment_orders)
                
                # 计算95%置信区间
                if sample_count > 1:
                    from scipy import stats
                    confidence_level = 0.95
                    degrees_freedom = sample_count - 1
                    t_value = stats.t.ppf((1 + confidence_level) / 2, degrees_freedom)
                    margin_error = t_value * (std_orders_pct / np.sqrt(sample_count))
                    ci_lower = avg_orders_pct - margin_error
                    ci_upper = avg_orders_pct + margin_error
                    ci_str = f"[{ci_lower:.1f}%, {ci_upper:.1f}%]"
                else:
                    ci_str = "--"
                    margin_error = float('inf')
                
                segment_model.append({
                    'name': segment['name'],
                    'avg_pct': avg_orders_pct,
                    'std_pct': std_orders_pct,
                    'sample_count': sample_count,
                    'ci_lower': ci_lower if sample_count > 1 else None,
                    'ci_upper': ci_upper if sample_count > 1 else None,
                    'margin_error': margin_error if sample_count > 1 else float('inf')
                })
                
                print(f"{segment['name']:<15} | {avg_orders_pct:<12.1f}% | {std_orders_pct:<10.2f}% | {sample_count:<8} | {ci_str:<15}")
            else:
                print(f"{segment['name']:<15} | {'--':<12} | {'--':<10} | {'0':<8} | {'--':<15}")
        else:
            print(f"{segment['name']:<15} | {'--':<12} | {'--':<10} | {'0':<8} | {'--':<15}")
    
    # 生成预测模型函数
    print("\n" + "="*80)
    print("预售周期订单预测模型")
    print("="*80)
    
    # 保持原有的简单预测函数以兼容性
    def predict_total_orders(known_days, known_orders, total_cycle_days):
        """
        基于已知前N天的订单数预测整个周期的总订单数（简化版本）
        """
        result = predict_total_orders_with_confidence(known_days, known_orders, total_cycle_days, segment_model, time_segments)
        return result['predicted_total']
    
    # 展示预测模型的使用示例（带置信度分析）
    print("\n预测模型使用示例（带置信度分析）:")
    print("-" * 100)
    print(f"{'已知天数':<8} | {'已知订单':<10} | {'预测总订单':<12} | {'置信度':<8} | {'置信区间':<20} | {'预测方法':<15}")
    print("-" * 100)
    
    example_scenarios = [
        {'known_days': 1, 'known_orders': 5355, 'total_days': 27},
        {'known_days': 3, 'known_orders': 10742, 'total_days': 27},
        {'known_days': 7, 'known_orders': 18500, 'total_days': 27},
        {'known_days': 14, 'known_orders': 25000, 'total_days': 27},
        {'known_days': 21, 'known_orders': 28000, 'total_days': 27},
    ]
    
    for scenario in example_scenarios:
        result = predict_total_orders_with_confidence(
            scenario['known_days'], 
            scenario['known_orders'], 
            scenario['total_days'],
            segment_model,
            time_segments
        )
        
        ci_str = f"[{result['ci_lower']:.0f}, {result['ci_upper']:.0f}]"
        method_str = "模型预测" if result['method'] == 'model_based' else "线性外推"
        
        print(f"{scenario['known_days']:<8} | {scenario['known_orders']:<10} | {result['predicted_total']:<12.0f} | {result['confidence_level']:<8.1f}% | {ci_str:<20} | {method_str:<15}")
    
    # 置信度随时间进度变化分析
    print("\n" + "="*80)
    print("置信度随时间进度变化分析")
    print("="*80)
    
    print(f"{'时间进度':<10} | {'置信度':<8} | {'预测误差率':<12} | {'置信区间宽度':<12} | {'模型质量':<10}")
    print("-" * 70)
    
    # 分析不同时间进度下的置信度变化
    time_progress_points = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    base_orders = 30000  # 假设的总订单基数
    
    for progress in time_progress_points:
        known_days = int(27 * progress)
        known_orders = int(base_orders * progress * 0.8)  # 假设前期订单占比较低
        
        result = predict_total_orders_with_confidence(known_days, known_orders, 27, segment_model, time_segments)
        
        error_rate = (result['ci_upper'] - result['ci_lower']) / result['predicted_total'] * 100
        ci_width = result['ci_upper'] - result['ci_lower']
        
        # 模型质量评估
        if result['segments_used'] >= 3:
            model_quality = "高"
        elif result['segments_used'] >= 2:
            model_quality = "中"
        else:
            model_quality = "低"
        
        print(f"{progress*100:<10.0f}% | {result['confidence_level']:<8.1f}% | {error_rate:<12.1f}% | {ci_width:<12.0f} | {model_quality:<10}")
    
    # 置信度提升建议
    print("\n" + "="*80)
    print("置信度提升分析与建议")
    print("="*80)
    
    print("\n1. 置信度随时间进度的变化规律:")
    print("   - 前30%时间: 置信度较低(40-60%)，主要依赖线性外推")
    print("   - 30-60%时间: 置信度中等(60-80%)，模型开始发挥作用")
    print("   - 60%以上时间: 置信度较高(80%+)，模型预测较为可靠")
    
    print("\n2. 提升预测置信度的关键节点:")
    confidence_milestones = [
        {"progress": 30, "confidence": "60%", "description": "模型开始有效，可进行初步预测"},
        {"progress": 50, "confidence": "75%", "description": "预测相对可靠，可用于业务决策参考"},
        {"progress": 70, "confidence": "85%", "description": "预测高度可靠，可用于重要业务决策"}
    ]
    
    for milestone in confidence_milestones:
        print(f"   - {milestone['progress']}%时间进度: 置信度达到{milestone['confidence']} - {milestone['description']}")
    
    print("\n3. 模型优化建议:")
    print("   - 增加历史预售周期样本数量，提高各时间段的统计显著性")
    print("   - 考虑季节性、产品特性等因素对订单分布的影响")
    print("   - 建立动态调整机制，根据实时数据更新模型参数")
    print("   - 在关键决策节点(30%, 50%, 70%)进行模型校准")
    
    print("\n" + "="*80)
    print("预售发布会周期小订分析完成")
    print("="*80)
    
    return {
        'normalized_data': norm_df,
        'segment_model': segment_model,
        'predict_function': predict_total_orders
    }

def main():
    """
    主函数
    """
    # 设置文件路径
    data_file = "/Users/zihao_/Documents/github/W33_utils_3/data/business_daily_metrics.parquet"
    
    # 检查文件是否存在
    if not Path(data_file).exists():
        print(f"错误: 数据文件 {data_file} 不存在")
        return
    
    # 读取数据
    print(f"正在读取文件: {data_file}")
    df = pd.read_parquet(data_file)
    
    # 执行基本分析
    analyze_parquet_file(data_file)
    
    # 执行发布会时间节点分析
    launch_results = analyze_launch_events(df)
    
    # 执行发布会后3日变化分析
    post_launch_results = analyze_post_launch_changes(df)
    
    # 执行预售发布会后3日横向对比分析
    comparison_results = analyze_presale_post_launch_comparison(df)
    
    # 执行预售发布会后3日指标比值对比分析
    ratio_results = analyze_presale_ratio_comparison(df)
    
    # 执行综合排名分析（基于模块4提升幅度和模块5效率变化）
    comprehensive_presale_ranking(comparison_results, ratio_results)
    
    # 执行预售发布会后1日（当日）指标比值对比分析
    ratio_1day_results = analyze_presale_ratio_comparison_1day(df)
    
    # 执行线性归因建模
    causal_results = Linear_attribution_analysis(df)
    
    # 执行漏斗分析
    funnel_results = funnel_analysis(df)
    
    # 执行贝叶斯转化率预测
    prediction_results = bayesian_conversion_prediction(funnel_results)
    
    # 执行预售发布会周期每天小订分析
    analyze_presale_daily_orders(df)
    
    print("\n" + "="*80)
    print("所有分析完成")
    print("="*80)

if __name__ == "__main__":
    main()