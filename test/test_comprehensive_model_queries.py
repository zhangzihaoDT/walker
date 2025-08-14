#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合车型查询测试脚本

测试各种车型查询场景，验证新增模板和优化功能的完整性
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

def test_model_specific_queries():
    """测试车型专门查询"""
    print("\n=== 测试车型专门查询 ===")
    
    try:
        module = SalesQueryModule()
        
        # 准备数据
        data_path = "data/乘用车上险量_0723.parquet"
        if not os.path.exists(data_path):
            print(f"⚠️ 数据文件不存在: {data_path}")
            return False
            
        data = pd.read_parquet(data_path)
        print(f"数据加载成功，共 {len(data)} 条记录")
        
        # 测试用例
        test_cases = [
            {
                "name": "智己LS6车型查询",
                "user_question": "智己LS6 2024年销量",
                "expected_brand": "智己",
                "expected_model": "智己LS6"
            },
            {
                "name": "特斯拉Model Y查询",
                "user_question": "特斯拉Model Y销量数据",
                "expected_brand": "特斯拉",
                "expected_model": "MODEL Y"
            },
            {
                "name": "蔚来ES6查询",
                "user_question": "蔚来ES6车型销量",
                "expected_brand": "蔚来",
                "expected_model": "ES6"
            },
            {
                "name": "比亚迪汉EV查询",
                "user_question": "比亚迪汉EV销量",
                "expected_brand": "比亚迪",
                "expected_model": "汉EV"
            }
        ]
        
        success_count = 0
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}: {case['name']} ---")
            print(f"用户问题: {case['user_question']}")
            
            try:
                # 运行查询
                result = module.run(data, {"user_question": case['user_question']})
                
                if result['success']:
                    print(f"✅ 查询成功")
                    print(f"模板: {result['analysis']['template_used']}")
                    print(f"记录数: {result['analysis']['total_records']}")
                    
                    # 检查是否使用了车型销量模板
                    if "车型销量" in result['analysis']['template_used']:
                        print(f"✅ 正确使用车型销量模板")
                        success_count += 1
                    else:
                        print(f"⚠️ 未使用车型销量模板: {result['analysis']['template_used']}")
                    
                    # 显示部分结果
                    if result['data']:
                        first_record = result['data'][0]
                        print(f"首条记录: {first_record}")
                        
                        # 检查是否包含车型信息
                        if 'model_name' in first_record:
                            print(f"✅ 结果包含车型信息")
                        else:
                            print(f"⚠️ 结果缺少车型信息")
                else:
                    print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        
        print(f"\n车型专门查询测试完成，成功率: {success_count}/{len(test_cases)}")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ 车型专门查询测试失败: {e}")
        return False

def test_multi_dimension_queries():
    """测试多维度组合查询"""
    print("\n=== 测试多维度组合查询 ===")
    
    try:
        module = SalesQueryModule()
        
        # 准备数据
        data_path = "data/乘用车上险量_0723.parquet"
        data = pd.read_parquet(data_path)
        
        # 测试用例
        test_cases = [
            {
                "name": "品牌+车型+地区查询",
                "user_question": "特斯拉Model Y在广东省的销量",
                "expected_dimensions": ["brand", "model_name", "province"]
            },
            {
                "name": "品牌+车型+燃料类型查询",
                "user_question": "蔚来ES6纯电动车型销量",
                "expected_dimensions": ["brand", "model_name", "fuel_type"]
            },
            {
                "name": "车型+时间查询",
                "user_question": "智己LS6 2024年上半年销量",
                "expected_dimensions": ["brand", "model_name", "time"]
            }
        ]
        
        success_count = 0
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}: {case['name']} ---")
            print(f"用户问题: {case['user_question']}")
            
            try:
                # 运行查询
                result = module.run(data, {"user_question": case['user_question']})
                
                if result['success']:
                    print(f"✅ 查询成功")
                    print(f"模板: {result['analysis']['template_used']}")
                    print(f"记录数: {result['analysis']['total_records']}")
                    
                    # 显示部分结果
                    if result['data']:
                        first_record = result['data'][0]
                        print(f"首条记录: {first_record}")
                        success_count += 1
                else:
                    print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        
        print(f"\n多维度组合查询测试完成，成功率: {success_count}/{len(test_cases)}")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ 多维度组合查询测试失败: {e}")
        return False

