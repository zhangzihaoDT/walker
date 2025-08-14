#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块与意图解析器集成测试
测试从用户问题到查询结果的完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
from agents.intent_parser import IntentParser
import json

def test_integration_workflow():
    """测试完整的集成工作流程"""
    print("=== 销量查询模块集成测试 ===")
    
    # 初始化模块
    sales_module = SalesQueryModule()
    intent_parser = IntentParser()
    
    # 测试用例
    test_cases = [
        {
            "question": "查询比亚迪品牌的销量数据",
            "expected_intent": "query_only",
            "description": "基本品牌销量查询"
        },
        {
            "question": "北京市纯电动车销量排行榜前5名",
            "expected_intent": "query_only", 
            "description": "地域+燃料类型排行榜查询"
        },
        {
            "question": "2023年豪华品牌销量趋势分析",
            "expected_intent": "data_analysis",
            "description": "时间趋势分析查询"
        },
        {
            "question": "一线城市SUV车型销量对比",
            "expected_intent": "data_analysis",
            "description": "多维度对比分析"
        },
        {
            "question": "广东省插电混动车型销量统计",
            "expected_intent": "query_only",
            "description": "省份+燃料类型查询"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {case['description']} ---")
        print(f"用户问题: {case['question']}")
        
        try:
            # 步骤1: 意图识别
            intent_result = intent_parser.parse_intent(case['question'])
            print(f"识别意图: {intent_result['intent']}")
            print(f"预期意图: {case['expected_intent']}")
            
            # 步骤2: 参数提取
            entities = intent_result.get('entities', {})
            print(f"提取实体: {entities}")
            
            # 步骤3: 构建查询参数
            query_params = build_query_params(case['question'], intent_result)
            print(f"查询参数: {json.dumps(query_params, ensure_ascii=False, indent=2)}")
            
            # 步骤4: 执行查询
            if intent_result['intent'] in ['query_only', 'data_analysis']:
                result = sales_module.execute(query_params)
                print(f"查询状态: {result['success']}")
                
                if result['success']:
                    print(f"结果数量: {len(result['data'])}")
                    print(f"查询总结: {result['summary'][:150]}...")
                    
                    # 显示前2条结果
                    if result['data']:
                        print("前2条结果:")
                        for j, row in enumerate(result['data'][:2]):
                            print(f"  {j+1}. {row}")
                else:
                    print(f"查询失败: {result.get('error', '未知错误')}")
            else:
                print("非查询类意图，跳过查询执行")
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()

def build_query_params(question: str, intent_result: dict) -> dict:
    """根据用户问题和意图结果构建查询参数"""
    params = {
        "query_type": "basic_sales",
        "dimensions": [],
        "filters": {},
        "limit": None
    }
    
    question_lower = question.lower()
    entities = intent_result.get('entities', {})
    
    # 根据问题内容推断查询类型
    if any(word in question_lower for word in ['排行榜', '排名', '前', '名', 'top']):
        params["query_type"] = "ranking"
        # 提取数量限制
        import re
        numbers = re.findall(r'前(\d+)', question)
        if numbers:
            params["limit"] = int(numbers[0])
        else:
            params["limit"] = 10
    elif any(word in question_lower for word in ['趋势', '变化', '走势', '分析']):
        params["query_type"] = "time_trend"
        params["dimensions"] = ["date"]
    elif any(word in question_lower for word in ['对比', '比较']):
        params["query_type"] = "comparison"
    
    # 根据问题内容推断维度
    dimension_keywords = {
        '品牌': 'brand',
        '省': 'province', 
        '市': 'city',
        '车型': 'model_name',
        '燃料': 'fuel_type',
        '车身': 'body_style'
    }
    
    for keyword, dimension in dimension_keywords.items():
        if keyword in question and dimension not in params["dimensions"]:
            params["dimensions"].append(dimension)
    
    # 如果没有明确维度，默认按品牌分组
    if not params["dimensions"] and params["query_type"] != "time_trend":
        params["dimensions"] = ["brand"]
    
    # 根据问题内容推断筛选条件
    filter_keywords = {
        '比亚迪': {'brand': '比亚迪'},
        '特斯拉': {'brand': '特斯拉'},
        '北京': {'province': '北京市'},
        '上海': {'province': '上海市'},
        '广东': {'province': '广东省'},
        '纯电动': {'fuel_type': '纯电动'},
        '插电': {'fuel_type': '插电式混合动力'},
        '混动': {'fuel_type': '插电式混合动力'},
        'suv': {'body_style': 'SUV'},
        '轿车': {'body_style': '轿车'},
        '一线城市': {'city_tier': '一线城市'},
        '豪华品牌': {'is_luxury_brand': True}
    }
    
    for keyword, filter_dict in filter_keywords.items():
        if keyword.lower() in question_lower:
            params["filters"].update(filter_dict)
    
    # 时间范围处理
    import re
    year_match = re.search(r'(\d{4})年', question)
    if year_match:
        year = year_match.group(1)
        params["start_date"] = f"{year}-01-01"
        params["end_date"] = f"{year}-12-31"
    
    return params

def test_parameter_validation():
    """测试参数验证功能"""
    print("\n=== 参数验证测试 ===")
    
    sales_module = SalesQueryModule()
    
    test_params = [
        {
            "name": "有效参数",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["brand", "fuel_type"],
                "filters": {"province": "北京市"},
                "limit": 10
            }
        },
        {
            "name": "无效查询类型",
            "params": {
                "query_type": "invalid_type",
                "dimensions": ["brand"]
            }
        },
        {
            "name": "无效维度",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["invalid_dimension"]
            }
        }
    ]
    
    for test in test_params:
        print(f"\n测试: {test['name']}")
        validation = sales_module.validate_parameters(test['params'])
        print(f"验证结果: {validation}")

def main():
    """主测试函数"""
    print("销量查询模块集成测试")
    print("=" * 60)
    
    # 运行集成测试
    test_integration_workflow()
    
    # 运行参数验证测试
    test_parameter_validation()
    
    print("\n=== 集成测试完成 ===")

if __name__ == "__main__":
    main()