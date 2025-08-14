#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试销量查询模块修复效果
"""

from modules.sales_query_module import SalesQueryModule
import pandas as pd

def test_zhiji_ls6_query():
    """测试智己LS6查询修复效果"""
    print("=== 测试智己LS6查询修复效果 ===")
    
    try:
        # 初始化模块
        module = SalesQueryModule()
        
        # 测试参数
        params = {
            'user_question': '智己LS6 2024年的销量',
            'data_source': 'data/乘用车上险量_0723.parquet'
        }
        
        print("1. 准备数据...")
        data = module.prepare_data(None, params)
        print(f"数据加载成功，形状: {data.shape}")
        
        print("\n2. 执行查询...")
        result = module.run(data, params)
        
        print(f"\n3. 查询结果分析:")
        print(f"查询成功: {result['success']}")
        print(f"返回记录数: {len(result['data'])}")
        
        print("\n4. 前5条结果:")
        for i, item in enumerate(result['data'][:5]):
            print(f"  {i+1}. {item}")
        
        print("\n5. 生成摘要:")
        summary = module.summarize(result)
        print(summary)
        
        # 验证是否还有0销量记录
        zero_sales_count = sum(1 for item in result['data'] if item.get('total_sales', 0) == 0)
        print(f"\n6. 验证结果:")
        print(f"0销量记录数: {zero_sales_count}")
        print(f"修复效果: {'✅ 成功' if zero_sales_count == 0 else '❌ 仍有问题'}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_zhiji_ls6_query()