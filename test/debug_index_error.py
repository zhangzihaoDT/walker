#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试索引错误问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
import traceback

def debug_index_error():
    print("🔍 开始调试索引错误问题")
    
    # 加载数据
    print("📊 加载数据...")
    import pandas as pd
    data = pd.read_parquet('data/乘用车上险量_0723.parquet')
    print(f"✅ 数据加载成功，共 {len(data)} 条记录")
    
    # 初始化模块
    module = SalesQueryModule()
    module.df = data  # 直接设置数据
    
    # 测试查询
    test_queries = [
        "特斯拉Model Y销量数据",
        "比亚迪汉销量"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}: {query} ---")
        
        try:
            # 使用正确的调用方式
            print(f"🔍 执行完整查询...")
            result = module.run(data, {"user_question": query})
            
            if result.get('success', False):
                analysis = result.get('analysis', {})
                template_used = analysis.get('template_used', '未知模板')
                total_records = analysis.get('total_records', 0)
                
                print(f"✅ 查询成功")
                print(f"使用模板: {template_used}")
                print(f"记录数: {total_records}")
                print(f"结果: {result.get('summary', 'N/A')}")
            else:
                print(f"❌ 查询失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            print("详细错误信息:")
            traceback.print_exc()

if __name__ == "__main__":
    debug_index_error()