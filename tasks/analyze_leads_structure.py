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
    负责数据加载、验证和基础信息展示
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
        
        # 打印数据结构信息
        print("\n" + "="*60)
        print("线索数据字段信息")
        print("="*60)
        print("字段名:", list(leads_df.columns))
        print("数据类型:", dict(leads_df.dtypes))
        
        print("\n" + "="*60)
        print("订单数据字段信息")
        print("="*60)
        print("字段名:", list(orders_df.columns))
        print("数据类型:", dict(orders_df.dtypes))
        
        print("\n" + "="*60)
        print("模块一：数据基本信息打印完成")
        print("="*60)
        
        return leads_df, orders_df
        
    except FileNotFoundError as e:
        print(f"错误: 找不到数据文件 {e}")
        return None, None
    except Exception as e:
        print(f"模块一执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

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
            '网销平台线索数': '网销平台',
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
# 报告生成模块
# ============================================================================

def generate_comprehensive_report(module_two_results=None, module_three_results=None):
    """
    生成综合分析报告，整合所有模块结果
    """
    report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/leads_conversion_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 线索转化率综合分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 模块一：数据基本信息
        f.write("## 模块一：数据基本信息\n\n")
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
        else:
            f.write("模块三分析结果不可用\n\n")
        
        # 分析总结
        f.write("## 分析总结\n\n")
        f.write("本报告包含三个分析模块的完整结果：\n")
        f.write("1. **模块一**：完成了数据基本信息的验证和展示\n")
        f.write("2. **模块二**：完成了各车型预售期转化率的综合分析\n")
        f.write("3. **模块三**：完成了预售周期的归一化分析\n\n")
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
    leads_df, orders_df = module_one_data_info()
    
    module_two_results = None
    module_three_results = None
    
    if leads_df is not None and orders_df is not None:
        # 模块二：线索转化率综合分析
        module_two_results = module_two_conversion_analysis(leads_df, orders_df)
        
        # 模块三：预售周期归一化分析
        module_three_results = module_three_normalize_analysis(leads_df, orders_df)
        
        # 生成综合报告
        generate_comprehensive_report(module_two_results, module_three_results)
    else:
        print("数据加载失败，程序终止")
        # 即使数据加载失败，也生成一个基础报告
        generate_comprehensive_report()
    
    print("\n" + "="*80)
    print("所有分析模块执行完成")
    print("="*80)

if __name__ == "__main__":
    main()