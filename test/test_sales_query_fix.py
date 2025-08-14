#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试销量查询修复效果

验证修复后的系统是否能正确处理：
1. 比亚迪 2024 年销量？
2. 智己 2024 年销量？
3. 智己LS6 2024年销量？

对比修复前后的结果
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

def load_test_data():
    """加载测试数据"""
    data_path = project_root / "data" / "乘用车上险量_0723.parquet"
    if not data_path.exists():
        print(f"❌ 数据文件不存在: {data_path}")
        return None
    
    df = pd.read_parquet(data_path)
    print(f"✅ 数据加载成功，形状: {df.shape}")
    return df

def test_query_with_comparison(data, question, expected_description):
    """测试查询并显示详细结果"""
    print(f"\n📋 测试查询: {question}")
    print(f"期望: {expected_description}")
    print("-" * 50)
    
    try:
        # 初始化模块
        module = SalesQueryModule()
        
        # 准备参数
        params = {
            'user_question': question,
            'data_source': 'data/乘用车上险量_0723.parquet'
        }
        
        # 提取参数
        extracted_params = module._extract_query_parameters(params)
        print(f"🔍 提取的参数:")
        for key, value in extracted_params.items():
            if value:  # 只显示非空值
                print(f"   {key}: {value}")
        
        # 执行查询
        result = module.run(data, params)
        
        # 显示结果
        if result and 'data' in result and result['data']:
            data_records = result['data']
            print(f"\n✅ 查询成功，返回 {len(data_records)} 条记录")
            
            # 显示销量数据
            for record in data_records:
                if 'total_sales' in record:
                    sales = record['total_sales']
                    brand = record.get('brand', '未知品牌')
                    model = record.get('model_name', '')
                    if model:
                        print(f"   📊 {brand} {model}: {sales:,} 辆")
                    else:
                        print(f"   📊 {brand}: {sales:,} 辆")
                elif 'sales_volume' in record:
                    sales = record['sales_volume']
                    brand = record.get('brand', '未知品牌')
                    print(f"   📊 {brand}: {sales:,} 辆")
            
            # 显示分析信息
            analysis = result.get('analysis', {})
            if analysis:
                print(f"\n📈 分析信息:")
                print(f"   查询类型: {analysis.get('query_type', 'N/A')}")
                print(f"   使用模板: {analysis.get('template_name', 'N/A')}")
                
                stats = analysis.get('statistics', {})
                if stats:
                    print(f"   统计信息: 总计{stats.get('total_sales', 0):,}辆")
        else:
            print("❌ 查询失败或无结果")
            if 'analysis' in result and 'error' in result['analysis']:
                print(f"   错误: {result['analysis']['error']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return None

def manual_verification(data, brand, year=2024, model_name=None):
    """手动验证查询结果"""
    print(f"\n🔍 手动验证: {brand} {year}年" + (f" {model_name}" if model_name else "") + "销量")
    
    try:
        # 过滤数据
        filtered_data = data[data['brand'] == brand].copy()
        
        # 时间过滤
        filtered_data['date'] = pd.to_datetime(filtered_data['date'])
        year_data = filtered_data[filtered_data['date'].dt.year == year]
        
        if model_name:
            # 车型过滤
            model_data = year_data[year_data['model_name'] == model_name]
            total_sales = model_data['sales_volume'].sum()
            print(f"   手动验证结果: {brand} {model_name} {year}年销量 = {total_sales:,} 辆")
        else:
            # 品牌总销量
            total_sales = year_data['sales_volume'].sum()
            print(f"   手动验证结果: {brand} {year}年销量 = {total_sales:,} 辆")
        
        return total_sales
        
    except Exception as e:
        print(f"   手动验证失败: {e}")
        return None

def main():
    """主测试函数"""
    print("🚀 销量查询修复效果测试")
    print("=" * 60)
    
    # 加载数据
    data = load_test_data()
    if data is None:
        return
    
    # 测试用例
    test_cases = [
        {
            "question": "比亚迪 2024 年销量？",
            "expected": "应该返回比亚迪品牌2024年的总销量",
            "manual_check": {"brand": "比亚迪", "year": 2024}
        },
        {
            "question": "智己 2024 年销量？",
            "expected": "应该返回智己品牌2024年的总销量（不是所有年份）",
            "manual_check": {"brand": "智己", "year": 2024}
        },
        {
            "question": "智己LS6 2024年销量？",
            "expected": "应该返回智己LS6车型2024年的销量（不是品牌总销量）",
            "manual_check": {"brand": "智己", "year": 2024, "model_name": "智己LS6"}
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} 测试用例 {i} {'='*20}")
        
        # 执行查询测试
        result = test_query_with_comparison(
            data, 
            test_case["question"], 
            test_case["expected"]
        )
        
        # 手动验证
        manual_check = test_case["manual_check"]
        manual_result = manual_verification(
            data,
            manual_check["brand"],
            manual_check["year"],
            manual_check.get("model_name")
        )
        
        # 对比结果
        if result and manual_result is not None:
            query_sales = None
            if 'data' in result and result['data']:
                for record in result['data']:
                    if 'total_sales' in record:
                        query_sales = record['total_sales']
                        break
                    elif 'sales_volume' in record:
                        query_sales = record['sales_volume']
                        break
            
            if query_sales is not None:
                if query_sales == manual_result:
                    print(f"✅ 结果一致: {query_sales:,} 辆")
                    results.append(True)
                else:
                    print(f"❌ 结果不一致: 查询={query_sales:,}, 手动={manual_result:,}")
                    results.append(False)
            else:
                print(f"❌ 无法提取查询结果")
                results.append(False)
        else:
            print(f"❌ 测试失败")
            results.append(False)
    
    # 总结
    print(f"\n{'='*20} 测试总结 {'='*20}")
    success_count = sum(results)
    total_count = len(results)
    
    print(f"📊 测试结果: {success_count}/{total_count} 通过")
    print(f"📊 成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！修复成功！")
        print("\n🔧 修复效果:")
        print("   ✅ 时间过滤问题已解决 - 正确识别2024年范围")
        print("   ✅ 车型识别问题已解决 - 能区分品牌和车型查询")
        print("   ✅ 参数提取已优化 - 支持GLM智能识别和备用方法")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
        
        # 显示失败的测试
        for i, (test_case, success) in enumerate(zip(test_cases, results), 1):
            if not success:
                print(f"   ❌ 测试 {i} 失败: {test_case['question']}")

if __name__ == "__main__":
    main()