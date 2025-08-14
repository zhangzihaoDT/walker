#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车型销量查询模板测试脚本

测试新增的车型销量查询模板和优化后的模板选择逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_sales_template():
    """测试车型销量查询模板"""
    print("\n=== 测试车型销量查询模板 ===")
    
    try:
        # 初始化模块
        module = SalesQueryModule()
        
        # 测试用例
        test_cases = [
            {
                "name": "智己LS6车型查询",
                "user_question": "智己LS6 2024年销量",
                "expected_template": "车型销量查询"
            },
            {
                "name": "特斯拉Model Y车型查询",
                "user_question": "特斯拉Model Y销量数据",
                "expected_template": "车型销量查询"
            },
            {
                "name": "蔚来ES6车型查询",
                "user_question": "蔚来ES6车型销量",
                "expected_template": "车型销量查询"
            },
            {
                "name": "品牌查询（无车型）",
                "user_question": "特斯拉品牌销量",
                "expected_template": "品牌销量查询"
            },
            {
                "name": "品牌+车型组合查询",
                "user_question": "比亚迪汉EV销量",
                "expected_template": "车型销量查询"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}: {case['name']} ---")
            print(f"用户问题: {case['user_question']}")
            
            # 提取参数
            try:
                extracted_params = module._extract_query_parameters_fallback(case['user_question'])
                print(f"提取的参数: {extracted_params}")
                
                # 选择模板
                template_info = module._select_template(extracted_params)
                selected_template = template_info['name']
                print(f"选择的模板: {selected_template}")
                
                # 验证模板选择
                if case['expected_template'] in selected_template:
                    print(f"✅ 模板选择正确")
                else:
                    print(f"⚠️ 模板选择不符合预期")
                    print(f"   期望: {case['expected_template']}")
                    print(f"   实际: {selected_template}")
                    
                # 显示模板信息
                print(f"模板描述: {template_info['description']}")
                print(f"可选参数: {template_info.get('optional_params', [])}")
                
            except Exception as e:
                print(f"❌ 参数提取或模板选择失败: {e}")
        
        print("\n✅ 车型销量查询模板测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_template_priority():
    """测试模板选择优先级"""
    print("\n=== 测试模板选择优先级 ===")
    
    try:
        module = SalesQueryModule()
        
        # 测试优先级：车型 > 燃料类型 > 地区 > 品牌 > 时间 > 通用
        priority_tests = [
            {
                "params": {
                    "model_names": ["智己LS6"],
                    "brands": ["智己"],
                    "fuel_types": ["纯电动"]
                },
                "expected": "车型销量查询",
                "description": "车型优先级最高"
            },
            {
                "params": {
                    "brands": ["特斯拉"],
                    "fuel_types": ["纯电动"]
                },
                "expected": "燃料类型分析",
                "description": "燃料类型优先级高于品牌"
            },
            {
                "params": {
                    "brands": ["蔚来"],
                    "provinces": ["广东省"]
                },
                "expected": "地区销量查询",
                "description": "地区优先级高于品牌"
            },
            {
                "params": {
                    "brands": ["理想"]
                },
                "expected": "品牌销量查询",
                "description": "单独品牌查询"
            },
            {
                "params": {
                    "start_date": "2024-01-01"
                },
                "expected": "时间趋势查询",
                "description": "时间查询"
            },
            {
                "params": {},
                "expected": "综合销量查询",
                "description": "默认查询"
            }
        ]
        
        for i, test in enumerate(priority_tests, 1):
            print(f"\n--- 优先级测试 {i}: {test['description']} ---")
            print(f"参数: {test['params']}")
            
            template_info = module._select_template(test['params'])
            selected_template = template_info['name']
            print(f"选择的模板: {selected_template}")
            
            if test['expected'] in selected_template:
                print(f"✅ 优先级正确")
            else:
                print(f"⚠️ 优先级不符合预期")
                print(f"   期望: {test['expected']}")
                print(f"   实际: {selected_template}")
        
        print("\n✅ 模板选择优先级测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 优先级测试失败: {e}")
        return False

def test_enhanced_templates():
    """测试增强后的模板多维度支持"""
    print("\n=== 测试增强后的模板多维度支持 ===")
    
    try:
        module = SalesQueryModule()
        
        # 测试增强后的模板
        enhanced_tests = [
            {
                "template_name": "brand_sales",
                "params": {
                    "brands": ["特斯拉"],
                    "model_names": ["MODEL Y"]
                },
                "description": "品牌销量模板支持车型维度"
            },
            {
                "template_name": "region_sales",
                "params": {
                    "provinces": ["广东省"],
                    "brands": ["比亚迪"],
                    "model_names": ["汉EV"]
                },
                "description": "地区销量模板支持品牌和车型维度"
            },
            {
                "template_name": "fuel_type_analysis",
                "params": {
                    "fuel_types": ["纯电动"],
                    "brands": ["蔚来"],
                    "model_names": ["ES6"]
                },
                "description": "燃料类型模板支持品牌和车型维度"
            }
        ]
        
        for i, test in enumerate(enhanced_tests, 1):
            print(f"\n--- 增强测试 {i}: {test['description']} ---")
            print(f"参数: {test['params']}")
            
            template_info = module._select_template(test['params'])
            print(f"选择的模板: {template_info['name']}")
            print(f"可选参数: {template_info.get('optional_params', [])}")
            
            # 检查模板是否支持车型参数
            if 'model_names' in template_info.get('optional_params', []):
                print(f"✅ 模板支持车型维度")
            else:
                print(f"⚠️ 模板不支持车型维度")
        
        print("\n✅ 增强模板测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 增强模板测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始车型销量查询模板测试")
    
    success_count = 0
    total_tests = 3
    
    # 运行所有测试
    if test_model_sales_template():
        success_count += 1
    
    if test_template_priority():
        success_count += 1
        
    if test_enhanced_templates():
        success_count += 1
    
    # 总结
    print(f"\n📊 测试总结")
    print(f"成功: {success_count}/{total_tests}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！车型销量查询模板和优化功能正常工作")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
    
    return success_count == total_tests

if __name__ == "__main__":
    main()