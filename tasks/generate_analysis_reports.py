#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告生成器
执行两个分析脚本并生成markdown格式的报告
"""

import sys
import io
from contextlib import redirect_stdout
from pathlib import Path
from datetime import datetime
import pandas as pd

# 导入分析模块
sys.path.append('/Users/zihao_/Documents/github/W33_utils_3/tasks')
from analyze_intention_data import (
    analyze_parquet_data as analyze_intention_parquet,
    calculate_lock_rate_indicator,
    analyze_by_vehicle_type,
    analyze_by_demographics,
    analyze_by_geography,
    analyze_by_channel,
    analyze_order_date_features,
    analyze_order_hour_features,
    analyze_leads_conversion_rate
)
from analyze_business_metrics import (
    analyze_parquet_file,
    analyze_launch_events,
    analyze_post_launch_changes,
    analyze_presale_post_launch_comparison,
    analyze_presale_ratio_comparison,
    analyze_presale_ratio_comparison_1day,
    Linear_attribution_analysis,
    leads_regression_model,
    funnel_analysis,
    bayesian_conversion_prediction,
    analyze_presale_daily_orders,
    comprehensive_presale_ranking
)

def capture_function_output(func, *args, **kwargs):
    """
    捕获函数的输出
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
    
    Returns:
        tuple: (函数返回值, 输出字符串)
    """
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"执行函数 {func.__name__} 时发生错误: {str(e)}")
            result = None
    
    output_text = output_buffer.getvalue()
    return result, output_text

def generate_intention_analysis_report():
    """
    生成意向订单分析报告
    
    Returns:
        str: markdown格式的报告内容
    """
    report_content = []
    report_content.append("# 意向订单数据分析报告\n")
    report_content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 文件路径
    file_path = "/Users/zihao_/Documents/github/W33_utils_3/data/intention_order_analysis.parquet"
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        report_content.append(f"**错误**: 文件不存在 - {file_path}\n")
        return "\n".join(report_content)
    
    try:
        # 1. 读取数据并分析基本信息
        result, output = capture_function_output(analyze_intention_parquet, file_path)
        if result is not None:
            df = result
            report_content.append("## 1. 数据基本信息分析\n")
            report_content.append("```\n")
            report_content.append(output)
            report_content.append("```\n\n")
            
            # 2. 计算锁单率指标
            result, output = capture_function_output(calculate_lock_rate_indicator, df)
            if result is not None:
                df = result
                report_content.append("## 2. 锁单率指标计算\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 3. 车型结构分析
                result, output = capture_function_output(analyze_by_vehicle_type, df)
                report_content.append("## 3. 车型结构分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 4. 人口统计学特征分析
                result, output = capture_function_output(analyze_by_demographics, df)
                report_content.append("## 4. 人口统计学特征分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 5. 地理位置分析
                result, output = capture_function_output(analyze_by_geography, df)
                report_content.append("## 5. 地理位置分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 6. 线索渠道分析
                result, output = capture_function_output(analyze_by_channel, df)
                report_content.append("## 6. 线索渠道分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 7. 线索转化率分析
                result, output = capture_function_output(analyze_leads_conversion_rate, df)
                report_content.append("## 7. 线索转化率分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 8. 下订日期特征分析
                result, output = capture_function_output(analyze_order_date_features, df)
                report_content.append("## 8. 下订日期特征分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                
                # 9. 下订时间（小时）特征分析
                result, output = capture_function_output(analyze_order_hour_features, df)
                report_content.append("## 9. 下订时间（小时）特征分析\n")
                report_content.append("```\n")
                report_content.append(output)
                report_content.append("```\n\n")
                

        else:
            report_content.append("**错误**: 无法读取数据文件\n")
            
    except Exception as e:
        report_content.append(f"**错误**: 生成报告时发生异常 - {str(e)}\n")
    
    return "\n".join(report_content)

def generate_business_metrics_report():
    """
    生成业务指标分析报告
    
    Returns:
        str: markdown格式的报告内容
    """
    report_content = []
    report_content.append("# 业务日常指标数据分析报告\n")
    report_content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 文件路径
    data_file = "/Users/zihao_/Documents/github/W33_utils_3/data/business_daily_metrics.parquet"
    
    # 检查文件是否存在
    if not Path(data_file).exists():
        report_content.append(f"**错误**: 数据文件 {data_file} 不存在\n")
        return "\n".join(report_content)
    
    try:
        # 读取数据
        df = pd.read_parquet(data_file)
        
        # 1. 基本文件分析
        result, output = capture_function_output(analyze_parquet_file, data_file)
        report_content.append("## 1. 数据文件基本信息分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 2. 发布会时间节点分析
        result, output = capture_function_output(analyze_launch_events, df)
        launch_results = result
        report_content.append("## 2. 发布会时间节点前30日指标分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 3. 发布会后3日变化分析
        result, output = capture_function_output(analyze_post_launch_changes, df)
        post_launch_results = result
        report_content.append("## 3. 发布会后3日指标变化幅度分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 4. 预售发布会后3日横向对比分析
        result, output = capture_function_output(analyze_presale_post_launch_comparison, df)
        comparison_results = result
        report_content.append("## 4. 预售发布会后3日指标横向对比分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 5. 预售发布会后3日指标比值对比分析
        result, output = capture_function_output(analyze_presale_ratio_comparison, df)
        ratio_results = result
        report_content.append("## 5. 预售发布会后3日指标比值对比分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 6. 预售发布会后1日指标比值对比分析
        result, output = capture_function_output(analyze_presale_ratio_comparison_1day, df)
        ratio_1day_results = result
        report_content.append("## 6. 预售发布会后1日（当日）指标比值对比分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 6.5. 预售发布会综合排名分析（基于模块4提升幅度和模块5效率变化）
        if comparison_results is not None and ratio_results is not None:
            result, output = capture_function_output(comprehensive_presale_ranking, comparison_results, ratio_results)
            comprehensive_results = result
            report_content.append("## 6.5. 预售发布会综合排名分析\n")
            report_content.append("```\n")
            report_content.append(output)
            report_content.append("```\n\n")
        else:
            report_content.append("## 6.5. 预售发布会综合排名分析\n")
            report_content.append("**错误**: 缺少模块4或模块5的分析结果，无法进行综合排名分析\n\n")
        
        # 7. 线性归因建模
        result, output = capture_function_output(Linear_attribution_analysis, df)
        causal_results = result
        report_content.append("## 7. 线性归因建模\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 7.5. 线索回归模型 - Lasso + 敏感性分析
        result, output = capture_function_output(leads_regression_model, df)
        leads_regression_results = result
        report_content.append("## 7.5. 线索回归模型 - Lasso + 敏感性分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 8. 漏斗分析
        result, output = capture_function_output(funnel_analysis, df)
        funnel_results = result
        report_content.append("## 8. 漏斗分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
        # 9. 贝叶斯转化率预测
        if funnel_results is not None:
            result, output = capture_function_output(bayesian_conversion_prediction, funnel_results)
            prediction_results = result
            report_content.append("## 9. 贝叶斯转化率预测\n")
            report_content.append("```\n")
            report_content.append(output)
            report_content.append("```\n\n")
        else:
            report_content.append("## 9. 贝叶斯转化率预测\n")
            report_content.append("**错误**: 漏斗分析结果为空，无法进行贝叶斯预测\n\n")
        
        # 10. 预售发布会周期每天小订分析
        result, output = capture_function_output(analyze_presale_daily_orders, df)
        report_content.append("## 10. 预售发布会周期每天小订分析\n")
        report_content.append("```\n")
        report_content.append(output)
        report_content.append("```\n\n")
        
    except Exception as e:
        report_content.append(f"**错误**: 生成报告时发生异常 - {str(e)}\n")
    
    return "\n".join(report_content)

def generate_reports():
    """
    生成两个分析报告的主函数
    """
    print("开始生成分析报告...")
    
    # 生成意向订单分析报告
    print("\n正在生成意向订单分析报告...")
    intention_report = generate_intention_analysis_report()
    
    # 保存意向订单分析报告
    intention_report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/intention_analysis_report.md"
    with open(intention_report_path, 'w', encoding='utf-8') as f:
        f.write(intention_report)
    print(f"意向订单分析报告已保存到: {intention_report_path}")
    
    # 生成业务指标分析报告
    print("\n正在生成业务指标分析报告...")
    business_report = generate_business_metrics_report()
    
    # 保存业务指标分析报告
    business_report_path = "/Users/zihao_/Documents/github/W33_utils_3/tasks/business_metrics_report.md"
    with open(business_report_path, 'w', encoding='utf-8') as f:
        f.write(business_report)
    print(f"业务指标分析报告已保存到: {business_report_path}")
    
    print("\n所有报告生成完成！")
    print(f"\n报告文件:")
    print(f"1. 意向订单分析报告: {intention_report_path}")
    print(f"2. 业务指标分析报告: {business_report_path}")

if __name__ == "__main__":
    generate_reports()