#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合销量查询测试脚本
测试修复后的销量查询模块的各种场景
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_query_scenarios():
    """测试各种查询场景"""
    print("=== 综合销量查询测试 ===")
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 准备数据
    print("\n1. 准备数据...")
    data = module.prepare_data(None, {})
    print(f"数据加载成功，形状: {data.shape}")
    
    # 测试场景
    test_cases = [
        {
            "name": "智己LS6 2024年销量查询",
            "question": "智己LS6 2024年的销量如何？",
            "expected_template": "品牌销量查询"
        },
        {
            "name": "特斯拉品牌销量查询",
            "question": "特斯拉2024年销量",
            "expected_template": "品牌销量查询"
        },
        {
            "name": "蔚来ES6车型查询",
            "question": "蔚来ES6销量情况",
            "expected_template": "品牌销量查询"
        },
        {
            "name": "广东省地区查询",
            "question": "广东省新能源汽车销量",
            "expected_template": "地区销量查询"
        },
        {
            "name": "电动车燃料类型查询",
            "question": "纯电动汽车销量分析",
            "expected_template": "燃料类型分析"
        },
        {
            "name": "时间趋势查询",
            "question": "2024年汽车销量趋势",
            "expected_template": "时间趋势查询"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {case['name']}")
        print(f"   问题: {case['question']}")
        
        try:
            # 运行查询
            result = module.run(data, {"user_question": case['question']})
            
            # 生成摘要
            summary = module.summarize(result)
            
            print(f"   ✅ 查询成功")
            print(f"   📊 数据条数: {len(result.get('data', []))}")
            print(f"   📝 摘要预览: {summary[:100]}...")
            
            results.append({
                "case": case['name'],
                "success": True,
                "data_count": len(result.get('data', [])),
                "summary": summary
            })
            
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
            results.append({
                "case": case['name'],
                "success": False,
                "error": str(e)
            })
    
    # 汇总结果
    print("\n=== 测试结果汇总 ===")
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"总测试数: {total_count}")
    print(f"成功数: {success_count}")
    print(f"失败数: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    # 详细结果
    print("\n=== 详细结果 ===")
    for result in results:
        if result['success']:
            print(f"✅ {result['case']}: {result['data_count']} 条数据")
        else:
            print(f"❌ {result['case']}: {result['error']}")
    
    return results

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 边界情况测试 ===")
    
    module = SalesQueryModule()
    data = module.prepare_data(None, {})
    
    edge_cases = [
        {
            "name": "空查询",
            "question": ""
        },
        {
            "name": "不存在的品牌",
            "question": "不存在品牌XYZ的销量"
        },
        {
            "name": "未来时间",
            "question": "2030年销量预测"
        },
        {
            "name": "复杂多条件",
            "question": "特斯拉Model Y在广东省深圳市2024年上半年纯电动车型销量前10名"
        }
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n{i}. 边界测试: {case['name']}")
        print(f"   问题: {case['question']}")
        
        try:
            result = module.run(data, {"user_question": case['question']})
            summary = module.summarize(result)
            print(f"   ✅ 处理成功: {len(result.get('data', []))} 条数据")
            print(f"   📝 摘要: {summary[:80]}...")
        except Exception as e:
            print(f"   ⚠️ 异常处理: {e}")

if __name__ == "__main__":
    try:
        # 运行综合测试
        test_results = test_query_scenarios()
        
        # 运行边界测试
        test_edge_cases()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()