#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块简化测试
不依赖LLM，直接测试模块功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
import json

def test_query_scenarios():
    """测试各种查询场景"""
    print("=== 销量查询模块场景测试 ===")
    
    sales_module = SalesQueryModule()
    
    # 测试场景
    scenarios = [
        {
            "name": "品牌销量查询",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["brand"],
                "filters": {},
                "limit": 5
            },
            "description": "查询各品牌销量排名"
        },
        {
            "name": "地域销量分析",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["province"],
                "filters": {"fuel_type": "纯电动"},
                "limit": 10
            },
            "description": "查询各省份纯电动车销量"
        },
        {
            "name": "燃料类型排行榜",
            "params": {
                "query_type": "ranking",
                "dimensions": ["fuel_type"],
                "filters": {},
                "limit": 5
            },
            "description": "燃料类型销量排行榜"
        },
        {
            "name": "豪华品牌时间趋势",
            "params": {
                "query_type": "time_trend",
                "dimensions": ["date"],
                "filters": {"is_luxury_brand": True},
                "start_date": "2023-01-01",
                "end_date": "2023-06-30"
            },
            "description": "2023年上半年豪华品牌销量趋势"
        },
        {
            "name": "多维度组合查询",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["brand", "fuel_type", "city_tier"],
                "filters": {"province": "广东省"},
                "limit": 8
            },
            "description": "广东省各品牌燃料类型城市层级销量"
        },
        {
            "name": "车身类型对比",
            "params": {
                "query_type": "comparison",
                "dimensions": ["body_style"],
                "filters": {"brand": "比亚迪"},
                "compare_field": "body_style"
            },
            "description": "比亚迪不同车身类型销量对比"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- 场景 {i}: {scenario['name']} ---")
        print(f"描述: {scenario['description']}")
        print(f"参数: {json.dumps(scenario['params'], ensure_ascii=False, indent=2)}")
        
        try:
            # 参数验证
            validation = sales_module.validate_parameters(scenario['params'])
            print(f"参数验证: {validation}")
            
            if validation['valid']:
                # 执行查询
                result = sales_module.execute(scenario['params'])
                print(f"执行状态: {result['success']}")
                
                if result['success']:
                    print(f"结果数量: {len(result['data'])}")
                    print(f"模块名称: {result['module']}")
                    
                    # 显示前3条结果
                    if result['data']:
                        print("前3条结果:")
                        for j, row in enumerate(result['data'][:3]):
                            print(f"  {j+1}. {row}")
                    
                    # 显示分析信息
                    if result.get('analysis'):
                        analysis = result['analysis']
                        print(f"分析统计: 记录数={analysis.get('record_count', 0)}")
                        if 'sales_stats' in analysis:
                            stats = analysis['sales_stats']
                            print(f"销量统计: 总计={stats.get('total', 0):,}, 平均={stats.get('mean', 0):.1f}")
                    
                    # 显示总结
                    print(f"查询总结: {result['summary'][:200]}...")
                    
                    # 显示洞察
                    if result.get('insights'):
                        print("关键洞察:")
                        for insight in result['insights'][:2]:
                            print(f"  - {insight}")
                else:
                    print(f"查询失败: {result.get('error', '未知错误')}")
            else:
                print(f"参数验证失败: {validation['error']}")
                
        except Exception as e:
            print(f"场景测试失败: {e}")
            import traceback
            traceback.print_exc()

def test_sql_generation():
    """测试SQL生成功能"""
    print("\n=== SQL生成测试 ===")
    
    sales_module = SalesQueryModule()
    
    test_cases = [
        {
            "name": "基本查询",
            "query_info": {
                "query_type": "basic_sales",
                "group_by": ["brand"],
                "where_conditions": ["fuel_type = '纯电动'"],
                "order_by": "total_sales DESC",
                "limit": 5
            }
        },
        {
            "name": "时间趋势查询",
            "query_info": {
                "query_type": "time_trend",
                "group_by": ["date"],
                "where_conditions": ["brand = '比亚迪'", "date >= '2023-01-01'"],
                "time_unit": "month"
            }
        },
        {
            "name": "排行榜查询",
            "query_info": {
                "query_type": "ranking",
                "group_by": ["brand"],
                "where_conditions": ["province = '北京市'"],
                "order_by": "total_sales DESC",
                "limit": 10
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        try:
            sql = sales_module._generate_sql(case['query_info'])
            print(f"生成的SQL: {sql}")
        except Exception as e:
            print(f"SQL生成失败: {e}")

def test_parameter_parsing():
    """测试参数解析功能"""
    print("\n=== 参数解析测试 ===")
    
    sales_module = SalesQueryModule()
    
    test_params = [
        {
            "name": "基本参数",
            "params": {
                "query_type": "basic_sales",
                "dimensions": ["brand", "fuel_type"],
                "filters": {"province": "北京市", "city_tier": "一线城市"},
                "limit": 10
            }
        },
        {
            "name": "时间范围参数",
            "params": {
                "query_type": "time_trend",
                "dimensions": "date",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "filters": {"brand": "特斯拉"}
            }
        },
        {
            "name": "排行榜参数",
            "params": {
                "query_type": "ranking",
                "dimensions": ["brand"],
                "filters": {"fuel_type": ["纯电动", "插电式混合动力"]},
                "limit": 5
            }
        }
    ]
    
    for case in test_params:
        print(f"\n{case['name']}:")
        try:
            parsed = sales_module._parse_query_params(case['params'])
            print(f"解析结果: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"参数解析失败: {e}")

def test_module_info():
    """测试模块信息"""
    print("\n=== 模块信息测试 ===")
    
    sales_module = SalesQueryModule()
    
    # 获取模块信息
    info = sales_module.get_module_info()
    print(f"模块信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
    
    # 获取数据需求
    requirements = sales_module.get_data_requirements()
    print(f"数据需求: {json.dumps(requirements, ensure_ascii=False, indent=2)}")
    
    # 检查兼容性（使用基类方法）
    try:
        compatibility = sales_module.check_compatibility("parquet", ["sales_volume", "date", "brand"])
        print(f"兼容性检查: {compatibility}")
    except AttributeError:
        print("兼容性检查: 方法未实现，跳过测试")

def main():
    """主测试函数"""
    print("销量查询模块功能测试")
    print("=" * 60)
    
    # 运行各项测试
    test_module_info()
    test_parameter_parsing()
    test_sql_generation()
    test_query_scenarios()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()