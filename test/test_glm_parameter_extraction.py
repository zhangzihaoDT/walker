#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GLM智能参数提取功能

验证新的GLM参数提取是否能正确识别：
1. 时间范围（解决终端输出中的时间过滤问题）
2. 车型信息（提升通用性）
3. 品牌信息
4. 其他查询参数
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.sales_query_module import SalesQueryModule
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_glm_parameter_extraction():
    """测试GLM智能参数提取功能"""
    print("🧪 测试GLM智能参数提取功能")
    print("=" * 50)
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 测试用例 - 这些是终端输出中出现问题的查询
    test_cases = [
        {
            "question": "比亚迪 2024 年销量？",
            "expected": {
                "brands": ["比亚迪"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        },
        {
            "question": "智己 2024 年销量？", 
            "expected": {
                "brands": ["智己"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        },
        {
            "question": "智己LS6 2024年的销量如何？",
            "expected": {
                "brands": ["智己"],
                "model_names": ["智己LS6"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        },
        {
            "question": "特斯拉Model Y今年销量怎么样？",
            "expected": {
                "brands": ["特斯拉"],
                "model_names": ["特斯拉Model Y"]
            }
        },
        {
            "question": "蔚来ES6和理想ONE 2023年销量对比",
            "expected": {
                "brands": ["蔚来", "理想"],
                "model_names": ["蔚来ES6", "理想ONE"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        },
        {
            "question": "新能源汽车前10名品牌销量",
            "expected": {
                "fuel_types": ["纯电动", "插电式混合动力"],
                "limit": 10
            }
        },
        {
            "question": "北京市纯电动汽车销量",
            "expected": {
                "provinces": ["北京市"],
                "fuel_types": ["纯电动"]
            }
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['question']}")
        
        try:
            # 提取参数
            params = {'user_question': test_case['question']}
            extracted = module._extract_query_parameters(params)
            
            print(f"✅ 提取结果:")
            for key, value in extracted.items():
                if value:  # 只显示非空值
                    print(f"   {key}: {value}")
            
            # 验证关键参数
            expected = test_case['expected']
            is_correct = True
            
            for key, expected_value in expected.items():
                actual_value = extracted.get(key)
                if key in ['brands', 'model_names', 'fuel_types']:
                    # 对于列表类型，检查是否包含期望的值
                    if not all(item in actual_value for item in expected_value):
                        print(f"❌ {key} 不匹配: 期望 {expected_value}, 实际 {actual_value}")
                        is_correct = False
                else:
                    # 对于其他类型，直接比较
                    if actual_value != expected_value:
                        print(f"❌ {key} 不匹配: 期望 {expected_value}, 实际 {actual_value}")
                        is_correct = False
            
            if is_correct:
                print(f"✅ 测试通过")
                success_count += 1
            else:
                print(f"❌ 测试失败")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n📊 测试总结:")
    print(f"   总测试数: {total_count}")
    print(f"   成功数: {success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有测试通过！GLM智能参数提取功能正常工作。")
    else:
        print("⚠️ 部分测试失败，需要进一步优化。")
    
    return success_count == total_count

def test_fallback_method():
    """测试备用方法是否正常工作"""
    print("\n🔄 测试备用参数提取方法")
    print("=" * 30)
    
    module = SalesQueryModule()
    
    test_question = "智己LS6 2024年销量"
    result = module._extract_query_parameters_fallback(test_question)
    
    print(f"问题: {test_question}")
    print(f"备用方法结果: {result}")
    
    # 验证备用方法是否正确识别了基本信息
    expected_brand = "智己" in result.get('brands', [])
    expected_model = "智己LS6" in result.get('model_names', [])
    expected_time = result.get('start_date') == '2024-01-01'
    
    if expected_brand and expected_model and expected_time:
        print("✅ 备用方法工作正常")
        return True
    else:
        print("❌ 备用方法存在问题")
        return False

if __name__ == "__main__":
    print("🚀 GLM智能参数提取测试")
    print("=" * 60)
    
    # 测试GLM智能提取
    glm_success = test_glm_parameter_extraction()
    
    # 测试备用方法
    fallback_success = test_fallback_method()
    
    print("\n🏁 最终结果:")
    if glm_success and fallback_success:
        print("✅ 所有功能测试通过，参数提取系统已优化完成！")
        print("\n🔧 主要改进:")
        print("   1. 使用GLM进行智能参数识别，提升通用性")
        print("   2. 改进时间范围识别，支持多种表达方式")
        print("   3. 增强车型识别能力，支持更多品牌")
        print("   4. 保留备用方法，确保系统稳定性")
    else:
        print("❌ 部分功能存在问题，需要进一步调试")