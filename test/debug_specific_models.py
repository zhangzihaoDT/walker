#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_specific_models():
    """测试特定车型查询"""
    print("🚀 开始测试特定车型查询")
    
    # 加载数据
    try:
        data = pd.read_parquet('data/乘用车上险量_0723.parquet')
        print(f"✅ 数据加载成功，共 {len(data)} 条记录")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    
    # 检查数据中的车型
    print("\n📊 数据中的车型信息:")
    unique_models = data['model_name'].unique()
    print(f"总车型数: {len(unique_models)}")
    
    # 查找特斯拉相关车型
    tesla_models = [model for model in unique_models if '特斯拉' in str(model) or 'Model' in str(model)]
    print(f"特斯拉相关车型: {tesla_models}")
    
    # 查找比亚迪相关车型
    byd_models = [model for model in unique_models if '比亚迪' in str(model) or '汉' in str(model)]
    print(f"比亚迪相关车型: {byd_models}")
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 测试用例
    test_cases = [
        {
            'name': '特斯拉Model Y查询',
            'question': '特斯拉Model Y销量数据',
            'expected_models': ['特斯拉Model Y']
        },
        {
            'name': '比亚迪汉EV查询', 
            'question': '比亚迪汉EV销量',
            'expected_models': ['比亚迪汉EV']
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {case['name']} ---")
        print(f"问题: {case['question']}")
        
        try:
            # 检查数据中是否存在期望的车型
            for expected_model in case['expected_models']:
                model_data = data[data['model_name'] == expected_model]
                print(f"数据中 '{expected_model}' 的记录数: {len(model_data)}")
                if len(model_data) > 0:
                    print(f"该车型的品牌: {model_data['brand'].unique()}")
                    print(f"该车型的总销量: {model_data['sales_volume'].sum():,}")
            
            # 执行查询
            result = module.run(data, {"user_question": case['question']})
            
            if result.get('success', False):
                analysis = result.get('analysis', {})
                template_used = analysis.get('template_used', '未知模板')
                total_records = analysis.get('total_records', 0)
                
                print(f"✅ 查询成功")
                print(f"使用模板: {template_used}")
                print(f"记录数: {total_records}")
                
                # 显示结果
                data_result = result.get('data', [])
                if data_result:
                    print(f"查询结果:")
                    for record in data_result[:3]:  # 显示前3条
                        print(f"  {record}")
                else:
                    print(f"⚠️ 查询成功但无数据返回")
                    
                    # 调试参数提取
                    params_used = analysis.get('parameters_used', {})
                    print(f"使用的参数: {params_used}")
                    
            else:
                error_info = result.get('analysis', {}).get('error') or result.get('error', '未知错误')
                print(f"❌ 查询失败: {error_info}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_specific_models()