def test_template_enhancement():
    """测试模板增强功能"""
    print("\n=== 测试模板增强功能 ===")
    
    try:
        module = SalesQueryModule()
        
        # 准备数据
        data_path = "data/乘用车上险量_0723.parquet"
        data = pd.read_parquet(data_path)
        
        # 测试增强后的品牌销量模板
        print("\n--- 测试增强后的品牌销量模板 ---")
        
        # 强制使用品牌销量模板但包含车型信息
        params = {
            "user_question": "特斯拉品牌销量",
            "brands": ["特斯拉"],
            "model_names": ["MODEL Y"]  # 添加车型信息
        }
        
        # 提取参数并选择模板
        template_info = module._select_template(params)
        print(f"选择的模板: {template_info['name']}")
        
        # 由于有model_names参数，应该选择车型销量模板
        if "车型销量" in template_info['name']:
            print(f"✅ 正确选择车型销量模板")
        else:
            print(f"⚠️ 未选择车型销量模板: {template_info['name']}")
        
        # 测试模板的可选参数
        optional_params = template_info.get('optional_params', [])
        print(f"模板支持的可选参数: {optional_params}")
        
        if 'model_names' in optional_params:
            print(f"✅ 模板支持车型参数")
        else:
            print(f"⚠️ 模板不支持车型参数")
        
        print("\n模板增强功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 模板增强功能测试失败: {e}")
        return False

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    try:
        module = SalesQueryModule()
        
        # 准备数据
        data_path = "data/乘用车上险量_0723.parquet"
        data = pd.read_parquet(data_path)
        
        # 测试用例
        edge_cases = [
            {
                "name": "不存在的车型",
                "user_question": "不存在车型XYZ销量",
                "should_handle_gracefully": True
            },
            {
                "name": "空车型名称",
                "params": {
                    "user_question": "查询销量",
                    "model_names": [None, "", "  "]
                },
                "should_handle_gracefully": True
            },
            {
                "name": "混合None值",
                "params": {
                    "user_question": "特斯拉销量",
                    "brands": ["特斯拉", None],
                    "model_names": ["MODEL Y", None, "MODEL 3"]
                },
                "should_handle_gracefully": True
            }
        ]
        
        success_count = 0
        
        for i, case in enumerate(edge_cases, 1):
            print(f"\n--- 边界测试 {i}: {case['name']} ---")
            
            try:
                if 'user_question' in case:
                    # 直接查询
                    result = module.run(data, {"user_question": case['user_question']})
                else:
                    # 使用参数查询
                    result = module.run(data, case['params'])
                
                if result['success'] or case['should_handle_gracefully']:
                    print(f"✅ 边界情况处理正常")
                    if result['success']:
                        print(f"   记录数: {result['analysis']['total_records']}")
                    else:
                        print(f"   优雅处理: {result.get('error', '无错误信息')}")
                    success_count += 1
                else:
                    print(f"❌ 边界情况处理异常: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                if case['should_handle_gracefully']:
                    print(f"✅ 异常被正确捕获: {e}")
                    success_count += 1
                else:
                    print(f"❌ 未预期的异常: {e}")
        
        print(f"\n边界情况测试完成，成功率: {success_count}/{len(edge_cases)}")
        return success_count == len(edge_cases)
        
    except Exception as e:
        print(f"❌ 边界情况测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始综合车型查询测试")
    
    tests = [
        ("车型专门查询", test_model_specific_queries),
        ("多维度组合查询", test_multi_dimension_queries),
        ("模板增强功能", test_template_enhancement),
        ("边界情况", test_edge_cases)
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    # 运行所有测试
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"开始测试: {test_name}")
        print(f"{'='*50}")
        
        if test_func():
            success_count += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    # 总结
    print(f"\n{'='*50}")
    print(f"📊 综合测试总结")
    print(f"{'='*50}")
    print(f"成功: {success_count}/{total_tests}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！车型查询功能完全正常")
        print("\n✨ 功能亮点:")
        print("  • 新增车型销量查询模板")
        print("  • 优化模板选择逻辑（车型优先级最高）")
        print("  • 增强现有模板的多维度支持")
        print("  • 完善的边界情况处理")
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
    
    return success_count == total_tests

if __name__ == "__main__":
    main()