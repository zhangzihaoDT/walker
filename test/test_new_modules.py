#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新创建的分析模块

验证param_segmenter、trend_analysis、yoy_comparison模块的基本功能，
并演示Walker策略流程的模块串联执行。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.param_segmenter import ParameterSegmenterModule
from modules.trend_analysis import TrendAnalysisModule
from modules.yoy_comparison import YoYComparisonModule


def create_sample_data():
    """创建示例数据用于测试"""
    # 生成2年的月度销售数据
    start_date = datetime(2022, 1, 1)
    dates = [start_date + timedelta(days=30*i) for i in range(24)]  # 24个月
    
    # 创建多个产品类别的数据
    categories = ['电子产品', '服装', '食品', '家居']
    regions = ['北京', '上海', '广州', '深圳']
    
    data = []
    for date in dates:
        for category in categories:
            for region in regions:
                # 生成带趋势和季节性的销售数据
                base_value = np.random.normal(1000, 200)
                
                # 添加年度增长趋势
                year_factor = 1 + (date.year - 2022) * 0.1
                
                # 添加季节性因素
                month_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
                
                # 不同类别的基础差异
                category_factor = {
                    '电子产品': 1.5,
                    '服装': 1.2,
                    '食品': 0.8,
                    '家居': 1.0
                }[category]
                
                sales = base_value * year_factor * month_factor * category_factor
                
                data.append({
                    'date': date,
                    'category': category,
                    'region': region,
                    'sales': max(0, sales),  # 确保非负
                    'quantity': int(sales / 50)  # 数量字段
                })
    
    return pd.DataFrame(data)


def test_param_segmenter():
    """测试参数细分模块"""
    print("\n=== 测试参数细分模块 ===")
    
    # 创建测试数据
    data = create_sample_data()
    
    # 初始化模块
    segmenter = ParameterSegmenterModule()
    
    # 测试模块信息
    print("模块信息:")
    module_info = segmenter.get_module_info()
    print(f"- 模块名: {module_info['module_name']}")
    print(f"- 描述: {module_info['description']}")
    
    # 测试需求声明
    requirements = segmenter.get_requirements()
    print(f"\n模块类型: {requirements['module_type']}")
    print(f"支持的数据库: {requirements['databases']}")
    
    # 执行分析
    params = {
        'segment_fields': ['category', 'region'],
        'aggregation_method': 'sum',
        'value_fields': ['sales'],
        'table_name': 'sales_data'
    }
    
    try:
        # 准备数据
        prepared_data = segmenter.prepare_data(data, params)
        print(f"\n准备的数据形状: {prepared_data.shape}")
        
        # 执行分析
        results = segmenter.run(prepared_data, params)
        print(f"\n生成的数据段数量: {results['analysis']['total_segments']}")
        
        # 生成总结
        summary = segmenter.summarize(results)
        print(f"\n分析总结:\n{summary}")
        
        print("✅ 参数细分模块测试通过")
        return results
        
    except Exception as e:
        print(f"❌ 参数细分模块测试失败: {e}")
        return None


def test_trend_analysis():
    """测试趋势分析模块"""
    print("\n=== 测试趋势分析模块 ===")
    
    # 创建测试数据
    data = create_sample_data()
    
    # 初始化模块
    trend_analyzer = TrendAnalysisModule()
    
    # 测试模块信息
    print("模块信息:")
    module_info = trend_analyzer.get_module_info()
    print(f"- 模块名: {module_info['module_name']}")
    print(f"- 描述: {module_info['description']}")
    
    # 测试需求声明
    requirements = trend_analyzer.get_requirements()
    print(f"\n模块类型: {requirements['module_type']}")
    print(f"必需字段: {requirements['data_fields']}")
    
    # 执行分析
    params = {
        'date_field': 'date',
        'value_field': 'sales',
        'category_field': 'category',
        'trend_method': 'linear',
        'table_name': 'sales_data'
    }
    
    try:
        # 准备数据
        prepared_data = trend_analyzer.prepare_data(data, params)
        print(f"\n准备的数据形状: {prepared_data.shape}")
        
        # 执行分析
        results = trend_analyzer.run(prepared_data, params)
        print(f"\n分析的类别数量: {len(results['analysis'].get('by_category', {}))}")
        
        # 生成总结
        summary = trend_analyzer.summarize(results)
        print(f"\n分析总结:\n{summary}")
        
        print("✅ 趋势分析模块测试通过")
        return results
        
    except Exception as e:
        print(f"❌ 趋势分析模块测试失败: {e}")
        return None


def test_yoy_comparison():
    """测试同比分析模块"""
    print("\n=== 测试同比分析模块 ===")
    
    # 创建测试数据
    data = create_sample_data()
    
    # 初始化模块
    yoy_analyzer = YoYComparisonModule()
    
    # 测试模块信息
    print("模块信息:")
    module_info = yoy_analyzer.get_module_info()
    print(f"- 模块名: {module_info['module_name']}")
    print(f"- 描述: {module_info['description']}")
    
    # 测试需求声明
    requirements = yoy_analyzer.get_requirements()
    print(f"\n模块类型: {requirements['module_type']}")
    print(f"必需字段: {requirements['data_fields']}")
    
    # 执行分析
    params = {
        'date_field': 'date',
        'value_field': 'sales',
        'category_field': 'category',
        'comparison_periods': 1,
        'time_granularity': 'month',
        'aggregation_method': 'sum',
        'table_name': 'sales_data'
    }
    
    try:
        # 准备数据
        prepared_data = yoy_analyzer.prepare_data(data, params)
        print(f"\n准备的数据形状: {prepared_data.shape}")
        
        # 执行分析
        results = yoy_analyzer.run(prepared_data, params)
        print(f"\n分析的类别数量: {len(results['analysis'].get('by_category', {}))}")
        
        # 生成总结
        summary = yoy_analyzer.summarize(results)
        print(f"\n分析总结:\n{summary}")
        
        print("✅ 同比分析模块测试通过")
        return results
        
    except Exception as e:
        print(f"❌ 同比分析模块测试失败: {e}")
        return None


