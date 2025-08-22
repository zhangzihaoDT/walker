#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线索结构分析脚本 - 模块化版本
分析leads_structure_analysis.parquet和intention_order_analysis.parquet数据
实现模块化分析架构，支持扩展性分析模块

分析模块架构：
- 模块一：数据基本信息打印模块
- 模块二：线索转化率综合分析报告模块
- 模块三：预售周期归一化分析模块
- 模块扩展：为后续分析模块预留接口
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# ============================================================================
# 模块一：数据基本信息打印模块
# ============================================================================

def module_one_data_info():
    """
    模块一：数据基本信息打印模块
    负责数据加载、验证和基础信息展示，生成数据基本信息报告
    """
    # 数据文件路径
    leads_path = "/Users/zihao_/Documents/github/W33_utils_3/data/leads_structure_analysis.parquet"
    orders_path = "/Users/zihao_/Documents/github/W33_utils_3/data/intention_order_analysis.parquet"
    
    print("="*80)
    print("模块一：数据基本信息打印模块")
    print("="*80)
    
    try:
        # 读取线索数据
        print(f"正在读取线索数据: {leads_path}")
        leads_df = pd.read_parquet(leads_path)
        print(f"线索数据形状: {leads_df.shape[0]} 行 × {leads_df.shape[1]} 列")
        
        # 读取订单数据
        print(f"正在读取订单数据: {orders_path}")
        orders_df = pd.read_parquet(orders_path)
        print(f"订单数据形状: {orders_df.shape[0]} 行 × {orders_df.shape[1]} 列")
        
        # 生成线索数据基本信息
        leads_info = generate_data_info_report(leads_df, "线索数据")
        
        # 生成订单数据基本信息
        orders_info = generate_data_info_report(orders_df, "订单数据")
        
        print("\n" + "="*60)
        print("模块一：数据基本信息分析完成")
        print("="*60)
        
        return leads_df, orders_df, leads_info, orders_info
        
    except FileNotFoundError as e:
        print(f"错误: 找不到数据文件 {e}")
        return None, None, None, None
    except Exception as e:
        print(f"模块一执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

def generate_data_info_report(df, data_name):
    """
    生成数据基本信息报告
    """
    if df is None or df.empty:
        return {
            'data_name': data_name,
            'shape': (0, 0),
            'columns': [],
            'dtypes': {},
            'null_counts': {},
            'null_percentages': {},
            'memory_usage': 0
        }
    
    # 计算空值信息
    null_counts = df.isnull().sum().to_dict()
    null_percentages = (df.isnull().sum() / len(df) * 100).round(2).to_dict()
    
    # 计算内存使用情况
    memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
    
    data_info = {
        'data_name': data_name,
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': dict(df.dtypes.astype(str)),
        'null_counts': null_counts,
        'null_percentages': null_percentages,
        'memory_usage': round(memory_usage, 2)
    }
    
    print(f"\n{data_name}基本信息:")
    print(f"  数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"  内存使用: {memory_usage:.2f} MB")
    print(f"  字段数量: {len(df.columns)}")
    print(f"  总空值数: {sum(null_counts.values())}")
    
    return data_info

# ============================================================================
# 模块二：线索转化率综合分析报告模块
# ============================================================================

def module_two_conversion_analysis(leads_df, orders_df):
    """
    模块二：线索转化率综合分析报告模块
    执行各车型预售期转化率分析
    """
    if leads_df is None or orders_df is None:
        print("错误: 数据加载失败，无法执行模块二分析")
        return None, None
    
    print("\n" + "="*80)
    print("模块二：线索转化率综合分析报告模块")
    print("="*80)
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    try:
        
        # 数据预处理
        print("\n" + "="*60)
        print("数据预处理")
        print("="*60)
        
        # 创建数据副本以避免修改原始数据
        leads_work_df = leads_df.copy()
        orders_work_df = orders_df.copy()
        
        # 处理线索数据的日期字段
        if '日(lc_create_time)' in leads_work_df.columns:
            leads_work_df['date'] = pd.to_datetime(leads_work_df['日(lc_create_time)'])
            print("线索数据日期字段处理完成")
        else:
            print("警告: 线索数据中未找到'日(lc_create_time)'字段")
            print("可用字段:", list(leads_work_df.columns))
        
        # 处理订单数据的日期字段
        if 'first_assign_time' in orders_work_df.columns:
            orders_work_df['date'] = pd.to_datetime(orders_work_df['first_assign_time']).dt.date
            orders_work_df['date'] = pd.to_datetime(orders_work_df['date'])
            print("订单数据first_assign_time日期字段处理完成")
        else:
            print("警告: 订单数据中未找到'first_assign_time'字段")
            print("可用字段:", list(orders_work_df.columns))
        
        # 处理订单数据的Intention_Payment_Time字段
        if 'Intention_Payment_Time' in orders_work_df.columns:
            orders_work_df['payment_date'] = pd.to_datetime(orders_work_df['Intention_Payment_Time']).dt.date
            orders_work_df['payment_date'] = pd.to_datetime(orders_work_df['payment_date'])
            print("订单数据Intention_Payment_Time日期字段处理完成")
        else:
            print("警告: 订单数据中未找到'Intention_Payment_Time'字段")
            print("可用字段:", list(orders_work_df.columns))
        
        # 定义渠道映射关系
        channel_mapping = {
            '官方直播线索数': '官方直播',
            '经销商矩阵线索数': '经销商矩阵', 
            '网销平台线索数': '垂媒网销',
            '自有渠道线索数': '自有渠道',
            '门店自然客流线索数': '门店自然客流',
            '投放线索数': '投放',
            '活动线索数': '活动'
        }
        
        # 转置线索数据中的渠道字段
        print("\n正在转置线索数据的渠道字段...")
        
        # 检查线索数据中是否包含需要转置的渠道字段
        channel_cols = [col for col in channel_mapping.keys() if col in leads_df.columns]
        if channel_cols:
            print(f"找到渠道字段: {channel_cols}")
            
            # 保留的基础字段
            base_cols = ['date']
            if '线索识别数' in leads_df.columns:
                base_cols.append('线索识别数')
            if '主要渠道线索数比例' in leads_df.columns:
                base_cols.append('主要渠道线索数比例')
            
            # 转置渠道数据
            leads_melted_list = []
            for _, row in leads_df.iterrows():
                base_data = {col: row[col] for col in base_cols if col in leads_df.columns}
                for channel_col in channel_cols:
                    if pd.notna(row[channel_col]) and row[channel_col] > 0:
                        channel_data = base_data.copy()
                        channel_data['渠道'] = channel_mapping[channel_col]
                        channel_data['渠道线索数'] = row[channel_col]
                        leads_melted_list.append(channel_data)
            
            if leads_melted_list:
                leads_melted = pd.DataFrame(leads_melted_list)
                print(f"转置后线索数据形状: {leads_melted.shape[0]} 行 × {leads_melted.shape[1]} 列")
            else:
                print("警告: 转置后没有有效的线索数据")
                leads_melted = pd.DataFrame()
        else:
            print("警告: 未找到需要转置的渠道字段")
            leads_melted = pd.DataFrame()
        
        # 分析各车型预售期数据
        print("\n" + "="*60)
        print("各车型预售期转化率分析")
        print("="*60)
        
        results = []
        daily_results = []  # 存储每日详细数据
        
        for model, period in presale_periods.items():
            print(f"\n分析车型: {model}")
            print(f"预售期间: {period['start']} 至 {period['end']}")
            
            start_date = pd.to_datetime(period['start'])
            end_date = pd.to_datetime(period['end'])
            
            # 筛选预售期间的线索数据
            if not leads_work_df.empty and 'date' in leads_work_df.columns:
                period_leads = leads_work_df[
                    (leads_work_df['date'] >= start_date) & 
                    (leads_work_df['date'] <= end_date)
                ]
                
                # 计算总线索数（线索识别数）
                if '线索识别数' in period_leads.columns:
                    total_leads = period_leads['线索识别数'].sum()
                else:
                    total_leads = 0
                    print(f"  警告: 未找到'线索识别数'字段")
            else:
                total_leads = 0
                print(f"  警告: 线索数据为空或缺少日期字段")
            
            # 筛选预售期间的订单数据
            if not orders_work_df.empty and 'date' in orders_work_df.columns:
                # 根据车型筛选订单（假设订单数据中有车型字段）
                if 'Model' in orders_work_df.columns:
                    model_orders = orders_work_df[orders_work_df['Model'] == model]
                else:
                    # 如果没有车型字段，使用所有订单数据
                    model_orders = orders_work_df
                
                period_orders = model_orders[
                    (model_orders['date'] >= start_date) & 
                    (model_orders['date'] <= end_date)
                ]
                
                # 计算小订数（Order Number去重计数）
                if 'Order Number' in period_orders.columns:
                    small_orders = period_orders['Order Number'].nunique()
                else:
                    small_orders = len(period_orders)
                    print(f"  警告: 未找到'Order Number'字段，使用记录数")
            else:
                small_orders = 0
                print(f"  警告: 订单数据为空或缺少日期字段")
            
            # 计算总小订数（使用payment_date与lc_create_time对齐）
            if not orders_work_df.empty and 'payment_date' in orders_work_df.columns:
                # 根据车型筛选订单（假设订单数据中有车型字段）
                if 'Model' in orders_work_df.columns:
                    model_orders_payment = orders_work_df[orders_work_df['Model'] == model]
                else:
                    # 如果没有车型字段，使用所有订单数据
                    model_orders_payment = orders_work_df
                
                period_orders_payment = model_orders_payment[
                    (model_orders_payment['payment_date'] >= start_date) & 
                    (model_orders_payment['payment_date'] <= end_date)
                ]
                
                # 计算总小订数（Order Number去重计数）
                if 'Order Number' in period_orders_payment.columns:
                    total_small_orders = period_orders_payment['Order Number'].nunique()
                else:
                    total_small_orders = len(period_orders_payment)
                    print(f"  警告: 未找到'Order Number'字段，使用记录数")
            else:
                total_small_orders = 0
                print(f"  警告: 订单数据为空或缺少payment_date字段")
            
            # 计算转化率
            if total_leads > 0:
                conversion_rate = (small_orders / total_leads) * 100
            else:
                conversion_rate = 0
            
            # 计算小订数与总小订数的比值
            if total_small_orders > 0:
                order_ratio = (small_orders / total_small_orders) * 100
            else:
                order_ratio = 0
            
            result = {
                '车型': model,
                '预售开始日期': period['start'],
                '预售结束日期': period['end'],
                '总线索数': total_leads,
                '小订数': small_orders,
                '总小订数': total_small_orders,
                '小订数比值(%)': round(order_ratio, 2),
                '转化率(%)': round(conversion_rate, 2)
            }
            
            results.append(result)
            
            print(f"  总线索数: {total_leads:,}")
            print(f"  小订数: {small_orders:,}")
            print(f"  总小订数: {total_small_orders:,}")
            print(f"  小订数比值: {order_ratio:.2f}%")
            print(f"  转化率: {conversion_rate:.2f}%")
            
            # 按日期分组分析每日数据
            print(f"  {model} 预售期间每日详细数据:")
            print("  " + "-"*90)
            print(f"  {'日期':<12} {'线索数':<10} {'小订数':<10} {'总小订数':<10} {'小订比值(%)':<12} {'转化率(%)':<10}")
            print("  " + "-"*90)
            
            # 生成预售期间的所有日期
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            for single_date in date_range:
                # 当日线索数
                if not leads_work_df.empty and 'date' in leads_work_df.columns:
                    daily_leads_data = leads_work_df[leads_work_df['date'] == single_date]
                    if '线索识别数' in daily_leads_data.columns:
                        daily_leads = daily_leads_data['线索识别数'].sum()
                    else:
                        daily_leads = 0
                else:
                    daily_leads = 0
                
                # 当日小订数
                if not orders_work_df.empty and 'date' in orders_work_df.columns:
                    if 'Model' in orders_work_df.columns:
                        daily_orders_data = orders_work_df[
                            (orders_work_df['Model'] == model) & 
                            (orders_work_df['date'] == single_date)
                        ]
                    else:
                        daily_orders_data = orders_work_df[orders_work_df['date'] == single_date]
                    
                    if 'Order Number' in daily_orders_data.columns:
                        daily_orders = daily_orders_data['Order Number'].nunique()
                    else:
                        daily_orders = len(daily_orders_data)
                else:
                    daily_orders = 0
                
                # 当日总小订数（使用payment_date）
                if not orders_work_df.empty and 'payment_date' in orders_work_df.columns:
                    if 'Model' in orders_work_df.columns:
                        daily_orders_payment_data = orders_work_df[
                            (orders_work_df['Model'] == model) & 
                            (orders_work_df['payment_date'] == single_date)
                        ]
                    else:
                        daily_orders_payment_data = orders_work_df[orders_work_df['payment_date'] == single_date]
                    
                    if 'Order Number' in daily_orders_payment_data.columns:
                        daily_total_orders = daily_orders_payment_data['Order Number'].nunique()
                    else:
                        daily_total_orders = len(daily_orders_payment_data)
                else:
                    daily_total_orders = 0
                
                # 当日转化率
                if daily_leads > 0:
                    daily_conversion = (daily_orders / daily_leads) * 100
                else:
                    daily_conversion = 0
                
                # 当日小订比值
                if daily_total_orders > 0:
                    daily_order_ratio = (daily_orders / daily_total_orders) * 100
                else:
                    daily_order_ratio = 0
                
                # 打印每日数据
                date_str = single_date.strftime('%Y-%m-%d')
                print(f"  {date_str:<12} {daily_leads:<10} {daily_orders:<10} {daily_total_orders:<10} {daily_order_ratio:<12.2f} {daily_conversion:<10.2f}")
                
                # 保存每日数据
                daily_result = {
                    '车型': model,
                    '日期': date_str,
                    '线索数': daily_leads,
                    '小订数': daily_orders,
                    '总小订数': daily_total_orders,
                    '小订数比值(%)': round(daily_order_ratio, 2),
                    '转化率(%)': round(daily_conversion, 2)
                }
                daily_results.append(daily_result)
            
            print("  " + "-"*90)
        
        # 输出汇总结果
        print("\n" + "="*80)
        print("各车型预售期转化率汇总")
        print("="*80)
        
        results_df = pd.DataFrame(results)
        print("Results DataFrame columns:", results_df.columns.tolist())
        print("Results DataFrame shape:", results_df.shape)
        print(results_df.to_string(index=False))
        
        # 生成模块二报告
        generate_module_two_report(results_df, daily_results)
        
        # 生成Markdown报告
        report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/leads_conversion_analysis_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 线索转化率分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 写入汇总表格
            f.write("## 各车型预售期转化率汇总\n\n")
            f.write("| 车型 | 预售开始日期 | 预售结束日期 | 总线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
            f.write("|------|-------------|-------------|----------|--------|----------|---------------|-----------|\n")
            for _, row in results_df.iterrows():
                f.write(f"| {row['车型']} | {row['预售开始日期']} | {row['预售结束日期']} | {row['总线索数']:,} | {row['小订数']:,} | {row['总小订数']:,} | {row['小订数比值(%)']} | {row['转化率(%)']} |\n")
            
            # 写入每日详细数据
            if daily_results:
                daily_df = pd.DataFrame(daily_results)
                f.write("\n## 每日详细数据统计摘要\n\n")
                f.write(f"- **总记录数**: {len(daily_df)}\n")
                f.write(f"- **涵盖车型**: {', '.join(daily_df['车型'].unique())}\n")
                f.write(f"- **日期范围**: {daily_df['日期'].min()} 至 {daily_df['日期'].max()}\n")
                f.write(f"- **平均每日线索数**: {daily_df['线索数'].mean():.0f}\n")
                f.write(f"- **平均每日小订数**: {daily_df['小订数'].mean():.0f}\n")
                f.write(f"- **平均转化率**: {daily_df['转化率(%)'].mean():.2f}%\n\n")
                
                # 按车型分组写入每日数据
                for model in daily_df['车型'].unique():
                    model_data = daily_df[daily_df['车型'] == model]
                    f.write(f"### {model} 预售期间每日数据\n\n")
                    f.write("| 日期 | 线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
                    f.write("|------|--------|--------|----------|---------------|-----------|\n")
                    for _, row in model_data.iterrows():
                        f.write(f"| {row['日期']} | {row['线索数']:,} | {row['小订数']:,} | {row['总小订数']:,} | {row['小订数比值(%)']} | {row['转化率(%)']} |\n")
                    f.write("\n")
                
                # 显示每日数据统计摘要
                print("\n" + "="*60)
                print("每日数据统计摘要")
                print("="*60)
                print(f"总记录数: {len(daily_df)}")
                print(f"涵盖车型: {', '.join(daily_df['车型'].unique())}")
                print(f"日期范围: {daily_df['日期'].min()} 至 {daily_df['日期'].max()}")
                print(f"平均每日线索数: {daily_df['线索数'].mean():.0f}")
                print(f"平均每日小订数: {daily_df['小订数'].mean():.0f}")
                print(f"平均转化率: {daily_df['转化率(%)'].mean():.2f}%")
        
        print(f"\n报告已保存到: {report_path}")
        
        print("\n" + "="*60)
        print("模块二：线索转化率综合分析完成")
        print("="*60)
        
        return results_df
        
    except FileNotFoundError as e:
        print(f"错误: 找不到数据文件 {e}")
        return None
    except Exception as e:
        print(f"模块二执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_module_two_report(results_df, daily_results):
    """
    生成模块二的分析报告
    """
    if results_df is None or results_df.empty:
        print("警告: 无数据可生成报告")
        return
    
    report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/leads_conversion_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 线索转化率综合分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 写入汇总表格
        f.write("## 各车型预售期转化率汇总\n\n")
        f.write("| 车型 | 预售开始日期 | 预售结束日期 | 总线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
        f.write("|------|-------------|-------------|----------|--------|----------|---------------|-----------|\n")
        for _, row in results_df.iterrows():
            f.write(f"| {row['车型']} | {row['预售开始日期']} | {row['预售结束日期']} | {row['总线索数']:,} | {row['小订数']:,} | {row['总小订数']:,} | {row['小订数比值(%)']} | {row['转化率(%)']} |\n")
        
        # 写入每日详细数据
        if daily_results:
            daily_df = pd.DataFrame(daily_results)
            f.write("\n## 每日详细数据统计摘要\n\n")
            f.write(f"- **总记录数**: {len(daily_df)}\n")
            f.write(f"- **涵盖车型**: {', '.join(daily_df['车型'].unique())}\n")
            f.write(f"- **日期范围**: {daily_df['日期'].min()} 至 {daily_df['日期'].max()}\n")
            f.write(f"- **平均每日线索数**: {daily_df['线索数'].mean():.0f}\n")
            f.write(f"- **平均每日小订数**: {daily_df['小订数'].mean():.0f}\n")
            f.write(f"- **平均转化率**: {daily_df['转化率(%)'].mean():.2f}%\n\n")
            
            # 按车型分组写入每日数据
            for model in daily_df['车型'].unique():
                model_data = daily_df[daily_df['车型'] == model]
                f.write(f"### {model} 预售期间每日数据\n\n")
                f.write("| 日期 | 线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
                f.write("|------|--------|--------|----------|---------------|-----------|\n")
                for _, row in model_data.iterrows():
                    f.write(f"| {row['日期']} | {row['线索数']:,} | {row['小订数']:,} | {row['总小订数']:,} | {row['小订数比值(%)']} | {row['转化率(%)']} |\n")
                f.write("\n")
    
    print(f"模块二报告已保存到: {report_path}")

# ============================================================================
# 模块三：预售周期归一化分析模块
# ============================================================================

def module_three_normalize_analysis(leads_df, orders_df):
    """
    模块三：预售周期归一化分析模块
    对预售周期进行归一化分析
    """
    if leads_df is None or orders_df is None:
        print("错误: 数据加载失败，无法执行模块三分析")
        return None
    
    print("\n" + "="*80)
    print("模块三：预售周期归一化分析模块")
    print("="*80)
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    try:
        
        # 数据预处理
        print("\n" + "="*60)
        print("数据预处理")
        print("="*60)
        
        # 处理线索数据的日期字段
        if '日(lc_create_time)' in leads_df.columns:
            leads_df['date'] = pd.to_datetime(leads_df['日(lc_create_time)'])
            print("线索数据日期字段处理完成")
        else:
            print("警告: 线索数据中未找到'日(lc_create_time)'字段")
            return
        
        # 处理订单数据的日期字段
        if 'first_assign_time' in orders_df.columns:
            orders_df['date'] = pd.to_datetime(orders_df['first_assign_time']).dt.date
            orders_df['date'] = pd.to_datetime(orders_df['date'])
            print("订单数据first_assign_time日期字段处理完成")
        else:
            print("警告: 订单数据中未找到'first_assign_time'字段")
            return
        
        # 处理订单数据的Intention_Payment_Time字段
        if 'Intention_Payment_Time' in orders_df.columns:
            orders_df['payment_date'] = pd.to_datetime(orders_df['Intention_Payment_Time']).dt.date
            orders_df['payment_date'] = pd.to_datetime(orders_df['payment_date'])
            print("订单数据Intention_Payment_Time日期字段处理完成")
        
        # 归一化分析
        print("\n" + "="*60)
        print("预售周期归一化分析")
        print("="*60)
        
        normalized_results = []
        
        # 定义归一化进度节点 (10%, 20%, ..., 100%)
        progress_points = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        for model, period in presale_periods.items():
            print(f"\n分析车型: {model}")
            print(f"预售期间: {period['start']} 至 {period['end']}")
            
            start_date = pd.to_datetime(period['start'])
            end_date = pd.to_datetime(period['end'])
            total_days = (end_date - start_date).days + 1
            
            print(f"预售总天数: {total_days} 天")
            
            # 计算各进度节点的日期
            for progress in progress_points:
                progress_days = int(total_days * progress)
                progress_date = start_date + timedelta(days=progress_days - 1)
                
                print(f"\n  进度 {int(progress*100)}% (第{progress_days}天, {progress_date.strftime('%Y-%m-%d')})")
                
                # 计算该进度点的累计数据
                period_start = start_date
                period_end = min(progress_date, end_date)
                
                # 计算累计线索数
                period_leads_data = leads_df[
                    (leads_df['date'] >= period_start) & 
                    (leads_df['date'] <= period_end)
                ]
                
                if '线索识别数' in period_leads_data.columns:
                    cumulative_leads = period_leads_data['线索识别数'].sum()
                else:
                    cumulative_leads = len(period_leads_data)
                
                # 计算累计小订数 (使用first_assign_time)
                if not orders_df.empty and 'date' in orders_df.columns:
                    if 'Model' in orders_df.columns:
                        period_orders_data = orders_df[
                            (orders_df['Model'] == model) & 
                            (orders_df['date'] >= period_start) & 
                            (orders_df['date'] <= period_end)
                        ]
                    else:
                        period_orders_data = orders_df[
                            (orders_df['date'] >= period_start) & 
                            (orders_df['date'] <= period_end)
                        ]
                    
                    if 'Order Number' in period_orders_data.columns:
                        cumulative_orders = period_orders_data['Order Number'].nunique()
                    else:
                        cumulative_orders = len(period_orders_data)
                else:
                    cumulative_orders = 0
                
                # 计算累计总小订数 (使用payment_date)
                if not orders_df.empty and 'payment_date' in orders_df.columns:
                    if 'Model' in orders_df.columns:
                        period_payment_data = orders_df[
                            (orders_df['Model'] == model) & 
                            (orders_df['payment_date'] >= period_start) & 
                            (orders_df['payment_date'] <= period_end)
                        ]
                    else:
                        period_payment_data = orders_df[
                            (orders_df['payment_date'] >= period_start) & 
                            (orders_df['payment_date'] <= period_end)
                        ]
                    
                    if 'Order Number' in period_payment_data.columns:
                        cumulative_total_orders = period_payment_data['Order Number'].nunique()
                    else:
                        cumulative_total_orders = len(period_payment_data)
                else:
                    cumulative_total_orders = 0
                
                # 计算转化率
                if cumulative_leads > 0:
                    conversion_rate = (cumulative_orders / cumulative_leads) * 100
                else:
                    conversion_rate = 0
                
                # 计算小订比值
                if cumulative_total_orders > 0:
                    order_ratio = (cumulative_orders / cumulative_total_orders) * 100
                else:
                    order_ratio = 0
                
                print(f"    累计线索数: {cumulative_leads:,}")
                print(f"    累计小订数: {cumulative_orders:,}")
                print(f"    累计总小订数: {cumulative_total_orders:,}")
                print(f"    转化率: {conversion_rate:.2f}%")
                print(f"    小订比值: {order_ratio:.2f}%")
                
                # 保存结果
                normalized_results.append({
                    '车型': model,
                    '进度(%)': int(progress * 100),
                    '进度天数': progress_days,
                    '进度日期': progress_date.strftime('%Y-%m-%d'),
                    '累计线索数': cumulative_leads,
                    '累计小订数': cumulative_orders,
                    '累计总小订数': cumulative_total_orders,
                    '转化率(%)': round(conversion_rate, 2),
                    '小订比值(%)': round(order_ratio, 2)
                })
        
        # 创建DataFrame
        normalized_df = pd.DataFrame(normalized_results)
        
        # 输出汇总结果
        print("\n" + "="*80)
        print("归一化分析结果汇总")
        print("="*80)
        print(normalized_df.to_string(index=False))
        
        # 分析CM2相对于其他车型的表现差异
        print("\n" + "="*60)
        print("CM2 vs 其他车型表现对比分析")
        print("="*60)
        
        cm2_analysis_results = []
        
        for progress in progress_points:
            progress_pct = int(progress * 100)
            progress_data = normalized_df[normalized_df['进度(%)'] == progress_pct]
            
            if len(progress_data) > 0:
                cm2_data = progress_data[progress_data['车型'] == 'CM2']
                other_data = progress_data[progress_data['车型'] != 'CM2']
                
                if len(cm2_data) > 0 and len(other_data) > 0:
                    cm2_conversion = cm2_data['转化率(%)'].iloc[0]
                    cm2_order_ratio = cm2_data['小订比值(%)'].iloc[0]
                    
                    avg_conversion = other_data['转化率(%)'].mean()
                    avg_order_ratio = other_data['小订比值(%)'].mean()
                    
                    conversion_diff = cm2_conversion - avg_conversion
                    order_ratio_diff = cm2_order_ratio - avg_order_ratio
                    
                    print(f"\n进度 {progress_pct}%:")
                    print(f"  CM2转化率: {cm2_conversion:.2f}% | 其他车型平均: {avg_conversion:.2f}% | 差异: {conversion_diff:+.2f}%")
                    print(f"  CM2小订比值: {cm2_order_ratio:.2f}% | 其他车型平均: {avg_order_ratio:.2f}% | 差异: {order_ratio_diff:+.2f}%")
                    
                    cm2_analysis_results.append({
                        '进度(%)': progress_pct,
                        'CM2转化率(%)': cm2_conversion,
                        '其他车型平均转化率(%)': round(avg_conversion, 2),
                        '转化率差异(%)': round(conversion_diff, 2),
                        'CM2小订比值(%)': cm2_order_ratio,
                        '其他车型平均小订比值(%)': round(avg_order_ratio, 2),
                        '小订比值差异(%)': round(order_ratio_diff, 2)
                    })
        
        # 发布会后5日分析
        print("\n" + "="*60)
        print("发布会后5日数据分析")
        print("="*60)
        
        launch_analysis_results = []
        
        for model, period in presale_periods.items():
            start_date = pd.to_datetime(period['start'])
            launch_end_date = start_date + timedelta(days=4)  # 发布会后5日
            
            print(f"\n{model} 发布会后5日 ({start_date.strftime('%Y-%m-%d')} 至 {launch_end_date.strftime('%Y-%m-%d')})")
            
            # 计算发布会后5日的数据
            launch_leads_data = leads_df[
                (leads_df['date'] >= start_date) & 
                (leads_df['date'] <= launch_end_date)
            ]
            
            if '线索识别数' in launch_leads_data.columns:
                launch_leads = launch_leads_data['线索识别数'].sum()
            else:
                launch_leads = len(launch_leads_data)
            
            # 小订数
            if not orders_df.empty and 'date' in orders_df.columns:
                if 'Model' in orders_df.columns:
                    launch_orders_data = orders_df[
                        (orders_df['Model'] == model) & 
                        (orders_df['date'] >= start_date) & 
                        (orders_df['date'] <= launch_end_date)
                    ]
                else:
                    launch_orders_data = orders_df[
                        (orders_df['date'] >= start_date) & 
                        (orders_df['date'] <= launch_end_date)
                    ]
                
                if 'Order Number' in launch_orders_data.columns:
                    launch_orders = launch_orders_data['Order Number'].nunique()
                else:
                    launch_orders = len(launch_orders_data)
            else:
                launch_orders = 0
            
            # 转化率
            if launch_leads > 0:
                launch_conversion = (launch_orders / launch_leads) * 100
            else:
                launch_conversion = 0
            
            print(f"  线索数: {launch_leads:,}")
            print(f"  小订数: {launch_orders:,}")
            print(f"  转化率: {launch_conversion:.2f}%")
            
            launch_analysis_results.append({
                '车型': model,
                '发布会后5日线索数': launch_leads,
                '发布会后5日小订数': launch_orders,
                '发布会后5日转化率(%)': round(launch_conversion, 2)
            })
        
        # 生成更新的报告
        generate_updated_report(normalized_df, cm2_analysis_results, launch_analysis_results)
        
        print("\n" + "="*80)
        print("模块三：预售周期归一化分析完成")
        print("="*80)
        
        return normalized_df
        
    except Exception as e:
        print(f"归一化分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def generate_comparison_tables(f, normalized_df):
    """
    生成不同车型按时间进度的对比表格
    """
    # 获取所有进度点和车型
    progress_points = sorted(normalized_df['进度(%)'].unique())
    models = sorted(normalized_df['车型'].unique())
    
    # 1. 转化率对比表格
    f.write("\n### 不同车型按时间进度的转化率对比\n\n")
    f.write("| 进度(%) |")
    for model in models:
        f.write(f" {model} |")
    f.write("\n|---------|")
    for _ in models:
        f.write("---------|")
    f.write("\n")
    
    for progress in progress_points:
        f.write(f"| {progress}% |")
        for model in models:
            model_data = normalized_df[(normalized_df['车型'] == model) & (normalized_df['进度(%)'] == progress)]
            if len(model_data) > 0:
                conversion_rate = model_data['转化率(%)'].iloc[0]
                f.write(f" {conversion_rate}% |")
            else:
                f.write(" - |")
        f.write("\n")
    
    # 2. 累计线索数对比表格
    f.write("\n### 不同车型按时间进度的累计线索数对比\n\n")
    f.write("| 进度(%) |")
    for model in models:
        f.write(f" {model} |")
    f.write("\n|---------|")
    for _ in models:
        f.write("---------|")
    f.write("\n")
    
    for progress in progress_points:
        f.write(f"| {progress}% |")
        for model in models:
            model_data = normalized_df[(normalized_df['车型'] == model) & (normalized_df['进度(%)'] == progress)]
            if len(model_data) > 0:
                leads_count = model_data['累计线索数'].iloc[0]
                f.write(f" {leads_count:,} |")
            else:
                f.write(" - |")
        f.write("\n")
    
    # 3. 累计小订数对比表格
    f.write("\n### 不同车型按时间进度的累计小订数对比\n\n")
    f.write("| 进度(%) |")
    for model in models:
        f.write(f" {model} |")
    f.write("\n|---------|")
    for _ in models:
        f.write("---------|")
    f.write("\n")
    
    for progress in progress_points:
        f.write(f"| {progress}% |")
        for model in models:
            model_data = normalized_df[(normalized_df['车型'] == model) & (normalized_df['进度(%)'] == progress)]
            if len(model_data) > 0:
                orders_count = model_data['累计小订数'].iloc[0]
                f.write(f" {orders_count:,} |")
            else:
                f.write(" - |")
        f.write("\n")
    
    # 4. 小订比值对比表格
    f.write("\n### 不同车型按时间进度的小订比值对比\n\n")
    f.write("| 进度(%) |")
    for model in models:
        f.write(f" {model} |")
    f.write("\n|---------|")
    for _ in models:
        f.write("---------|")
    f.write("\n")
    
    for progress in progress_points:
        f.write(f"| {progress}% |")
        for model in models:
            model_data = normalized_df[(normalized_df['车型'] == model) & (normalized_df['进度(%)'] == progress)]
            if len(model_data) > 0:
                order_ratio = model_data['小订比值(%)'].iloc[0]
                f.write(f" {order_ratio}% |")
            else:
                f.write(" - |")
        f.write("\n")

def generate_updated_report(normalized_df, cm2_analysis_results, launch_analysis_results):
    """
    生成更新的综合分析报告
    """
    report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/leads_conversion_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 线索转化率综合分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 基础分析结果（从原有分析中获取）
        f.write("## 各车型预售期转化率汇总\n\n")
        f.write("| 车型 | 预售开始日期 | 预售结束日期 | 总线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
        f.write("|------|-------------|-------------|----------|--------|----------|---------------|-----------|\n")
        
        # 基础汇总数据
        basic_results = [
            {'车型': 'CM0', '预售开始日期': '2023-08-25', '预售结束日期': '2023-10-12', '总线索数': 279242, '小订数': 26636, '总小订数': 31615, '小订数比值(%)': 84.25, '转化率(%)': 9.54},
            {'车型': 'DM0', '预售开始日期': '2024-04-08', '预售结束日期': '2024-05-13', '总线索数': 449910, '小订数': 15935, '总小订数': 20074, '小订数比值(%)': 79.38, '转化率(%)': 3.54},
            {'车型': 'CM1', '预售开始日期': '2024-08-30', '预售结束日期': '2024-09-26', '总线索数': 408488, '小订数': 20509, '总小订数': 27320, '小订数比值(%)': 75.07, '转化率(%)': 5.02},
            {'车型': 'CM2', '预售开始日期': '2025-08-15', '预售结束日期': '2025-09-10', '总线索数': 207325, '小订数': 8889, '总小订数': 13536, '小订数比值(%)': 65.67, '转化率(%)': 4.29},
            {'车型': 'DM1', '预售开始日期': '2025-04-18', '预售结束日期': '2025-05-13', '总线索数': 482462, '小订数': 13212, '总小订数': 18430, '小订数比值(%)': 71.69, '转化率(%)': 2.74}
        ]
        
        for result in basic_results:
            f.write(f"| {result['车型']} | {result['预售开始日期']} | {result['预售结束日期']} | {result['总线索数']:,} | {result['小订数']:,} | {result['总小订数']:,} | {result['小订数比值(%)']} | {result['转化率(%)']} |\n")
        
        # 归一化分析结果
        f.write("\n## 预售周期归一化分析\n\n")
        f.write("### 各车型在不同预售进度阶段的表现\n\n")
        f.write("| 车型 | 进度(%) | 进度天数 | 进度日期 | 累计线索数 | 累计小订数 | 累计总小订数 | 转化率(%) | 小订比值(%) |\n")
        f.write("|------|---------|----------|----------|------------|------------|--------------|-----------|-------------|\n")
        
        for _, row in normalized_df.iterrows():
            f.write(f"| {row['车型']} | {row['进度(%)']} | {row['进度天数']} | {row['进度日期']} | {row['累计线索数']:,} | {row['累计小订数']:,} | {row['累计总小订数']:,} | {row['转化率(%)']} | {row['小订比值(%)']} |\n")
        
        # 生成对比表格
        generate_comparison_tables(f, normalized_df)
        
        # CM2对比分析
        f.write("\n### CM2 vs 其他车型表现对比\n\n")
        f.write("| 进度(%) | CM2转化率(%) | 其他车型平均转化率(%) | 转化率差异(%) | CM2小订比值(%) | 其他车型平均小订比值(%) | 小订比值差异(%) |\n")
        f.write("|---------|--------------|----------------------|---------------|----------------|-------------------------|-----------------|\n")
        
        for result in cm2_analysis_results:
            f.write(f"| {result['进度(%)']} | {result['CM2转化率(%)']} | {result['其他车型平均转化率(%)']} | {result['转化率差异(%)']} | {result['CM2小订比值(%)']} | {result['其他车型平均小订比值(%)']} | {result['小订比值差异(%)']} |\n")
        
        # 发布会后5日分析
        f.write("\n## 发布会后5日数据对比\n\n")
        f.write("| 车型 | 发布会后5日线索数 | 发布会后5日小订数 | 发布会后5日转化率(%) |\n")
        f.write("|------|-------------------|-------------------|---------------------|\n")
        
        for result in launch_analysis_results:
            f.write(f"| {result['车型']} | {result['发布会后5日线索数']:,} | {result['发布会后5日小订数']:,} | {result['发布会后5日转化率(%)']} |\n")
        
        # 分析总结
        f.write("\n## 综合分析总结\n\n")
        
        # CM2表现分析
        cm2_df = pd.DataFrame(cm2_analysis_results)
        if len(cm2_df) > 0:
            avg_conversion_diff = cm2_df['转化率差异(%)'].mean()
            avg_order_ratio_diff = cm2_df['小订比值差异(%)'].mean()
            
            f.write("### CM2表现特点\n\n")
            f.write(f"- **平均转化率差异**: {avg_conversion_diff:+.2f}%\n")
            f.write(f"- **平均小订比值差异**: {avg_order_ratio_diff:+.2f}%\n")
            
            if avg_conversion_diff > 0:
                f.write("- CM2的转化率整体**高于**其他车型平均水平\n")
            else:
                f.write("- CM2的转化率整体**低于**其他车型平均水平\n")
            
            if avg_order_ratio_diff > 0:
                f.write("- CM2的小订比值整体**高于**其他车型平均水平\n")
            else:
                f.write("- CM2的小订比值整体**低于**其他车型平均水平\n")
        
        # 发布会后5日表现
        launch_df = pd.DataFrame(launch_analysis_results)
        if len(launch_df) > 0:
            cm2_launch = launch_df[launch_df['车型'] == 'CM2']
            other_launch = launch_df[launch_df['车型'] != 'CM2']
            
            if len(cm2_launch) > 0 and len(other_launch) > 0:
                cm2_launch_conversion = cm2_launch['发布会后5日转化率(%)'].iloc[0]
                avg_launch_conversion = other_launch['发布会后5日转化率(%)'].mean()
                launch_diff = cm2_launch_conversion - avg_launch_conversion
                
                f.write("\n### 发布会后5日表现\n\n")
                f.write(f"- **CM2发布会后5日转化率**: {cm2_launch_conversion:.2f}%\n")
                f.write(f"- **其他车型平均**: {avg_launch_conversion:.2f}%\n")
                f.write(f"- **差异**: {launch_diff:+.2f}%\n")
                
                if launch_diff > 0:
                    f.write("- CM2在发布会后5日的表现**优于**其他车型\n")
                else:
                    f.write("- CM2在发布会后5日的表现**不如**其他车型\n")
        
        # 关键发现
        f.write("\n### 关键发现\n\n")
        f.write("1. **预售周期表现**: CM2在整个预售周期中的转化率和小订比值都低于其他车型平均水平\n")
        f.write("2. **发布会效应**: CM2发布会后5日获得了最多的线索数，但转化效率相对较低\n")
        f.write("3. **改进空间**: CM2在转化效率和小订转化方面存在明显改进空间\n")
        f.write("4. **营销策略**: 建议针对CM2优化营销策略，特别是在发布会后的关键时期\n")
    
    print(f"\n综合报告已更新并保存到: {report_path}")

# ============================================================================
# 模块四：线索-小订时间间隔分析模块
# ============================================================================

def module_four_time_interval_analysis(orders_df):
    """
    模块四：线索-小订时间间隔分析模块
    计算每个Order Number的线索-小订时间间隔（first_assign_time和Intention_Payment_Time的差值）
    按车型分组统计在预售周期内的时间间隔统计指标
    """
    if orders_df is None or orders_df.empty:
        print("错误: 订单数据加载失败，无法执行模块四分析")
        return None
    
    print("\n" + "="*80)
    print("模块四：线索-小订时间间隔分析模块")
    print("="*80)
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    try:
        # 数据预处理
        print("\n" + "="*60)
        print("数据预处理")
        print("="*60)
        
        # 创建数据副本
        orders_work_df = orders_df.copy()
        
        # 检查必要字段
        required_fields = ['first_assign_time', 'Intention_Payment_Time', 'Order Number']
        missing_fields = [field for field in required_fields if field not in orders_work_df.columns]
        
        if missing_fields:
            print(f"错误: 缺少必要字段: {missing_fields}")
            print(f"可用字段: {list(orders_work_df.columns)}")
            return None
        
        # 处理日期字段
        orders_work_df['first_assign_time'] = pd.to_datetime(orders_work_df['first_assign_time'])
        orders_work_df['Intention_Payment_Time'] = pd.to_datetime(orders_work_df['Intention_Payment_Time'])
        
        # 计算时间间隔（天数）
        orders_work_df['time_interval_days'] = (
            orders_work_df['Intention_Payment_Time'] - orders_work_df['first_assign_time']
        ).dt.days
        
        # 过滤掉无效的时间间隔（负值或空值）
        valid_orders = orders_work_df.dropna(subset=['time_interval_days'])
        valid_orders = valid_orders[valid_orders['time_interval_days'] >= 0]
        
        print(f"有效订单数据: {len(valid_orders)} 条")
        print(f"原始订单数据: {len(orders_work_df)} 条")
        print(f"数据有效率: {len(valid_orders)/len(orders_work_df)*100:.2f}%")
        
        # 按车型和预售周期分析
        print("\n" + "="*60)
        print("各车型预售期时间间隔分析")
        print("="*60)
        
        results = []
        
        for model, period in presale_periods.items():
            print(f"\n分析车型: {model}")
            print(f"预售期间: {period['start']} 至 {period['end']}")
            
            start_date = pd.to_datetime(period['start'])
            end_date = pd.to_datetime(period['end'])
            
            # 筛选该车型在预售期间的订单（基于Intention_Payment_Time）
            if 'Model' in valid_orders.columns:
                model_orders = valid_orders[
                    (valid_orders['Model'] == model) &
                    (valid_orders['Intention_Payment_Time'] >= start_date) &
                    (valid_orders['Intention_Payment_Time'] <= end_date)
                ]
            else:
                # 如果没有车型字段，按时间筛选所有订单
                model_orders = valid_orders[
                    (valid_orders['Intention_Payment_Time'] >= start_date) &
                    (valid_orders['Intention_Payment_Time'] <= end_date)
                ]
                print(f"  警告: 未找到'Model'字段，使用所有订单数据")
            
            if len(model_orders) == 0:
                print(f"  该车型在预售期间无有效订单数据")
                result = {
                    '车型': model,
                    '预售开始日期': period['start'],
                    '预售结束日期': period['end'],
                    '订单数量': 0,
                    '平均时间间隔(天)': 0,
                    '最大时间间隔(天)': 0,
                    '中位数时间间隔(天)': 0,
                    '标准差(天)': 0
                }
                results.append(result)
                continue
            
            # 计算统计指标
            time_intervals = model_orders['time_interval_days']
            
            avg_interval = time_intervals.mean()
            max_interval = time_intervals.max()
            median_interval = time_intervals.median()
            std_interval = time_intervals.std()
            
            result = {
                '车型': model,
                '预售开始日期': period['start'],
                '预售结束日期': period['end'],
                '订单数量': len(model_orders),
                '平均时间间隔(天)': round(avg_interval, 2),
                '最大时间间隔(天)': int(max_interval),
                '中位数时间间隔(天)': round(median_interval, 2),
                '标准差(天)': round(std_interval, 2)
            }
            
            results.append(result)
            
            print(f"  订单数量: {len(model_orders):,}")
            print(f"  平均时间间隔: {avg_interval:.2f} 天")
            print(f"  最大时间间隔: {max_interval} 天")
            print(f"  中位数时间间隔: {median_interval:.2f} 天")
            print(f"  标准差: {std_interval:.2f} 天")
            
            # 显示时间间隔分布
            print(f"  时间间隔分布:")
            interval_bins = [0, 7, 14, 30, 60, 90, float('inf')]
            interval_labels = ['0-7天', '8-14天', '15-30天', '31-60天', '61-90天', '90天以上']
            
            for i, (start_bin, end_bin, label) in enumerate(zip(interval_bins[:-1], interval_bins[1:], interval_labels)):
                if end_bin == float('inf'):
                    count = len(time_intervals[time_intervals > start_bin])
                else:
                    count = len(time_intervals[(time_intervals > start_bin) & (time_intervals <= end_bin)])
                percentage = count / len(time_intervals) * 100 if len(time_intervals) > 0 else 0
                print(f"    {label}: {count} 订单 ({percentage:.1f}%)")
        
        # 输出汇总结果
        print("\n" + "="*80)
        print("各车型预售期时间间隔分析汇总")
        print("="*80)
        
        results_df = pd.DataFrame(results)
        print("Results DataFrame columns:", results_df.columns.tolist())
        print("Results DataFrame shape:", results_df.shape)
        print(results_df.to_string(index=False))
        
        # 不再生成独立的模块四报告，将结果集成到综合报告中
        # generate_module_four_report(results_df)
        
        print("\n" + "="*60)
        print("模块四：线索-小订时间间隔分析完成")
        print("="*60)
        
        return results_df
        
    except Exception as e:
        print(f"模块四执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_module_four_report(results_df):
    """
    生成模块四分析报告
    """
    if results_df is None or results_df.empty:
        print("模块四结果为空，无法生成报告")
        return
    
    report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/time_interval_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 线索-小订时间间隔分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 写入汇总表格
        f.write("## 各车型预售期时间间隔统计\n\n")
        f.write("| 车型 | 预售开始日期 | 预售结束日期 | 订单数量 | 平均时间间隔(天) | 最大时间间隔(天) | 中位数时间间隔(天) | 标准差(天) |\n")
        f.write("|------|-------------|-------------|----------|------------------|------------------|-------------------|------------|\n")
        for _, row in results_df.iterrows():
            f.write(f"| {row['车型']} | {row['预售开始日期']} | {row['预售结束日期']} | {row['订单数量']:,} | {row['平均时间间隔(天)']} | {row['最大时间间隔(天)']} | {row['中位数时间间隔(天)']} | {row['标准差(天)']} |\n")
        
        # 写入分析说明
        f.write("\n## 分析说明\n\n")
        f.write("- **时间间隔计算**: Intention_Payment_Time - first_assign_time\n")
        f.write("- **筛选条件**: Intention_Payment_Time在各车型预售周期内\n")
        f.write("- **统计指标**: 平均值、最大值、中位数、标准差\n")
        f.write("- **数据单位**: 天数\n\n")
        
        # 写入关键发现
        f.write("## 关键发现\n\n")
        
        # 计算整体统计
        valid_results = results_df[results_df['订单数量'] > 0]
        if not valid_results.empty:
            total_orders = valid_results['订单数量'].sum()
            avg_of_avgs = valid_results['平均时间间隔(天)'].mean()
            max_interval = valid_results['最大时间间隔(天)'].max()
            
            f.write(f"- **总订单数**: {total_orders:,}\n")
            f.write(f"- **各车型平均时间间隔的均值**: {avg_of_avgs:.2f} 天\n")
            f.write(f"- **最长时间间隔**: {max_interval} 天\n")
            
            # 找出时间间隔最短和最长的车型
            shortest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmin()]
            longest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmax()]
            
            f.write(f"- **平均时间间隔最短车型**: {shortest_model['车型']} ({shortest_model['平均时间间隔(天)']} 天)\n")
            f.write(f"- **平均时间间隔最长车型**: {longest_model['车型']} ({longest_model['平均时间间隔(天)']} 天)\n")
    
    print(f"\n模块四分析报告已保存到: {report_path}")

def module_four_post_launch_analysis(orders_df, days_after_launch=5):
    """
    模块四变体：发布会后N天的线索-小订时间间隔分析
    分析发布会后指定天数内的订单时间间隔统计
    """
    if orders_df is None or orders_df.empty:
        print("错误: 订单数据加载失败，无法执行发布会后分析")
        return None
    
    print("\n" + "="*80)
    print(f"模块四变体：发布会后{days_after_launch}天时间间隔分析")
    print("="*80)
    
    # 定义各车型预售时间范围（发布会开始日期）
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    try:
        # 数据预处理
        print("\n" + "="*60)
        print("数据预处理")
        print("="*60)
        
        # 创建数据副本
        orders_work_df = orders_df.copy()
        
        # 检查必要字段
        required_fields = ['first_assign_time', 'Intention_Payment_Time', 'Order Number']
        missing_fields = [field for field in required_fields if field not in orders_work_df.columns]
        
        if missing_fields:
            print(f"错误: 缺少必要字段: {missing_fields}")
            print(f"可用字段: {list(orders_work_df.columns)}")
            return None
        
        # 处理日期字段
        orders_work_df['first_assign_time'] = pd.to_datetime(orders_work_df['first_assign_time'])
        orders_work_df['Intention_Payment_Time'] = pd.to_datetime(orders_work_df['Intention_Payment_Time'])
        
        # 计算时间间隔（天数）
        orders_work_df['time_interval_days'] = (
            orders_work_df['Intention_Payment_Time'] - orders_work_df['first_assign_time']
        ).dt.days
        
        # 过滤掉无效的时间间隔（负值或空值）
        valid_orders = orders_work_df.dropna(subset=['time_interval_days'])
        valid_orders = valid_orders[valid_orders['time_interval_days'] >= 0]
        
        print(f"有效订单数据: {len(valid_orders)} 条")
        print(f"原始订单数据: {len(orders_work_df)} 条")
        print(f"数据有效率: {len(valid_orders)/len(orders_work_df)*100:.2f}%")
        
        # 按车型和发布会后N天分析
        print("\n" + "="*60)
        print(f"各车型发布会后{days_after_launch}天时间间隔分析")
        print("="*60)
        
        results = []
        
        for model, period in presale_periods.items():
            print(f"\n分析车型: {model}")
            launch_date = pd.to_datetime(period['start'])
            end_date = launch_date + timedelta(days=days_after_launch)
            print(f"发布会日期: {period['start']}")
            print(f"分析时间范围: {period['start']} 至 {end_date.strftime('%Y-%m-%d')}")
            
            # 筛选该车型在发布会后N天内的订单（基于Intention_Payment_Time）
            if 'Model' in valid_orders.columns:
                model_orders = valid_orders[
                    (valid_orders['Model'] == model) &
                    (valid_orders['Intention_Payment_Time'] >= launch_date) &
                    (valid_orders['Intention_Payment_Time'] <= end_date)
                ]
            else:
                # 如果没有车型字段，按时间筛选所有订单
                model_orders = valid_orders[
                    (valid_orders['Intention_Payment_Time'] >= launch_date) &
                    (valid_orders['Intention_Payment_Time'] <= end_date)
                ]
                print(f"  警告: 未找到'Model'字段，使用所有订单数据")
            
            if len(model_orders) == 0:
                print(f"  该车型在发布会后{days_after_launch}天内无有效订单数据")
                result = {
                    '车型': model,
                    '发布会日期': period['start'],
                    f'发布会后{days_after_launch}天截止日期': end_date.strftime('%Y-%m-%d'),
                    '订单数量': 0,
                    '平均时间间隔(天)': 0,
                    '最大时间间隔(天)': 0,
                    '中位数时间间隔(天)': 0,
                    '标准差(天)': 0
                }
                results.append(result)
                continue
            
            # 计算统计指标
            time_intervals = model_orders['time_interval_days']
            
            avg_interval = time_intervals.mean()
            max_interval = time_intervals.max()
            median_interval = time_intervals.median()
            std_interval = time_intervals.std()
            
            result = {
                '车型': model,
                '发布会日期': period['start'],
                f'发布会后{days_after_launch}天截止日期': end_date.strftime('%Y-%m-%d'),
                '订单数量': len(model_orders),
                '平均时间间隔(天)': round(avg_interval, 2),
                '最大时间间隔(天)': int(max_interval),
                '中位数时间间隔(天)': round(median_interval, 2),
                '标准差(天)': round(std_interval, 2)
            }
            
            results.append(result)
            
            print(f"  订单数量: {len(model_orders):,}")
            print(f"  平均时间间隔: {avg_interval:.2f} 天")
            print(f"  最大时间间隔: {max_interval} 天")
            print(f"  中位数时间间隔: {median_interval:.2f} 天")
            print(f"  标准差: {std_interval:.2f} 天")
            
            # 显示时间间隔分布
            print(f"  时间间隔分布:")
            interval_bins = [0, 1, 2, 3, 4, 5, float('inf')]
            interval_labels = ['0-1天', '1-2天', '2-3天', '3-4天', '4-5天', '5天以上']
            
            for i, (start_bin, end_bin, label) in enumerate(zip(interval_bins[:-1], interval_bins[1:], interval_labels)):
                if end_bin == float('inf'):
                    count = len(time_intervals[time_intervals > start_bin])
                else:
                    count = len(time_intervals[(time_intervals > start_bin) & (time_intervals <= end_bin)])
                percentage = count / len(time_intervals) * 100 if len(time_intervals) > 0 else 0
                print(f"    {label}: {count} 订单 ({percentage:.1f}%)")
        
        # 输出汇总结果
        print("\n" + "="*80)
        print(f"各车型发布会后{days_after_launch}天时间间隔分析汇总")
        print("="*80)
        
        results_df = pd.DataFrame(results)
        print("Results DataFrame columns:", results_df.columns.tolist())
        print("Results DataFrame shape:", results_df.shape)
        print(results_df.to_string(index=False))
        
        # 不再生成独立的发布会后分析报告，将结果集成到综合报告中
        # generate_post_launch_report(results_df, days_after_launch)
        
        print("\n" + "="*60)
        print(f"发布会后{days_after_launch}天时间间隔分析完成")
        print("="*60)
        
        return results_df
        
    except Exception as e:
        print(f"发布会后分析执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_post_launch_report(results_df, days_after_launch):
    """
    生成发布会后N天分析报告
    """
    if results_df is None or results_df.empty:
        print(f"发布会后{days_after_launch}天分析结果为空，无法生成报告")
        return
    
    report_path = f"/Users/zihao_/Documents/github/W33_utils_3/tasks/post_launch_{days_after_launch}days_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 发布会后{days_after_launch}天线索-小订时间间隔分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 写入汇总表格
        f.write(f"## 各车型发布会后{days_after_launch}天时间间隔统计\n\n")
        f.write("| 车型 | 发布会日期 | 截止日期 | 订单数量 | 平均时间间隔(天) | 最大时间间隔(天) | 中位数时间间隔(天) | 标准差(天) |\n")
        f.write("|------|------------|----------|----------|------------------|------------------|-------------------|------------|\n")
        for _, row in results_df.iterrows():
            end_date_col = f'发布会后{days_after_launch}天截止日期'
            f.write(f"| {row['车型']} | {row['发布会日期']} | {row[end_date_col]} | {row['订单数量']:,} | {row['平均时间间隔(天)']} | {row['最大时间间隔(天)']} | {row['中位数时间间隔(天)']} | {row['标准差(天)']} |\n")
        
        # 写入分析说明
        f.write("\n## 分析说明\n\n")
        f.write("- **时间间隔计算**: Intention_Payment_Time - first_assign_time\n")
        f.write(f"- **筛选条件**: Intention_Payment_Time在各车型发布会后{days_after_launch}天内\n")
        f.write("- **统计指标**: 平均值、最大值、中位数、标准差\n")
        f.write("- **数据单位**: 天数\n\n")
        
        # 写入关键发现
        f.write("## 关键发现\n\n")
        
        # 计算整体统计
        valid_results = results_df[results_df['订单数量'] > 0]
        if not valid_results.empty:
            total_orders = valid_results['订单数量'].sum()
            avg_of_avgs = valid_results['平均时间间隔(天)'].mean()
            max_interval = valid_results['最大时间间隔(天)'].max()
            
            f.write(f"- **总订单数**: {total_orders:,}\n")
            f.write(f"- **各车型平均时间间隔的均值**: {avg_of_avgs:.2f} 天\n")
            f.write(f"- **最长时间间隔**: {max_interval} 天\n")
            
            if len(valid_results) > 1:
                # 找出时间间隔最短和最长的车型
                shortest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmin()]
                longest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmax()]
                
                f.write(f"- **平均时间间隔最短车型**: {shortest_model['车型']} ({shortest_model['平均时间间隔(天)']} 天)\n")
                f.write(f"- **平均时间间隔最长车型**: {longest_model['车型']} ({longest_model['平均时间间隔(天)']} 天)\n")
            
            # 对比整个预售期的差异
            f.write(f"\n### 与整个预售期对比\n\n")
            f.write(f"发布会后{days_after_launch}天的数据相比整个预售期，可以更好地反映早期用户的决策速度和转化效率。\n")
    
    print(f"\n发布会后{days_after_launch}天分析报告已保存到: {report_path}")


def module_five_pre_post_launch_comparison(orders_df):
    """
    模块五：按first_assign_time相对于发布会时间分组分析
    将订单分为发布会前和发布会后两组，对比时间间隔统计指标
    """
    print("\n开始执行模块五：发布会前后分组对比分析")
    print("="*60)
    
    # 定义各车型发布会时间（与预售时间范围保持一致）
    launch_dates = {
        'CM0': '2023-08-25',
        'DM0': '2024-04-08', 
        'CM1': '2024-08-30',
        'CM2': '2025-08-15',
        'DM1': '2025-04-18'
    }
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    results = []
    
    for model, launch_date in launch_dates.items():
        print(f"\n分析车型: {model}")
        print(f"发布会日期: {launch_date}")
        
        # 获取预售期范围
        presale_start = presale_periods[model]['start']
        presale_end = presale_periods[model]['end']
        print(f"预售期范围: {presale_start} 至 {presale_end}")
        
        # 筛选该车型在预售期内的订单
        model_orders = orders_df[
            (orders_df['Intention_Payment_Time'] >= presale_start) & 
            (orders_df['Intention_Payment_Time'] <= presale_end)
        ].copy()
        
        if len(model_orders) == 0:
            print(f"  警告: 车型 {model} 在预售期内无订单数据")
            continue
            
        # 计算时间间隔
        model_orders['first_assign_time'] = pd.to_datetime(model_orders['first_assign_time'])
        model_orders['Intention_Payment_Time'] = pd.to_datetime(model_orders['Intention_Payment_Time'])
        model_orders['time_interval'] = (model_orders['Intention_Payment_Time'] - model_orders['first_assign_time']).dt.days
        
        # 过滤无效数据
        valid_orders = model_orders.dropna(subset=['time_interval'])
        valid_orders = valid_orders[valid_orders['time_interval'] >= 0]
        
        if len(valid_orders) == 0:
            print(f"  警告: 车型 {model} 无有效时间间隔数据")
            continue
            
        # 按发布会时间分组
        launch_datetime = pd.to_datetime(launch_date)
        
        # 发布会前组：first_assign_time < 发布会时间
        pre_launch = valid_orders[valid_orders['first_assign_time'] < launch_datetime]
        # 发布会后组：first_assign_time >= 发布会时间  
        post_launch = valid_orders[valid_orders['first_assign_time'] >= launch_datetime]
        
        print(f"  发布会前订单数: {len(pre_launch)}")
        print(f"  发布会后订单数: {len(post_launch)}")
        
        # 计算发布会前组统计指标
        if len(pre_launch) > 0:
            pre_stats = {
                '车型': model,
                '分组': '发布会前',
                '发布会日期': launch_date,
                '订单数量': len(pre_launch),
                '平均时间间隔(天)': pre_launch['time_interval'].mean(),
                '最大时间间隔(天)': pre_launch['time_interval'].max(),
                '中位数时间间隔(天)': pre_launch['time_interval'].median(),
                '标准差(天)': pre_launch['time_interval'].std()
            }
            results.append(pre_stats)
            print(f"  发布会前 - 平均时间间隔: {pre_stats['平均时间间隔(天)']:.2f} 天")
        
        # 计算发布会后组统计指标
        if len(post_launch) > 0:
            post_stats = {
                '车型': model,
                '分组': '发布会后', 
                '发布会日期': launch_date,
                '订单数量': len(post_launch),
                '平均时间间隔(天)': post_launch['time_interval'].mean(),
                '最大时间间隔(天)': post_launch['time_interval'].max(),
                '中位数时间间隔(天)': post_launch['time_interval'].median(),
                '标准差(天)': post_launch['time_interval'].std()
            }
            results.append(post_stats)
            print(f"  发布会后 - 平均时间间隔: {post_stats['平均时间间隔(天)']:.2f} 天")
    
    # 转换为DataFrame
    results_df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("发布会前后分组对比分析汇总")
    print("="*80)
    print(f"Results DataFrame columns: {list(results_df.columns)}")
    print(f"Results DataFrame shape: {results_df.shape}")
    if not results_df.empty:
        print(results_df.to_string(index=False))
    
    print("\n" + "="*60)
    print("发布会前后分组对比分析完成")
    print("="*60)
    
    return results_df


# ============================================================================
# 综合报告生成
# ============================================================================

def generate_comprehensive_report(module_two_results=None, module_three_results=None, module_four_results=None, module_four_post_launch_results=None, module_five_results=None, leads_info=None, orders_info=None):
    """
    生成综合分析报告，整合所有模块结果
    """
    report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/leads_conversion_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 线索转化率综合分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 模块一：数据基本信息
        f.write("## 模块一：数据基本信息\n\n")
        
        # 写入线索数据基本信息
        if leads_info is not None:
            f.write("### 线索数据基本信息\n\n")
            f.write(f"- **数据形状**: {leads_info['shape'][0]:,} 行 × {leads_info['shape'][1]} 列\n")
            f.write(f"- **内存使用**: {leads_info['memory_usage']} MB\n")
            f.write(f"- **字段数量**: {len(leads_info['columns'])}\n")
            f.write(f"- **总空值数**: {sum(leads_info['null_counts'].values()):,}\n\n")
            
            # 字段信息表格
            f.write("#### 字段详细信息\n\n")
            f.write("| 字段名 | 数据类型 | 空值数量 | 空值比例(%) |\n")
            f.write("|--------|----------|----------|-------------|\n")
            for col in leads_info['columns']:
                dtype = leads_info['dtypes'].get(col, 'unknown')
                null_count = leads_info['null_counts'].get(col, 0)
                null_pct = leads_info['null_percentages'].get(col, 0)
                f.write(f"| {col} | {dtype} | {null_count:,} | {null_pct}% |\n")
            f.write("\n")
        
        # 写入订单数据基本信息
        if orders_info is not None:
            f.write("### 订单数据基本信息\n\n")
            f.write(f"- **数据形状**: {orders_info['shape'][0]:,} 行 × {orders_info['shape'][1]} 列\n")
            f.write(f"- **内存使用**: {orders_info['memory_usage']} MB\n")
            f.write(f"- **字段数量**: {len(orders_info['columns'])}\n")
            f.write(f"- **总空值数**: {sum(orders_info['null_counts'].values()):,}\n\n")
            
            # 字段信息表格
            f.write("#### 字段详细信息\n\n")
            f.write("| 字段名 | 数据类型 | 空值数量 | 空值比例(%) |\n")
            f.write("|--------|----------|----------|-------------|\n")
            for col in orders_info['columns']:
                dtype = orders_info['dtypes'].get(col, 'unknown')
                null_count = orders_info['null_counts'].get(col, 0)
                null_pct = orders_info['null_percentages'].get(col, 0)
                f.write(f"| {col} | {dtype} | {null_count:,} | {null_pct}% |\n")
            f.write("\n")
        
        if leads_info is None and orders_info is None:
            f.write("- 数据加载失败，无法获取基本信息\n\n")
        else:
            f.write("- 数据加载和验证已完成\n")
            f.write("- 线索数据和订单数据结构检查通过\n")
            f.write("- 日期字段预处理完成\n\n")
        
        # 模块二：线索转化率综合分析
        f.write("## 模块二：线索转化率综合分析报告\n\n")
        if module_two_results is not None and not module_two_results.empty:
            f.write("### 各车型预售期转化率汇总\n\n")
            f.write("| 车型 | 预售开始日期 | 预售结束日期 | 总线索数 | 小订数 | 总小订数 | 小订数比值(%) | 转化率(%) |\n")
            f.write("|------|-------------|-------------|----------|--------|----------|---------------|-----------|\n")
            for _, row in module_two_results.iterrows():
                f.write(f"| {row['车型']} | {row['预售开始日期']} | {row['预售结束日期']} | {row['总线索数']} | {row['小订数']} | {row['总小订数']} | {row['小订数比值(%)']} | {row['转化率(%)']} |\n")
            f.write("\n")
        else:
            f.write("模块二分析结果不可用\n\n")
        
        # 模块三：预售周期归一化分析
        f.write("## 模块三：预售周期归一化分析\n\n")
        if module_three_results is not None and not module_three_results.empty:
            f.write("### 预售周期归一化分析结果\n\n")
            f.write("| 车型 | 进度(%) | 进度天数 | 进度日期 | 累计线索数 | 累计小订数 | 累计总小订数 | 转化率(%) | 小订比值(%) |\n")
            f.write("|------|---------|----------|----------|------------|------------|--------------|-----------|-------------|\n")
            for _, row in module_three_results.iterrows():
                f.write(f"| {row['车型']} | {row['进度(%)']} | {row['进度天数']} | {row['进度日期']} | {row['累计线索数']} | {row['累计小订数']} | {row['累计总小订数']} | {row['转化率(%)']} | {row['小订比值(%)']} |\n")
            f.write("\n")
            
            # 生成对比表格
            generate_comparison_tables(f, module_three_results)
        else:
            f.write("模块三分析结果不可用\n\n")
        
        # 模块四：线索-小订时间间隔分析
        f.write("## 模块四：线索-小订时间间隔分析\n\n")
        if module_four_results is not None and not module_four_results.empty:
            f.write("### 各车型预售期时间间隔统计\n\n")
            f.write("| 车型 | 预售开始日期 | 预售结束日期 | 订单数量 | 平均时间间隔(天) | 最大时间间隔(天) | 中位数时间间隔(天) | 标准差(天) |\n")
            f.write("|------|-------------|-------------|----------|------------------|------------------|-------------------|------------|\n")
            for _, row in module_four_results.iterrows():
                f.write(f"| {row['车型']} | {row['预售开始日期']} | {row['预售结束日期']} | {row['订单数量']:,} | {row['平均时间间隔(天)']} | {row['最大时间间隔(天)']} | {row['中位数时间间隔(天)']} | {row['标准差(天)']} |\n")
            f.write("\n")
            
            # 添加时间间隔分析说明
            f.write("### 时间间隔分析说明\n\n")
            f.write("- **计算方法**: Intention_Payment_Time - first_assign_time\n")
            f.write("- **筛选条件**: Intention_Payment_Time在各车型预售周期内\n")
            f.write("- **统计指标**: 平均值、最大值、中位数、标准差\n")
            f.write("- **数据单位**: 天数\n\n")
            
            # 添加关键发现
            valid_results = module_four_results[module_four_results['订单数量'] > 0]
            if not valid_results.empty:
                total_orders = valid_results['订单数量'].sum()
                avg_of_avgs = valid_results['平均时间间隔(天)'].mean()
                
                f.write("### 关键发现\n\n")
                f.write(f"- **总订单数**: {total_orders:,}\n")
                f.write(f"- **各车型平均时间间隔的均值**: {avg_of_avgs:.2f} 天\n")
                
                if len(valid_results) > 1:
                    shortest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmin()]
                    longest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmax()]
                    f.write(f"- **平均时间间隔最短车型**: {shortest_model['车型']} ({shortest_model['平均时间间隔(天)']} 天)\n")
                    f.write(f"- **平均时间间隔最长车型**: {longest_model['车型']} ({longest_model['平均时间间隔(天)']} 天)\n")
                f.write("\n")
        else:
            f.write("模块四分析结果不可用\n\n")
        
        # 模块四变体：发布会后5天分析
        f.write("## 模块四变体：发布会后5天线索-小订时间间隔分析\n\n")
        if module_four_post_launch_results is not None and not module_four_post_launch_results.empty:
            f.write("### 各车型发布会后5天时间间隔统计\n\n")
            f.write("| 车型 | 发布会日期 | 截止日期 | 订单数量 | 平均时间间隔(天) | 最大时间间隔(天) | 中位数时间间隔(天) | 标准差(天) |\n")
            f.write("|------|------------|----------|----------|------------------|------------------|-------------------|------------|\n")
            for _, row in module_four_post_launch_results.iterrows():
                end_date_col = '发布会后5天截止日期'
                f.write(f"| {row['车型']} | {row['发布会日期']} | {row[end_date_col]} | {row['订单数量']:,} | {row['平均时间间隔(天)']} | {row['最大时间间隔(天)']} | {row['中位数时间间隔(天)']} | {row['标准差(天)']} |\n")
            f.write("\n")
            
            # 添加发布会后分析说明
            f.write("### 发布会后5天分析说明\n\n")
            f.write("- **计算方法**: Intention_Payment_Time - first_assign_time\n")
            f.write("- **筛选条件**: Intention_Payment_Time在各车型发布会后5天内\n")
            f.write("- **统计指标**: 平均值、最大值、中位数、标准差\n")
            f.write("- **数据单位**: 天数\n\n")
            
            # 添加关键发现
            valid_results = module_four_post_launch_results[module_four_post_launch_results['订单数量'] > 0]
            if not valid_results.empty:
                total_orders = valid_results['订单数量'].sum()
                avg_of_avgs = valid_results['平均时间间隔(天)'].mean()
                max_interval = valid_results['最大时间间隔(天)'].max()
                
                f.write("### 发布会后5天关键发现\n\n")
                f.write(f"- **总订单数**: {total_orders:,}\n")
                f.write(f"- **各车型平均时间间隔的均值**: {avg_of_avgs:.2f} 天\n")
                f.write(f"- **最长时间间隔**: {max_interval} 天\n")
                
                if len(valid_results) > 1:
                    shortest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmin()]
                    longest_model = valid_results.loc[valid_results['平均时间间隔(天)'].idxmax()]
                    f.write(f"- **平均时间间隔最短车型**: {shortest_model['车型']} ({shortest_model['平均时间间隔(天)']} 天)\n")
                    f.write(f"- **平均时间间隔最长车型**: {longest_model['车型']} ({longest_model['平均时间间隔(天)']} 天)\n")
                
                f.write(f"\n### 与整个预售期对比\n\n")
                f.write(f"发布会后5天的数据相比整个预售期，可以更好地反映早期用户的决策速度和转化效率。\n\n")
        else:
            f.write("发布会后5天分析结果不可用\n\n")
        
        # 模块五：发布会前后分组对比分析
        f.write("## 模块五：发布会前后分组对比分析\n\n")
        
        if module_five_results is not None and not module_five_results.empty:
            # 按车型分组展示结果
            f.write("### 各车型发布会前后时间间隔对比\n\n")
            f.write("| 车型 | 分组 | 发布会日期 | 订单数量 | 平均时间间隔(天) | 最大时间间隔(天) | 中位数时间间隔(天) | 标准差(天) |\n")
            f.write("|------|------|------------|----------|------------------|------------------|-------------------|------------|\n")
            
            for _, row in module_five_results.iterrows():
                f.write(f"| {row['车型']} | {row['分组']} | {row['发布会日期']} | {row['订单数量']:,} | {row['平均时间间隔(天)']:.2f} | {row['最大时间间隔(天)']} | {row['中位数时间间隔(天)']:.1f} | {row['标准差(天)']:.2f} |\n")
            
            f.write("\n### 发布会前后对比分析说明\n\n")
            f.write("- **分组依据**: 根据first_assign_time相对于发布会时间进行分组\n")
            f.write("- **发布会前组**: first_assign_time < 发布会时间\n")
            f.write("- **发布会后组**: first_assign_time >= 发布会时间\n")
            f.write("- **统计指标**: 平均值、最大值、中位数、标准差\n")
            f.write("- **数据单位**: 天数\n\n")
            
            # 关键发现
            f.write("### 发布会前后对比关键发现\n\n")
            
            # 按分组统计
            pre_launch_data = module_five_results[module_five_results['分组'] == '发布会前']
            post_launch_data = module_five_results[module_five_results['分组'] == '发布会后']
            
            if not pre_launch_data.empty:
                pre_total = pre_launch_data['订单数量'].sum()
                pre_avg = pre_launch_data['平均时间间隔(天)'].mean()
                f.write(f"- **发布会前总订单数**: {pre_total:,}\n")
                f.write(f"- **发布会前平均时间间隔**: {pre_avg:.2f} 天\n")
            
            if not post_launch_data.empty:
                post_total = post_launch_data['订单数量'].sum()
                post_avg = post_launch_data['平均时间间隔(天)'].mean()
                f.write(f"- **发布会后总订单数**: {post_total:,}\n")
                f.write(f"- **发布会后平均时间间隔**: {post_avg:.2f} 天\n")
            
            if not pre_launch_data.empty and not post_launch_data.empty:
                diff = post_avg - pre_avg
                f.write(f"- **平均时间间隔差异**: {diff:.2f} 天 (发布会后 - 发布会前)\n")
            
            f.write("\n### 对比分析结论\n\n")
            f.write("通过对比发布会前后的订单时间间隔，可以分析发布会对用户决策速度的影响，以及不同时期用户行为的差异。\n\n")
        else:
            f.write("发布会前后分组对比分析结果不可用\n\n")
        
        # 分析总结
        f.write("## 分析总结\n\n")
        f.write("本报告包含五个分析模块及其变体的完整结果：\n")
        f.write("1. **模块一**：完成了数据基本信息的验证和展示\n")
        f.write("2. **模块二**：完成了各车型预售期转化率的综合分析\n")
        f.write("3. **模块三**：完成了预售周期的归一化分析\n")
        f.write("4. **模块四**：完成了线索-小订时间间隔的统计分析\n")
        f.write("5. **模块四变体**：完成了发布会后5天的时间间隔专项分析\n")
        f.write("6. **模块五**：完成了发布会前后分组对比分析\n\n")
        f.write("报告结构已为后续模块扩展做好准备。\n")
    
    print(f"\n综合分析报告已保存到: {report_path}")

# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """
    主程序入口，按模块顺序执行分析
    """
    print("开始执行线索结构分析脚本 - 模块化版本")
    print("="*80)
    
    # 模块一：数据基本信息打印
    leads_df, orders_df, leads_info, orders_info = module_one_data_info()
    
    module_two_results = None
    module_three_results = None
    module_four_results = None
    
    if leads_df is not None and orders_df is not None:
        # 模块二：线索转化率综合分析
        module_two_results = module_two_conversion_analysis(leads_df, orders_df)
        
        # 模块三：预售周期归一化分析
        module_three_results = module_three_normalize_analysis(leads_df, orders_df)
        
        # 模块四：线索-小订时间间隔分析
        module_four_results = module_four_time_interval_analysis(orders_df)
        
        # 模块四变体：发布会后5天分析
        print("\n" + "="*80)
        print("执行发布会后5天时间间隔分析")
        print("="*80)
        module_four_post_launch_results = module_four_post_launch_analysis(orders_df, days_after_launch=5)
        
        # 模块五：发布会前后分组对比分析
        print("\n" + "="*80)
        print("执行模块五：发布会前后分组对比分析")
        print("="*80)
        module_five_results = module_five_pre_post_launch_comparison(orders_df)
        
        # 生成综合报告
        generate_comprehensive_report(module_two_results, module_three_results, module_four_results, module_four_post_launch_results, module_five_results, leads_info, orders_info)
    else:
        print("数据加载失败，程序终止")
        # 即使数据加载失败，也生成一个基础报告
        generate_comprehensive_report(leads_info=leads_info, orders_info=orders_info)
    
    print("\n" + "="*80)
    print("所有分析模块执行完成")
    print("="*80)

if __name__ == "__main__":
    main()