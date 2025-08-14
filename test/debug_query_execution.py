#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试查询执行流程
"""

import sys
sys.path.append('.')

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_query_execution():
    """调试查询执行流程"""
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 加载数据
    data_path = Path('data/乘用车上险量_0723.parquet')
    if not data_path.exists():
        print(f"❌ 数据文件不存在: {data_path}")
        return
    
    df = pd.read_parquet(data_path)
    print(f"📊 数据加载成功，形状: {df.shape}")
    print(f"📋 数据列: {list(df.columns)}")
    
    # 检查智己LS6的数据
    zhiji_data = df[df['brand'] == '智己']
    print(f"\n🔍 智己品牌数据: {len(zhiji_data)} 条")
    
    if len(zhiji_data) > 0:
        print(f"智己车型: {zhiji_data['model_name'].unique()}")
        ls6_data = zhiji_data[zhiji_data['model_name'] == '智己LS6']
        print(f"智己LS6数据: {len(ls6_data)} 条")
        
        if len(ls6_data) > 0:
            print(f"智己LS6日期范围: {ls6_data['date'].min()} 到 {ls6_data['date'].max()}")
            print(f"智己LS6总销量: {ls6_data['sales_volume'].sum():,.0f}")
            
            # 检查2024年数据
            ls6_2024 = ls6_data[ls6_data['date'].dt.year == 2024]
            print(f"智己LS6 2024年数据: {len(ls6_2024)} 条")
            if len(ls6_2024) > 0:
                print(f"智己LS6 2024年销量: {ls6_2024['sales_volume'].sum():,.0f}")
    
    # 测试查询
    test_question = "智己LS6 2024年销量"
    print(f"\n🧪 测试查询: {test_question}")
    
    # 1. 参数提取
    params = {'user_question': test_question}
    extracted_params = module._extract_query_parameters(params)
    print(f"\n📝 提取的参数:")
    for key, value in extracted_params.items():
        print(f"  {key}: {value}")
    
    # 2. 模板选择
    template_info = module._select_template(extracted_params)
    print(f"\n📋 选择的模板: {template_info['name']}")
    
    # 3. 执行查询
    try:
        result_df = module._execute_query(df, template_info, extracted_params)
        print(f"\n📊 查询结果:")
        print(f"  结果行数: {len(result_df)}")
        if len(result_df) > 0:
            print(f"  结果列: {list(result_df.columns)}")
            print(f"  前3行数据:")
            for i, row in result_df.head(3).iterrows():
                print(f"    {dict(row)}")
        else:
            print("  ❌ 查询结果为空")
            
            # 调试空结果
            print("\n🔍 调试空结果:")
            
            # 检查过滤后的数据
            debug_df = df.copy()
            
            # 品牌过滤
            if extracted_params.get('brands'):
                valid_brands = [b for b in extracted_params['brands'] if b is not None]
                if valid_brands:
                    debug_df = debug_df[debug_df['brand'].isin(valid_brands)]
                    print(f"  品牌过滤后: {len(debug_df)} 条")
            
            # 车型过滤
            if extracted_params.get('model_names'):
                valid_model_names = [m for m in extracted_params['model_names'] if m is not None]
                if valid_model_names:
                    print(f"  要过滤的车型: {valid_model_names}")
                    print(f"  数据中的车型: {debug_df['model_name'].unique()[:10]}")
                    debug_df = debug_df[debug_df['model_name'].isin(valid_model_names)]
                    print(f"  车型过滤后: {len(debug_df)} 条")
            
            # 时间过滤
            if extracted_params.get('start_date'):
                start_date = pd.to_datetime(extracted_params['start_date'])
                debug_df = debug_df[debug_df['date'] >= start_date]
                print(f"  开始时间过滤后: {len(debug_df)} 条")
            
            if extracted_params.get('end_date'):
                end_date = pd.to_datetime(extracted_params['end_date'])
                debug_df = debug_df[debug_df['date'] <= end_date]
                print(f"  结束时间过滤后: {len(debug_df)} 条")
            
            if len(debug_df) > 0:
                print(f"  过滤后数据样例:")
                print(debug_df[['brand', 'model_name', 'date', 'sales_volume']].head())
    
    except Exception as e:
        print(f"❌ 查询执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_query_execution()