def test_walker_strategy_flow():
    """测试Walker策略流程：模块串联执行"""
    print("\n=== 测试Walker策略流程 ===")
    
    # 创建测试数据
    data = create_sample_data()
    print(f"原始数据形状: {data.shape}")
    
    # 步骤1: 参数细分 - 按类别分组
    print("\n步骤1: 参数细分")
    segmenter = ParameterSegmenterModule()
    segment_params = {
        'segment_fields': ['category'],
        'aggregation_method': 'none',  # 不聚合，保留原始数据
        'table_name': 'sales_data'
    }
    
    try:
        # 执行参数细分
        prepared_data = segmenter.prepare_data(data, segment_params)
        segment_results = segmenter.run(prepared_data, segment_params)
        
        print(f"生成了 {segment_results['analysis']['total_segments']} 个数据段")
        
        # 步骤2: 对每个分组执行趋势分析
        print("\n步骤2: 趋势分析")
        trend_analyzer = TrendAnalysisModule()
        trend_params = {
            'date_field': 'date',
            'value_field': 'sales',
            'trend_method': 'linear'
        }
        
        category_trends = {}
        for segment_name, segment_info in segment_results['segments'].items():
            segment_data = segment_info['data']
            
            # 为每个分组执行趋势分析
            trend_prepared = trend_analyzer.prepare_data(segment_data, trend_params)
            trend_result = trend_analyzer.run(trend_prepared, trend_params)
            
            category_trends[segment_name] = {
                'trend_direction': trend_result['analysis'].get('trend_direction', '未知'),
                'trend_strength': trend_result['analysis'].get('trend_strength', 0),
                'slope': trend_result['analysis'].get('slope', 0)
            }
        
        print("各类别趋势分析结果:")
        for category, trend_info in category_trends.items():
            print(f"- {category}: {trend_info['trend_direction']}趋势，强度 {trend_info['trend_strength']:.2f}")
        
        # 步骤3: 同比分析
        print("\n步骤3: 同比分析")
        yoy_analyzer = YoYComparisonModule()
        yoy_params = {
            'date_field': 'date',
            'value_field': 'sales',
            'category_field': 'category',
            'comparison_periods': 1,
            'time_granularity': 'month',
            'aggregation_method': 'sum'
        }
        
        yoy_prepared = yoy_analyzer.prepare_data(data, yoy_params)
        yoy_results = yoy_analyzer.run(yoy_prepared, yoy_params)
        
        print("同比分析完成")
        if 'by_category' in yoy_results['analysis']:
            category_yoy = yoy_results['analysis']['by_category']
            print("各类别同比增长率:")
            for category, yoy_info in category_yoy.items():
                avg_growth = yoy_info.get('average_growth_rate', 0)
                print(f"- {category}: 平均同比增长 {avg_growth:.1f}%")
        
        # 步骤4: 综合洞察生成
        print("\n步骤4: 综合洞察")
        insights = []
        
        # 结合趋势和同比分析结果
        for category in category_trends.keys():
            trend_info = category_trends[category]
            
            if 'by_category' in yoy_results['analysis']:
                yoy_info = yoy_results['analysis']['by_category'].get(category, {})
                avg_growth = yoy_info.get('average_growth_rate', 0)
                
                insight = f"{category}: {trend_info['trend_direction']}趋势（强度{trend_info['trend_strength']:.2f}），平均同比增长{avg_growth:.1f}%"
                insights.append(insight)
        
        print("综合分析洞察:")
        for insight in insights:
            print(f"- {insight}")
        
        print("\n✅ Walker策略流程测试通过")
        print("成功演示了：参数细分 → 趋势分析 → 同比分析 → 综合洞察的完整流程")
        
    except Exception as e:
        print(f"❌ Walker策略流程测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("开始测试新创建的分析模块...")
    
    # 测试各个模块
    test_param_segmenter()
    test_trend_analysis()
    test_yoy_comparison()
    
    # 测试Walker策略流程
    test_walker_strategy_flow()
    
    print("\n🎉 所有测试完成！")
    print("\n新模块功能说明:")
    print("1. ParameterSegmenterModule: 参数细分器，按指定维度对数据进行分组切片")
    print("2. TrendAnalysisModule: 趋势分析器，分析时间序列数据的趋势变化")
    print("3. YoYComparisonModule: 同比分析器，进行年同比分析")
    print("\n这些模块都实现了BaseAnalysisModule的标准接口，")
    print("包括新增的get_requirements()方法，可以在Walker策略流程中稳定运行。")


if __name__ == '__main__':
    main()