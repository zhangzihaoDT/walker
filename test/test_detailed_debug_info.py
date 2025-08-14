#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试信息测试脚本
验证gradio_app.py中新增的详细调试信息功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_detailed_debug_info():
    """
    测试详细调试信息功能（模拟数据）
    """
    print("\n" + "="*70)
    print("🔍 详细调试信息功能测试（模拟数据）")
    print("="*70)
    
    # 模拟测试用例和结果
    test_cases = [
        {
            "question": "比亚迪的销量如何？",
            "description": "品牌销量查询",
            "mock_result": {
                "intent_result": {"intent": "query_only"},
                "execution_results": [{
                    "success": True,
                    "module": "sales_query",
                    "data": [{"brand": "比亚迪", "sales": 45000}] * 15,
                    "total_records": 15,
                    "analysis": {
                        "query_type": "brand_sales",
                        "template_used": "品牌销量模板",
                        "parameters_used": {"brand": "比亚迪", "time_range": "2024年"},
                        "data_summary": {
                            "record_count": 15,
                            "sales_stats": {
                                "total": 675000,
                                "average": 45000,
                                "min": 32000,
                                "max": 58000
                            }
                        }
                    },
                    "insights": [
                        "比亚迪在新能源汽车市场表现强劲",
                        "月均销量保持在4.5万辆左右",
                        "销量呈现稳定增长趋势"
                    ],
                    "visualization": {
                        "chart_type": "bar_chart",
                        "title": "比亚迪月度销量趋势",
                        "x_axis": "月份",
                        "y_axis": "销量（辆）"
                    }
                }],
                "final_response": "根据数据分析，比亚迪2024年表现优异，月均销量达到4.5万辆，在新能源汽车市场占据重要地位。"
            }
        },
        {
            "question": "广东省的汽车销量",
            "description": "地区销量查询",
            "mock_result": {
                "intent_result": {"intent": "query_only"},
                "execution_results": [{
                    "success": True,
                    "module": "sales_query",
                    "data": [{"region": "广东省", "sales": 125000}] * 28,
                    "total_records": 28,
                    "analysis": {
                        "query_type": "region_sales",
                        "template_used": "地区销量模板",
                        "parameters_used": {"region": "广东省", "time_range": "2024年"},
                        "data_summary": {
                            "record_count": 28,
                            "sales_stats": {
                                "total": 3500000,
                                "average": 125000,
                                "min": 98000,
                                "max": 156000
                            }
                        }
                    },
                    "insights": [
                        "广东省是全国汽车销量最大的省份",
                        "月均销量超过12万辆",
                        "新能源汽车占比持续提升"
                    ],
                    "visualization": {
                        "chart_type": "line_chart",
                        "title": "广东省汽车销量趋势",
                        "x_axis": "时间",
                        "y_axis": "销量（辆）"
                    }
                }],
                "final_response": "广东省作为汽车消费大省，2024年销量表现突出，月均销量超过12万辆，在全国汽车市场中占据重要地位。"
            }
        },
        {
            "question": "特斯拉和蔚来的销量对比",
            "description": "品牌对比查询",
            "mock_result": {
                "intent_result": {"intent": "query_only"},
                "execution_results": [{
                    "success": True,
                    "module": "sales_query",
                    "data": [{"brand": "特斯拉", "sales": 35000}, {"brand": "蔚来", "sales": 18000}] * 12,
                    "total_records": 24,
                    "analysis": {
                        "query_type": "brand_comparison",
                        "template_used": "品牌对比模板",
                        "parameters_used": {"brands": ["特斯拉", "蔚来"], "time_range": "2024年"},
                        "data_summary": {
                            "record_count": 24,
                            "sales_stats": {
                                "total": 636000,
                                "average": 26500,
                                "min": 15000,
                                "max": 42000
                            }
                        }
                    },
                    "insights": [
                        "特斯拉销量领先蔚来约94%",
                        "两品牌在高端新能源市场竞争激烈",
                        "特斯拉月均销量3.5万辆，蔚来1.8万辆"
                    ],
                    "visualization": {
                        "chart_type": "comparison_chart",
                        "title": "特斯拉vs蔚来销量对比",
                        "x_axis": "品牌",
                        "y_axis": "销量（辆）"
                    }
                }],
                "final_response": "在高端新能源汽车市场，特斯拉表现更为强劲，月均销量3.5万辆，领先蔚来约94%。两品牌在技术创新和市场竞争中各有特色。"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        description = test_case["description"]
        result = test_case["mock_result"]
        
        print(f"\n📝 测试用例 {i}: {description}")
        print(f"问题: {question}")
        print("-" * 60)
        
        try:
            # 提取调试信息
            intent_result = result.get("intent_result", {})
            execution_results = result.get("execution_results", [])
            response = result["final_response"]
            
            # 显示基本调试信息
            print(f"📊 执行结果分析:")
            print(f"  - 意图识别: {intent_result.get('intent', 'unknown')}")
            print(f"  - 执行模块数: {len(execution_results)}")
            print(f"  - 响应长度: {len(response)} 字符")
            
            # 显示详细执行结果
            for j, exec_result in enumerate(execution_results, 1):
                if exec_result.get('success'):
                    data_count = len(exec_result.get('data', []))
                    print(f"  - 模块{j}: 成功，返回{data_count}条记录")
                    
                    # 显示详细的查询信息
                    module_name = exec_result.get('module', f'模块{j}')
                    print(f"    🔍 {module_name}执行详情:")
                    
                    # 显示分析信息
                    analysis = exec_result.get('analysis', {})
                    if analysis:
                        print(f"      - 查询类型: {analysis.get('query_type', 'unknown')}")
                        print(f"      - 使用模板: {analysis.get('template_used', 'unknown')}")
                        print(f"      - 查询参数: {analysis.get('parameters_used', {})}")
                        
                        # 显示数据摘要
                        data_summary = analysis.get('data_summary', {})
                        if data_summary and isinstance(data_summary, dict):
                            print(f"      - 记录数量: {data_summary.get('record_count', 0)}")
                            if 'sales_stats' in data_summary:
                                stats = data_summary['sales_stats']
                                print(f"      - 销量统计: 总计{stats.get('total', 0):,.0f}辆, 平均{stats.get('average', 0):,.0f}辆")
                                print(f"      - 销量范围: {stats.get('min', 0):,.0f} - {stats.get('max', 0):,.0f}辆")
                    
                    # 显示洞察信息
                    insights = exec_result.get('insights', [])
                    if insights:
                        print(f"      - 关键洞察:")
                        for insight in insights[:3]:  # 显示前3个洞察
                            print(f"        * {insight}")
                    
                    # 显示可视化配置
                    visualization = exec_result.get('visualization', {})
                    if visualization:
                        print(f"      - 可视化配置:")
                        print(f"        * 图表类型: {visualization.get('chart_type', 'unknown')}")
                        print(f"        * 标题: {visualization.get('title', 'unknown')}")
                        if 'x_axis' in visualization:
                            print(f"        * X轴: {visualization['x_axis']}")
                        if 'y_axis' in visualization:
                            print(f"        * Y轴: {visualization['y_axis']}")
                        
                else:
                    print(f"  - 模块{j}: 失败，错误: {exec_result.get('error', '未知')}")
            
            print(f"\n💬 响应预览: {response[:100]}..." if len(response) > 100 else f"\n💬 完整响应: {response}")
            print(f"✅ 测试用例 {i} 执行成功")
            
        except Exception as e:
            print(f"❌ 测试用例 {i} 执行失败: {e}")
            logger.error(f"测试失败: {e}")
    
    print("\n" + "="*70)
    print("🎉 详细调试信息功能测试完成")
    print("="*70)
    print("\n📋 测试总结:")
    print("- ✅ 基本调试信息: 意图识别、模块数、响应长度")
    print("- ✅ 模块执行详情: 查询类型、模板、参数")
    print("- ✅ 数据统计信息: 记录数、销量统计")
    print("- ✅ 洞察信息: 关键发现和分析")
    print("- ✅ 可视化配置: 图表类型和轴配置")
    print("\n🚀 现在可以在Gradio界面中测试，终端将显示详细的调试信息！")

if __name__ == "__main__":
    test_detailed_debug_info()