#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块测试脚本
测试各种查询场景和参数组合
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
import json

def test_basic_sales_query():
    """测试基本销量查询"""
    print("\n=== 测试基本销量查询 ===")
    
    module = SalesQueryModule()
    
    # 测试参数
    params = {
        "query_type": "basic_sales",
        "dimensions": ["brand"],
        "filters": {},
        "limit": 10
    }
    
    try:
        result = module.execute(params)
        print(f"执行状态: {result['success']}")
        print(f"模块名称: {result['module']}")
        
        if result['success'] and result['data']:
            print(f"查询结果数量: {len(result['data'])}")
            print("前3条结果:")
            for i, row in enumerate(result['data'][:3]):
                print(f"  {i+1}. {row}")
        
        print(f"总结: {result['summary'][:100]}...")
        
    except Exception as e:
        print(f"测试失败: {e}")

def test_time_trend_query():
    """测试时间趋势查询"""
    print("\n=== 测试时间趋势查询 ===")
    
    module = SalesQueryModule()
    
    params = {
        "query_type": "time_trend",
        "dimensions": ["date"],
        "filters": {"brand": "比亚迪"},
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    
    try:
        result = module.execute(params)
        print(f"执行状态: {result['success']}")
        print(f"模块名称: {result['module']}")
        
        if result['success'] and result['data']:
            print(f"查询结果数量: {len(result['data'])}")
            print("前3条结果:")
            for i, row in enumerate(result['data'][:3]):
                print(f"  {i+1}. {row}")
        
        print(f"总结: {result['summary'][:100]}...")
        
    except Exception as e:
        print(f"测试失败: {e}")

def test_ranking_query():
    """测试排行榜查询"""
    print("\n=== 测试排行榜查询 ===")
    
    module = SalesQueryModule()
    
    params = {
        "query_type": "ranking",
        "dimensions": ["brand"],
        "filters": {"fuel_type": "纯电动"},
        "limit": 5
    }
    
    try:
        result = module.execute(params)
        print(f"执行状态: {result['success']}")
        print(f"模块名称: {result['module']}")
        
        if result['success'] and result['data']:
            print(f"查询结果数量: {len(result['data'])}")
            print("排行榜结果:")
            for i, row in enumerate(result['data']):
                print(f"  第{i+1}名: {row}")
        
        print(f"总结: {result['summary'][:100]}...")
        
    except Exception as e:
        print(f"测试失败: {e}")

def test_multi_dimension_query():
    """测试多维度查询"""
    print("\n=== 测试多维度查询 ===")
    
    module = SalesQueryModule()
    
    params = {
        "query_type": "basic_sales",
        "dimensions": ["brand", "fuel_type", "province"],
        "filters": {"city_tier": "一线城市"},
        "limit": 10
    }
    
    try:
        result = module.execute(params)
        print(f"执行状态: {result['success']}")
        print(f"模块名称: {result['module']}")
        
        if result['success'] and result['data']:
            print(f"查询结果数量: {len(result['data'])}")
            print("前3条结果:")
            for i, row in enumerate(result['data'][:3]):
                print(f"  {i+1}. {row}")
        
        print(f"总结: {result['summary'][:100]}...")
        
    except Exception as e:
        print(f"测试失败: {e}")

def test_parameter_parsing():
    """测试参数解析功能"""
    print("\n=== 测试参数解析功能 ===")
    
    module = SalesQueryModule()
    
    # 模拟从intent_parser解析出的参数
    test_cases = [
        {
            "user_question": "查询比亚迪品牌的销量",
            "parsed_params": {
                "entities": {"brand": "比亚迪"},
                "intent": "query_sales",
                "query_type": "basic_sales"
            }
        },
        {
            "user_question": "北京市纯电动车销量排行榜前10名",
            "parsed_params": {
                "entities": {"province": "北京市", "fuel_type": "纯电动"},
                "intent": "query_ranking",
                "query_type": "ranking",
                "limit": 10
            }
        },
        {
            "user_question": "2023年豪华品牌销量趋势",
            "parsed_params": {
                "entities": {"is_luxury_brand": True, "year": 2023},
                "intent": "query_trend",
                "query_type": "time_trend"
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['user_question']}")
        try:
            parsed_params = module._parse_query_params(case['parsed_params'])
            print(f"解析结果: {json.dumps(parsed_params, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"解析失败: {e}")

def main():
    """主测试函数"""
    print("销量查询模块功能测试")
    print("=" * 50)
    
    # 运行各项测试
    test_parameter_parsing()
    test_basic_sales_query()
    test_time_trend_query()
    test_ranking_query()
    test_multi_dimension_query()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()