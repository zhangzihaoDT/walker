#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间范围提取功能

验证改进后的时间范围识别是否支持更多时间表达方式
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.sales_query_module import SalesQueryModule

def test_time_extraction():
    """测试时间范围提取功能"""
    print("🕒 时间范围提取功能测试")
    print("=" * 50)
    
    module = SalesQueryModule()
    
    # 测试用例
    test_cases = [
        # 基本年份
        {
            "question": "智己 2024年销量",
            "expected": {"start_date": "2024-01-01", "end_date": "2024-12-31", "time_granularity": "year"}
        },
        {
            "question": "比亚迪 2023年的销量数据",
            "expected": {"start_date": "2023-01-01", "end_date": "2023-12-31", "time_granularity": "year"}
        },
        
        # 月份
        {
            "question": "特斯拉 2024年3月销量",
            "expected": {"start_date": "2024-03-01", "end_date": "2024-03-31", "time_granularity": "month"}
        },
        {
            "question": "蔚来 2024年12月的销量",
            "expected": {"start_date": "2024-12-01", "end_date": "2024-12-31", "time_granularity": "month"}
        },
        
        # 季度
        {
            "question": "理想 2024年第一季度销量",
            "expected": {"start_date": "2024-01-01", "end_date": "2024-03-31", "time_granularity": "month"}
        },
        {
            "question": "小鹏 2024年第三季度的表现",
            "expected": {"start_date": "2024-07-01", "end_date": "2024-09-30", "time_granularity": "month"}
        },
        
        # 半年
        {
            "question": "宝马 2024年上半年销量",
            "expected": {"start_date": "2024-01-01", "end_date": "2024-06-30", "time_granularity": "month"}
        },
        {
            "question": "奔驰 2024年下半年的销量情况",
            "expected": {"start_date": "2024-07-01", "end_date": "2024-12-31", "time_granularity": "month"}
        },
        
        # 相对时间
        {
            "question": "智己今年的销量",
            "expected": {"start_date": f"{datetime.now().year}-01-01", "end_date": f"{datetime.now().year}-12-31", "time_granularity": "year"}
        },
        {
            "question": "比亚迪去年销量如何",
            "expected": {"start_date": f"{datetime.now().year-1}-01-01", "end_date": f"{datetime.now().year-1}-12-31", "time_granularity": "year"}
        },
        
        # 时间范围
        {
            "question": "特斯拉 2023-2024年销量对比",
            "expected": {"start_date": "2023-01-01", "end_date": "2024-12-31", "time_granularity": "year"}
        },
        {
            "question": "蔚来 2022到2024年的销量趋势",
            "expected": {"start_date": "2022-01-01", "end_date": "2024-12-31", "time_granularity": "year"}
        },
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected = test_case["expected"]
        
        print(f"\n📋 测试 {i}: {question}")
        
        try:
            # 提取参数
            params = {'user_question': question}
            extracted = module._extract_query_parameters_fallback(params)
            
            # 检查时间相关字段
            actual = {
                "start_date": extracted.get('start_date'),
                "end_date": extracted.get('end_date'),
                "time_granularity": extracted.get('time_granularity')
            }
            
            print(f"   期望: {expected}")
            print(f"   实际: {actual}")
            
            # 验证结果
            if actual == expected:
                print(f"   ✅ 通过")
                success_count += 1
            else:
                print(f"   ❌ 失败")
                # 详细对比
                for key in expected:
                    if actual.get(key) != expected[key]:
                        print(f"      {key}: 期望 '{expected[key]}', 实际 '{actual.get(key)}'")
        
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 总结
    print(f"\n{'='*20} 测试总结 {'='*20}")
    print(f"📊 测试结果: {success_count}/{total_count} 通过")
    print(f"📊 成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有时间范围提取测试通过！")
        print("\n🔧 支持的时间表达方式:")
        print("   ✅ 具体年份: 2024年、2023年等")
        print("   ✅ 具体月份: 2024年3月、12月等")
        print("   ✅ 季度: 第一季度、第三季度等")
        print("   ✅ 半年: 上半年、下半年")
        print("   ✅ 相对时间: 今年、去年")
        print("   ✅ 时间范围: 2023-2024年、2022到2024年")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
        
        # 显示失败的测试
        failed_tests = []
        for i, test_case in enumerate(test_cases, 1):
            try:
                params = {'user_question': test_case["question"]}
                extracted = module._extract_query_parameters_fallback(params)
                actual = {
                    "start_date": extracted.get('start_date'),
                    "end_date": extracted.get('end_date'),
                    "time_granularity": extracted.get('time_granularity')
                }
                if actual != test_case["expected"]:
                    failed_tests.append(f"测试 {i}: {test_case['question']}")
            except:
                failed_tests.append(f"测试 {i}: {test_case['question']} (异常)")
        
        for failed in failed_tests:
            print(f"   ❌ {failed}")

def test_brand_model_extraction():
    """测试品牌和车型提取功能"""
    print("\n\n🚗 品牌和车型提取功能测试")
    print("=" * 50)
    
    module = SalesQueryModule()
    
    test_cases = [
        {
            "question": "智己LS6 2024年销量",
            "expected_brands": ["智己"],
            "expected_models": ["智己LS6"]
        },
        {
            "question": "特斯拉Model Y和Model 3的销量对比",
            "expected_brands": ["特斯拉"],
            "expected_models": ["特斯拉Model Y", "特斯拉Model 3"]
        },
        {
            "question": "蔚来ES6、ES8和ET7的销量",
            "expected_brands": ["蔚来"],
            "expected_models": ["蔚来ES6", "蔚来ES8", "蔚来ET7"]
        },
        {
            "question": "理想ONE和理想L9哪个卖得好",
            "expected_brands": ["理想"],
            "expected_models": ["理想ONE", "理想L9"]
        },
        {
            "question": "小鹏P7和小鹏G9的销量情况",
            "expected_brands": ["小鹏"],
            "expected_models": ["小鹏P7", "小鹏G9"]
        },
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected_brands = test_case["expected_brands"]
        expected_models = test_case["expected_models"]
        
        print(f"\n📋 测试 {i}: {question}")
        
        try:
            params = {'user_question': question}
            extracted = module._extract_query_parameters_fallback(params)
            
            actual_brands = extracted.get('brands', [])
            actual_models = extracted.get('model_names', [])
            
            print(f"   期望品牌: {expected_brands}")
            print(f"   实际品牌: {actual_brands}")
            print(f"   期望车型: {expected_models}")
            print(f"   实际车型: {actual_models}")
            
            # 验证结果（顺序不重要）
            brands_match = set(actual_brands) == set(expected_brands)
            models_match = set(actual_models) == set(expected_models)
            
            if brands_match and models_match:
                print(f"   ✅ 通过")
                success_count += 1
            else:
                print(f"   ❌ 失败")
                if not brands_match:
                    print(f"      品牌不匹配")
                if not models_match:
                    print(f"      车型不匹配")
        
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print(f"\n📊 品牌车型提取测试结果: {success_count}/{total_count} 通过")
    print(f"📊 成功率: {success_count/total_count*100:.1f}%")

def main():
    """主测试函数"""
    print("🚀 销量查询模块 - 参数提取功能全面测试")
    print("=" * 60)
    
    # 测试时间范围提取
    test_time_extraction()
    
    # 测试品牌车型提取
    test_brand_model_extraction()
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

if __name__ == "__main__":
    main()