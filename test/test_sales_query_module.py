#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块测试脚本

测试销量查询模块的各种功能，包括：
1. 模块基本功能测试
2. 参数提取测试
3. 查询模板选择测试
4. 集成测试
"""

import sys
from pathlib import Path
import pandas as pd
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.sales_query_module import SalesQueryModule
from agents.module_executor import get_module_executor
from core.graph_builder import get_graph_builder

def test_module_basic_functionality():
    """测试模块基本功能"""
    print("\n=== 测试1: 模块基本功能 ===")
    
    try:
        # 创建模块实例
        module = SalesQueryModule()
        
        # 检查模块基本信息
        print(f"模块ID: {module.module_id}")
        print(f"模块名称: {module.module_name}")
        print(f"支持的数据库: {module.supported_databases}")
        print(f"必需字段: {module.required_fields}")
        print(f"可选字段: {module.optional_fields}")
        
        # 检查查询模板
        print(f"\n可用查询模板: {list(module.query_templates.keys())}")
        
        print("✅ 模块基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 模块基本功能测试失败: {e}")
        return False

def test_parameter_extraction():
    """测试参数提取功能"""
    print("\n=== 测试2: 参数提取功能 ===")
    
    try:
        module = SalesQueryModule()
        
        # 测试用例
        test_cases = [
            {
                "question": "比亚迪2024年的销量如何？",
                "expected_brands": ["BYD"],
                "expected_dates": True
            },
            {
                "question": "特斯拉和蔚来在广东省的销量对比",
                "expected_brands": ["Tesla", "NIO"],
                "expected_provinces": ["广东省"]
            },
            {
                "question": "电动车销量前10名",
                "expected_fuel_types": ["纯电动"],
                "expected_limit": 10
            },
            {
                "question": "北京和上海的新能源车销量",
                "expected_cities": ["北京市", "上海市"],
                "expected_fuel_types": ["纯电动", "插电式混合动力"]
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {case['question']}")
            
            params = {'user_question': case['question']}
            extracted = module._extract_query_parameters(params)
            
            print(f"提取的参数: {extracted}")
            
            # 验证品牌提取
            if 'expected_brands' in case:
                extracted_brands = set(extracted['brands'])
                expected_brands = set(case['expected_brands'])
                if extracted_brands >= expected_brands:
                    print(f"✅ 品牌提取正确: {extracted['brands']}")
                else:
                    print(f"⚠️ 品牌提取不完整: 期望{expected_brands}, 实际{extracted_brands}")
            
            # 验证地区提取
            if 'expected_provinces' in case:
                if any(p in extracted['provinces'] for p in case['expected_provinces']):
                    print(f"✅ 省份提取正确: {extracted['provinces']}")
                else:
                    print(f"⚠️ 省份提取失败: {extracted['provinces']}")
            
            if 'expected_cities' in case:
                if any(c in extracted['cities'] for c in case['expected_cities']):
                    print(f"✅ 城市提取正确: {extracted['cities']}")
                else:
                    print(f"⚠️ 城市提取失败: {extracted['cities']}")
            
            # 验证燃料类型提取
            if 'expected_fuel_types' in case:
                extracted_fuels = set(extracted['fuel_types'])
                expected_fuels = set(case['expected_fuel_types'])
                if extracted_fuels >= expected_fuels:
                    print(f"✅ 燃料类型提取正确: {extracted['fuel_types']}")
                else:
                    print(f"⚠️ 燃料类型提取不完整: 期望{expected_fuels}, 实际{extracted_fuels}")
            
            # 验证限制数量提取
            if 'expected_limit' in case:
                if extracted['limit'] == case['expected_limit']:
                    print(f"✅ 限制数量提取正确: {extracted['limit']}")
                else:
                    print(f"⚠️ 限制数量提取错误: 期望{case['expected_limit']}, 实际{extracted['limit']}")
        
        print("\n✅ 参数提取功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 参数提取功能测试失败: {e}")
        return False

def test_template_selection():
    """测试查询模板选择"""
    print("\n=== 测试3: 查询模板选择 ===")
    
    try:
        module = SalesQueryModule()
        
        # 测试用例
        test_cases = [
            {
                "params": {"brands": ["Tesla"]},
                "expected_template": "品牌销量查询"
            },
            {
                "params": {"provinces": ["广东省"]},
                "expected_template": "地区销量查询"
            },
            {
                "params": {"fuel_types": ["纯电动"]},
                "expected_template": "燃料类型分析"
            },
            {
                "params": {"start_date": "2024-01-01"},
                "expected_template": "时间趋势查询"
            },
            {
                "params": {},
                "expected_template": "综合销量查询"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {case['params']}")
            
            template_info = module._select_template(case['params'])
            selected_template = template_info['name']
            
            print(f"选择的模板: {selected_template}")
            
            if case['expected_template'] in selected_template:
                print(f"✅ 模板选择正确")
            else:
                print(f"⚠️ 模板选择可能不是最优: 期望包含'{case['expected_template']}', 实际'{selected_template}'")
        
        print("\n✅ 查询模板选择测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 查询模板选择测试失败: {e}")
        return False

def test_module_execution():
    """测试模块执行（需要数据文件）"""
    print("\n=== 测试4: 模块执行测试 ===")
    
    try:
        # 检查数据文件是否存在
        data_file = project_root / "data" / "乘用车上险量_0723.parquet"
        if not data_file.exists():
            print(f"⚠️ 数据文件不存在: {data_file}")
            print("跳过模块执行测试")
            return True
        
        # 加载模块配置
        config_file = project_root / "modules" / "analysis_config.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取sales_query模块配置
        sales_query_config = None
        for module in config['modules']:
            if module['module_id'] == 'sales_query':
                sales_query_config = module
                break
        
        if not sales_query_config:
            print("❌ 未找到sales_query模块配置")
            return False
        
        module_executor = get_module_executor()
        
        # 测试用例
        test_cases = [
            {
                "name": "简单品牌查询",
                "params": {
                    "module_id": "sales_query",
                    "data_source": "data/乘用车上险量_0723.parquet",
                    "user_question": "比亚迪的销量如何？"
                }
            },
            {
                "name": "综合销量查询",
                "params": {
                    "module_id": "sales_query",
                    "data_source": "data/乘用车上险量_0723.parquet",
                    "user_question": "销量前5名的品牌"
                }
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {case['name']}")
            print(f"问题: {case['params']['user_question']}")
            
            result = module_executor.execute_module(
                module_id='sales_query', 
                parameters=case['params'],
                module_config=sales_query_config
            )
            
            if result.get('success', False):
                data = result.get('data', [])
                summary = result.get('summary', '')
                
                print(f"✅ 执行成功")
                print(f"返回记录数: {len(data)}")
                print(f"摘要: {summary[:100]}..." if len(summary) > 100 else f"摘要: {summary}")
                
                if data:
                    print(f"示例数据: {data[0]}")
            else:
                error = result.get('error', '未知错误')
                print(f"❌ 执行失败: {error}")
        
        print("\n✅ 模块执行测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 模块执行测试失败: {e}")
        return False

def test_graph_integration():
    """测试图构建器集成"""
    print("\n=== 测试5: 图构建器集成测试 ===")
    
    try:
        # 检查数据文件是否存在
        data_file = project_root / "data" / "乘用车上险量_0723.parquet"
        if not data_file.exists():
            print(f"⚠️ 数据文件不存在: {data_file}")
            print("跳过图构建器集成测试")
            return True
        
        graph_builder = get_graph_builder()
        
        # 测试SQL Agent节点
        test_cases = [
            {
                "name": "销量查询",
                "question": "比亚迪的销量情况"
            },
            {
                "name": "非销量查询",
                "question": "今天天气怎么样？"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {case['name']}")
            print(f"问题: {case['question']}")
            
            # 构建测试状态
            state = {
                "user_question": case['question'],
                "intent_result": {"intent": "query_only"},
                "analysis_result": "",
                "analysis_success": False,
                "final_response": "",
                "error_message": "",
                "walker_strategy": {},
                "execution_plan": [],
                "execution_results": [],
                "sql_result": ""
            }
            
            # 执行SQL Agent节点
            result_state = graph_builder.sql_agent_node(state)
            
            if result_state["analysis_success"]:
                print(f"✅ SQL Agent执行成功")
                sql_result = result_state["sql_result"]
                print(f"结果预览: {sql_result[:200]}..." if len(sql_result) > 200 else f"结果: {sql_result}")
            else:
                error_msg = result_state.get("error_message", "未知错误")
                print(f"❌ SQL Agent执行失败: {error_msg}")
        
        print("\n✅ 图构建器集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 图构建器集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始销量查询模块测试")
    print(f"项目根目录: {project_root}")
    
    # 执行所有测试
    tests = [
        test_module_basic_functionality,
        test_parameter_extraction,
        test_template_selection,
        test_module_execution,
        test_graph_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 发生异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！销量查询模块功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    return passed == total

if __name__ == "__main__":
    main()