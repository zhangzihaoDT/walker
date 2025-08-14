#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块演示脚本

展示销量查询模块的核心功能，包括：
1. 品牌销量查询
2. 时间趋势分析
3. 地区销量对比
4. 燃料类型分析
"""

import sys
from pathlib import Path
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.module_executor import get_module_executor

def load_sales_query_config():
    """加载销量查询模块配置"""
    config_file = project_root / "modules" / "analysis_config.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    for module in config['modules']:
        if module['module_id'] == 'sales_query':
            return module
    
    raise ValueError("未找到sales_query模块配置")

def demo_brand_query():
    """演示品牌销量查询"""
    print("\n=== 品牌销量查询演示 ===")
    
    module_executor = get_module_executor()
    config = load_sales_query_config()
    
    test_questions = [
        "比亚迪的销量如何？",
        "特斯拉和蔚来的销量对比",
        "销量前5名的品牌"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        
        params = {
            "data_source": "data/乘用车上险量_0723.parquet",
            "user_question": question
        }
        
        result = module_executor.execute_module(
            module_id='sales_query',
            parameters=params,
            module_config=config
        )
        
        if result.get('success', False):
            data = result.get('data', [])
            summary = result.get('summary', '')
            
            print(f"✅ 查询成功")
            print(f"摘要: {summary}")
            
            if data:
                print("前3条结果:")
                for i, record in enumerate(data[:3], 1):
                    if 'brand' in record and 'total_sales' in record:
                        print(f"  {i}. {record['brand']}: {record['total_sales']:,} 辆")
                    else:
                        print(f"  {i}. {record}")
        else:
            print(f"❌ 查询失败: {result.get('error', '未知错误')}")

def demo_time_trend():
    """演示时间趋势查询"""
    print("\n=== 时间趋势查询演示 ===")
    
    module_executor = get_module_executor()
    config = load_sales_query_config()
    
    question = "2024年的销量趋势"
    print(f"\n问题: {question}")
    
    params = {
        "data_source": "data/乘用车上险量_0723.parquet",
        "user_question": question
    }
    
    result = module_executor.execute_module(
        module_id='sales_query',
        parameters=params,
        module_config=config
    )
    
    if result.get('success', False):
        data = result.get('data', [])
        summary = result.get('summary', '')
        
        print(f"✅ 查询成功")
        print(f"摘要: {summary}")
        
        if data:
            print("时间趋势数据（前5条）:")
            for i, record in enumerate(data[:5], 1):
                print(f"  {i}. {record}")
    else:
        print(f"❌ 查询失败: {result.get('error', '未知错误')}")

def demo_fuel_type_analysis():
    """演示燃料类型分析"""
    print("\n=== 燃料类型分析演示 ===")
    
    module_executor = get_module_executor()
    config = load_sales_query_config()
    
    question = "电动车和汽油车的销量对比"
    print(f"\n问题: {question}")
    
    params = {
        "data_source": "data/乘用车上险量_0723.parquet",
        "user_question": question
    }
    
    result = module_executor.execute_module(
        module_id='sales_query',
        parameters=params,
        module_config=config
    )
    
    if result.get('success', False):
        data = result.get('data', [])
        summary = result.get('summary', '')
        
        print(f"✅ 查询成功")
        print(f"摘要: {summary}")
        
        if data:
            print("燃料类型分析结果:")
            for i, record in enumerate(data, 1):
                if 'fuel_type' in record and 'total_sales' in record:
                    print(f"  {i}. {record['fuel_type']}: {record['total_sales']:,} 辆")
                else:
                    print(f"  {i}. {record}")
    else:
        print(f"❌ 查询失败: {result.get('error', '未知错误')}")

def main():
    """主函数"""
    print("🚗 销量查询模块功能演示")
    print("=" * 50)
    
    # 检查数据文件是否存在
    data_file = project_root / "data" / "乘用车上险量_0723.parquet"
    if not data_file.exists():
        print(f"❌ 数据文件不存在: {data_file}")
        print("请确保数据文件存在后再运行演示")
        return
    
    try:
        # 演示各种查询功能
        demo_brand_query()
        demo_time_trend()
        demo_fuel_type_analysis()
        
        print("\n" + "=" * 50)
        print("✅ 销量查询模块演示完成！")
        print("\n模块功能总结:")
        print("- ✅ 品牌销量查询")
        print("- ✅ 时间趋势分析")
        print("- ✅ 燃料类型分析")
        print("- ✅ 参数自动提取")
        print("- ✅ 查询模板选择")
        print("- ✅ 结果格式化")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()