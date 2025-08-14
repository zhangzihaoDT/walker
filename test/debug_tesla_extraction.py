#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_tesla_extraction():
    """调试特斯拉Model Y参数提取"""
    print("🔍 调试特斯拉Model Y参数提取")
    
    # 加载数据
    try:
        data = pd.read_parquet('data/乘用车上险量_0723.parquet')
        print(f"✅ 数据加载成功，共 {len(data)} 条记录")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 测试不同的查询表达方式
    test_questions = [
        '特斯拉Model Y销量',
        '特斯拉 Model Y销量',
        'Model Y销量',
        '特斯拉ModelY销量',
        '特斯拉Model Y销量数据'
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 测试 {i}: {question} ---")
        
        try:
            # 直接调用参数提取方法
            params = module._extract_query_parameters({'user_question': question})
            print(f"提取的参数: {params}")
            
            # 检查提取的品牌和车型
            brands = params.get('brands', [])
            model_names = params.get('model_names', [])
            
            print(f"品牌: {brands}")
            print(f"车型: {model_names}")
            
            # 检查数据中是否存在这些值
            if brands:
                for brand in brands:
                    if brand:
                        brand_data = data[data['brand'] == brand]
                        print(f"数据中品牌 '{brand}' 的记录数: {len(brand_data)}")
            
            if model_names:
                for model in model_names:
                    if model:
                        model_data = data[data['model_name'] == model]
                        print(f"数据中车型 '{model}' 的记录数: {len(model_data)}")
            
            # 如果有品牌和车型，检查组合
            if brands and model_names:
                for brand in brands:
                    for model in model_names:
                        if brand and model:
                            combined_data = data[(data['brand'] == brand) & (data['model_name'] == model)]
                            print(f"数据中品牌 '{brand}' + 车型 '{model}' 的记录数: {len(combined_data)}")
                            if len(combined_data) > 0:
                                print(f"总销量: {combined_data['sales_volume'].sum():,}")
            
        except Exception as e:
            print(f"❌ 参数提取失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_tesla_extraction()