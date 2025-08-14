#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging

# 设置日志级别为ERROR以减少输出
logging.basicConfig(level=logging.ERROR)

def test_final_fix():
    """最终修复验证"""
    print("🔧 最终修复验证测试")
    
    # 加载数据
    try:
        data = pd.read_parquet('data/乘用车上险量_0723.parquet')
        print(f"✅ 数据加载成功，共 {len(data)} 条记录")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    
    # 检查数据中的实际车型
    print("\n📊 数据验证:")
    tesla_data = data[data['brand'] == '特斯拉']
    byd_data = data[data['brand'] == '比亚迪']
    
    print(f"特斯拉数据: {len(tesla_data)} 条")
    if len(tesla_data) > 0:
        print(f"特斯拉车型: {tesla_data['model_name'].unique()}")
        model_y_data = tesla_data[tesla_data['model_name'] == 'Model Y']
        print(f"Model Y数据: {len(model_y_data)} 条，总销量: {model_y_data['sales_volume'].sum():,}")
    
    print(f"比亚迪数据: {len(byd_data)} 条")
    if len(byd_data) > 0:
        print(f"比亚迪车型: {byd_data['model_name'].unique()[:10]}")
        han_data = byd_data[byd_data['model_name'] == '汉']
        print(f"汉数据: {len(han_data)} 条，总销量: {han_data['sales_volume'].sum():,}")
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 测试用例
    test_cases = [
        {
            'name': '特斯拉Model Y查询',
            'question': '特斯拉Model Y销量'
        },
        {
            'name': '比亚迪汉查询',
            'question': '比亚迪汉销量'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {case['name']} ---")
        print(f"问题: {case['question']}")
        
        try:
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
                    for record in data_result:
                        print(f"  {record}")
                else:
                    print(f"⚠️ 查询成功但无数据返回")
                    
            else:
                error_info = result.get('analysis', {}).get('error') or result.get('error', '未知错误')
                print(f"❌ 查询失败: {error_info}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_final_fix()